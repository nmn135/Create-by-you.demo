// ============================================================
// src/audio.js - Ambient audio system (Web Audio API, no external files)
// Creates subtle room drone + fire crackle atmosphere
// ============================================================

export class AmbientAudio {
  constructor() {
    this.ctx = null;
    this.running = false;
    this._droneGain = null;
    this._fireGain = null;
    this._musicVol = 0.6;      // 背景音乐音量（设置面板可调，0~1）
    this._musicGain = null;
    this._musicTimer = null;
    this._padOscs = [];
    this._padLfo = null;
    this._crackleTimer = null;
  }

  async start() {
    if (this.running) return;
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();

      // --- Room drone: low-passed deep noise (sealed hall rumble) ---
      const droneBuf = this.ctx.createBuffer(1, this.ctx.sampleRate * 3, this.ctx.sampleRate);
      const data = droneBuf.getChannelData(0);
      for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
      const droneSrc = this.ctx.createBufferSource();
      droneSrc.buffer = droneBuf;
      droneSrc.loop = true;
      const droneLP = this.ctx.createBiquadFilter();
      droneLP.type = 'lowpass';
      droneLP.frequency.value = 120; // 更贴近纯闷响（原 160 有中频余量，听着偏"沙"）
      droneLP.Q.value = 0.8;
      const droneGain = this.ctx.createGain();
      droneGain.gain.value = 0.012; // barely audible
      droneSrc.connect(droneLP).connect(droneGain).connect(this.ctx.destination);
      droneSrc.start();
      this._droneGain = droneGain;

      // --- 火堆氛围：极轻的低频火床 + 随机噼啪爆裂（替代连续带通白噪声，消除"沙沙"） ---
      const fireBuf = this.ctx.createBuffer(1, this.ctx.sampleRate * 0.6, this.ctx.sampleRate);
      const fd = fireBuf.getChannelData(0);
      for (let i = 0; i < fd.length; i++) fd[i] = Math.random() * 2 - 1;
      const fireSrc = this.ctx.createBufferSource();
      fireSrc.buffer = fireBuf;
      fireSrc.loop = true;
      const fireBP = this.ctx.createBiquadFilter();
      fireBP.type = 'bandpass';
      fireBP.frequency.value = 500;  // 原 700 连续白噪声是中频"沙沙"主源；压到很低
      fireBP.Q.value = 2.5;
      const fireGain = this.ctx.createGain();
      fireGain.gain.value = 0.004; // 微弱火床气流感（原 0.012 持续噪声明显偏吵）
      fireSrc.connect(fireBP).connect(fireGain).connect(this.ctx.destination);
      fireSrc.start();
      this._fireGain = fireGain;

      // 噼啪声：随机短噪声脉冲，稀疏自然，不带连续噪声
      this._crackleTimer = setInterval(() => this._scheduleCrackle(), 160);

      // --- 背景音乐：神秘古殿氛围（低音持续音 + 五声音阶泛音 + 大厅混响）---
      this._buildMusic();

      this.running = true;
      console.log('[音频] 环境音启动（殿堂闷响 + 火把微声 + 背景音乐）');
    } catch (e) {
      console.warn('[音频] 启动失败:', e.message);
    }
  }

  stop() {
    if (this._musicTimer) { clearInterval(this._musicTimer); this._musicTimer = null; }
    if (this._crackleTimer) { clearInterval(this._crackleTimer); this._crackleTimer = null; }
    if (this.ctx) { this.ctx.close(); this.ctx = null; this.running = false; }
  }

  // ============================================================
  // 背景音乐（Web Audio 程序化合成，无外置文件）
  // 设计：A 小调持续低音 pad（呼吸感）+ 稀疏五声音阶泛音 + 低频根音脉冲
  //       通过卷积混响模拟大厅空间感；音量远低于音效，不抢戏。
  // ============================================================

  /** 生成指数衰减噪声的脉冲响应（简单大厅混响） */
  _makeImpulse(duration, decay) {
    const rate = this.ctx.sampleRate;
    const len = Math.floor(rate * duration);
    const buf = this.ctx.createBuffer(2, len, rate);
    for (let ch = 0; ch < 2; ch++) {
      const data = buf.getChannelData(ch);
      // 一阶低通把脉冲做"暖"（原为全频白噪声，混响尾音偏"shh"沙沙）
      let last = 0;
      const a = Math.exp(-2 * Math.PI * 1800 / rate); // ~1.8kHz 暗化
      for (let i = 0; i < len; i++) {
        const x = Math.random() * 2 - 1;
        last += a * (x - last);
        data[i] = last * Math.pow(1 - i / len, decay);
      }
    }
    return buf;
  }

  /** 火堆噼啪：随机短噪声脉冲（稀疏、带通、快衰减），不带连续噪声 */
  _scheduleCrackle() {
    if (!this.ctx || !this.running) return;
    try {
      const t = this.ctx.currentTime;
      // 35% 留白，让噼啪稀疏自然
      if (Math.random() < 0.35) return;
      const dur = 0.03 + Math.random() * 0.09;
      const n = Math.floor(this.ctx.sampleRate * dur);
      const buf = this.ctx.createBuffer(1, n, this.ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      const bp = this.ctx.createBiquadFilter();
      bp.type = 'bandpass';
      bp.frequency.value = 1200 + Math.random() * 2400; // 噼啪声偏中高频，短促
      bp.Q.value = 3.0;
      const g = this.ctx.createGain();
      const peak = 0.006 + Math.random() * 0.02;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(peak, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(bp).connect(g).connect(this.ctx.destination);
      src.start(t); src.stop(t + dur + 0.05);
    } catch (e) { /* 音频失败静默 */ }
  }

  /** 启动背景音乐节点 + 调度器 */
  _buildMusic() {
    const ctx = this.ctx;

    // 主音量母线：干声直出 + 并行送入大厅混响
    // 混响返回串 1.8kHz 低通并降低湿声（原 0.8 湿声 + 全频噪声脉冲 = 音乐上的"shh"沙沙）
    const musicGain = ctx.createGain();
    musicGain.gain.value = 0.18 * this._musicVol;
    const conv = ctx.createConvolver();
    conv.buffer = this._makeImpulse(2.8, 2.0);
    const convLP = ctx.createBiquadFilter();
    convLP.type = 'lowpass';
    convLP.frequency.value = 1800;
    convLP.Q.value = 0.5;
    const wet = ctx.createGain();
    wet.gain.value = 0.35;
    musicGain.connect(ctx.destination);
    musicGain.connect(conv).connect(convLP).connect(wet).connect(ctx.destination);
    this._musicGain = musicGain;

    // --- 低音持续音 pad：A2(110) + E3(165) + A3(220)，每音微失谐对，低通呼吸 ---
    const padFilter = ctx.createBiquadFilter();
    padFilter.type = 'lowpass';
    padFilter.frequency.value = 480;
    padFilter.Q.value = 0.6;
    const padGain = ctx.createGain();
    padGain.gain.value = 0.3;
    padFilter.connect(padGain).connect(musicGain);
    this._padFilter = padFilter;

    const padRoot = 110; // A2
    for (const [mult, gv] of [[1, 0.5], [1.5, 0.4], [2.0, 0.22]]) {
      for (const det of [-2.5, 2.5]) {
        const o = ctx.createOscillator();
        o.type = 'sine';
        o.frequency.value = padRoot * mult;
        o.detune.value = det;
        const g = ctx.createGain();
        g.gain.value = gv;
        o.connect(g).connect(padFilter);
        o.start();
        this._padOscs.push(o);
      }
    }

    // 低通截止频率慢呼吸 LFO（±140Hz @0.03Hz）
    const lfo = ctx.createOscillator();
    lfo.frequency.value = 0.03;
    const lfoGain = ctx.createGain();
    lfoGain.gain.value = 140;
    lfo.connect(lfoGain).connect(padFilter.frequency);
    lfo.start();
    this._padLfo = lfo;

    // --- 稀疏泛音调度器（A 小调五声音阶），每 2.4s 一步 ---
    const scale = [220.00, 261.63, 293.66, 329.63, 392.00, 440.00]; // A3 C4 D4 E4 G4 A5
    this._musicStep = 0;
    this._musicNext = ctx.currentTime + 0.4;
    this._musicTimer = setInterval(() => {
      if (!this.running || !this.ctx) return;
      try {
        while (this._musicNext < this.ctx.currentTime + 1.0) {
          this._schedulePluck(this._musicNext, scale);
          this._musicNext += 2.4;
        }
      } catch (e) { /* 音频失败静默 */ }
    }, 200);
  }

  /** 调度一个音乐步：每 8 步插一次 A1 低频根音脉冲；其余 30% 休止，否则弹一个柔和泛音 */
  _schedulePluck(t, scale) {
    const ctx = this.ctx;
    if (!ctx) return;
    const step = this._musicStep++;
    const musicGain = this._musicGain;

    // 低频根音脉冲（每 8 步 = 约 19s 一次）
    if (step % 8 === 0) {
      const o = ctx.createOscillator();
      o.type = 'sine';
      o.frequency.value = 55; // A1
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.3, t + 0.5);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 4.6);
      o.connect(g).connect(musicGain);
      o.start(t); o.stop(t + 4.7);
    }

    // 30% 休止，让乐句留白
    if (Math.random() < 0.3) return;

    // 从五声音阶选音（20% 概率回落低八度，增加流动感）
    let f = scale[Math.floor(Math.random() * scale.length)];
    if (Math.random() < 0.2) f /= 2;

    const o = ctx.createOscillator();
    o.type = 'triangle';
    o.frequency.value = f;
    const g = ctx.createGain();
    const dur = 1.8 + Math.random() * 1.5;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(0.12, t + 0.5);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(musicGain);
    o.start(t); o.stop(t + dur + 0.1);
  }

  /** 背景音乐音量（0~1），设置面板联动 */
  set musicVolume(v) {
    this._musicVol = Math.max(0, Math.min(1, v));
    if (this._musicGain) this._musicGain.gain.value = 0.18 * this._musicVol;
  }

  /** 脚步声：低频短促脉冲（走/跑音量不同，volScale 0~1 距离衰减），无外置音频文件 */
  step(running, volScale = 1) {
    if (!this.ctx || !this.running) return;
    try {
      const t = this.ctx.currentTime;
      const o = this.ctx.createOscillator();
      const lp = this.ctx.createBiquadFilter();
      const g = this.ctx.createGain();
      o.type = 'sine';
      o.frequency.value = 80 + Math.random() * 30;
      lp.type = 'lowpass';
      lp.frequency.value = 200;
      const base = (running ? 0.07 : 0.045) * Math.max(0, Math.min(1, volScale));
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(base, t + 0.006);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.1);
      o.connect(lp).connect(g).connect(this.ctx.destination);
      o.start(t);
      o.stop(t + 0.12);
    } catch (e) { /* 音频失败静默 */ }
  }

  /** 跳：短促上升扫频（蹬地呼气感） */
  jump() {
    if (!this.ctx || !this.running) return;
    try {
      const t = this.ctx.currentTime;
      const o = this.ctx.createOscillator();
      const g = this.ctx.createGain();
      o.type = 'triangle';
      o.frequency.setValueAtTime(180, t);
      o.frequency.exponentialRampToValueAtTime(430, t + 0.12);
      g.gain.setValueAtTime(0.05, t);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
      o.connect(g).connect(this.ctx.destination);
      o.start(t); o.stop(t + 0.2);
    } catch (e) { /* 音频失败静默 */ }
  }

  /** 落地：低频撞击，音量随冲击力（impact 0~1） */
  land(impact) {
    if (!this.ctx || !this.running) return;
    try {
      const t = this.ctx.currentTime;
      const o = this.ctx.createOscillator();
      const lp = this.ctx.createBiquadFilter();
      const g = this.ctx.createGain();
      o.type = 'sine';
      o.frequency.setValueAtTime(65 + Math.random() * 20, t);
      lp.type = 'lowpass'; lp.frequency.value = 150;
      const vol = 0.02 + impact * 0.08;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(vol, t + 0.004);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
      o.connect(lp).connect(g).connect(this.ctx.destination);
      o.start(t); o.stop(t + 0.18);
    } catch (e) { /* 音频失败静默 */ }
  }

  set droneVolume(v) { if (this._droneGain) this._droneGain.gain.value = v; }
  set fireVolume(v) { if (this._fireGain) this._fireGain.gain.value = v; }
}
