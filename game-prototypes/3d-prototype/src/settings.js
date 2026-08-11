// ============================================================
// src/settings.js — 设置面板
// ============================================================
// 功能：
//   1. 按键提示显示/隐藏开关
//   2. 鼠标灵敏度调节
//   3. 快捷键说明（完整列表）
//   4. 改键：视角切换键 / 奔跑键（持久化 localStorage）
// 自包含 DOM + 样式；O 键或设置按钮打开。
// ============================================================

const DEFAULTS = {
  showHints: true,
  sensitivity: 1.0,
  toggleKey: 'c',
  runKey: 'shift',
};

export class Settings {
  constructor({ onApply }) {
    this.onApply = onApply || (() => {});
    this.settings = this._load();
    this._injectStyle();
    this._buildPanel();
    this._buildToggleBtn();
    this._bindKeys();
  }

  _load() {
    try {
      const raw = localStorage.getItem('sealed_settings');
      if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
    } catch (e) { /* ignore */ }
    return { ...DEFAULTS };
  }

  _save() {
    try { localStorage.setItem('sealed_settings', JSON.stringify(this.settings)); } catch (e) { /* ignore */ }
    this.onApply && this.onApply(this.settings);
  }

  _injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      #settings-btn {
        position: fixed; right: 14px; top: 14px; z-index: 5000;
        padding: 6px 12px; border-radius: 6px; cursor: pointer;
        background: rgba(10, 14, 20, 0.7); color: #a8d8e8;
        border: 1px solid rgba(92, 200, 216, 0.35); font-size: 12px;
        letter-spacing: 1px;
      }
      #settings-btn:hover { background: rgba(92, 200, 216, 0.2); }
      #settings-panel {
        position: fixed; right: 16px; top: 50px; z-index: 5000;
        width: 320px; padding: 18px 20px;
        background: linear-gradient(160deg, rgba(18,24,32,0.96), rgba(10,14,20,0.96));
        border: 1px solid rgba(92, 200, 216, 0.3); border-radius: 10px;
        color: #d8d0c0; font-size: 13px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6);
        display: none;
      }
      #settings-panel.visible { display: block; }
      #settings-panel h3 { margin: 0 0 12px; font-size: 15px; color: #5cc8d8; letter-spacing: 3px; }
      #settings-panel .set-row {
        display: flex; justify-content: space-between; align-items: center;
        margin: 10px 0; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
      }
      #settings-panel .set-row label { color: #a8b0b8; }
      #settings-panel .set-row input[type=range] { width: 120px; }
      #settings-panel .set-row select {
        background: rgba(20,28,36,0.9); color: #d8d0c0; border: 1px solid rgba(92,200,216,0.3);
        border-radius: 4px; padding: 3px 8px; font-size: 12px;
      }
      #settings-panel .set-keys { margin: 12px 0 4px; font-size: 12px; color: #8a9098; line-height: 1.9; }
      #settings-panel .set-keys b { color: #5cc8d8; font-weight: normal; }
      #settings-close {
        margin-top: 14px; width: 100%; padding: 8px; border-radius: 6px; cursor: pointer;
        background: rgba(92, 200, 216, 0.15); color: #cfeef8;
        border: 1px solid rgba(92, 200, 216, 0.4); font-size: 13px; letter-spacing: 2px;
      }
      #settings-close:hover { background: rgba(92, 200, 216, 0.3); }
    `;
    document.head.appendChild(style);
  }

  _buildToggleBtn() {
    const btn = document.createElement('button');
    btn.id = 'settings-btn';
    btn.textContent = '⚙ 设置';
    btn.addEventListener('click', () => this.toggle());
    document.body.appendChild(btn);
  }

  _buildPanel() {
    const panel = document.createElement('div');
    panel.id = 'settings-panel';
    panel.innerHTML = `
      <h3>设 置</h3>
      <div class="set-row">
        <label>按键提示显示</label>
        <select id="set-showhints">
          <option value="1">显示</option>
          <option value="0">隐藏</option>
        </select>
      </div>
      <div class="set-row">
        <label>鼠标灵敏度</label>
        <input type="range" id="set-sens" min="0.3" max="2.5" step="0.1">
      </div>
      <div class="set-row">
        <label>视角切换键</label>
        <select id="set-togglekey">
          <option value="c">C</option>
          <option value="v">V</option>
          <option value="tab">Tab</option>
        </select>
      </div>
      <div class="set-row">
        <label>奔跑键</label>
        <select id="set-runkey">
          <option value="shift">Shift</option>
          <option value="alt">Alt</option>
          <option value="r">R</option>
        </select>
      </div>
      <div class="set-keys">
        <b>WASD</b> 移动 · <b>Shift</b> 奔跑 · <b>空格</b> 跳 · <b>Ctrl</b> 蹲<br>
        <b>C</b> 切换视角 · <b>点击</b> 锁定鼠标 · <b>Esc</b> 释放<br>
        <b>V</b> 关系网 · <b>M</b> 记忆 · <b>H</b> 帮助 · <b>T</b> 对话演出
      </div>
      <button id="settings-close">关闭</button>
    `;
    document.body.appendChild(panel);
    this.panelEl = panel;

    // 绑定控件
    this.hintsSel = panel.querySelector('#set-showhints');
    this.sensRange = panel.querySelector('#set-sens');
    this.toggleSel = panel.querySelector('#set-togglekey');
    this.runSel = panel.querySelector('#set-runkey');

    this.hintsSel.value = this.settings.showHints ? '1' : '0';
    this.sensRange.value = this.settings.sensitivity;
    this.toggleSel.value = this.settings.toggleKey;
    this.runSel.value = this.settings.runKey;

    this.hintsSel.addEventListener('change', () => {
      this.settings.showHints = this.hintsSel.value === '1';
      this._save();
    });
    this.sensRange.addEventListener('input', () => {
      this.settings.sensitivity = parseFloat(this.sensRange.value);
      this._save();
    });
    this.toggleSel.addEventListener('change', () => {
      this.settings.toggleKey = this.toggleSel.value;
      this._save();
    });
    this.runSel.addEventListener('change', () => {
      this.settings.runKey = this.runSel.value;
      this._save();
    });
    panel.querySelector('#settings-close').addEventListener('click', () => this.close());
  }

  _bindKeys() {
    // O 键开设置（输入框内不触发）
    window.addEventListener('keydown', (e) => {
      if (e.key.toLowerCase() === 'o' && !(e.target && e.target.closest && e.target.closest('input, textarea'))) {
        this.toggle();
      }
    });
  }

  toggle() {
    this.panelEl.classList.toggle('visible');
  }
  open() { this.panelEl.classList.add('visible'); }
  close() { this.panelEl.classList.remove('visible'); }

  /** 供其他模块读取设置 */
  get(key) { return this.settings[key]; }
}
