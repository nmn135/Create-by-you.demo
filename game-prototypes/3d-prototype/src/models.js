// ============================================================
// src/models.js — 角色模型加载与动画管理（FBX + GLB 双格式）
// ============================================================
// 约定（文件放 game-prototypes/assets/models/，经 server.py 的
// /models/ 白名单映射提供）：
//   models/<npc>_tpose.fbx 或 .glb   角色模型（T-Pose，含骨骼）—— 必需
//   models/<npc>_idle.fbx  .glb      待机动画（可选，循环）
//   models/<npc>_talk.fbx  .glb      说话动画（可选，一次性，播完回 idle）
//   models/<npc>_walk.fbx  .glb      行走动画（可选，预留）
// 任何文件缺失 → 返回 null，前端保持现有几何人形，静默回退不报错。
// GLB 模型若内嵌动画（gltf.animations），自动作为 idle 使用。
//
// 单位自适应：Mixamo FBX 可能以 cm（角色高 ~170）或 m（~1.7）导出，
// Sketchfab GLB 多为 m 或 cm；加载后按包围盒高度归一化到 targetHeight，
// 再叠加角色体型系数。
// ============================================================

export class ModelManager {
  /**
   * @param {object}   opts
   * @param {THREE}    opts.THREE
   * @param {FBXLoader} opts.FBXLoader
   * @param {GLTFLoader} opts.GLTFLoader  可选；存在则支持 .glb
   * @param {THREE.Scene} opts.scene
   * @param {object}   opts.config     按 npcKey 的 { scale, rotY } 配置
   * @param {number}   opts.targetHeight 归一化目标高度（米），默认 1.75
   * @param {string}   opts.baseUrl    模型 URL 前缀，默认 'models/'
   */
  constructor({ THREE, FBXLoader, GLTFLoader, scene, config = {}, targetHeight = 1.75, baseUrl = 'models/', onStatus }) {
    this.THREE = THREE;
    this.FBXLoader = FBXLoader || null;
    this.GLTFLoader = GLTFLoader || null;
    this.scene = scene;
    this.onStatus = onStatus || null;
    this.config = config;
    this.targetHeight = targetHeight;
    this.baseUrl = baseUrl;
    this.models = {};   // npcKey -> { group, mixer, clips, current }
    this._pendingTalk = {}; // 模型未加载时请求的 talk（加载完成后补播）
    this._disposed = false;

    // 加载管理器：拦截 FBX 内嵌的绝对路径纹理引用（如 D:/tools/...），
    // 用 1x1 透明 GIF 代替，避免每个模型加载时打出一串 403 控制台错误。
    // （liana 系列 FBX 由旧源模型重导出，残留 Windows 绝对路径纹理引用，
    //   模型本身已是纯色材质，贴图不需要。）
    this._manager = new THREE.LoadingManager();
    this._manager.setURLModifier((url) => {
      if (/[A-Za-z]:[\\/]/.test(url)) {
        return 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
      }
      return url;
    });
  }

  // ------------------------------------------------------------
  // 工具
  // ------------------------------------------------------------
  async _fileExists(url) {
    try {
      // 15s：模型文件最大 16MB，慢环境（软件渲染/弱网/高负载）下 5s 会误判缺失
      const resp = await fetch(url, { method: 'GET', signal: AbortSignal.timeout(15000) });
      if (!resp.ok) return false;
      if (resp.body && resp.body.cancel) { try { await resp.body.cancel(); } catch (e) { /* ignore */ } }
      return true;
    } catch (e) {
      return false;
    }
  }

  _loadFbx(loader, url) {
    return new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject);
    });
  }

  _loadGltf(loader, url) {
    return new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject);
    });
  }

  /** 过滤根骨骼位移（mixamorigHips.position），防止原地动画漂移 */
  _stripRootMotion(clip) {
    const kept = clip.tracks.filter((t) => !/mixamorigHips\.position/.test(t.name));
    if (kept.length === clip.tracks.length) return clip;
    return new this.THREE.AnimationClip(clip.name, clip.duration, kept);
  }

  /** 归一化：单位自适应 + 体型缩放 + 地面对齐 + 阴影 + 朝向（FBX/GLB 共用） */
  _normalize(model, npcKey, cfg) {
    const cfg2 = this.config[npcKey] || {};
    const targetH = this.targetHeight * (cfg2.scale !== undefined ? cfg2.scale : 1);
    const box = new this.THREE.Box3().setFromObject(model);
    const rawH = box.max.y - box.min.y;
    if (rawH > 0.001) {
      const s = targetH / rawH;
      model.scale.setScalar(Math.min(20, Math.max(0.005, s)));
    }
    const box2 = new this.THREE.Box3().setFromObject(model);
    model.position.y = -box2.min.y;
    model.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    if (cfg2.rotY) model.rotation.y = cfg2.rotY;
    // 保存基础朝向（供程序化摆动）
    model.userData.baseRotY = model.rotation.y;
    // 保存归一化 scale（供程序化呼吸）
    model.userData.baseScale = model.scale.x;
    return rawH;
  }

  // ------------------------------------------------------------
  // 加载单个 NPC：模型 + 动画；缺失/失败返回 null
  // ------------------------------------------------------------
  async loadNPC(npcKey, cfg) {
    // 探测格式：优先 .fbx（Mixamo），其次 .glb（Sketchfab）
    const fbxUrl = this.baseUrl + npcKey + '_tpose.fbx';
    const glbUrl = this.baseUrl + npcKey + '_tpose.glb';
    const useFbx = this.FBXLoader && (await this._fileExists(fbxUrl));
    const useGlb = !useFbx && this.GLTFLoader && (await this._fileExists(glbUrl));
    if (!useFbx && !useGlb) {
      console.log('[模型] ' + npcKey + '：未找到 ' + fbxUrl + ' 或 ' + glbUrl + '，保持几何人形');
      this._emit(npcKey, '未找到模型文件（几何人形）');
      return null;
    }
    this._emit(npcKey, '加载中…');

    let model;
    let clips = {};
    let rawH;
    const ext = useFbx ? 'fbx' : 'glb';
    try {
      if (useFbx) {
        const loader = new this.FBXLoader(this._manager);
        const obj = await this._loadFbx(loader, fbxUrl);
        model = obj;
        rawH = this._normalize(model, npcKey, cfg);
        // FBX 动画：逐个文件加载
        for (const kind of ['idle', 'talk', 'walk']) {
          const url = this.baseUrl + npcKey + '_' + kind + '.fbx';
          if (!(await this._fileExists(url))) continue;
          try {
            const o = await this._loadFbx(loader, url);
            const clip = o.animations && o.animations[0];
            if (clip) clips[kind] = this._stripRootMotion(clip);
          } catch (e) {
            console.warn('[模型] ' + npcKey + ' 动画 ' + kind + ' 加载失败（' + e.message + '）');
          }
        }
      } else {
        const loader = new this.GLTFLoader(this._manager);
        const gltf = await this._loadGltf(loader, glbUrl);
        model = gltf.scene;
        rawH = this._normalize(model, npcKey, cfg);
        // GLB 内嵌动画：按名字匹配 idle/talk/walk，否则第一个当 idle
        const anims = gltf.animations || [];
        for (const a of anims) {
          const n = a.name.toLowerCase();
          if (n.includes('idle') && !clips.idle) clips.idle = a;
          else if (n.includes('talk') || n.includes('speak') || n.includes('gesture')) clips.talk = clips.talk || a;
          else if (n.includes('walk') || n.includes('run')) clips.walk = clips.walk || a;
        }
        if (!clips.idle && anims.length) clips.idle = anims[0];
      }
    } catch (e) {
      console.warn('[模型] ' + npcKey + ' 加载失败（' + e.message + '），保持几何人形');
      this._emit(npcKey, '加载失败（几何人形）');
      return null;
    }

    // --- 组装动画混合器 ---
    const mixer = new this.THREE.AnimationMixer(model);
    const state = { group: model, mixer, clips, current: null };
    this.models[npcKey] = state;

    model.userData.modelLoaded = true;
    model.userData.mood = 'default';
    model.userData.trust = 0.5;
    model.userData.baseColor = cfg.color !== undefined ? cfg.color : 0x888888;
    // 保存归一化后的地面位置（供程序化呼吸还原）
    model.userData.baseY = model.position.y;

    if (clips.idle) {
      const idle = mixer.clipAction(clips.idle);
      idle.setLoop(this.THREE.LoopRepeat);
      idle.play();
      state.current = 'idle';
    }

    // 若加载期间有 talk 请求，补播一次
    if (this._pendingTalk[npcKey]) {
      delete this._pendingTalk[npcKey];
      this.playAnimation(npcKey, 'talk');
    }

    console.log('[模型] ' + npcKey + ' 加载完成（' + ext + '），动画: ' + Object.keys(clips).join(', ') +
      '（单位' + (rawH > 10 ? 'cm' : 'm') + ' → 归一化至 ' + (this.targetHeight * (this.config[npcKey]?.scale || 1)).toFixed(2) + 'm）');
    this._emit(npcKey, '模型已加载 · 动画: ' + (Object.keys(clips).join(', ') || '无'));
    return model;
  }

  // ------------------------------------------------------------
  // 动画切换
  // ------------------------------------------------------------
  /** 播放指定动画；talk 为一次性，播完自动回 idle */
  playAnimation(npcKey, name) {
    const st = this.models[npcKey];
    if (!st) {
      console.log('[模型] ' + npcKey + ' 尚未加载完成，忽略动画请求: ' + name);
      return;
    }
    const clip = st.clips[name];
    if (!clip) {
      console.log('[模型] ' + npcKey + ' 无动画 ' + name + '（可用: ' + Object.keys(st.clips).join(',') + '）');
      return;
    }
    if (st.current === name) return;
    console.log('[模型] ' + npcKey + ' 播放动画: ' + name + '（' + clip.duration.toFixed(2) + 's, ' + clip.tracks.length + ' 轨）');

    const prevAction = st.current ? st.mixer.clipAction(st.clips[st.current]) : null;
    const nextAction = st.mixer.clipAction(clip);

    if (name === 'talk') {
      nextAction.setLoop(this.THREE.LoopOnce);
      nextAction.clampWhenFinished = true;
      nextAction.onFinished = () => {
        if (this.models[npcKey]) this.playAnimation(npcKey, 'idle');
      };
      nextAction.reset();
      nextAction.play();
    } else {
      nextAction.setLoop(this.THREE.LoopRepeat);
      nextAction.reset();
      nextAction.play();
    }

    if (prevAction && prevAction !== nextAction) {
      prevAction.crossFadeTo(nextAction, 0.3, false);
    }
    st.current = name;
  }

  _emit(npcKey, msg) {
    if (this.onStatus) {
      try { this.onStatus(npcKey, msg); } catch (e) { /* ignore */ }
    }
  }

  playTalk(npcKey) {
    if (!this.models[npcKey]) {
      // 模型还在加载：记录请求，加载完成后自动补播
      this._pendingTalk[npcKey] = true;
      console.log('[模型] ' + npcKey + ' 加载中，talk 已挂起待播');
      return;
    }
    this.playAnimation(npcKey, 'talk');
  }
  playIdle(npcKey) { this.playAnimation(npcKey, 'idle'); }

  /** 每帧调用：更新全部动画混合器 */
  update(dt) {
    if (this._disposed) return;
    const t = this.THREE;
    for (const key in this.models) {
      const st = this.models[key];
      st.mixer.update(dt);
      // talk 播完自动回 idle（轮询检测，不依赖 finished 事件，更稳）
      if (st.current === 'talk' && st.clips.talk) {
        const act = st.mixer.clipAction(st.clips.talk);
        if (act.time >= st.clips.talk.duration - 0.05) {
          this.playAnimation(key, 'idle');
        }
      }
      // 无 idle 动画的模型：程序化待机（呼吸 + 轻微转身摆动）
      if (!st.clips.idle && st.group) {
        const time = (this._breathTime = (this._breathTime || 0) + (dt || 0.016));
        const phase = key.charCodeAt(0) % 7;
        // 呼吸：基于归一化 baseScale 轻微缩放（不覆盖 model.scale）
        const bs = st.group.userData.baseScale || 1;
        const breathe = bs * (1 + Math.sin(time * 1.8 + phase) * 0.015);
        st.group.scale.setScalar(breathe);
        // 悬浮呼吸（基于归一化地面位置）
        const baseY = st.group.userData.baseY !== undefined ? st.group.userData.baseY : 0;
        st.group.position.y = baseY + Math.sin(time * 1.3 + phase) * 0.025;
        // 轻微转身摆动（±4°，模拟张望）
        const baseRot = st.group.userData.baseRotY !== undefined ? st.group.userData.baseRotY : 0;
        st.group.rotation.y = baseRot + Math.sin(time * 0.6 + phase) * 0.07;
      }
    }
  }

  // ------------------------------------------------------------
  // 情绪 / 信任度 → 模型发光表现（不染色贴图，只动 emissive）
  // ------------------------------------------------------------
  setMood(npcKey, mood) {
    const st = this.models[npcKey];
    if (!st) return;
    st.group.userData.mood = mood;
    this._applyVisual(st);
  }

  setTrust(npcKey, trust) {
    const st = this.models[npcKey];
    if (!st) return;
    st.group.userData.trust = trust;
    this._applyVisual(st);
  }

  _applyVisual(st) {
    const ud = st.group.userData;
    const mood = ud.mood || 'default';
    const trust = ud.trust !== undefined ? ud.trust : 0.5;

    const MOOD_EMISSIVE = {
      angry: 0xff2020,
      vulnerable: 0x4060ff,
      hopeful: 0xffd700,
      tense: 0xff8888,
    };
    const moodColor = MOOD_EMISSIVE[mood];
    const base = new this.THREE.Color(ud.baseColor);
    const em = moodColor ? new this.THREE.Color(moodColor) : base.clone().multiplyScalar(0.55);
    const intensity = (moodColor ? 0.4 : 0.12) * (0.35 + trust * 1.3);

    st.group.traverse((child) => {
      if (child.isMesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        for (const m of mats) {
          if (m && m.emissive !== undefined && m.emissive !== null) {
            m.emissive.copy(em);
            m.emissiveIntensity = intensity;
          }
        }
      }
    });
  }

  /** 释放全部资源（可选） */
  dispose() {
    this._disposed = true;
    for (const key in this.models) {
      const st = this.models[key];
      st.mixer.stopAllAction();
      st.mixer.uncacheRoot(st.group);
      this.scene.remove(st.group);
    }
    this.models = {};
  }
}
