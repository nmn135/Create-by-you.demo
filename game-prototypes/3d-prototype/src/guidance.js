// ============================================================
// src/guidance.js — 完整引导系统
// ============================================================
// 组件：
//   1. 开场目标卡片（剧情背景 + 怎么玩三步 + 你的身份）
//   2. 常驻「当前目标」面板（按阶段显示主线目标与建议行动）
//   3. NPC 入场介绍卡（名字 / 种族 / 目的）
//   4. 帮助弹窗（完整教程 + 快捷键表）
// 自包含：DOM 与样式全部在此模块内创建/注入，不依赖 index.html 内部变量。
// ============================================================

const STAGES = {
  0: {
    title: '封印等待苏醒',
    goal: '殿门已封。四族冒险者即将到来——你是第五人，千年来第一个无关之人。守护灵在殿中央注视着你。',
    action: '点击下方「⏭ 等待…」按钮，让第一位到访者入场',
  },
  1: {
    title: '第一位到访者',
    goal: '罗格·铁牙（兽人战士）已入场。他为何而来？',
    action: '点击他头上的名字标签 → 在底部输入框提问 → 回车发送。聊到没有新信息后，点「⏭ 叫下一位」',
  },
  2: {
    title: '墙上的秘密',
    goal: '巴鲁克（矮人佣兵）入场后一直盯着西墙。那里有他不愿提及的东西。',
    action: '与巴鲁克交谈，试探他在看什么；也可先叫下一位到访者',
  },
  3: {
    title: '血脉与恩怨',
    goal: '莉安娜（精灵学者）认出了这座殿的风格。矮人与精灵之间的气氛开始紧绷。',
    action: '分别与他们交谈，按 V 键观察关系网的变化',
  },
  4: {
    title: '四族齐聚',
    goal: '玛格丽特（人族牧师）入场，脸上带着血迹。四族已到齐——每个人的秘密都牵动着封印。',
    action: '自由探索：对话套秘密（追问 / 安慰 / 挑拨）、🔇 悄悄话交易、观察守护灵态度。你的每一句话都在改写世界线',
  },
};

const NPC_INTRO = {
  rog:      { title: '罗格·铁牙',  race: '兽人 · 战士', desc: '来寻找祖传战斧的兽人战士。粗鲁，但坦诚。',            color: '#c4544a' },
  baruk:    { title: '巴鲁克',      race: '矮人 · 佣兵', desc: '只想要自己那份报酬的矮人佣兵。但他总盯着西墙。',        color: '#d4a843' },
  liana:    { title: '莉安娜',      race: '精灵 · 学者', desc: '来取回古代知识的精灵学者。她似乎认出了这座殿。',        color: '#6fbf6f' },
  margaret: { title: '玛格丽特',    race: '人类 · 牧师', desc: '奉教会之命而来的牧师。她脸上带着血迹。',                color: '#e8e0d8' },
};

export class Guidance {
  constructor() {
    this._stage = 0;
    this._injectStyle();
    this._buildIntro();
    this._buildGoalPanel();
    this._buildNpcCard();
    this._buildHelp();
  }

  // ------------------------------------------------------------
  // 样式注入
  // ------------------------------------------------------------
  _injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      /* ===== 引导系统 ===== */
      .g-overlay {
        position: fixed; inset: 0; z-index: 5000;
        display: flex; align-items: center; justify-content: center;
        background: rgba(5, 8, 12, 0.82);
        backdrop-filter: blur(4px);
        opacity: 1; transition: opacity 0.45s ease;
      }
      .g-overlay.hidden { opacity: 0; pointer-events: none; }
      .g-card {
        width: min(560px, 92vw); max-height: 86vh; overflow-y: auto;
        background: linear-gradient(160deg, #141a22 0%, #0c1016 100%);
        border: 1px solid rgba(212, 168, 67, 0.45);
        border-radius: 12px; padding: 26px 30px;
        box-shadow: 0 0 60px rgba(92, 200, 216, 0.15), 0 20px 60px rgba(0,0,0,0.6);
        color: #d8d0c0; font-family: inherit;
      }
      .g-card h2 {
        margin: 0 0 4px; font-size: 24px; letter-spacing: 6px;
        color: #e8e0d8; text-align: center;
      }
      .g-card .g-sub { text-align: center; color: #8a8f98; font-size: 12px; margin-bottom: 16px; }
      .g-card h3 {
        margin: 18px 0 6px; font-size: 14px; color: #d4a843;
        letter-spacing: 2px; border-bottom: 1px solid rgba(212,168,67,0.25); padding-bottom: 4px;
      }
      .g-card p { margin: 6px 0; line-height: 1.75; font-size: 13.5px; }
      .g-card .g-hi { color: #5cc8d8; }
      .g-steps { margin: 8px 0 4px; padding-left: 4px; }
      .g-steps li { margin: 5px 0; line-height: 1.6; font-size: 13.5px; }
      .g-steps b { color: #e8e0d8; }
      .g-btn-row { display: flex; justify-content: center; gap: 12px; margin-top: 20px; }
      .g-btn {
        padding: 10px 30px; border-radius: 8px; cursor: pointer; font-size: 15px;
        border: 1px solid rgba(212,168,67,0.6); background: rgba(212,168,67,0.15);
        color: #f0e6c8; letter-spacing: 3px; transition: all 0.2s;
      }
      .g-btn:hover { background: rgba(212,168,67,0.32); box-shadow: 0 0 18px rgba(212,168,67,0.3); }
      .g-btn.ghost { border-color: rgba(140,150,160,0.4); background: transparent; color: #9aa0a8; letter-spacing: 1px; }
      .g-btn.ghost:hover { background: rgba(140,150,160,0.12); box-shadow: none; }
      .g-keys { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 12.5px; }
      .g-keys td { padding: 3px 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }
      .g-keys td:first-child { width: 42%; color: #5cc8d8; white-space: nowrap; }
      .g-keys td:last-child { color: #a8aeb6; }

      /* 当前目标面板（左上角） */
      #g-goal-panel {
        position: fixed; top: 42%; left: 16px; z-index: 3000;
        width: 250px; padding: 12px 14px;
        background: linear-gradient(160deg, rgba(18,24,32,0.92), rgba(10,14,20,0.92));
        border: 1px solid rgba(92,200,216,0.28); border-left: 3px solid #5cc8d8;
        border-radius: 8px; color: #d8d0c0;
        box-shadow: 0 6px 24px rgba(0,0,0,0.5);
        transition: opacity 0.4s ease, transform 0.4s ease;
      }
      #g-goal-panel.hidden { opacity: 0; transform: translateX(-16px); pointer-events: none; }
      #g-goal-panel .g-title { font-size: 13px; letter-spacing: 3px; color: #5cc8d8; margin-bottom: 6px; }
      #g-goal-panel .g-stage-title { font-size: 15px; color: #f0e6c8; font-weight: 600; margin-bottom: 4px; }
      #g-goal-panel .g-goal { font-size: 12.5px; line-height: 1.65; color: #b8bcc2; margin-bottom: 8px; }
      #g-goal-panel .g-action {
        font-size: 12.5px; line-height: 1.6; color: #d4a843;
        border-top: 1px dashed rgba(212,168,67,0.3); padding-top: 7px;
      }
      #g-goal-panel .g-action b { color: #f0e6c8; }
      #g-goal-panel .g-foot { margin-top: 8px; font-size: 11px; color: #6a7078; text-align: right; }

      /* NPC 入场介绍卡（底部居中） */
      #g-npc-card {
        position: fixed; left: 50%; bottom: 150px; z-index: 3000;
        transform: translateX(-50%) translateY(20px);
        display: flex; align-items: center; gap: 14px;
        padding: 12px 20px; min-width: 320px; max-width: 520px;
        background: linear-gradient(160deg, rgba(20,26,34,0.96), rgba(12,16,22,0.96));
        border: 1px solid var(--g-npc-color, #5cc8d8); border-left: 4px solid var(--g-npc-color, #5cc8d8);
        border-radius: 10px; color: #d8d0c0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6);
        opacity: 0; pointer-events: none;
        transition: opacity 0.4s ease, transform 0.4s ease;
      }
      #g-npc-card.visible { opacity: 1; transform: translateX(-50%) translateY(0); }
      #g-npc-card .g-dot {
        width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0;
        background: var(--g-npc-color, #5cc8d8); box-shadow: 0 0 12px var(--g-npc-color, #5cc8d8);
      }
      #g-npc-card .g-npc-title { font-size: 17px; color: #f0e6c8; font-weight: 600; }
      #g-npc-card .g-npc-race { font-size: 11.5px; color: #8a8f98; letter-spacing: 1px; margin-top: 1px; }
      #g-npc-card .g-npc-desc { font-size: 12.5px; color: #b8bcc2; line-height: 1.55; margin-top: 3px; }
    `;
    document.head.appendChild(style);
  }

  // ------------------------------------------------------------
  // 1. 开场目标卡片
  // ------------------------------------------------------------
  _buildIntro() {
    const el = document.createElement('div');
    // g-intro 卡片已移除（开场改用黑屏打字）
    return;
    el.id = 'g-intro';
    el.className = 'g-overlay';
    el.innerHTML = `
      <div class="g-card">
        <h2>封印之殿</h2>
        <div class="g-sub">以自然语言对话驱动的 3D 叙事体验</div>
        <p>千年前，半神法师 <b>艾瑟林</b> 在大陆中心设下预言：当 <span class="g-hi">人类、精灵、矮人、兽人</span> 四族同时抵达殿心，封印将解除——释放能满足一切心愿、或毁灭一切贪念的力量。</p>
        <p>千年后，四族探险者找到了它。殿门在他们踏入的瞬间封死。中央浮雕亮起，一个声音在每个人脑海中响起：<i>「心中所念，即为钥匙。证明你们的灵魂值得。」</i></p>
        <h3>你的身份</h3>
        <p>你是 <b class="g-hi">第五个</b> 进入殿中的人——不属于任何与这座殿有宿怨的种族。千年来第一个无关之人。守护灵对你格外关注。</p>
        <h3>怎么玩</h3>
        <ol class="g-steps">
          <li><b>叫入</b>：点「⏭ 等待…」按钮，让冒险者依次入场</li>
          <li><b>对话</b>：点人物头上的名字标签 → 在底部输入框说话 → 回车发送</li>
          <li><b>改变</b>：你的话会改变他们的关系、揭开秘密、最终决定封印的结局</li>
        </ol>
        <div class="g-btn-row">
          <button class="g-btn" id="g-intro-enter">进入封印之殿</button>
          <button class="g-btn ghost" id="g-intro-help">先看完整帮助</button>
        </div>
      </div>
    `;
    document.body.appendChild(el);
    el.querySelector('#g-intro-enter').addEventListener('click', () => this.hideIntro());
    el.querySelector('#g-intro-help').addEventListener('click', () => { this.hideIntro(); this.showHelp(); });
  }

  showIntro() {
    const el = document.getElementById('g-intro');
    if (!el) return; // g-intro 卡片未创建（开场已改直接进入）时静默跳过，避免 null 崩溃
    el.classList.remove('hidden');
  }

  hideIntro() {
    const el = document.getElementById('g-intro');
    if (!el) return;
    el.classList.add('hidden');
  }

  // ------------------------------------------------------------
  // 2. 常驻「当前目标」面板
  // ------------------------------------------------------------
  _buildGoalPanel() {
    const el = document.createElement('div');
    el.id = 'g-goal-panel';
    el.innerHTML = `
      <div class="g-title">当前目标</div>
      <div class="g-stage-title" id="g-goal-title">封印等待苏醒</div>
      <div class="g-goal" id="g-goal-text"></div>
      <div class="g-action" id="g-goal-action"></div>
      <div class="g-foot">V 关系网 · M 记忆 · H 帮助</div>
    `;
    document.body.appendChild(el);
    this.setStage(0);
  }

  setStage(stage) {
    this._stage = stage;
    const s = STAGES[stage] || STAGES[4];
    const titleEl = document.getElementById('g-goal-title');
    const textEl = document.getElementById('g-goal-text');
    const actionEl = document.getElementById('g-goal-action');
    if (!titleEl) return;
    titleEl.textContent = s.title;
    textEl.textContent = s.goal;
    actionEl.innerHTML = '<b>建议行动：</b>' + s.action;
  }

  hideGoalPanel() {
    document.getElementById('g-goal-panel').classList.add('hidden');
  }

  // ------------------------------------------------------------
  // 3. NPC 入场介绍卡
  // ------------------------------------------------------------
  _buildNpcCard() {
    const el = document.createElement('div');
    el.id = 'g-npc-card';
    el.innerHTML = `
      <div class="g-dot"></div>
      <div>
        <div class="g-npc-title" id="g-npc-title"></div>
        <div class="g-npc-race" id="g-npc-race"></div>
        <div class="g-npc-desc" id="g-npc-desc"></div>
      </div>
    `;
    document.body.appendChild(el);
    this._npcTimer = null;
  }

  showNpcIntro(npcKey) {
    const info = NPC_INTRO[npcKey];
    const el = document.getElementById('g-npc-card');
    if (!info || !el) return;
    el.style.setProperty('--g-npc-color', info.color);
    el.querySelector('#g-npc-title').textContent = info.title;
    el.querySelector('#g-npc-race').textContent = info.race;
    el.querySelector('#g-npc-desc').textContent = info.desc;
    el.classList.add('visible');
    if (this._npcTimer) clearTimeout(this._npcTimer);
    this._npcTimer = setTimeout(() => el.classList.remove('visible'), 7000);
  }

  // ------------------------------------------------------------
  // 4. 帮助弹窗
  // ------------------------------------------------------------
  _buildHelp() {
    const el = document.createElement('div');
    el.id = 'g-help';
    el.className = 'g-overlay hidden';
    el.innerHTML = `
      <div class="g-card">
        <h2>怎么玩</h2>
        <div class="g-sub">封印之殿 · 操作指南</div>
        <h3>对话三步</h3>
        <ol class="g-steps">
          <li><b>选对象</b>：点击殿中人物头上的名字标签（高亮即选中）；悄悄话模式下先点「🔇 悄悄话」再点目标</li>
          <li><b>输入</b>：在底部输入框打字（Shift+Enter 换行）</li>
          <li><b>发送</b>：按 Enter 回车。NPC 会回应，并改变彼此的关系</li>
        </ol>
        <h3>推进剧情</h3>
        <p>跟当前人物聊到没有新信息后，点「⏭ 叫下一位」让下一位到访者入场。四族全部到场后，世界完全展开。</p>
        <h3>两种对话模式</h3>
        <p>🌐 <b>公开</b>：所有人都听得到，可能引发连锁反应；🔇 <b>悄悄话</b>：单独密谈，第三方听不到内容——但守护灵始终在听。</p>
        <h3>快捷键</h3>
        <table class="g-keys">
          <tr><td>Enter / Shift+Enter</td><td>发送 / 换行</td></tr>
          <tr><td>点击 NPC 名字标签</td><td>选择对话对象</td></tr>
          <tr><td>V</td><td>关系网（NPC 之间的态度变化）</td></tr>
          <tr><td>M</td><td>记忆（你掌握的信息与秘密）</td></tr>
          <tr><td>H</td><td>打开本帮助</td></tr>
          <tr><td>R / F / G</td><td>重置视角 / 聚焦守护灵 / 俯视全局</td></tr>
          <tr><td>Q / E · W / S</td><td>符文明暗 · 屏幕色温</td></tr>
          <tr><td>T · 空格</td><td>对话演出面板 · 下一句</td></tr>
        </table>
        <div class="g-btn-row">
          <button class="g-btn" id="g-help-close">知道了</button>
        </div>
      </div>
    `;
    document.body.appendChild(el);
    el.querySelector('#g-help-close').addEventListener('click', () => this.hideHelp());
  }

  showHelp() {
    document.getElementById('g-help').classList.remove('hidden');
  }

  hideHelp() {
    document.getElementById('g-help').classList.add('hidden');
  }
}
