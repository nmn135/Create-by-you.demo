---
tags: [game-design, sealed-hall, assets]
date: 2026-08-10
---

# 封印之殿 — 资产管理

## 目录结构

```
assets/
├── models/      # 3D 角色模型（Mixamo FBX/GLB）
├── textures/    # 场景纹理（石材、符文、藤蔓、圣徽）
├── audio/       # 环境音效
└── README.md    # 本文件
```

## 资产清单

### 角色模型（偏写实，来源：Mixamo）

| 角色 | 模型 | 动画 | 状态 |
|------|------|------|:---:|
| 莉安娜（精灵） | — | 待机、走路、情绪手势 | ⬜ |
| 巴鲁克（矮人） | — | 待机、走路、情绪手势 | ⬜ |
| 玛格丽特（牧师） | — | 待机、走路、情绪手势 | ⬜ |
| 罗格（兽人） | — | 待机、走路、情绪手势 | ⬜ |
| 守护灵（发光人形） | 自定义 | 悬浮、颜色变化 | ⬜ |

### 场景资产（偏写实，来源：Sketchfab / Poly Haven / AmbientCG）

| 资产 | 用途 | 来源 | 状态 |
|------|------|------|:---:|
| 石墙纹理 | 大殿墙壁 | AmbientCG | ✅ |
| 石地板纹理 | 大殿地面 | AmbientCG | ✅ |
| 苔藓/藤蔓 | 精灵区 | AmbientCG | ✅ |
| 金属纹理 | 矮人区 | AmbientCG | ✅ |
| 木材纹理 | 家具/门 | AmbientCG | ✅ |
| HDR 环境贴图 | PBR 光照 | Poly Haven | ✅ |
| 符文贴图 | 矮人区墙壁 | 自定义 | ⬜ |
| 圣徽灼痕 | 人类区 | 自定义 | ⬜ |
| 浮雕核心 | 中央 | 自定义 | ⬜ |

### 已下载纹理（`textures/`，全部 CC0）

| 本地文件 | 来源资产 | 分辨率 | 用途 | 来源 URL |
|---|---|---|---|---|
| `stone_wall_color.jpg` | AmbientCG Bricks100 | 2048×1024 | 大殿石墙 | [Bricks100](https://ambientcg.com/a/Bricks100) |
| `stone_floor_color.jpg` | AmbientCG Concrete030 | 2048×2048 | 石地板 | [Concrete030](https://ambientcg.com/a/Concrete030) |
| `moss_color.jpg` | AmbientCG Moss001 | 2048×2048 | 精灵区苔藓 | [Moss001](https://ambientcg.com/a/Moss001) |
| `metal_color.jpg` | AmbientCG Metal063 | 2048×2048 | 矮人区金属 | [Metal063](https://ambientcg.com/a/Metal063) |
| `wood_color.jpg` | AmbientCG Wood095 | 2048×1024 | 家具/门 | [Wood095](https://ambientcg.com/a/Wood095) |
| `old_hall.hdr` | Poly Haven Old Hall | 2K | 古殿环境 HDRI | [old_hall](https://polyhaven.com/a/old_hall) |

> 注：仅下载了 Color（Diffuse）贴图；完整 PBR 贴图集见 `textures/DOWNLOAD_NOTES.md`。

## 许可证要求

- 所有资产必须为 **CC0** 或 **可商用免费**
- Mixamo 资产仅限 Adobe 许可范围使用
- 自定义资产标记来源

## 更新日志

- 2026-08-10：初始化资产目录和清单
- 2026-08-10：从 AmbientCG 下载 5 张 CC0 纹理（石墙/地板/苔藓/金属/木材）+ Poly Haven Old Hall HDRI 到 `textures/`
