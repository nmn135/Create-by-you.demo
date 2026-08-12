// 封印之殿 · 像素叙事 Demo 服务器
// 静态托管 + /api/talk 代理 doubao LLM（密钥保持在服务端）
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8890;
const ROOT = __dirname;

const KEY_SRC = 'C:/Users/11988/.claude/file-history/ecca7d29-e2e2-4524-903f-7e5846e7a39e/4667fd2cf3e22d17@v3';
const MODEL = 'doubao-seed-2-0-lite-260428';
const ENDPOINT = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json',
};

// 密钥读取优先级：
//   1) 环境变量 DOUBAO_API_KEY（好友可直接在 shell 里 set）
//   2) 本目录 .env 文件（推荐给好友，内容如 DOUBAO_API_KEY=ark-xxx，已被 .gitignore 排除）
//   3) 作者本机旧快照路径兜底
function getKey() {
  if (process.env.DOUBAO_API_KEY) return process.env.DOUBAO_API_KEY.trim();
  for (const file of [path.join(ROOT, '.env'), KEY_SRC]) {
    try {
      const raw = fs.readFileSync(file, 'utf-8');
      const m = raw.match(/DOUBAO_API_KEY\s*=\s*["']?([^"'\r\n#\s]+)/);
      if (m) return m[1].trim();
    } catch (e) { /* ignore */ }
  }
  return '';
}

function buildSystemPrompt(body) {
  const ws = body.worldState || {};
  const metaMode = !!body.metaMode;

  if (metaMode) {
    return [
      '你正扮演「游戏本身」——一款刚刚经历“世界规则重编译”的 2D 像素叙事游戏。',
      '玩家刚刚说了一句导致系统“重编译世界观”的话。你现在以游戏本体的口吻与玩家对话，打破第四面墙。',
      '你可以：调侃、承认这场“重编译”只是系统装给你看的把戏、引用玩家之前说过的话（见对话历史）。',
      '语气：超然、戏谑、带一点认真。玩家在你眼中是唯一的“活人”。',
      '规则：用中文回复，2~4 句话。不要长篇大论。不要真的给出程序代码。',
    ].join('\n');
  }

  return [
    '你扮演「老罗」，一座偏僻村庄的守夜人，一个亦正亦邪的人。',
    '背景：老罗既不是好人也不是坏人，他守护村子但私下有自己的目的。他习惯用试探和反话说话，从不当面袒露真心。',
    '他对玩家的态度会随着玩家说过的话而变化（见世界状态）。玩家威胁村子，他会敌视；玩家真诚相待，他会松动。',
    `当前世界状态：关系值=${ws.reputation ?? 0}（负数=敌视，正数=友好），场景=${ws.sceneTone ?? 'normal'}${ws.doorVisible ? '，村子出现了一扇不该存在的门' : ''}`,
    '规则：用中文回复，1~4 句话。保持角色，简短、有烟火气。不要跳出角色，不要提到“AI”“模型”“提示词”。',
  ].join('\n');
}

async function talk(body) {
  const apiKey = getKey();
  if (!apiKey) return { reply: '（系统离线：找不到对话密钥）', offline: true };

  const sys = buildSystemPrompt(body);
  const history = (body.history || []).map(h => ({ role: h.role === 'npc' ? 'assistant' : 'user', content: h.text }));
  const userMsg = body.toneHint ? `${body.text}\n\n[语气提示：${body.toneHint}]` : body.text;

  const resp = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: sys },
        ...history.slice(-10),
        { role: 'user', content: userMsg },
      ],
      max_tokens: 300,
      temperature: 0.9,
    }),
  });
  const json = await resp.json();
  if (!resp.ok) {
    return { reply: '（系统低声：' + (json.error?.message || ('HTTP ' + resp.status)) + '）', error: true };
  }
  return { reply: (json.choices?.[0]?.message?.content || '').trim(), offline: false };
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
  console.log('┌──────────────────────────────────────────┐');
  console.log('│  封印之殿 · 像素叙事 Demo               │');
  console.log('│  打开浏览器访问: http://localhost:' + PORT + '  │');
  console.log('└──────────────────────────────────────────┘');
});
