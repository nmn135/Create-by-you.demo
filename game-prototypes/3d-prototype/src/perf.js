// ============================================================
// src/perf.js — 性能监控（FPS 统计 / renderer.info / HUD / 基线记录）
// ============================================================
// 功能：
//   1. FPS 统计：滑动窗口 300 帧 → 实时 FPS + 1% low
//   2. renderer.info 采样：draw calls / triangles / geometries / textures
//   3. HUD 面板：左下角两行小面板，P 键或 setVisible() 开关
//   4. 调试钩子：window.__getPerfStats() / window.__getPerfBaseline()
//   5. 基线记录：每秒采样，30s 后 console.table 输出 min/avg/max + 峰值
//   6. 自动降级回调：启动 5s 平均 FPS < 30 → onAutoDowngrade()
// 画质档位执行由 index.html 的 applyQuality() 负责，本模块只统计、
// 显示当前档位标签，并把"该降档"的信号抛给回调。
// ============================================================

const WINDOW = 300;        // 滑动窗口帧数（1% low 计算基数）
const HUD_REFRESH_MS = 500; // HUD DOM 刷新间隔
const AUTO_MS = 5000;      // 自动降级判定时刻（启动后）
const AUTO_FPS = 30;       // 自动降级阈值

export class PerfMonitor {
  /**
   * @param {object}  opts
   * @param {THREE.WebGLRenderer} opts.renderer
   * @param {Function} [opts.onAutoDowngrade]  平均 FPS < 30 时回调（只触发一次）
   */
  constructor({ renderer, onAutoDowngrade }) {
    this.renderer = renderer;
    this.onAutoDowngrade = onAutoDowngrade || null;
    this._frames = [];      // 滑动窗口帧时间（秒）
    this._fps = 0;          // EMA 平滑实时 FPS
    this._fpsLow1 = 0;      // 1% low
    this._fpsHistory = [];  // 每秒采样一次，用于基线与自动降级判定
    this._lastFpsSample = 0;
    this._drawPeak = 0;
    this._triPeak = 0;
    this._baselineLogged = false;
    this._autoChecked = false;
    this._quality = 'high';
    this._startedAt = performance.now();
    this._injectStyle();
    this._buildHud();
    this._bindKeys();
    // 调试钩子（自动化验证用，符合项目惯例）
    window.__getPerfStats = () => this.getStats();
    window.__getPerfBaseline = () => this.getBaseline();
  }

  /** 每帧调用（dt 为 animate() 钳制后的帧时间，秒） */
  tick(dt) {
    const now = performance.now();
    const fps = dt > 0 ? 1 / dt : 0;

    // 滑动窗口
    this._frames.push(dt);
    if (this._frames.length > WINDOW) this._frames.shift();

    // 实时 FPS（EMA 平滑，防抖动）
    this._fps = this._fps === 0 ? fps : this._fps * 0.95 + fps * 0.05;

    // 1% low：窗口内最慢 1% 帧的平均帧率（300 帧 → 最慢 3 帧）
    if (this._frames.length >= WINDOW) {
      const sorted = [...this._frames].sort((a, b) => b - a); // 帧时间降序
      const worst = Math.max(1, Math.floor(WINDOW * 0.01));
      let sum = 0;
      for (let i = 0; i < worst; i++) sum += sorted[sorted.length - 1 - i];
      this._fpsLow1 = 1 / (sum / worst);
    }

    // 每秒采样（基线 + 自动降级判定）
    if (now - this._lastFpsSample >= 1000) {
      this._lastFpsSample = now;
      this._fpsHistory.push(fps);
      const info = this.renderer.info;
      if (info.render.calls > this._drawPeak) this._drawPeak = info.render.calls;
      if (info.render.triangles > this._triPeak) this._triPeak = info.render.triangles;

      // 自动降级：启动 5s 采样平均 < 30fps，只触发一次
      if (!this._autoChecked && now - this._startedAt >= AUTO_MS && this._fpsHistory.length >= 5) {
        this._autoChecked = true;
        const head = this._fpsHistory.slice(0, 5);
        const avg = head.reduce((a, b) => a + b, 0) / head.length;
        if (avg < AUTO_FPS && this.onAutoDowngrade) {
          console.warn('[性能] 5s 平均帧率 ' + avg.toFixed(1) + 'fps < ' + AUTO_FPS + '，触发自动降档');
          this.onAutoDowngrade();
        }
      }

      // 基线记录：30s 后输出一次汇总
      if (!this._baselineLogged && now - this._startedAt >= 30000) {
        this._baselineLogged = true;
        const h = this._fpsHistory;
        if (h.length > 0) {
          const min = Math.min(...h), max = Math.max(...h);
          const avg = h.reduce((a, b) => a + b, 0) / h.length;
          console.table({
            平均FPS: Number(avg.toFixed(1)),
            最低FPS: Number(min.toFixed(1)),
            最高FPS: Number(max.toFixed(1)),
            峰值DrawCalls: this._drawPeak,
            峰值Triangles: this._triPeak,
            画质档位: this._quality,
          });
        }
      }
    }

    // HUD DOM 刷新（节流 500ms）
    if (now - this._lastHudAt >= HUD_REFRESH_MS) {
      this._lastHudAt = now;
      this._updateHud();
    }
  }

  /** 供 index.html applyQuality() 调用，同步档位标签 */
  setQuality(level) {
    this._quality = level || 'high';
    this._updateHud();
  }

  setVisible(v) {
    this._visible = !!v;
    if (this.hudEl) this.hudEl.style.display = this._visible ? '' : 'none';
  }

  getStats() {
    const info = this.renderer.info;
    return {
      fps: Number(this._fps.toFixed(1)),
      fpsLow1: Number(this._fpsLow1.toFixed(1)),
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      geometries: info.memory.geometries,
      textures: info.memory.textures,
      quality: this._quality,
    };
  }

  getBaseline() {
    const h = this._fpsHistory;
    if (h.length === 0) return null;
    return {
      fpsMin: Number(Math.min(...h).toFixed(1)),
      fpsMax: Number(Math.max(...h).toFixed(1)),
      fpsAvg: Number((h.reduce((a, b) => a + b, 0) / h.length).toFixed(1)),
      drawCallsPeak: this._drawPeak,
      trianglesPeak: this._triPeak,
      quality: this._quality,
    };
  }

  // ------------------------------------------------------------
  // 内部：HUD DOM
  // ------------------------------------------------------------
  _injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      #perf-hud {
        position: fixed; left: 14px; bottom: 14px; z-index: 4500;
        padding: 6px 10px; border-radius: 6px; pointer-events: none;
        background: rgba(8, 12, 18, 0.62); color: #a8d8e8;
        border: 1px solid rgba(92, 200, 216, 0.22);
        font: 11px/1.7 "Consolas", "Courier New", monospace;
        letter-spacing: 0.5px; user-select: none;
      }
      #perf-hud b { color: #7fe0f0; font-weight: normal; }
      #perf-hud .perf-q { color: #e8c878; }
    `;
    document.head.appendChild(style);
  }

  _buildHud() {
    const el = document.createElement('div');
    el.id = 'perf-hud';
    el.innerHTML =
      '<div>FPS <b id="perf-fps">--</b> · 1%low <b id="perf-low">--</b> · 画质 <span class="perf-q" id="perf-q">高</span></div>' +
      '<div>DrawCalls <b id="perf-dc">--</b> · Tris <b id="perf-tri">--</b></div>';
    document.body.appendChild(el);
    this.hudEl = el;
    this.fpsEl = el.querySelector('#perf-fps');
    this.lowEl = el.querySelector('#perf-low');
    this.qEl = el.querySelector('#perf-q');
    this.dcEl = el.querySelector('#perf-dc');
    this.triEl = el.querySelector('#perf-tri');
  }

  _updateHud() {
    if (!this.hudEl || !this._visible) return;
    const s = this.getStats();
    this.fpsEl.textContent = String(Math.round(s.fps));
    this.lowEl.textContent = s.fpsLow1 > 0 ? String(Math.round(s.fpsLow1)) : '--';
    this.qEl.textContent = this._quality === 'high' ? '高' : this._quality === 'medium' ? '中' : '低';
    this.dcEl.textContent = String(s.drawCalls);
    this.triEl.textContent = s.triangles > 1000 ? (s.triangles / 1000).toFixed(1) + 'k' : String(s.triangles);
  }

  /** P 键开关 HUD（输入框聚焦时不触发） */
  _bindKeys() {
    window.addEventListener('keydown', (e) => {
      if (e.key.toLowerCase() !== 'p') return;
      if (e.target && e.target.closest && e.target.closest('input, textarea')) return;
      this.setVisible(!this._visible);
    });
  }
}
