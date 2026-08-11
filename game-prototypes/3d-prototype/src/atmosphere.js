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

  /** 墙面装饰 */
  _buildWallDecor() {
    const T = this.THREE;
    const d = this.HALL.depth;
    const w = this.HALL.width;

    // 挂毯（南墙中央，玛格丽特区）
    const tapestryMat = new T.MeshStandardMaterial({
      color: 0x7a2a2a, roughness: 0.95, metalness: 0,
      emissive: 0x3a1010, emissiveIntensity: 0.15,
    });
    const tapestry = new T.Mesh(new T.PlaneGeometry(3.0, 2.2), tapestryMat);
    tapestry.position.set(0, 2.8, d / 2 - 0.05);
    tapestry.rotation.y = Math.PI;  // 面向殿内
    this.scene.add(tapestry);

    // 旗帜（北墙入口两侧）
    const flagMat = new T.MeshStandardMaterial({
      color: 0x2a4a7a, roughness: 0.9, side: T.DoubleSide,
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
