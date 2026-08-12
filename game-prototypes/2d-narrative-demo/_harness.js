'use strict';
// DOM/Canvas stub 环境：把 index.html 的内联脚本原样跑一遍，抓运行时错误 + 端到端驱动对话
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('NO SCRIPT'); process.exit(1); }
const SCRIPT = m[1];

function makeCtx2d() {
  const c = {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '8px mono',
    imageSmoothingEnabled: false,
    _calls: [],
    setTransform: (...a) => c._calls.push(['setTransform', a]),
    fillRect: (...a) => c._calls.push(['fillRect', a, c.fillStyle]),
    strokeRect: (...a) => c._calls.push(['strokeRect', a]),
    drawImage: (...a) => c._calls.push(['drawImage', a]),
    fillText: (...a) => c._calls.push(['fillText', a]),
    measureText: t => ({ width: String(t).length * 4 }),
    beginPath: () => c._calls.push(['beginPath']),
    arc: (...a) => c._calls.push(['arc', a]),
    stroke: () => c._calls.push(['stroke']),
  };
  return c;
}

function makeEl(id) {
  const el = {
    id, _listeners: {}, _children: [],
    style: {}, classList: { _s: new Set(), add(...c) { c.forEach(x => this._s.add(x)); }, remove(...c) { c.forEach(x => this._s.delete(x)); }, contains(c) { return this._s.has(c); } },
    dataset: {},
    value: '', placeholder: '', disabled: false,
    scrollTop: 0, scrollHeight: 0,
    appendChild(child) { el._children.push(child); return child; },
    focus() {}, blur() {},
    addEventListener(type, fn) { (el._listeners[type] = el._listeners[type] || []).push(fn); },
    dispatch(type, ev) { (el._listeners[type] || []).forEach(fn => fn(ev || { preventDefault() {}, code: '' })); },
    getContext() { if (!el._ctx2d) el._ctx2d = makeCtx2d(); return el._ctx2d; },
  };
  Object.defineProperty(el, 'innerHTML', {
    get() { return el._innerHTML || ''; },
    set(v) { el._innerHTML = v; el._children.length = 0; },
    configurable: true,
  });
  Object.defineProperty(el, 'textContent', {
    get() { return el._textContent || ''; },
    set(v) { el._textContent = v; el._children.length = 0; },
    configurable: true,
  });
  return el;
}

const elements = {};
function getEl(id) { return elements[id] || (elements[id] = makeEl(id)); }

const rafCallbacks = [];
const images = [];
class ImageStub {
  constructor() { this.complete = false; this.naturalWidth = 0; this.naturalHeight = 0; this._src = ''; images.push(this); }
  set src(v) {
    this._src = v;
    if (v === 'bg.png') { this.complete = true; this.naturalWidth = 320; this.naturalHeight = 180; }
    else { this.complete = false; this.naturalWidth = 0; this.naturalHeight = 0; }
  }
  get src() { return this._src; }
}

const store = new Map();
const localStorage = {
  getItem: k => store.has(k) ? store.get(k) : null,
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k),
};

let rafNow = 0;
const performanceStub = { now: () => rafNow };

const fetchLog = [];
async function fetchStub(url, opts) {
  const body = JSON.parse((opts && opts.body) || '{}');
  fetchLog.push({ url, body });
  if (url === '/api/endgame') {
    return { ok: true, status: 200, json: async () => ({
      ending: body.ending || null, epilogue: '测试结局·' + (body.ending || '续写'), offline: false,
    }) };
  }
  const reply = '（测试回复）这城里没有第八天。';
  return { ok: true, status: 200, json: async () => ({
    reply, facts: [], deltas: {}, repDelta: 0, node: null, secret: null,
  }) };
}

const docListeners = {};
const context = {
  console,
  Math, JSON, Object, Array, String, Number, Set, Map, Date, Promise, RegExp, Error,
  setTimeout, clearTimeout, setInterval, clearInterval,
  isNaN, parseFloat, parseInt, isFinite, encodeURIComponent, decodeURIComponent,
  window: null, document: null, localStorage, performance: performanceStub,
  Image: ImageStub, AudioContext: class {
    constructor() { this.state = 'suspended'; this.currentTime = 0; this.destination = {}; }
    resume() { this.state = 'running'; }
    createOscillator() { return { frequency: {}, type: '', connect() {}, start() {}, stop() {} }; }
    createGain() {
      const g = { gain: {} };
      g.gain.setValueAtTime = () => {}; g.gain.exponentialRampToValueAtTime = () => {};
      g.connect = () => {}; return g;
    }
  },
  requestAnimationFrame(fn) { rafCallbacks.push(fn); return rafCallbacks.length; },
  fetch: fetchStub,
};
context.window = context;
context.document = {
  getElementById: getEl,
  createElement: tag => makeEl(tag),
  addEventListener(type, fn) { (docListeners[type] = docListeners[type] || []).push(fn); },
  dispatchKey(code) { (docListeners.keydown || []).forEach(fn => fn({ code, preventDefault() {} })); },
  body: getEl('body'),
};

const results = { ok: true, errors: [] };
let fail = false;
function run(tag, fn) {
  try { fn(); console.log('  ✓ ' + tag); }
  catch (e) { fail = true; results.ok = false; results.errors.push({ tag, err: e.message }); console.log('  ✗ ' + tag + ' :: ' + e.message); }
}
async function runAsync(tag, fn) {
  try { await fn(); console.log('  ✓ ' + tag); }
  catch (e) { fail = true; results.ok = false; results.errors.push({ tag, err: e.message }); console.log('  ✗ ' + tag + ' :: ' + e.message); }
}
const frame = () => { const cb = rafCallbacks[rafCallbacks.length - 1]; if (cb) { rafNow += 16; cb(rafNow); } };

(async () => {
  // 1. 全脚本加载
  run('脚本加载（无顶层错误）', () => { vm.runInNewContext(SCRIPT, context, { filename: 'index.html' }); });
  const G = context.window.__game;
  if (!G) { console.error('✗ window.__game 未暴露'); process.exit(1); }
  const ctx2d = getEl('game').getContext('2d');

  // 1b. 开场背景故事介绍
  await runAsync('开场背景故事(btn-new→intro→ESC跳过)', async () => {
    store.delete('seventhDaySave_v2');
    getEl('btn-new').dispatch('click');   // clearSave + playIntro
    if (G.state !== 'intro') throw new Error('state=' + G.state + ' 应 intro');
    const introEl = getEl('intro');
    if (!introEl.classList.contains('on')) throw new Error('intro 遮罩未显示');
    await new Promise(r => setTimeout(r, 200));
    if (!getEl('intro-text').textContent) throw new Error('开场文案未开始');
    context.document.dispatchKey('Escape');   // 跳过 → explore
    if (G.state !== 'explore') throw new Error('跳过失败 state=' + G.state);
    if (G.introRunning) throw new Error('introRunning 应 false');
  });

  // 2. day7 画帧
  run('day7 场景一帧', () => { G.world.scene = 'day7'; G.world.gossipLevel = 0; G.world.sceneTone = 'normal'; frame(); });

  // 3. day2 无正式图回退
  run('day2(无正式图) 一帧', () => { G.world.scene = 'day2'; G.world.gossipLevel = 1; ctx2d._calls.length = 0; frame(); });
  run('day2 tint 生效', () => {
    if (!ctx2d._calls.some(c => c[0] === 'fillRect' && String(c[2]) === 'rgba(26,22,40,0.34)')) throw new Error('day2 tint 未画');
  });
  run('day2 程序化元素被画（裂痕/涂鸦/告示/传单）', () => {
    const n = ctx2d._calls.filter(c => c[0] === 'fillRect').length;
    if (n < 30) throw new Error('fillRect 调用过少(' + n + ')，程序化元素可能缺失');
  });

  // 4. bg_day2 正式图就绪分支
  run('bg_day2 就绪后走帧', () => {
    const b = images.find(i => i._src === 'bg_day2.png');
    b.complete = true; b.naturalWidth = 320; b.naturalHeight = 180;
    ctx2d._calls.length = 0; frame();
    if (ctx2d._calls.some(c => c[0] === 'fillRect' && String(c[1][0]) === 'rgba(26,22,40,0.34)')) throw new Error('有正式图仍画 tint');
    b.complete = false; b.naturalWidth = 0;
  });

  // 5. loadGame 各种档
  const mkSave = over => Object.assign({ version: 2, world: { dayCycle: 7, bellStruck: false, gossipLevel: 0, sceneTone: 'normal', doorVisible: false, scene: 'day7', reputation: 0 }, npcs: {}, facts: [], playerSecrets: [], secretsKnownBy: { mayor: ['mayor'], pawn: ['mayor', 'pawn'], bard: ['bard'] }, historyLog: [], leakedSecret: null }, over);
  run('loadGame(非法版本)→false', () => { store.set('seventhDaySave_v2', JSON.stringify({ version: 99 })); if (G.loadGame()) throw new Error('应 false'); });
  run('loadGame(无档)→false', () => { store.delete('seventhDaySave_v2'); if (G.loadGame()) throw new Error('应 false'); });
  run('loadGame(day2 档)恢复 scene', () => { store.set('seventhDaySave_v2', JSON.stringify(mkSave({ world: { dayCycle: 8, scene: 'day2', gossipLevel: 1, sceneTone: 'night', reputation: 2 } }))); if (!G.loadGame()) throw new Error('load 失败'); if (G.world.scene !== 'day2') throw new Error('scene=' + G.world.scene); });
  run('loadGame(旧档无 scene)回退 day7', () => { const s = mkSave({}); delete s.world.scene; store.set('seventhDaySave_v2', JSON.stringify(s)); if (!G.loadGame()) throw new Error('load 失败'); if (G.world.scene !== 'day7') throw new Error('scene=' + G.world.scene); });

  // 6. lastReply 载档记忆气泡
  run('lastReply 恢复 + 记忆气泡', () => {
    const s = mkSave({});
    s.npcs = { pawn: { rel: { trust: 0, fear: 0, like: 0, suspect: 2 }, heard: [], x: 250, sIdx: 0, lastReply: '有些话，说给没听过的人听，才值钱。', lastPlayerLine: '我把秘密告诉你' } };
    store.set('seventhDaySave_v2', JSON.stringify(s));
    if (!G.loadGame()) throw new Error('load 失败');
    if (G.npcs.pawn.lastReply !== '有些话，说给没听过的人听，才值钱。') throw new Error('lastReply 未恢复');
    if (!G.npcs.pawn.bubble) throw new Error('记忆气泡未生成');
    if (G.npcs.pawn.bubble.ttl !== 8) throw new Error('气泡 ttl 应为 8');
  });

  // 7. greeting(pawn) 引导分支（有秘密 & 无流言）
  await runAsync('greeting(pawn) 引导分支触发', async () => {
    G.clearSave(); G.loadGame();
    G.world.gossipLevel = 0; G.world.scene = 'day7';
    G.debugSetPos('mayor', G.bellPos.x);             // 市长已在钟楼 → 引导演出跳过
    await G.triggerScratch1();                       // state → explore
    G.debugLearnSecret('mayor');                     // 玩家已知一个秘密
    G.debugTeleport(250); G.debugSetPos('pawn', 250);
    context.document.dispatchKey('KeyE');
    await new Promise(r => setTimeout(r, 900));       // 等 typeReply 打完
    const cur = getEl('dlg-current').textContent;
    if (!/捂在怀里/.test(cur)) throw new Error('引导分支未触发，cur=' + cur);
    context.document.dispatchKey('Escape'); // 关对话
  });

  // 8. 端到端：E 键开对话 → greeting → sendMessage → lastReply 捕获
  await runAsync('端到端对话(openDialogue+sendMessage)', async () => {
    store.delete('seventhDaySave_v2'); G.loadGame();
    G.world.scene = 'day2'; G.world.gossipLevel = 1;
    G.world.bellStruck = false;
    G.debugSetPos('mayor', G.bellPos.x);  // 引导演出跳过，快速进 explore
    // 进入 explore 态
    await G.triggerScratch1();            // 结束后 state=explore
    if (G.state !== 'explore') throw new Error('state=' + G.state);
    G.debugTeleport(250); G.debugSetPos('pawn', 250);
    fetchLog.length = 0;
    context.document.dispatchKey('KeyE'); // → openDialogue(pawn)
    const dlg = getEl('dialogue');
    if (!dlg.classList.contains('open')) throw new Error('对话面板未打开');
    // greeting 默认欢迎已写入 dlgCur（typeReply 是 async，sleep 24ms/字符 → 需要等）
    await new Promise(r => setTimeout(r, 300));
    const cur = getEl('dlg-current').textContent;
    if (!/当铺老板/.test(cur)) throw new Error('greeting 未显示，cur=' + cur);
    // 发消息
    getEl('dlg-input').value = '我相信你，跟你说个秘密';
    getEl('dlg-send').dispatch('click');
    await new Promise(r => setTimeout(r, 300));
    if (!G.npcs.pawn.lastReply) throw new Error('lastReply 未捕获');
    if (G.npcs.pawn.lastPlayerLine !== '我相信你，跟你说个秘密') throw new Error('lastPlayerLine 未捕获');
    // worldState.scene 传给了后端
    const sent = fetchLog.find(f => f.url === '/api/talk');
    if (!sent) throw new Error('未请求 /api/talk');
    if (sent.body.worldState.scene !== 'day2') throw new Error('worldState.scene=' + sent.body.worldState.scene);
    if (sent.body.npc !== 'pawn') throw new Error('npc=' + sent.body.npc);
  });

  // 9. saveGame 结构含 lastReply
  run('saveGame 写入 lastReply/lastPlayerLine', () => {
    G.saveGame();
    const s = JSON.parse(store.get('seventhDaySave_v2'));
    if (!s.npcs.pawn || s.npcs.pawn.lastReply !== G.npcs.pawn.lastReply) throw new Error('lastReply 未入档');
  });

  // 10. triggerScratch2 完整演出
  await runAsync('triggerScratch2 → scene=day2', async () => {
    G.clearSave(); G.loadGame();
    G.world.scene = 'day7'; G.world.gossipLevel = 0; G.world.bellStruck = false;
    await G.triggerScratch2();
    if (G.world.scene !== 'day2') throw new Error('scene=' + G.world.scene);
    if (G.world.gossipLevel !== 1) throw new Error('gossip=' + G.world.gossipLevel);
    if (G.world.dayCycle !== 8) throw new Error('dayCycle=' + G.world.dayCycle);
  });

  // 11. HUD 场景标签
  run('updateHud 场景标签', () => {
    G.world.scene = 'day2';
    G.saveGame();
    frame(); // loop 内 updateHud
    const hud = getEl('hud-scene').textContent;
    if (!/第二天/.test(hud)) throw new Error('HUD 未显示 第二天，得=' + hud);
    G.world.scene = 'day7';
  });

  // 12. tickGossip/doGossip 不炸
  run('tickNpcs/tickGossip 帧循环', () => { for (let i = 0; i < 5; i++) frame(); });

  // 13. 气泡超长文字被截断（不溢出）
  run('气泡超长文字被截断', () => {
    const LONG = '这是一句非常非常非常非常非常非常非常非常长的闲聊话用来测试气泡截断';
    G.npcs.bard.bubble = { text: LONG, ttl: 3 };
    G.debugSetPos('bard', 150);
    ctx2d._calls.length = 0;
    frame();
    const texts = ctx2d._calls.filter(c => c[0] === 'fillText').map(c => String(c[1][0]));
    const t = texts.find(x => /…/.test(x));
    if (!t) throw new Error('未见截断省略号，texts=' + JSON.stringify(texts));
    if (t.length >= LONG.length) throw new Error('未截短');
  });

  // 14. 相邻气泡上下分层不重叠
  run('相邻气泡上下分层不重叠', () => {
    G.npcs.pawn.bubble = { text: '泡一', ttl: 3 };
    G.npcs.bard.bubble = { text: '泡二', ttl: 3 };
    G.debugSetPos('pawn', 150); G.debugSetPos('bard', 156);
    ctx2d._calls.length = 0;
    frame();
    const bubbleYs = ctx2d._calls.filter(c => c[0] === 'fillText').map(c => c[1][2]).filter(y => y >= 90 && y <= 122);
    if (new Set(bubbleYs).size < 2) throw new Error('气泡未分层，ys=' + JSON.stringify([...new Set(bubbleYs)]));
  });

  // 15. 骑砍式话题栏
  await runAsync('话题栏渲染(pawn默认2项)+告别', async () => {
    G.clearSave(); G.loadGame();
    G.world.gossipLevel = 0; G.world.scene = 'day7';
    G.debugResetSecrets(); // 清掉前序测试残留的秘密，验证"新档只有2项"
    G.debugOpenDialogue('pawn');
    await new Promise(r => setTimeout(r, 500)); // 等 greeting 打完
    const box = getEl('dlg-topics');
    const labels = box._children.map(b => b.textContent);
    if (JSON.stringify(labels) !== JSON.stringify(['告别', '打听消息'])) throw new Error('labels=' + JSON.stringify(labels));
    // 告别 → 关闭对话
    box._children[0].dispatch('click');
    if (getEl('dialogue').classList.contains('open')) throw new Error('告别未关闭对话');
    if (G.state !== 'explore') throw new Error('state=' + G.state);
  });

  await runAsync('话题条件解锁(交易出现)', async () => {
    G.debugLearnSecret('mayor');
    G.debugOpenDialogue('pawn');
    await new Promise(r => setTimeout(r, 500));
    const box = getEl('dlg-topics');
    const labels = box._children.map(b => b.textContent);
    if (!labels.includes('交易')) throw new Error('交易未解锁，labels=' + JSON.stringify(labels));
  });

  await runAsync('话题"打听消息"走AI', async () => {
    fetchLog.length = 0;
    const box = getEl('dlg-topics');
    const gossip = box._children.find(b => b.textContent === '打听消息');
    if (!gossip) throw new Error('无打听消息按钮');
    gossip.dispatch('click');
    await new Promise(r => setTimeout(r, 400)); // 等 sendMessage 完成
    const sent = fetchLog.find(f => f.url === '/api/talk' && f.body.text === '城里最近有什么新鲜事？');
    if (!sent) throw new Error('未发送打听消息，fetchLog=' + JSON.stringify(fetchLog.map(f => f.body.text)));
    if (!G.npcs.pawn.lastReply) throw new Error('lastReply 未更新');
    G.debugCloseDialogue();
  });

  await runAsync('话题"交易"条件线走AI', async () => {
    fetchLog.length = 0;
    G.debugOpenDialogue('pawn');
    await new Promise(r => setTimeout(r, 500));
    const box = getEl('dlg-topics');
    const trade = box._children.find(b => b.textContent === '交易');
    if (!trade) throw new Error('无交易按钮');
    trade.dispatch('click');
    await new Promise(r => setTimeout(r, 400));
    const sent = fetchLog.find(f => f.url === '/api/talk' && f.body.text === '我想跟你做笔生意。');
    if (!sent) throw new Error('未发送交易，fetchLog=' + JSON.stringify(fetchLog.map(f => f.body.text)));
    G.debugCloseDialogue();
  });

  // 16. 对话相机推近
  await runAsync('对话相机推近NPC后回位', async () => {
    G.debugResetSecrets();
    G.debugSetPos('pawn', 250);
    G.debugOpenDialogue('pawn');
    for (let i = 0; i < 60; i++) frame();   // 推近收敛
    const c = G.cam;
    if (c.zoom < 1.2) throw new Error('未推近 zoom=' + c.zoom.toFixed(3));
    if (Math.abs(c.x - 250) > 40) throw new Error('未对准 NPC x=' + c.x.toFixed(1) + ' npc=250');
    G.debugCloseDialogue();
    for (let i = 0; i < 60; i++) frame();   // 回位收敛
    const c2 = G.cam;
    if (c2.zoom > 1.05) throw new Error('未回位 zoom=' + c2.zoom.toFixed(3));
    if (Math.abs(c2.x - 160) > 40) throw new Error('未回到中心 x=' + c2.x.toFixed(1));
    // 非对话时相机应完整显示场景（ty≈0）
    if (Math.abs(c2.y - 90) > 40) throw new Error('y 未回位 y=' + c2.y.toFixed(1));
  });

  // 17. 像素肖像（48×48 程序化 + PNG 覆盖）
  run('肖像程序化绘制(市长)', () => {
    G.debugOpenDialogue('mayor');
    const avc = getEl('dlg-avatar').getContext('2d');
    if (!avc._calls.some(c => c[0] === 'fillRect')) throw new Error('程序化肖像无绘制');
    G.debugCloseDialogue();
  });
  run('肖像 PNG 覆盖生效', () => {
    const p = images.find(i => i._src === 'portrait_mayor.png');
    if (!p) throw new Error('portrait_mayor.png 未预加载');
    p.complete = true; p.naturalWidth = 48; p.naturalHeight = 48;
    const avc = getEl('dlg-avatar').getContext('2d');
    avc._calls.length = 0;
    G.debugOpenDialogue('mayor');
    if (!avc._calls.some(c => c[0] === 'drawImage')) throw new Error('PNG 覆盖未走 drawImage');
    G.debugCloseDialogue();
    p.complete = false; p.naturalWidth = 0;
  });

  // 18. 音频系统（M 静音 / init / sfx / BGM 不抛错）
  run('音频静音开关(M 键)', () => {
    context.document.dispatchKey('KeyM');
    if (!G.muted) throw new Error('M 未静音');
    context.document.dispatchKey('KeyM');
    if (G.muted) throw new Error('M 未恢复');
  });
  run('音频 init/sfx/BGM 不抛错', () => {
    G.audio.init();
    G.audio.sfx('open'); G.audio.sfx('close'); G.audio.sfx('send');
    G.audio.sfx('secret'); G.audio.sfx('step'); G.audio.sfx('ending');
    G.audio.switchBgm('day7'); G.audio.switchBgm('day2'); G.audio.stopBgm();
  });

  // 19. 引导移动 walkToBell（对话动作可视化）
  await runAsync('引导移动 walkToBell(市长走向钟楼)', async () => {
    G.clearSave(); G.loadGame();
    G.debugSetPos('mayor', 50);
    const bp = G.bellPos.x;
    let arrived = false;
    const w = G.walkToBell('mayor', '测试带路', () => { arrived = true; });
    if (G.state !== 'guide') throw new Error('walk 中 state 应 guide，得=' + G.state);
    await w;
    if (!arrived) throw new Error('onArrive 未触发');
    if (Math.abs(G.npcs.mayor.x - bp) > 1) throw new Error('市长未到钟楼 x=' + G.npcs.mayor.x);
    if (G.walking) throw new Error('walking 应 false');
    if (G.state !== 'explore') throw new Error('结束后 state 应 explore');
  });

  // 20. 刻痕三：买那批话（当铺话题）
  await runAsync('话题"买那批话"(当铺)→收下话', async () => {
    G.clearSave(); G.loadGame();
    G.world.bellStruck = true; G.world.gossipLevel = 0; G.world.fragments = false;
    G.debugOpenDialogue('pawn');
    await new Promise(r => setTimeout(r, 600));
    const box = getEl('dlg-topics');
    const labels = box._children.map(b => b.textContent);
    if (!labels.includes('买那批话')) throw new Error('买那批话未出现，labels=' + JSON.stringify(labels));
    box._children.find(b => b.textContent === '买那批话').dispatch('click');
    await new Promise(r => setTimeout(r, 2600)); // handleTopic 300ms + buyFragments 2000ms
    if (!G.fragments) throw new Error('fragments 未置位');
    if (G.state !== 'explore') throw new Error('buyFragments 后 state=' + G.state);
  });

  // 21. 刻痕三：归还墨（说书人话题）→ inkDone
  await runAsync('话题"归还墨"(说书人)→刻痕三', async () => {
    G.clearSave(); G.loadGame();
    G.world.bellStruck = true; G.world.fragments = true; G.world.inkDone = false;
    G.debugSetPos('bard', G.bellPos.x); // 已到钟楼 → 跳过 walk
    G.debugOpenDialogue('bard');
    await new Promise(r => setTimeout(r, 600));
    const box = getEl('dlg-topics');
    const labels = box._children.map(b => b.textContent);
    if (!labels.includes('归还墨')) throw new Error('归还墨未出现，labels=' + JSON.stringify(labels));
    box._children.find(b => b.textContent === '归还墨').dispatch('click');
    await new Promise(r => setTimeout(r, 2800)); // 300 + walk(sleep400) + event 1800
    if (!G.inkDone) throw new Error('inkDone 未置位');
  });

  // 22. classifyEnding 确定性分类 + 隐藏结局门
  run('classifyEnding 确定性分类', () => {
    G.world.authorConfessed = false;
    if (G.classifyEnding('我把结局写完，迎来第八天') !== '续写') throw new Error('续写 分类失败');
    if (G.classifyEnding('烧了这座城吧') !== '抹去') throw new Error('抹去 分类失败');
    if (G.classifyEnding('合上书吧') !== '合卷') throw new Error('合卷 分类失败');
    if (G.classifyEnding('我想相信你') !== '续写') throw new Error('未坦白不应解锁 坦白之后');
    G.debugConfess();
    if (G.classifyEnding('我相信你') !== '坦白之后') throw new Error('坦白之后 分类失败');
    G.world.authorConfessed = false;
  });
  run('DEFAULT_EPILOGUE 四条世界线齐全', () => {
    const de = G.DEFAULT_EPILOGUE;
    for (const k of ['续写', '合卷', '抹去', '坦白之后']) {
      if (typeof de[k] !== 'string' || !de[k].length) throw new Error(k + ' 兜底文案缺失');
    }
  });

  // 23. endGame 直接调用：分类 + LLM epilogue + 存档往返
  await runAsync('endGame(续写) + 存档往返', async () => {
    G.clearSave(); G.loadGame();
    G.world.bellStruck = true; G.world.gossipLevel = 1; G.world.fragments = true; G.world.inkDone = true;
    fetchLog.length = 0;
    await G.endGame('我把这座城写完，迎来第八天');
    if (G.ending !== '续写') throw new Error('ending=' + G.ending);
    const sent = fetchLog.find(f => f.url === '/api/endgame');
    if (!sent) throw new Error('未请求 /api/endgame');
    if (sent.body.ending !== '续写') throw new Error('endgame body ending=' + sent.body.ending);
    if (getEl('event').classList.contains('on')) throw new Error('演出遮罩未关闭');
    // 存档往返
    G.saveGame();
    G.world.ending = null;
    G.loadGame();
    if (G.ending !== '续写') throw new Error('ending 未入档，load 后=' + G.ending);
  });

  // 24. 终局：四层剧场 → authorConfessed → 最后一句话 → 坦白之后
  await runAsync('四层剧场 + 终局(坦白之后)', async () => {
    G.resetNewGame();
    G.world.bellStruck = true; G.world.gossipLevel = 1; G.world.fragments = true; G.world.inkDone = true;
    G.debugOpenDialogue('meta');
    let waited = 0;
    while (!G.authorConfessed && waited < 9000) { await new Promise(r => setTimeout(r, 200)); waited += 200; }
    if (!G.authorConfessed) throw new Error('四层剧场未完成，authorConfessed=false');
    if (G.ending) throw new Error('未说最后一句话不应有 ending');
    fetchLog.length = 0;
    getEl('dlg-input').value = '我相信你';
    getEl('dlg-send').dispatch('click');
    waited = 0;
    while (!G.ending && waited < 9000) { await new Promise(r => setTimeout(r, 200)); waited += 200; }
    if (G.ending !== '坦白之后') throw new Error('ending=' + G.ending);
    const sent = fetchLog.find(f => f.url === '/api/endgame');
    if (!sent) throw new Error('未请求 /api/endgame');
    if (sent.body.ending !== '坦白之后') throw new Error('endgame body ending=' + sent.body.ending);
    if (sent.body.authorConfessed !== true) throw new Error('authorConfessed 未传给服务端');
  });

  // 25. 刻痕三/结局 状态入档往返
  run('刻痕三状态(fragments/inkDone/authorConfessed)入档往返', () => {
    G.world.fragments = true; G.world.inkDone = true; G.world.authorConfessed = true;
    G.saveGame();
    G.world.fragments = false; G.world.inkDone = false; G.world.authorConfessed = false;
    G.loadGame();
    if (!G.fragments || !G.inkDone || !G.authorConfessed) throw new Error('刻痕三状态未往返');
  });

  // 26. resetNewGame 清空旧循环/结局
  run('resetNewGame 清空旧循环/结局', () => {
    G.world.ending = '合卷'; G.world.inkDone = true; G.world.fragments = true;
    G.world.authorConfessed = true; G.world.bellStruck = true; G.world.scene = 'day2';
    G.debugLearnSecret('mayor');
    G.resetNewGame();
    if (G.world.ending !== null) throw new Error('ending 未清空');
    if (G.world.inkDone) throw new Error('inkDone 未清空');
    if (G.world.fragments) throw new Error('fragments 未清空');
    if (G.world.authorConfessed) throw new Error('authorConfessed 未清空');
    if (G.world.bellStruck) throw new Error('bellStruck 未清空');
    if (G.world.scene !== 'day7') throw new Error('scene=' + G.world.scene);
    if (G.world.dayCycle !== 7) throw new Error('dayCycle=' + G.world.dayCycle);
  });

  console.log('\n========== 结果 ==========');
  if (results.ok) { console.log('全部通过 ✓'); process.exit(0); }
  else { console.error(JSON.stringify(results.errors, null, 2)); process.exit(1); }
})();
