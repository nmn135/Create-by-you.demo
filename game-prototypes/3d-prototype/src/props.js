// ============================================================
// src/props.js — 场景道具加载器（Poly Haven 家具 FBX）
// ============================================================
// 加载 assets/models/prop_*.fbx，摆放到酒馆布局位置。
// 加载失败静默回退（保持程序化几何体）。
// ============================================================

export class Props {
  constructor({ THREE, FBXLoader, scene }) {
    this.THREE = THREE;
    this.FBXLoader = FBXLoader;
    this.scene = scene;
    this._load();
  }

  async _load() {
    if (!this.FBXLoader) return;
    // 与 models.js 同款防御：拦截 FBX 内嵌的 Windows 绝对路径纹理引用 → 1x1 透明 GIF，
    // 避免道具模型像 liana 那样打出隐藏 403（render_odin 处理管线可能残留 D:/ 路径）。
    const manager = new this.THREE.LoadingManager();
    manager.setURLModifier((url) => {
      if (/[A-Za-z]:[\\/]/.test(url)) {
        return 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
      }
      return url;
    });
    const loader = new this.FBXLoader(manager);

    // 布局：模型文件 → [位置, 旋转, 缩放]
    const layout = [
      { file: 'prop_cabinet.fbx', pos: [8.0, 0, -4.5], rotY: Math.PI / 2, scale: 1.1, name: '哥特柜' },
      { file: 'prop_table.fbx', pos: [-4.5, 0, 0.5], rotY: 0, scale: 1.2, name: '木桌' },
      { file: 'prop_table.fbx', pos: [4.5, 0, 0.5], rotY: 0, scale: 1.2, name: '木桌' },
      { file: 'prop_chair.fbx', pos: [-4.5, 0, 1.4], rotY: 0, scale: 1.0, name: '木椅' },
      { file: 'prop_chair.fbx', pos: [4.5, 0, 1.4], rotY: 0, scale: 1.0, name: '木椅' },
      { file: 'prop_armchair.fbx', pos: [7.5, 0, 4.5], rotY: -Math.PI / 2, scale: 1.0, name: '扶手椅' },
    ];

    for (const item of layout) {
      try {
        const url = '/models/' + item.file;
        const resp = await fetch(url, { method: 'GET' });
        if (!resp.ok) continue;
        const model = await new Promise((res, rej) => loader.load(url, res, undefined, rej));

        // 归一化：缩放到合理尺寸 + 地面对齐
        const box = new this.THREE.Box3().setFromObject(model);
        const h = box.max.y - box.min.y;
        if (h > 0.001 && item.scale) model.scale.setScalar(item.scale);
        const box2 = new this.THREE.Box3().setFromObject(model);
        model.position.y = -box2.min.y;
        model.position.x = item.pos[0];
        model.position.z = item.pos[2];
        if (item.rotY) model.rotation.y = item.rotY;
        model.traverse((c) => {
          if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; }
        });
        this.scene.add(model);
        console.log('[道具] 加载:', item.name, '(' + item.file + ')');
      } catch (e) {
        console.warn('[道具] 加载失败:', item.file, e.message.split('\n')[0]);
      }
    }
  }
}
