---
tags: [game-design, sealed-hall, assets]
date: 2026-08-10
---

# 3D 资产链接

## Mixamo 角色

> 注：Mixamo 官网: https://www.mixamo.com/（Adobe 账号登录）
> 所有动画共享：idle（待机）、walking（走路）、gesture（手势对话）、sad/defeated（崩溃）

### 莉安娜（精灵学者）

| 类型 | 名称 | 来源 | 备注 |
|------|------|------|------|
| 模型 | Stylized Elf Huntress | CGTrader（Mixamo 兼容） | 偏写实精灵女性，可上传至 Mixamo 绑骨 |
| 模型 | Mystic Priestess | CGTrader | 学者/法师气质 |
| 备用 | Mixamo 内置 "Elf" 角色 | Mixamo | 偏卡通，可用作测试 |
| 动画 | Idle, Walking, Talking | Mixamo | [直达搜索](https://www.mixamo.com/#/?page=1&query=elf+female+idle) |

### 巴鲁克（矮人佣兵）

| 类型 | 名称 | 来源 | 备注 |
|------|------|------|------|
| 模型 | Dwarf Warrior | CGHub | 矮壮战士体型 |
| 模型 | Military Dwarf | TurboSquid | 矿工/佣兵气质 |
| 备用 | Mixamo 内置 "Dwarf" | Mixamo | 测试用 |
| 动画 | Idle, Walking, Gesture | Mixamo | [直达搜索](https://www.mixamo.com/#/?page=1&query=dwarf+warrior) |

### 玛格丽特（女牧师）

| 类型 | 名称 | 来源 | 备注 |
|------|------|------|------|
| 模型 | Mystic Priestess | CGTrader | 长袍、严肃气质 |
| 模型 | Medieval Woman Robe | Sketchfab | CC0 可商用 |
| 备用 | Mixamo 内置 "Woman Robe" | Mixamo | 测试用 |
| 动画 | Idle, Walking, Sad | Mixamo | [直达搜索](https://www.mixamo.com/#/?page=1&query=priest+robe+female) |

### 罗格（兽人战士）

| 类型 | 名称 | 来源 | 备注 |
|------|------|------|------|
| 模型 | Orc Warrior | Sketchfab | CC0 |
| 模型 | Orc Warrior | CGTrader | 偏写实 |
| 模型 | Fantasy Orc | CGTrader | 高细节 |
| 动画 | Idle, Walking, Gesture | Mixamo | [直达搜索](https://www.mixamo.com/#/?page=1&query=orc+warrior) |

---

## Sketchfab 场景资产

### 古殿/神庙（最推荐）

| 资产 | 链接 | 许可 | 备注 |
|------|------|:---:|------|
| Ancient Temple Modular Kit | Sketchfab 搜索 | CC0/CC-BY | 模块化，可搭建大殿 |
| Dungeon Assets | Sketchfab 搜索 | CC0 | 地牢/古殿通用 |

### 石材纹理

| 资产 | 来源 | 许可 |
|------|------|:---:|
| Limestone Wall | Sketchfab | CC0 |
| Medieval Stone Wall | Sketchfab | CC0 |
| Mossy Stone Wall | Poly Haven | CC0 |
| Monastery Stone Floor | Poly Haven | CC0 |
| Medieval Blocks | Poly Haven | CC0 |

### 符文/魔法阵

| 资产 | 来源 | 许可 |
|------|------|:---:|
| Candlelit Runic Altar | Sketchfab | CC0 |
| Cyan Arcane Rune Circle CC0 | Sketchfab | CC0 |

### 圣徽/教堂

| 资产 | 来源 | 许可 |
|------|------|:---:|
| Gothic Fantasy Cross | Sketchfab | CC0 |
| 11th Century Artifact Cross | Sketchfab | CC0 |

### Sketchfab CC0 文化资产合集

史密斯学会等 27 家机构联合发布的 CC0 3D 资产合集，可在 Sketchfab 搜索 "CC0 Cultural Heritage" 找到。

---

## Poly Haven 资产

### HDRI 环境贴图

| 名称 | 用途 | 链接 |
|------|------|------|
| **Old Hall** | 废弃维多利亚大厅，最适合古殿氛围 | polyhaven.com |

### PBR 纹理

| 名称 | 类别 |
|------|------|
| Mossy Stone Wall | 石材+苔藓 |
| Monastery Stone Floor | 石地板 |
| Mossy Brick | 砖墙+苔藓 |
| Brick Moss | 砖+苔藓 |
| Medieval Blocks | 中世纪石砖 |
| Wooden Planks | 木板 |
| Worn Corrugated Iron | 旧金属 |

---

## 其他免费资源站

| 站点 | 说明 |
|------|------|
| [AmbientCG](https://ambientcg.com/) | CC0 PBR 材质，质量极高 |
| [OpenGameArt](https://opengameart.org/) | 游戏资产合集 |
| [BlendSwap](https://www.blendswap.com/) | Blender 模型分享 |
| [Free3D](https://free3d.com/) | 免费 3D 模型 |
| [Quixel Megascans](https://quixel.com/megascans) | UE 用户免费（需 Epic 账号） |
| [CC0 Textures](https://cc0-textures.com/) | CC0 纹理 |

---

## Mixamo 工作流指南

1. 在 Mixamo 网站上传自定义模型（FBX/OBJ 格式）
2. Mixamo 自动绑骨（需手动放置 6 个关节标记点）
3. 选择动画 → 下载（FBX with skin / FBX for Unity 均可）
4. 在 Blender 中转换 FBX → GLB（Three.js 推荐格式）
5. 使用 Three.js GLTFLoader 加载

## 推荐原型最小成本组合

| 组件 | 来源 | 数量 |
|------|------|:---:|
| 角色模型 | Mixamo 内置（测试）+ CGTrader（正式） | 4 |
| 动画 | Mixamo（idle + walk + 2 gesture） | 4×4=16 |
| 场景主结构 | 程序化 BoxGeometry（已在 index.html） | — |
| 纹理 | Poly Haven CC0 | 5-8 张 |
| HDRI | Poly Haven Old Hall | 1 |

## 许可注意事项

- Mixamo 动画：Adobe 通用条款，可用于商业游戏
- Sketchfab CC0：完全自由使用
- Poly Haven：CC0
- CGTrader/TurboSquid：需逐项检查许可（部分 Royalty Free）
