// ============================================================
// src/fps_controller.js — 全视角控制器（俯瞰 / 第一人称 / 第三人称）
// ============================================================
// 功能：
//   1. C 键循环切换：俯瞰 → 第一人称 → 第三人称
//   2. WASD 移动 + Shift 奔跑 + 空格跳 + Ctrl 蹲
//   3. 第一/第三人称：鼠标视角（Pointer Lock / 拖拽）
//   4. 第三人称：相机跟玩家身后，可见玩家化身
//   5. 殿内碰撞（边界限制）
// ============================================================

export class FPSController {
  constructor({ THREE, camera, scene, controls, bounds = null, height = 1.6, FBXLoader = null, GLTFLoader = null, sensitivity = 1.0, toggleKey = 'c', runKey = 'shift' }) {
    this.THREE = THREE;
    this.camera = camera;
    this.scene = scene;
    this.controls = controls;
    this.bounds = bounds || { minX: -9, maxX: 9, minZ: -6, maxZ: 6 };
    this.height = height;
    this.FBXLoader = FBXLoader;
    this.GLTFLoader = GLTFLoader;
    this.sensitivity = sensitivity;
    this.toggleKey = toggleKey;
    this.runKey = runKey;

    this.mode = 'overview';   // overview | fps | tps
    this.velocity = new THREE.Vector3();
    this.direction = new THREE.Vector3();
    // 初始朝殿内（+Z 方向）：玩家在入口 (0,0,-5.5)，面壁朝 -Z，转 PI 朝 +Z 看大厅
    this.euler = new THREE.Euler(0, Math.PI, 0, 'YXZ');
    this.yawTarget = Math.PI;      // 平滑转向目标（yaw）
    this.pitchTarget = 0;       // 平滑转向目标（pitch）
    this.tpsEuler = new THREE.Euler(0.35, 0, 0, 'YXZ');  // 第三人称俯角
    this.moveSpeed = 4.0;
    this.runSpeed = 7.5;
    this.keys = {};
    this.pos = new THREE.Vector3(0, 0, -5.5);  // 玩家位置（入口内侧）
    this.velY = 0;           // 垂直速度（跳）
    this.grounded = true;
    this.crouching = false;
    this.eyeHeight = height;

    this._injectStyle();
    this._buildUI();
    this._buildAvatar();
    this._bindEvents();
    this._loadAvatarModel();
    // 立即暴露实例（调试/自动化）
    window.__fpsController = this;
  }

  /** 加载真实玩家模型（Knight FBX）替代占位盒 */
  async _loadAvatarModel() {
    try {
      const tposeUrl = '/models/player_tpose.fbx';
      const resp = await fetch(tposeUrl, { method: 'GET' });
      if (!resp.ok) { console.log('[玩家模型] 未找到，使用占位化身'); return; }

      let model;
      if (this.FBXLoader) {
        const loader = new this.FBXLoader();
        model = await new Promise((res, rej) => loader.load(tposeUrl, res, undefined, rej));
      } else {
        console.log('[玩家模型] 无 FBXLoader，使用占位化身');
        return;
      }

      // 归一化到 1.7m
      const box = new this.THREE.Box3().setFromObject(model);
      const h = box.max.y - box.min.y;
      if (h > 0.001) model.scale.setScalar(1.7 / h);
      const box2 = new this.THREE.Box3().setFromObject(model);
      model.position.y = -box2.min.y;
      model.traverse((c) => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });

      // 移除占位盒
      while (this.avatar.children.length) this.avatar.remove(this.avatar.children[0]);
      this.avatar.add(model);
      this.avatar.userData.model = model;

      // 加载 idle/walk 动画
      this.avatarClips = {};
      for (const kind of ['idle', 'walk']) {
        const url = '/models/player_' + kind + '.fbx';
        try {
          const r = await fetch(url, { method: 'GET' });
          if (!r.ok) continue;
          const loader = new this.FBXLoader();
          const obj = await new Promise((res, rej) => loader.load(url, res, undefined, rej));
          const clip = obj.animations && obj.animations[0];
          if (clip) {
            // 过滤 root motion
            const kept = clip.tracks.filter(t => !/mixamorigHips\.position/.test(t.name));
            this.avatarClips[kind] = kept.length === clip.tracks.length ? clip :
              new this.THREE.AnimationClip(clip.name, clip.duration, kept);
          }
        } catch (e) { console.warn('[玩家模型] 动画', kind, '加载失败'); }
      }

      if (Object.keys(this.avatarClips).length) {
        this.avatarMixer = new this.THREE.AnimationMixer(this.avatar);
        if (this.avatarClips.idle) {
          const act = this.avatarMixer.clipAction(this.avatarClips.idle);
          act.setLoop(this.THREE.LoopRepeat); act.play();
        }
      }
      console.log('[玩家模型] Knight 加载完成');
    } catch (e) {
      console.warn('[玩家模型] 加载失败:', e.message);
    }
  }

  _injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      #fps-hint {
        position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%);
        z-index: 4000; padding: 6px 18px; border-radius: 20px;
        background: rgba(10, 14, 20, 0.82); color: #a8d8e8;
        border: 1px solid rgba(92, 200, 216, 0.4);
        font-size: 13px; letter-spacing: 1px;
        display: none; white-space: nowrap;
      }
      #fps-hint.visible { display: block; }
      #fps-crosshair {
        position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);
        width: 6px; height: 6px; border-radius: 50%;
        background: rgba(200, 230, 240, 0.8); z-index: 4000;
        display: none; pointer-events: none;
      }
      #fps-crosshair.visible { display: block; }
      #fps-vignette {
        position: fixed; inset: 0; z-index: 3500; pointer-events: none;
        background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.65) 100%);
        display: none;
      }
      #fps-vignette.visible { display: block; }
    `;
    document.head.appendChild(style);
  }

  _buildUI() {
    const hint = document.createElement('div');
    hint.id = 'fps-hint';
    hint.textContent = 'C 切换视角 · WASD 移动 · Shift 奔跑 · 空格跳 · Ctrl 蹲';
    document.body.appendChild(hint);
    this.hintEl = hint;

    const crosshair = document.createElement('div');
    crosshair.id = 'fps-crosshair';
    document.body.appendChild(crosshair);
    this.crosshairEl = crosshair;

    const vignette = document.createElement('div');
    vignette.id = 'fps-vignette';
    document.body.appendChild(vignette);
    this.vignetteEl = vignette;
  }

  /** 玩家化身（第三人称可见：半透明白色人形） */
  _buildAvatar() {
    const T = this.THREE;
    const g = new T.Group();
    // 躯干
    const torso = new T.Mesh(
      new T.BoxGeometry(0.5, 0.7, 0.3),
      new T.MeshStandardMaterial({ color: 0xaac8d8, transparent: true, opacity: 0.75 })
    );
    torso.position.y = 1.15;
    g.add(torso);
    // 头
    const head = new T.Mesh(
      new T.SphereGeometry(0.18, 12, 10),
      new T.MeshStandardMaterial({ color: 0xd8e8f0, transparent: true, opacity: 0.85 })
    );
    head.position.y = 1.75;
    g.add(head);
    // 朝向箭头
    const arrow = new T.Mesh(
      new T.ConeGeometry(0.08, 0.2, 8),
      new T.MeshBasicMaterial({ color: 0x5cc8d8 })
    );
    arrow.position.set(0, 0.1, 0.3);
    arrow.rotation.x = Math.PI / 2;
    g.add(arrow);

    // 玩家脚下光圈（第一/三人称定位用）
    const ring = new T.Mesh(
      new T.RingGeometry(0.45, 0.55, 24),
      new T.MeshBasicMaterial({ color: 0x5cc8d8, transparent: true, opacity: 0.5, side: T.DoubleSide })
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.02;
    g.add(ring);

    g.visible = false;
    this.scene.add(g);
    this.avatar = g;
  }

  _bindEvents() {
    const isTyping = (e) => e.target && e.target.closest && e.target.closest('input, textarea');
    window.addEventListener('keydown', (e) => {
      const k = e.key.toLowerCase();
      this.keys[k] = true;
      // 第一/三人称下：拦截 WASD/空格/Ctrl（防止输入框吃按键 + 浏览器默认动作）
      const moveKeys = ['w', 'a', 's', 'd', ' ', 'control', this.runKey, this.toggleKey];
      if (this.mode !== 'overview' && moveKeys.includes(k) && !isTyping(e)) {
        e.preventDefault();
      }
      // 空格跳（仅第一/三人称）
      if (k === ' ' && this.mode !== 'overview' && this.grounded && !isTyping(e)) {
        this.velY = 5.2;
        this.grounded = false;
      }
      // Z 蹲（Ctrl 被浏览器抢键且卡页面，改 Z）
      if (k === 'z' || k === 'control') {
        this.crouching = true;
        if (this.mode !== 'overview' && k !== 'control') e.preventDefault();
      }
      // 切换视角
      if (k === this.toggleKey && !isTyping(e)) this.toggle();
      // F 全屏
      if (k === 'f' && !isTyping(e)) this.toggleFullscreen();
      // Enter 进入输入模式（第一/三人称，非输入状态）
      if (k === 'enter' && this.mode !== 'overview' && !isTyping(e)) {
        const inp = document.getElementById('chat-input');
        if (inp) { inp.focus(); e.preventDefault(); }
      }
    });
    window.addEventListener('keyup', (e) => {
      const k = e.key.toLowerCase();
      this.keys[k] = false;
      if (k === 'z' || k === 'control') this.crouching = false;
    });

    // 点击进入第一/三人称鼠标控制
    window.addEventListener('click', (e) => {
      if (this.mode === 'overview') return;
      if (e.target && e.target.closest && e.target.closest('input, textarea, button, #fps-hint, .g-overlay, #ui-layout-controls, #opening-overlay')) return;
      if (document.pointerLockElement) return;
      document.body.requestPointerLock && document.body.requestPointerLock();
    });

    // 鼠标视角（Pointer Lock 或拖拽）
    let dragging = false, lastX = 0, lastY = 0;
    document.addEventListener('mousemove', (e) => {
      if (this.mode === 'overview') return;
      if (document.pointerLockElement === document.body) {
        const sens = 0.0022 * this.sensitivity;
        // Clamp per-event delta to prevent flash-back from abnormal movementX/Y spikes
        const mx = Math.max(-200, Math.min(200, e.movementX));
        const my = Math.max(-200, Math.min(200, e.movementY));
        this.yawTarget -= mx * sens;
        this.pitchTarget = Math.max(-1.25, Math.min(1.25, this.pitchTarget - my * sens)); // pitch clamp ~71.6 deg, avoid gimbal lock
        this.tpsEuler.y = this.yawTarget;
      } else if (dragging) {
        const dx2 = e.clientX - lastX, dy2 = e.clientY - lastY;
        if (Math.abs(dx2) < 150) this.yawTarget -= dx2 * 0.005 * this.sensitivity;
        if (Math.abs(dy2) < 150)
        this.pitchTarget = Math.max(-1.25, Math.min(1.25, this.pitchTarget - (e.clientY - lastY) * 0.005 * this.sensitivity));
        this.euler.x = Math.max(-1.25, Math.min(1.25, this.euler.x)); // pitch clamp ~71.6 deg, avoid gimbal lock
        this.tpsEuler.y = this.yawTarget;
        lastX = e.clientX; lastY = e.clientY;
      }
    });
    // Reset mouse state on pointer lock change (prevent flash-back on fast mouse movement)
    document.addEventListener('pointerlockchange', () => {
      if (document.pointerLockElement === document.body) {
        lastX = 0; lastY = 0; // will be set on next mousemove
      }
    });
    document.addEventListener('mousedown', (e) => {
      if (this.mode === 'overview') return;
      if (e.target && e.target.closest && e.target.closest('input, textarea, button, .g-overlay, #ui-layout-controls, #opening-overlay')) return;
      if (document.pointerLockElement) return;
      dragging = true; lastX = e.clientX; lastY = e.clientY;
    });
    document.addEventListener('mouseup', () => { dragging = false; });

    window.addEventListener('blur', () => { this.keys = {}; });
  }

  /** 全屏切换（F 键） */
  toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
    } catch (e) { /* 全屏不可用时静默 */ }
  }

  toggle() {
    // 去掉上帝视角：只在 fps / tps 间切换
    this.setMode(this.mode === 'fps' ? 'tps' : 'fps');
  }

  setMode(mode) {
    this.mode = mode;
    if (mode === 'overview') {
      this.hintEl.classList.remove('visible');
      this.crosshairEl.classList.remove('visible');
      this.vignetteEl.classList.remove('visible');
      this.avatar.visible = false;
      if (document.pointerLockElement) document.exitPointerLock();
      this.controls.enabled = true;
      // 相机回到俯瞰
      this.camera.position.set(0, 18, 14);
      this.controls.target.set(0, 2.5, 0);
      this.controls.update();
    } else {
      this.hintEl.classList.add('visible');
      this.crosshairEl.classList.add('visible');
      this.vignetteEl.classList.add('visible');
      this.avatar.visible = mode === 'tps';
      this.controls.enabled = false;
      // 相机从玩家位置开始，朝殿内（+Z）
      this.camera.position.set(this.pos.x, this.pos.y + this.eyeHeight, this.pos.z);
      this.euler.set(0, Math.PI, 0, 'YXZ');
      this.yawTarget = Math.PI;
      this.pitchTarget = 0;
      if (mode === 'tps') this.tpsEuler.set(0.35, Math.PI, 0, 'YXZ');
    }
    console.log('[视角] 切换 →', mode);
    // 暴露实例供调试/自动化验证
    window.__fpsController = this;
  }

  /** 每帧调用 */
  update(dt) {
    dt = Math.min(dt, 0.05);

    // 俯瞰模式：不控制相机
    if (this.mode === 'overview') return;

    // ---- 移动 ----
    const forward = new this.THREE.Vector3(0, 0, -1).applyEuler(new this.THREE.Euler(0, this.euler.y, 0));
    const right = new this.THREE.Vector3(1, 0, 0).applyEuler(new this.THREE.Euler(0, this.euler.y, 0));
    forward.y = 0; forward.normalize();
    right.y = 0; right.normalize();

    const dir = new this.THREE.Vector3();
    if (this.keys['w']) dir.add(forward);
    if (this.keys['s']) dir.sub(forward);
    if (this.keys['d']) dir.add(right);
    if (this.keys['a']) dir.sub(right);

    let speed = this.keys[this.runKey] ? this.runSpeed : this.moveSpeed;
    if (this.crouching) speed *= 0.5;
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.pos.addScaledVector(dir, speed * dt);
    }

    // ---- 跳 / 蹲 / 重力 ----
    const targetEye = this.crouching ? this.height * 0.55 : this.height;

    this.eyeHeight += (targetEye - this.eyeHeight) * Math.min(8 * dt, 1);
    if (!this.grounded) {
      this.velY -= 14 * dt;  // 重力
      this.pos.y += this.velY * dt;
      if (this.pos.y <= 0) { this.pos.y = 0; this.velY = 0; this.grounded = true; }
    } else {
      this.pos.y = 0;
    }

    // ---- 碰撞：边界 ----
    const b = this.bounds;
    this.pos.x = Math.max(b.minX, Math.min(b.maxX, this.pos.x));
    this.pos.z = Math.max(b.minZ, Math.min(b.maxZ, this.pos.z));

    // ---- 平滑转向：euler 向目标 lerp（角度环绕，消除瞬移/卡顿）----
    {
      let dy = this.yawTarget - this.euler.y;
      while (dy > Math.PI) dy -= Math.PI * 2;
      while (dy < -Math.PI) dy += Math.PI * 2;
      this.euler.y += dy * Math.min(15 * dt, 1);
      const dp = this.pitchTarget - this.euler.x;
      this.euler.x += dp * Math.min(15 * dt, 1);
    }

    // ---- 应用相机 ----
    if (this.mode === 'fps') {
      this.camera.position.set(this.pos.x, this.pos.y + this.eyeHeight, this.pos.z);
      this.camera.quaternion.setFromEuler(this.euler);
    } else if (this.mode === 'tps') {
      // 第三人称：相机在玩家身后上方
      const back = new this.THREE.Vector3(0, 0, 1).applyEuler(new this.THREE.Euler(0, this.euler.y, 0));
      const camDist = this.crouching ? 2.2 : 3.0;
      const camHeight = this.crouching ? 1.2 : 1.8;
      const target = new this.THREE.Vector3(
        this.pos.x + back.x * camDist,
        this.pos.y + camHeight,
        this.pos.z + back.z * camDist
      );
      this.camera.position.lerp(target, Math.min(12 * dt, 1));
      this.camera.lookAt(this.pos.x, this.pos.y + 1.4, this.pos.z);
      // 化身跟随（朝向 = 相机 yaw，跟随视角转向）
      this.avatar.position.set(this.pos.x, this.pos.y, this.pos.z);
      this.avatar.rotation.y = this.euler.y + Math.PI;  // 化身面朝移动方向（相机前方）
    }

    // 更新化身动画（走动/待机切换；奔跑加速）
    if (this.avatarMixer) {
      this.avatarMixer.update(dt);
      const moving = this.keys['w'] || this.keys['s'] || this.keys['a'] || this.keys['d'];
      const running = moving && this.keys[this.runKey];
      const wantWalk = moving && !!this.avatarClips.walk;
      if (wantWalk && this.avatarAnim !== 'walk') {
        if (this.avatarClips.walk) {
          const act = this.avatarMixer.clipAction(this.avatarClips.walk);
          act.setLoop(this.THREE.LoopRepeat); act.reset(); act.play();
          if (this.avatarClips.idle) this.avatarMixer.clipAction(this.avatarClips.idle).crossFadeTo(act, 0.25, false);
        }
        this.avatarAnim = 'walk';
      }
      // 奔跑：walk 动画加速（Shift 1.8x），慢走 1.0x
      if (this.avatarAnim === 'walk' && this.avatarClips.walk) {
        const act = this.avatarMixer.clipAction(this.avatarClips.walk);
        act.timeScale = running ? 1.8 : 1.0;
      } else if (!wantWalk && this.avatarAnim !== 'idle') {
        if (this.avatarClips.idle) {
          const act = this.avatarMixer.clipAction(this.avatarClips.idle);
          act.setLoop(this.THREE.LoopRepeat); act.reset(); act.play();
          if (this.avatarClips.walk) this.avatarMixer.clipAction(this.avatarClips.walk).crossFadeTo(act, 0.25, false);
        }
        this.avatarAnim = 'idle';
      }
    }
  }
}
