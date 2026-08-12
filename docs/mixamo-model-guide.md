---
title: 封印之殿 — Mixamo 模型挑选与下载指引
date: 2026-08-10
tags: [game-design, sealed-hall, mixamo, models]
---

# Mixamo 模型挑选与下载指引

> 角色模型走 **Mixamo**（免费、可商用、无需署名，唯一限制是不能把模型当独立资产再分发——整合进游戏完全合规）。前端已具备 FBX 加载能力（`3d-prototype/src/models.js`），**你只需下载文件放进 `assets/models/`，刷新页面即生效**。

## 一、你需要下载什么（4 个角色）

每个角色 **最低 2 个文件**（T-Pose 模型 + Idle 动画），推荐 3 个（+ Talk 说话动画）：

| 文件 | 内容 | 必需？ |
|------|------|:---:|
| `<角色>_tpose.fbx` | 角色模型（T-Pose，含骨骼） | ✅ 必需 |
| `<角色>_idle.fbx`  | 待机动画（循环播放） | ✅ 必需 |
| `<角色>_talk.fbx`  | 说话动画（对话时播，播完回 idle） | ⭐ 推荐 |
| `<角色>_walk.fbx`  | 行走动画（预留，以后入场演出用） | 可选 |

共 **8~12 个文件**，每个约 1-5MB。

## 二、角色挑选清单

打开 <https://www.mixamo.com> → 顶部 **Characters** 页签。按"体型/气质"方向挑，**名字仅供参考**（Mixamo 角色库约 108 个，直接在页面里预览选最顺眼的）：

| 角色 | 方向 | 候选（预览时按感觉挑） |
|------|------|----------------------|
| **莉安娜**（精灵学者） | 苗条女性、学者/长袍气质 | Medea、Ely、Scarlet、Lily |
| **巴鲁克**（矮人佣兵） | 壮实矮壮男性 | Wrestler、Peasant Man、Warrior |
| **玛格丽特**（人族牧师） | 端庄女性、圣职感 | **Paladin w-Prop**（圣骑士带道具，最贴牧师）、Maria、Zoe |
| **罗格**（兽人战士） | 最高大威猛 | **Warrok**、Heraklios、Warrior、Knight |

> 没有专门的矮人/兽人模型？没关系——前端会自动按体型系数缩放：**巴鲁克 0.82 倍（矮壮）+ 面朝西墙**、**罗格 1.10 倍（高大）**。再用每人的专属颜色和特征物区分（代码已按 `MODEL_CONFIG` 处理）。

## 三、动画挑选清单

打开 **Animations** 页签，搜索关键词预览：

| 动画 | 搜索词 | 建议 |
|------|--------|------|
| **Idle 待机** | `idle` | 每人 1 个自然站姿（如 Idle、Idle (Happy) 等，风格越自然越好） |
| **Talking 说话** | `talking` | 说话手势动画，自然即可 |
| Walking 行走 | `walking` | 可选，标准步态 |

> ⚠️ **关键**：全部动画必须从**同一个 T-Pose 角色**下载（骨骼一致，否则动画错乱抽搐）。顺序：先在 Characters 页选定角色 → 保持该角色选中状态切到 Animations 页，下载的动画就属于它。

## 四、下载设置（必须照做）

### 1. 下载角色模型（T-Pose）

- Characters 页选中角色 → 页面右侧会显示角色预览
- **不要**选任何动画，直接点 **Download** 按钮
- 下载设置弹窗中：
  - **Format**: `FBX for Unity (.fbx)`
  - **Pose**: `T-Pose`
  - Skin: 保持默认（含皮肤/骨骼）
- 下载 → 重命名为 `<角色>_tpose.fbx`

### 2. 下载动画（without skin）

- Animations 页选好动画 → 点 **Download**
- 下载设置弹窗中：
  - **Format**: `FBX for Unity (.fbx)`
  - **Skin**: ⚠️ 勾选 **Without Skin**（只要动画数据，不要网格）
  - Frames per second: 30 即可
- 下载 → 重命名为 `<角色>_<动画>.fbx`

### 3. 文件命名与放置

| 角色 | 角色 ID | 文件名前缀 |
|------|---------|-----------|
| 莉安娜 | liana | `liana_tpose.fbx` / `liana_idle.fbx` / `liana_talk.fbx` |
| 巴鲁克 | baruk | `baruk_tpose.fbx` / `baruk_idle.fbx` / `baruk_talk.fbx` |
| 玛格丽特 | margaret | `margaret_tpose.fbx` / `margaret_idle.fbx` / `margaret_talk.fbx` |
| 罗格 | rog | `rog_tpose.fbx` / `rog_idle.fbx` / `rog_talk.fbx` |

**放置目录**：`D:\Create by you.demo\game-prototypes\assets\models\`

```
assets/models/
├── liana_tpose.fbx     liana_idle.fbx     liana_talk.fbx
├── baruk_tpose.fbx     baruk_idle.fbx     baruk_talk.fbx
├── margaret_tpose.fbx  margaret_idle.fbx  margaret_talk.fbx
└── rog_tpose.fbx       rog_idle.fbx       rog_talk.fbx
```

## 五、验收标准

放好文件后：

1. 启动服务器：`cd D:\Create by you.demo\game-prototypes && python server.py`
2. 浏览器打开 `http://localhost:8080`
3. 点「⏭ 等待…」让角色入场
4. 期望：角色入场后显示为**真实模型**（替代盒子人形），站姿播放 idle 动画，说话时播放 talk 动画
5. 服务器控制台应打印：`[模型] liana 加载完成，动画: idle, talk（单位cm → 归一化至 1.75m）` 之类的日志
6. 若某个文件缺失/损坏：该角色**自动保持几何人形**，其余正常，不影响试玩

## 六、常见问题

| 问题 | 处理 |
|------|------|
| 模型加载后**太大/太小** | 前端按包围盒高度自动归一化到 1.75m，理论上无需手动调；若仍不满意，改 `index.html` 的 `MODEL_CONFIG` 里 `scale` 值 |
| 动画**漂移/滑步** | 前端已过滤根骨骼位移（`mixamorigHips.position`），正常不会发生 |
| 动画**抽搐/错乱** | 动画不是从同一个 T-Pose 角色下载的——重新用同一角色下载 |
| 模型**悬空或陷入地面** | 前端自动对齐地面（包围盒 min.y → 0），如仍有问题截图反馈 |
| 加载后角色**颜色怪** | 前端不染色模型贴图，只做微光表现；若贴图本身偏暗是 Mixamo 默认材质，可后续再调 |

## 七、最终选定清单（doubao-vision 逐图分析后确定，2026-08-10）

| 角色 | 选定模型 | 来源 | 文件（放入 assets/models/） | 说明 |
|------|---------|------|--------------------------|------|
| **巴鲁克** | Peasant Man | Mixamo | `baruk_tpose.fbx` + `baruk_idle.fbx` + `baruk_talk.fbx` | 矮壮 + 中世纪冒险装束，完美契合矮人佣兵 |
| **罗格** | Warrok | Mixamo | `rog_tpose.fbx` + `rog_idle.fbx` + `rog_talk.fbx` | 高大 + 兽角战斗服，完美契合兽人战士 |
| **玛格丽特** | Maria 或 Eva | Mixamo | `margaret_tpose.fbx` + `margaret_idle.fbx` + `margaret_talk.fbx` | 女性战斗装（Mixamo 无圣职女性）；游戏内加圣徽特征物 + 白金调色弥补 |
| **莉安娜** | Elf Servant | Sketchfab | `liana_tpose.glb` | CC BY 许可（免费可商用，需署名）；GLB 内嵌动画自动识别 |

### 莉安娜（Sketchfab）下载步骤

1. 打开 <https://sketchfab.com/3d-models/elf-servant-dc76ab92d6a34b12be404b3625877cee>（登录后可见 Download）
2. Download → 选 **glTF/GLB (Binary .glb)**
3. 重命名为 `liana_tpose.glb` 放入 `game-prototypes/assets/models/`
4. 前端自动探测 `.glb`（models.js 已支持）；若模型无动画则静态站立，不影响游戏

### 注意

- Mixamo 三个角色的动画必须从**各自选定角色**下载（骨骼一致）
- 备选：玛格丽特可选 `Paladin w-Prop`（中世纪重甲圣职感最强，但为男性模型）；莉安娜备选 `body base low poly elf`（CC BY，素体）
- CC BY 模型正式发布时需保留署名（当前原型阶段可忽略）
- 罗格备选：Heraklios / Knight


---

## 八、自动化管线（2026-08-12 实测打通 ⭐）

> 这一节是 2026-08-12 通宵实测跑通的全自动流程。**明天要换全部角色模型时直接照做**，无需手动点 Mixamo 网页。

### 0. 前置：保持登录的 Chrome

- Mixamo 登录状态保存在**保活 Chrome profile** 里（CDP 端口 **9222**）。
- 若 Chrome 没开：先启动保活 Chrome 并手动登录 Mixamo 一次，之后流程全自动。
- 检查：`curl http://localhost:9222/json` 能返回页面列表即正常。

### 1. 上传角色 → 自动绑定

脚本：`D:/tools/playwright/cdp_mixamo_walk_fetch.js`

```
1. 新开页签打开 mixamo.com
2. setInputFiles 上传 <角色>.fbx（FBX 二进制，含骨骼）
3. 自动点 Autorig 弹窗 → NEXT → NEXT（轮询最多 60 次等绑定完成）
4. 绑定完成后即处于该角色的 Animations 页
```

> ⚠️ 上传用的源模型**必须含骨骼**（T-Pose 或 A-Pose 均可，Mixamo 自动重绑）。

### 2. 下载动画（自动）

脚本：`D:/tools/playwright/cdp_mixamo_walk_download.js`（对"当前已加载角色"下载指定动画）

```
1. 在 Animations 搜索框输入动画名（如 Walking）
2. 找卡片：必须严格 name === 'Walking'（正则 /^Walking/ 会误中 "Walking Left Turn"）
3. 点 DOWNLOAD → 下载设置：
   - Format: FBX Binary（内部值 fbx7_2019）   ← 实测有效，勿用 FBX for Unity
   - Pose:   T-Pose
   - Skin:   With Skin（tpose） / Without Skin（动画）
4. 等 download 事件 → saveAs 到 assets/models/<角色>_<动画>.fbx
```

> 💡 **换模型的最快路径**：上传新模型绑定后，依次下载 idle / talk / walk，覆盖同名文件，刷新页面即生效。三个动画必须从**同一个 T-Pose 角色**下载（骨架一致）。

### 3. 骨架命名（绑定规则）

| 角色 | 骨架前缀 | 说明 |
|------|---------|------|
| baruk / margaret / rog | `mixamorig*` | Mixamo 标准命名 |
| **liana** | `Bip001*` | 用户原模型自带 Bip 骨架，重上传后仍保留 |

动画按**骨骼名字**绑定（`AnimationMixer.clipAction` → `getObjectByName`），所以即使骨架不同，只要动画和模型来自同一 T-Pose 角色就正常。**换模型后请全组重新下载，不要混用。**

### 4. 验证（每次替换后必跑）

```bash
cd /d/tools/playwright
node cdp_clean_404_check.js   # 4 NPC 全 [idle,talk,walk]，REAL_404: NONE，ERRORS: NONE
node cdp_bone_real2.js        # 骨骼四元数运动验证（talk 臂 0.7+ rad / walk 0.3+ rad）
```

> 缺哪个文件游戏不会崩（自动回落几何人形），但控制台会出现该文件的 404 探测记录。

> ⚠️ **验证方式提醒（2026-08-12）**：判断"模型是否渲染"一律用 **渲染统计 + 像素探针**（见 `cdp_render_compare.js` / `cdp_knight_final.js`），**不要依赖 doubao 对全场景截图的判断**——已实测 doubao 对"白色模型 + 暖光石墙"场景连误报两次"无实体"（而像素探针确认模型正常渲染）。doubao 仅适合辅助看近景/特写。替换模型后跑完上列脚本外，可用：
> ```bash
> node cdp_render_compare.js   # 打印化身/NPC 渲染 draw calls + tris（>0 即渲染成功）
> ```

## 九、当前模型资产状态（2026-08-12 早）

| 角色 | 模型文件 | 动画 | 骨架 | 状态 |
|------|---------|------|------|:---:|
| 莉安娜 liana | `liana_tpose.fbx` | idle / talk / walk | Bip001 | ✅ 白模 `#cccccc`，动画齐 |
| 巴鲁克 baruk | `baruk_tpose.fbx` | idle / talk / walk | mixamorig | ✅ |
| 玛格丽特 margaret | `margaret_tpose.fbx` | idle / talk / walk | mixamorig | ✅ |
| 罗格 rog | `rog_tpose.fbx` | idle / talk / walk | mixamorig | ✅ |
| 玩家 player | `player_tpose.fbx` | idle / walk | — | ✅ |

> **更正（相对本文档第七节）**：莉安娜现用 **Mixamo FBX**（`liana_tpose.fbx`），不再是 Sketchfab Elf Servant（旧 `liana_tpose.glb` 已弃用但未删）。全部角色均为 Mixamo 资产，动画三件套齐备。

**现有测试脚本**（`D:/tools/playwright/`）：`cdp_mixamo_walk_fetch.js`（上传+绑定+下载）、`cdp_mixamo_walk_download.js`（单动画下载）、`cdp_clean_404_check.js`（回归）、`cdp_bone_real2.js`（骨骼运动验证）、`cdp_liana_armtrace.js`（talk 手臂轨迹采样）。
