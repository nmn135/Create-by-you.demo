// ============================================================
// src/atmosphere.js — 场景氛围增强（暖光 + 装饰 + 地面细节）
// ============================================================
// 功能：
//   1. 暖色环境光（酒馆氛围）+ 火把补光
//   2. 墙面装饰：旗帜 / 挂毯 / 盾牌
//   3. 地面细节：碎石 / 稻草 / 酒渍
//   4. 天花吊灯暖光
// 由 index.html 实例化。
// ============================================================

export class Atmosphere {
  constructor({ THREE, scene, HALL, wallThick, wallHeight }) {
    this.THREE = THREE;
    this.scene = scene;
    this.HALL = HALL;
    this.wallThick = wallThick;
    this.wallHeight = wallHeight;

    this._buildLights();
    this._buildWallDecor();
    this._buildFloorDetails();
  }

  /** 暖色氛围光（酒馆烛光感） */
  _buildLights() {
    const T = this.THREE;

    // 暖色环境光（替代过暗的默认环境光）
    this.warmAmbient = new T.AmbientLight(0x9a7a52, 1.1);
    this.scene.add(this.warmAmbient);

    // 中央偏暖的点光（模拟吊灯/火堆）
    this.centerWarm = new T.PointLight(0xff9a4a, 1.6, 14, 0.8);
    this.centerWarm.position.set(0, this.HALL.height - 1.2, 0);
    this.scene.add(this.centerWarm);

    // 地面漫反射补光
    this.floorBounce = new T.PointLight(0x6a5a3a, 0.4, 8, 1.2);
    this.floorBounce.position.set(0, 0.3, 0);
    this.scene.add(this.floorBounce);
  }

  /** 程序化旗帜纹理（canvas：蓝底条纹 + 金边 + 星徽） */
  _createFlagTexture() {
    const c = document.createElement('canvas');
    c.width = 128; c.height = 192;
    const x = c.getContext('2d');
    // 蓝底
    x.fillStyle = '#2a4a7a';
    x.fillRect(0, 0, 128, 192);
    // 竖向条纹
    for (let i = 0; i < 128; i += 6) {
      x.fillStyle = (i / 6) % 2 === 0 ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.05)';
      x.fillRect(i, 0, 6, 192);
    }
    // 噪点
    for (let i = 0; i < 180; i++) {
      x.fillStyle = `rgba(0,0,0,${(Math.random() * 0.06).toFixed(3)})`;
      x.fillRect(Math.random() * 128, Math.random() * 192, 1, 1);
    }
    // 金边
    x.strokeStyle = '#c8a860';
    x.lineWidth = 3;
    x.strokeRect(5, 5, 118, 182);
    // 中央八芒星（神殿/教会感）
    const cx = 64, cy = 96;
    x.fillStyle = 'rgba(200,168,96,0.9)';
    x.save();
    x.translate(cx, cy);
    for (let i = 0; i < 4; i++) {
      x.rotate(Math.PI / 2);
      x.beginPath();
      x.moveTo(0, -26); x.lineTo(7, 0); x.lineTo(0, 26); x.lineTo(-7, 0);
      x.closePath(); x.fill();
    }
    x.restore();
    return new this.THREE.CanvasTexture(c);
  }

  /** 墙面装饰 */
  _buildWallDecor() {
    const T = this.THREE;
    const d = this.HALL.depth;
    const w = this.HALL.width;

    // 挂毯（中央远墙）—— 用户反馈"中间的板子还在"，已按反馈移除，避免正中遮挡视线
    // 如需保留墙面装饰，可改挂更贴墙的浮雕/壁画，勿再使用居中大块平板。
    // const tapestryMat = new T.MeshStandardMaterial({ ... }); (removed 2026-08-12)

    // 旗帜（北墙入口两侧）—— 程序化旗帜纹理（条纹+金边+星徽）
    const flagTex = this._createFlagTexture();
    const flagMat = new T.MeshStandardMaterial({
      map: flagTex, color: 0xffffff, roughness: 0.9, side: T.DoubleSide,
      emissive: 0x0a1a3a, emissiveIntensity: 0.1,
    });
    for (const side of [-1, 1]) {
      const flag = new T.Mesh(new T.PlaneGeometry(1.4, 1.9), flagMat);
      flag.position.set(side * 3.5, 3.0, -(d / 2) + 0.05);
      flag.rotation.y = side > 0 ? Math.PI : 0;
      this.scene.add(flag);
      // 旗杆
      const pole = new T.Mesh(
        new T.CylinderGeometry(0.04, 0.04, 1.6, 6),
        new T.MeshStandardMaterial({ color: 0x5a4428, roughness: 0.8 })
      );
      pole.position.set(side * 3.5, 2.2, -(d / 2) + 0.05);
      this.scene.add(pole);
    }

    // 盾牌（东墙）
    const shieldMat = new T.MeshStandardMaterial({
      color: 0x8a6a3a, roughness: 0.6, metalness: 0.5,
      emissive: 0x2a1a0a, emissiveIntensity: 0.1,
    });
    for (const z of [-3, 0, 3]) {
      const shield = new T.Mesh(new T.CircleGeometry(0.55, 12), shieldMat);
      shield.position.set(w / 2 - 0.05, 2.2, z);
      shield.rotation.y = Math.PI / 2;
      this.scene.add(shield);
    }
  }

  /** 地面细节（碎石/稻草/酒渍） */
  _buildFloorDetails() {
    const T = this.THREE;

    // 中央法阵周围碎石圈
    const stoneMat = new T.MeshStandardMaterial({ color: 0x5a5548, roughness: 0.95 });
    for (let i = 0; i < 16; i++) {
      const ang = (Math.PI * 2 / 16) * i;
      const r = 3.2 + Math.random() * 0.6;
      const s = new T.Mesh(
        new T.DodecahedronGeometry(0.12 + Math.random() * 0.1, 0),
        stoneMat
      );
      s.position.set(Math.cos(ang) * r, 0.04, Math.sin(ang) * r);
      s.rotation.set(Math.random() * 3, Math.random() * 3, 0);
      s.scale.y = 0.4;
      s.receiveShadow = true;
      this.scene.add(s);
    }

    // 稻草堆（兽人区角落）
    const strawMat = new T.MeshStandardMaterial({ color: 0x8a7a3a, roughness: 1 });
    for (const pos of [{ x: 7.5, z: 4.5 }, { x: -7.5, z: 4.5 }]) {
      const straw = new T.Mesh(new T.SphereGeometry(0.5, 10, 8), strawMat);
      straw.position.set(pos.x, 0.15, pos.z);
      straw.scale.set(2.2, 0.6, 1.6);
      straw.receiveShadow = true;
      this.scene.add(straw);
    }

    // 酒渍/污渍（暗色斑点）
    const stainMat = new T.MeshStandardMaterial({
      color: 0x1a1008, roughness: 1, transparent: true, opacity: 0.7,
    });
    for (let i = 0; i < 8; i++) {
      const stain = new T.Mesh(
        new T.CircleGeometry(0.3 + Math.random() * 0.4, 8),
        stainMat
      );
      stain.rotation.x = -Math.PI / 2;
      stain.position.set(
        (Math.random() - 0.5) * 14,
        0.015,
        (Math.random() - 0.5) * 8
      );
      this.scene.add(stain);
    }
  }
}
