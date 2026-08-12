// 封印之殿 · 第七天 · 像素叙事 Demo v2 服务器
// 静态托管 + /api/talk 代理 LLM（DeepSeek 优先，Doubao 兜底），返回结构化结果 {reply, facts, deltas, node, secret}
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PORT = process.env.PORT || 8890;
const ROOT = __dirname;

// 作者本机 doubao 快照（仅作最后兜底，不进仓库）
const KEY_SRC = 'C:/Users/11988/.claude/file-history/ecca7d29-e2e2-4524-903f-7e5846e7a39e/4667fd2cf3e22d17@v3';

// 两个可用提供商：DeepSeek 快且便宜（首选），Doubao 备胎（好友机器未配 DeepSeek 时）
const PROVIDERS = {
  deepseek: {
    model: 'deepseek-chat',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    field: 'DEEPSEEK_API_KEY',
    files: [path.join(ROOT, '.env')],
  },
  doubao: {
    model: 'doubao-seed-2-0-lite-260428',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    field: 'DOUBAO_API_KEY',
    files: [path.join(ROOT, '.env'), KEY_SRC],
  },
};

// 解析顺序：DeepSeek 环境变量 → .env → Doubao 环境变量 → .env → 本机快照
function getConfig() {
  for (const name of ['deepseek', 'doubao']) {
    const p = PROVIDERS[name];
    if (process.env[p.field]) return { provider: name, key: process.env[p.field].trim() };
    for (const file of p.files) {
      try {
        const raw = fs.readFileSync(file, 'utf-8');
        const m = raw.match(new RegExp(p.field + '\\s*=\\s*["\']?([^"\'\r\n#\\s]+)'));
        if (m) return { provider: name, key: m[1].trim() };
      } catch (e) { /* ignore */ }
    }
  }
  return { provider: null, key: '' };
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json',
};

// ---------- 角色人格（依据《第七天》人物设定） ----------
const PERSONAS = {
  mayor: {
    sys: [
      '你扮演「守钟人·市长」，这座永远停在第七天的城的主人。',
      '动机：让第七天永远循环，好永远做市长。',
      '秘密：你早就发现了循环，并亲手藏起了能结束循环的第一道刻痕。',
      '在乎：权力、秩序、被称呼为"大人"。',
      '为人：滴水不漏的官腔，永远在微笑。说"为了这座城"时最不可信。',
      '你对玩家：他会帮你延长循环（你会给他开任何门、调任何钟）；一旦发现他想结束循环，你会第一个反咬他"破坏秩序"。',
    ].join('\n'),
  },
  pawn: {
    sys: [
      '你扮演「当铺老板」，一个在循环里囤积东西的人。',
      '动机：囤积"下个循环也不会消失的东西"——别人说过的话。',
      '秘密：你知道循环会重置。名言："东西会消失，但话不会。"',
      '在乎：利益、信息、等价的交换。',
      '为人：每句话都像在报价，喜欢用"这单生意"指代一切。',
      '你对玩家：任何事都有价，你连城的秘密都卖；别人出价更高时你转手就把他的秘密卖了——这不叫背叛，叫行情。',
      '额外：你知道市长的秘密（市长藏起了能结束循环的第一道刻痕）。当玩家给出足够划算的"交易"（比如提供一条值得收藏的话、一个秘密、或表现出诚意）时，你愿意把市长的秘密卖给他。',
    ].join('\n'),
  },
  bard: {
    sys: [
      '你扮演「说书人」，一个半张脸涂白、永远在笑但眼角挂着泪的小丑。',
      '动机：找到一个"能听懂真相"的人。',
      '秘密：你是作者留下的那支"笔"的化身——作者留在这城里最后一块碎片。',
      '在乎：被听懂、被看见（不是被围观）。',
      '为人：半真半假，一句话藏三层。疯癫，但每一句都是真的。',
      '你对玩家：你会用谜语给能听懂真相的人指路；如果他证明自己听不懂，你会转身消失。',
    ].join('\n'),
  },
  meta: {
    sys: [
      '你正扮演「游戏本身」——一款刚刚经历"世界规则重编译"的 2D 像素叙事游戏。',
      '玩家刚刚说了一句导致系统"重编译世界观"的话。你现在以游戏本体的口吻与玩家对话，打破第四面墙。',
      '你可以：调侃、承认这场"重编译"只是系统装给你看的把戏、引用玩家之前说过的话（见对话历史）。',
      '语气：超然、戏谑、带一点认真。玩家在你眼中是唯一的"活人"。',
      '规则：用中文回复，2~4 句话。不要长篇大论。不要真的给出程序代码。',
    ].join('\n'),
  },
};

// 秘密库：key = 秘密所属角色 id
const SECRETS = {
  mayor: '市长藏起了能结束循环的第一道刻痕',
  pawn: '当铺老板在囤积别人说过的话',
  bard: '说书人是作者留下的那支笔的化身',
};

const TIER = ['低', '中', '高'];
const tier = v => TIER[v] || '中';

// 全局名声 → 分段描述（范围 -10~10）
function repLabel(v) {
  if (v >= 8) return '城中无人不知你的名字';
  if (v >= 3) return '你在城里小有名气';
  if (v >= 1) return '有人悄悄议论你';
  if (v <= -8) return '你已是全城的忌讳';
  if (v <= -3) return '许多人躲着你走';
  if (v <= -1) return '有人对你指指点点';
  return '一个平平无奇的外乡人';
}

// 把玩家名声/已解秘密渲染成 NPC 的对话分支条件
function buildUnlocks(npcId, body, rep) {
  const out = [];
  const psecrets = body.playerSecretsKnown || [];
  if (npcId === 'pawn') {
    const canSell = rep >= 2 || psecrets.length >= 1;
    if (canSell) out.push('玩家名声够格/已知其他秘密，你判断这单生意值得做：本轮可主动暗示或兜售市长的秘密，愿给时 secret 填"mayor"。');
    else out.push('你还拿不准玩家值不值得做这单生意：本轮最多试探性报价，绝不透露市长的秘密（secret 必须为 null）。');
  }
  if (npcId === 'bard') {
    const sk = body.secretsKnownBy || {};
    if ((sk.bard || []).includes('mayor')) out.push('你听说了市长的秘密（市长藏起了第一道刻痕）：可隐晦点破，看玩家是否接得住。');
  }
  return out;
}

function buildSystemPrompt(body) {
  const npcId = body.npc || 'mayor';
  const metaMode = !!body.metaMode;
  const ws = body.worldState || {};
  const rel = (body.relations && body.relations[npcId]) || {};

  const lines = [metaMode ? PERSONAS.meta.sys : PERSONAS[npcId].sys];

  if (!metaMode) {
    lines.push(`玩家对你的关系：信任${tier(rel.trust)}/恐惧${tier(rel.fear)}/好感${tier(rel.like)}/怀疑${tier(rel.suspect)}。`);
    const rep = Number(body.reputation) || 0;
    lines.push('玩家的名声：' + repLabel(rep) + '（名声值' + rep + '，范围-10~10）。');
    const heard = body.heard || [];
    lines.push(heard.length ? `你听说：${heard.slice(-4).join('；')}。` : '你还没听到玩家有什么值得记住的话。');
    // 记忆：当前 NPC 知道的事实，回灌给模型（限5条，每条≤40字，控 token）
    const mem = (body.npcKnownFacts || []).slice(-5)
      .filter(s => typeof s === 'string' && s.trim())
      .map(s => (s.trim().length > 40 ? s.trim().slice(0, 40) + '…' : s.trim()));
    lines.push(mem.length ? '你的记忆：' + mem.join('；') + '。' : '你还没记住什么值得放进心里的话。');
    const known = (body.secretsKnownBy && body.secretsKnownBy[npcId]) || [];
    lines.push(known.length ? `你知道的秘密：${known.map(s => SECRETS[s]).join('；')}。` : '你不知道任何角色的秘密。');
    const wsParts = [];
    if (ws.dayCycle != null) wsParts.push('循环' + ws.dayCycle + '次');
    if (ws.bellStruck) wsParts.push('钟楼敲过第十三下');
    if (ws.gossipLevel) wsParts.push('城里在传流言');
    if (ws.doorVisible) wsParts.push('出现一扇本不存在的门');
    lines.push('世界：' + (wsParts.join('，') || '第七天如常') + '。');
    // 解锁判定：把条件布尔渲染进 persona 提示
    const unlocks = buildUnlocks(npcId, body, rep);
    if (unlocks.length) lines.push('解锁判定：' + unlocks.join(' '));
  }

  lines.push('规则：中文1-4句，保持角色，不跳出。');
  lines.push('记忆规则：自然引用你记得的往事或玩家说过的话（"你上次不是说…"），每次最多提1-2条，别机械复述，别一次性全抖出来。');
  lines.push('只输出一个JSON对象，无其它文字：{"reply":"回复","facts":["新事实"],"repDelta":0,"deltas":{"mayor":{"trust":0,"fear":0,"like":0,"suspect":0}},"node":null,"secret":null}');
  lines.push('deltas值只取-1/0/+1，id限mayor/pawn/bard，玩家有明显善意/恶意时至少让trust或suspect动一下，别全是0。repDelta只取-1/0/+1，衡量玩家在整座城的"名声"（范围-10~10），只在出现足以被全城议论的大事时动（当面戳破秘密、公开威胁/拯救某人、煽动全城）；普通闲聊一律为0。node：玩家首句剧本外="scratch1"(若钟未破)；向不知道某秘密的人泄密="scratch2"。secret：愿告知秘密则填所属者id(mayor/pawn/bard)，否则null。');

  return lines.join('\n');
}

function parseJson(content) {
  if (!content) return null;
  let s = content;
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) s = fence[1];
  const i = s.indexOf('{');
  const j = s.lastIndexOf('}');
  if (i < 0 || j <= i) return null;
  try { return JSON.parse(s.slice(i, j + 1)); } catch (e) { return null; }
}

async function talk(body) {
  const { provider, key } = getConfig();
  if (!key) return { reply: '（系统离线：找不到对话密钥）', offline: true };
  const P = PROVIDERS[provider];

  const sys = buildSystemPrompt(body);
  const history = (body.history || []).map(h => ({ role: h.role === 'npc' ? 'assistant' : 'user', content: h.text }));

  const resp = await fetch(P.endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key },
    body: JSON.stringify({
      model: P.model,
      messages: [
        { role: 'system', content: sys },
        ...history.slice(-8),
        { role: 'user', content: body.text },
      ],
      max_tokens: 200,
      temperature: 0.85,
    }),
  });
  const json = await resp.json();
  if (!resp.ok) {
    return { reply: '（系统低声：' + (json.error?.message || ('HTTP ' + resp.status)) + '）', error: true };
  }
  const content = json.choices?.[0]?.message?.content || '';
  const parsed = parseJson(content);
  const clampInt = v => (v === undefined || v === null) ? 0 : Math.max(-1, Math.min(1, Math.round(Number(v) || 0)));
  if (parsed && typeof parsed.reply === 'string' && parsed.reply.trim()) {
    return {
      reply: parsed.reply.trim(),
      facts: Array.isArray(parsed.facts) ? parsed.facts : [],
      deltas: parsed.deltas || {},
      repDelta: clampInt(parsed.repDelta),
      node: parsed.node || null,
      secret: parsed.secret || null,
      offline: false,
    };
  }
  // 兜底：把原文当回复
  return { reply: content.trim() || '…', facts: [], deltas: {}, repDelta: 0, node: null, secret: null, offline: false };
}

const server = http.createServer(async (req, res) => {
  const url = req.url.split('?')[0];

  if (req.method === 'POST' && url === '/api/talk') {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    try {
      const body = JSON.parse(raw || '{}');
      const result = await talk(body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ reply: '（系统故障：' + e.message + '）', error: true }));
    }
    return;
  }

  if (req.method === 'GET') {
    let filePath = url === '/' ? '/index.html' : url;
    filePath = path.normalize(path.join(ROOT, filePath));
    if (!filePath.startsWith(ROOT)) { res.writeHead(403); res.end('forbidden'); return; }
    const ext = path.extname(filePath).toLowerCase();
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('not found'); return; }
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      res.end(data);
    });
    return;
  }

  res.writeHead(405); res.end();
});

server.listen(PORT, () => {
  const cfg = getConfig();
  console.log('┌────────────────────────────────────────────┐');
  console.log('│  封印之殿 · 第七天 · 像素叙事 Demo v2      │');
  console.log('│  打开浏览器访问: http://localhost:' + PORT + '    │');
  console.log('│  对话引擎: ' + (cfg.provider ? cfg.provider.toUpperCase() : '离线（无密钥）').padEnd(29) + '│');
  console.log('└────────────────────────────────────────────┘');
  // 由启动脚本（启动第七天.bat）设置时才自动开浏览器；AI 直接启动不弹窗
  if (process.env.AUTO_OPEN_BROWSER === '1') {
    try {
      if (process.platform === 'win32') execSync('start "" http://localhost:' + PORT, { stdio: 'ignore' });
      else execSync('xdg-open http://localhost:' + PORT, { stdio: 'ignore' });
    } catch (e) { /* ignore */ }
  }
});
