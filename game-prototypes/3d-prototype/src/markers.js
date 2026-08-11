// ============================================================
// src/markers.js — 场景布局引导标记
// ============================================================
// 解决"看不出玩家在哪 / 门在哪 / NPC 朝哪 / 暗语在哪"：
//   1. 玩家位置：入口内侧发光光圈 + 光柱 + "你在这里"标签
//   2. 入口：门柱光效 + "入口·已封死"标签
//   3. 西墙暗语：发光符文点 + 呼吸 + "墙上的暗语"标签
//   4. NPC 朝向：每个 NPC 脚前一个发光箭头，随其朝向与位置同步
// 自包含 DOM/样式；需要每帧调用 update()。
// ============================================================

export class SceneMarkers {
  /**
   * @param {object}   opts
   * @param {THREE}    opts.THREE
   * @param {THREE.Scene} opts.scene
   * @param {THREE.Camera} opts.camera
   * @param {object}   opts.npcMeshes   index.html 的 npcMeshes 注册表
   */
  constructor({ THREE, scene, camera, npcMeshes }) {
    this.THREE = THREE;
    this.scene = scene;
    this.camera = camera;
    this.npcMeshes = npcMeshes;

    this._injectStyle();
    this._buildPlayerMarker();
    this._buildEntranceMarker();
    this._buildRuneMarker();
    this._buildNpcArrows();

    // 标签容器（CSS overlay）
    this.labels = document.createElement('div');
    this.labels.id = 'scene-labels';
    document.body.appendChild(this.labels);
    this._labelEls = {};
    this._makeLabel('player', '你在这里 · 入口');
    this._makeLabel('entrance', '入口 · 已封死');
    this._makeLabel('rune', '墙上的暗语');

    this._worldPositions = {
      player:   new THREE.Vector3(0, 2.3, -5.5),
      entrance: new THREE.Vector3(0, 4.6, -7.3),
      rune:     new THREE.Vector3(-8.4, 2.7, 3.5),
    };
  }

  _injectStyle() {
    const style = document.createElement('style');
    style.textContent = `
      #scene-labels { position: fixed; inset: 0; pointer-events: none; z-index: 2000; }
      .scene-label {
        position: absolute; transform: translate(-50%, -120%);
        padding: 3px 10px; border-radius: 12px; font-size: 12px; letter-spacing: 1px;
        background: rgba(10, 14, 20, 0.78); color: #d8f0e8; white-space: nowrap;
        border: 1px solid rgba(120, 220, 200, 0.4); opacity: 0;
        transition: opacity 0.3s;
      }
      .scene-label.entrance { color: #ffd2a8; border-color: rgba(255, 140, 90, 0.5); }
      .scene-label.rune { color: #ffe9b0; border-color: rgba(212, 168, 67, 0.55); }
    `;
    document.head.appendChild(style);
  }

  _makeLabel(key, text, cls) {
    const el = document.createElement('div');
    el.className = 'scene-label' + (cls ? ' ' + cls : '');
    el.textContent = text;
    this.labels.appendChild(el);
    this._labelEls[key] = el;
  }

  // ------------------------------------------------------------
  // 1. 玩家位置标记（入口内侧）
  // ------------------------------------------------------------
  _buildPlayerMarker() {
    const T = this.THREE;
    const g = new T.Group();
    g.position.set(0, 0.02, -5.5);

    // 地面光圈
    const ringGeo = new T.RingGeometry(0.55, 0.75, 32);
    const ringMat = new T.MeshBasicMaterial({
      color: 0x5cc8d8, transparent: true, opacity: 0.55,
      side: T.DoubleSide, depthWrite: false,
    });
    const ring = new T.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    g.add(ring);

    // 直立光柱（半透明）
    const pillarGeo = new T.CylinderGeometry(0.06, 0.06, 2.1, 8, 1, true);
    const pillarMat = new T.MeshBasicMaterial({
      color: 0x5cc8d8, transparent: true, opacity: 0.22,
      side: T.DoubleSide, depthWrite: false,
      blending: T.AdditiveBlending,
    });
    const pillar = new T.Mesh(pillarGeo, pillarMat);
    pillar.position.y = 1.05;
    g.add(pillar);

    // 顶部光点
    const dotGeo = new T.SphereGeometry(0.09, 12, 10);
    const dotMat = new T.MeshBasicMaterial({ color: 0x7fe8f8, transparent: true, opacity: 0.9 });
    const dot = new T.Mesh(dotGeo, dotMat);
    dot.position.y = 2.1;
    g.add(dot);

    this.scene.add(g);
    this.playerGroup = g;
  }

  // ------------------------------------------------------------
  // 2. 入口标记（北墙中央门柱）
  // ------------------------------------------------------------
  _buildEntranceMarker() {
    const T = this.THREE;
    const g = new T.Group();
    const mat = new T.MeshBasicMaterial({
      color: 0xff8c5a, transparent: true, opacity: 0.4,
      blending: T.AdditiveBlending, depthWrite: false,
    });
    for (const side of [-1, 1]) {
      const pillarGeo = new T.BoxGeometry(0.14, 4.4, 0.14);
      const pillar = new T.Mesh(pillarGeo, mat);
      pillar.position.set(side * 1.6, 2.2, -7.32);
      g.add(pillar);
    }
    // 顶部横梁
    const beamGeo = new T.BoxGeometry(3.34, 0.14, 0.14);
    const beam = new T.Mesh(beamGeo, mat);
    beam.position.set(0, 4.4, -7.32);
    g.add(beam);
    this.scene.add(g);
    this.entranceGroup = g;
  }

  // ------------------------------------------------------------
  // 3. 西墙暗语标记（baruk 看的位置）
  // ------------------------------------------------------------
  _buildRuneMarker() {
    const T = this.THREE;
    const g = new T.Group();
    g.position.set(-9.55, 1.5, 3.5);

    const runeGeo = new T.PlaneGeometry(0.5, 0.5);
    const runeMat = new T.MeshBasicMaterial({
      color: 0xffd700, transparent: true, opacity: 0.9,
      side: T.DoubleSide, depthWrite: false,
      blending: T.AdditiveBlending,
    });
    const rune = new T.Mesh(runeGeo, runeMat);
    // 面朝东（殿内）
    rune.rotation.y = Math.PI / 2;
    g.add(rune);

    // 外圈光环
    const ringGeo = new T.RingGeometry(0.38, 0.48, 24);
    const ringMat = new T.MeshBasicMaterial({
      color: 0xffd700, transparent: true, opacity: 0.5,
      side: T.DoubleSide, depthWrite: false,
    });
    const ring = new T.Mesh(ringGeo, ringMat);
    ring.rotation.y = Math.PI / 2;
    g.add(ring);

    this.scene.add(g);
    this.runeGroup = g;
    this._runeElapsed = 0;
  }

  // ------------------------------------------------------------
  // 4. NPC 朝向箭头（脚前，随位置/朝向同步）
  // ------------------------------------------------------------
  _buildNpcArrows() {
    const T = this.THREE;
    this.arrows = {};
    Object.keys(this.npcMeshes).forEach((key) => {
      const shape = new T.Shape();
      shape.moveTo(0, 0.30);
      shape.lineTo(-0.20, -0.15);
      shape.lineTo(0, -0.04);
      shape.lineTo(0.20, -0.15);
      shape.closePath();
      const geo = new T.ShapeGeometry(shape);
      const mat = new T.MeshBasicMaterial({
        color: 0x8ff0ff, transparent: true, opacity: 1,
        side: T.DoubleSide, depthWrite: false,
      });
      const arrow = new T.Mesh(geo, mat);
      arrow.rotation.x = -Math.PI / 2;
      arrow.position.y = 0.18;
      this.scene.add(arrow);
      this.arrows[key] = arrow;
    });
  }

  // ------------------------------------------------------------
  // 每帧更新
  // ------------------------------------------------------------
  update(dt) {
    const T = this.THREE;

    // 暗语符文呼吸
    this._runeElapsed = (this._runeElapsed || 0) + (dt || 0.016);
    const pulse = 0.55 + Math.sin(this._runeElapsed * 2.2) * 0.35;
    if (this.runeGroup) {
      this.runeGroup.children[0].material.opacity = pulse;
      this.runeGroup.children[1].material.opacity = 0.3 + Math.sin(this._runeElapsed * 2.2) * 0.2;
    }

    // 玩家标记光柱呼吸
    if (this.playerGroup) {
      const p = this.playerGroup.children[1];
      if (p) p.material.opacity = 0.16 + Math.sin(this._runeElapsed * 1.6) * 0.08;
    }

    // NPC 朝向箭头：放在 NPC 面向方向前方 0.55m，随位置/朝向同步
    Object.keys(this.arrows).forEach((key) => {
      const arrow = this.arrows[key];
      const entry = this.npcMeshes[key];
      if (!entry || !arrow) return;
      const pos = entry.group.position;
      const rotY = entry.group.rotation.y || 0;
      arrow.position.x = pos.x + Math.sin(rotY) * 0.55;
      arrow.position.z = pos.z - Math.cos(rotY) * 0.55;
      arrow.rotation.y = rotY;
    });

    // 标签投影
    const halfW = window.innerWidth / 2;
    const halfH = window.innerHeight / 2;
    Object.entries(this._worldPositions).forEach(([key, worldPos]) => {
      const el = this._labelEls[key];
      if (!el) return;
      const vec = worldPos.clone().project(this.camera);
      if (vec.z > 1) { el.style.opacity = '0'; return; }
      const sx = vec.x * halfW + halfW;
      const sy = -vec.y * halfH + halfH;
      if (sx < -50 || sx > window.innerWidth + 50 || sy < -50 || sy > window.innerHeight + 50) {
        el.style.opacity = '0'; return;
      }
      el.style.left = sx + 'px';
      el.style.top = sy + 'px';
      el.style.opacity = '1';
    });
  }
}
