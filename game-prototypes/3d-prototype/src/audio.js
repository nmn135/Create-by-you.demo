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
      droneLP.frequency.value = 160;
      droneLP.Q.value = 0.4;
      const droneGain = this.ctx.createGain();
      droneGain.gain.value = 0.018; // barely audible
      droneSrc.connect(droneLP).connect(droneGain).connect(this.ctx.destination);
      droneSrc.start();
      this._droneGain = droneGain;

      // --- Fire crackle: band-passed noise (subtle, like distant torches) ---
      const fireBuf = this.ctx.createBuffer(1, this.ctx.sampleRate * 0.6, this.ctx.sampleRate);
      const fd = fireBuf.getChannelData(0);
      for (let i = 0; i < fd.length; i++) fd[i] = Math.random() * 2 - 1;
      const fireSrc = this.ctx.createBufferSource();
      fireSrc.buffer = fireBuf;
      fireSrc.loop = true;
      const fireBP = this.ctx.createBiquadFilter();
      fireBP.type = 'bandpass';
      fireBP.frequency.value = 700;
      fireBP.Q.value = 1.5;
      const fireGain = this.ctx.createGain();
      fireGain.gain.value = 0.012;
      fireSrc.connect(fireBP).connect(fireGain).connect(this.ctx.destination);
      fireSrc.start();
      this._fireGain = fireGain;

      this.running = true;
      console.log('[音频] 环境音启动（殿堂闷响 + 火把微声）');
    } catch (e) {
      console.warn('[音频] 启动失败:', e.message);
    }
  }

  stop() {
    if (this.ctx) { this.ctx.close(); this.ctx = null; this.running = false; }
  }

  set droneVolume(v) { if (this._droneGain) this._droneGain.gain.value = v; }
  set fireVolume(v) { if (this._fireGain) this._fireGain.gain.value = v; }
}
