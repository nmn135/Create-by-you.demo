# AUTOWORK_LOG — 自主工作日志

> 自动续跑会话：2026-08-12 02:57 ~ 12:00（用户 12:00 回收工作）
> 每 30 分钟自动唤醒推进，本文件为唯一进度记录。

---

## ⏱ 当前状态（2026-08-12 05:08）

- **#6 莉安娜动画增强**：✅ 完全交付（白模 + idle/talk/walk + 引擎/doubao 双验收）
- **4 NPC 动画**：✅ 全 [idle,talk,walk]，入场演出就绪
- **场景材质 / 手感 / 氛围**：✅ 完成并回归（403 已根治，控制台零 4xx 零错误）
- **明日换模**：✅ 流程文档化（docs/mixamo-model-guide.md §8 自动化管线），验证脚本就绪
- **Python 后端**：✅ 测试全绿（30/30 · 46/46 · 9 轮零失言）
- 下一步：见文末最新周期；核心任务基本收尾，按 cron 继续推进打磨

---

## 02:57 会话启动

**背景**：用户在 02:57 启动 9 小时自主工作模式。目标：12:00 前持续产出，任何想法都先做出来。

**任务清单**：
- #6 莉安娜动画增强（进行中，卡在 Mixamo 绑骨）
- #5 场景道具/玩家模型替换（待办）
- #9 自动化搭建（本次）
- #10 莉安娜模型最终判定
- #11 夜间自检报告 NIGHTLY_REPORT.md
- #12 测试套件验证

**本次完成**：
1. ✅ cron 自动化挂载：每 30 分钟唤醒（`19,49 * * * *`，id `7f8b819e`，durable）
2. ✅ 任务清单建立（#9-#12）
3. 进行中：模型最终判定（渲染 liana_cleanbiped.fbx）

**关键文件**：
- 源模型（Odin NPC）：`D:\tools\playwright\render_odin\source\NPC_Elf_female.fbx`
- 清理后 Biped（带裙，53骨）：`D:\tools\playwright\liana_cleanbiped.fbx`
- 注意：`nightelf_src/source/PrincessRig.fbx` 是被否决的 night elf 模型（jointN 骨骼），勿再处理

---

## 03:35 周期完成

**用户指示**：转向"建筑场景材质 + 游戏手感"（人物搁置），遇到决策自己选，不卡死。9小时自主工作。

### 模型最终判定（#10，挂起）
- ✅ 修好 `fbx_clean_biped.py` 两个 bug：① 删 DummyRoot 级联清空骨架 → 删前重挂子骨骼；② 旋转方向 +90°→-90°（源模型头朝 -Y）
- ✅ doubao 验证 `liana_cleanbiped.fbx`：头朝上、穿裙、双腿完整连续、A-pose
- ⏸️ 未做 Mixamo 上传测试（用户中断转向其他工作），已挂起，回头的唯一待办

### 场景材质（#13）✅
- index.html PBR 块：法线贴图接入（石墙/木地板/木梁/深色木，35 网格带 normalMap）
- 新增：木质天花板（y=7.65，俯瞰隐藏、FPS 显示，`onModeChange` 联动）
- 新增：四角石柱 4 根（0.5×7×0.5，石墙纹理+法线）
- 新增：南北墙 4 盏暖色壁灯（PointLight 无阴影）
- 验证：CDP 程序化检查 `{ceilingExists:true, columns:4, normalMappedMeshes:35}` ✓

### 游戏手感（#14）✅
- fps_controller.js：水平速度平滑插值（accel=14/decel=12，起步顺滑/松键滑行）
- 头部晃动（走/跑不同频率幅度）+ 奔跑 FOV +9° 平滑扩张
- 脚步声：audio.js 新增 `step(running)`，index.html 接线，每跨一步低频脉冲
- 验证：CDP 行走测试 `{P1加速中2.58m/s, P2满速4.0, FOV_DELTA+8.5°, ERRORS:NONE}` ✓

### 其他
- 重启卡死的 keep-alive Chrome（CDP 连接超时），profile 保留 Mixamo 登录
- 已知 404：`liana_tpose.fbx`、`baruk_walk.fbx`、`margaret_walk.fbx`（#5/#6 遗留，非材质问题）

### 测试套件验证（#12）✅
- `test_state_machine.py`（根）：**30 通过 / 0 失败** ✓
- `tests/test_endings.py`：**46 通过 / 0 失败** ✓
- `tests/test_dialogue_scenarios.py`：完成 — 3 策略 × 3 轮 = 9 轮对话模拟，0 失言，触发结局：无，已存 `tests/scenario_results.json`
- 执行方式：`PYTHONIOENCODING=utf-8 python <file>`（pytest 未安装，直接运行）
- JS 语法自检：src 下 8 个模块 `node --check` 全部 OK

### 夜间报告（#11）✅
- `NIGHTLY_REPORT.md` 已追加 2026-08-12 凌晨轮汇总（见文件尾部）

### 第二波（03:24~）：手感+氛围续做
- ✅ #16 **跳跃/落地音效 + 横扫相机侧倾**：audio.js 加 `jump()`/`land(impact)`，fps_controller 加 `onJumpSound`/`onLandSound` 回调 + A/D 横扫时相机 roll（跑 0.05/走 0.028）。CDP 验证：bank 0.0267、jumpCount=1、landCount=1 impact=0.77
- ✅ #15 **壁灯火焰动效**：4 盏壁灯加火焰光球+光晕+木质灯座，animate 循环闪烁（光强 5.5±1.2 抖动、火焰缩放±0.22），低画质熄灭远端。CDP 验证：4.30→6.51→4.88 抖动 ✓ 豆包确认暖色光源
- ✅ #17 **空间音频**：animate 按玩家到最近光源（4火把+4壁灯+吊灯）距离平滑调 fire/drone 音量（8m 内火声渐强、角落闷响更沉）。CDP 验证：近火把 fireVol 0.0324↑/drone 0.0199↓，中心 0.0174↓/0.0239↑
- 🐛 **修复音频 setter 误用**：`setFireVolume()` 不存在（audio.js 是 ES6 属性 setter `fireVolume=`），曾每帧抛异常中断 animate → 改属性赋值
- ✅ #18 **综合回归**：4 NPC 模型全加载、天花板✓、壁灯火焰4✓、35法线网格✓、第三人称Knight化身✓、0页面错误（仅3个已知404探测）
- ✅ **挂毯纹理修复**：豆包反馈南墙挂毯是"纯红无纹理方块"（像加载失败）→ atmosphere.js 程序化 canvas 织物纹理（竖条纹+金边+菱形徽记），豆包确认图案规整

### 03:45 追加
- ✅ **下蹲 FOV 收缩**：蹲下 FOV −5°（潜行感），奔跑 +9° 保持。CDP 验证：蹲 45.14（−4.86）/ 回正 49.86 / 跑 58.74（+8.88），0 错误
- ✅ **旗帜纹理**：atmosphere.js 程序化旗帜（蓝底条纹+金边+八芒星徽），豆包确认非纯色
- ✅ #5 **场景道具/玩家模型替换完成**：家具（哥特柜/木桌/木椅/扶手椅）+ 玩家 Knight 化身 + 4 NPC 模型全部就位；仅剩 walk 动画缺失（baruk/margaret，需 Mixamo，归入 #6）
- ✅ #19 **设置持久化验证**：灵敏度 2.0 / toggleKey v / runKey alt 刷新后正确恢复
- 🐛 **自动降档永久锁低修复**：`settings.setQuality(q, false)` 新增 persist 参数，自动降档不再写 localStorage（一次性降档，改回由用户决定）。验证：headless 自动降档后 localStorage 仍为 medium ✓

**最终综合回归（03:45）**：4 NPC 模型✓ + 天花板✓ + 壁灯火焰4✓ + 35法线网格✓ + Knight化身✓ + 191网格/16灯光/20纹理 + 0非404错误 ✓（仅3个已知404探测：baruk_walk/margaret_walk/liana_tpose.fbx）

**下一步**：继续打磨至 12:00（cron 每 30 分钟唤醒续跑）。

---

## 04:0x 周期 — Mixamo 突破（#6 莉安娜动画完成）

**里程碑**：挂起数小时的 Mixamo 上传管线终于打通，莉安娜动画增强（#6）**功能上完成**。

### 打通的关键路径（已固化到脚本，可复用）
1. **上传**：reload 页面 → 点 "UPLOAD CHARACTER" → 等 2.5s → `setInputFiles('input#file', file)`（隐藏 input，非 filechooser 事件）→ 监控 API `POST /api/v1/characters` 202 → `.autorig-modal` → 连点两次 NEXT（"CHANGE CHARACTER" 弹窗）
2. **动画下载**：Animations 页 scroll-load 产品列表 → 点 `.product-product-animation` 卡（名称/描述前缀匹配）→ 主 DOWNLOAD → 设 Format=`fbx7_2019`(FBX Binary)、Pose=`t-pose` → 弹窗 DOWNLOAD → `waitForEvent('download')` → `saveAs()`
3. **搜索**：点 input → `fill('')` → `pressSequentially(q)` → `press('Enter')`（value-setter 方案无效）
4. **骨骼关键事实**：Mixamo 下载的 FBX 保留 3ds-Max Biped 骨名（`Bip001`），**不是** `mixamorig`。所有动画文件共用同一骨架 → 直接绑定即可

### 已安装资产
| 文件 | 大小 | 说明 |
|------|------|------|
| `liana_tpose.fbx` | 5.5MB | T-pose，Bip001 骨架，106 LimbNodes / 318 bones / 6 SkinnedMeshes，白灰素模 |
| `liana_idle.fbx` | 5.85MB | "Idle"(Looking Over Both Shoulders) 循环 |
| `liana_talk.fbx` | 5.83MB | "Talking"(Asking A Question With Two Hands) 3.93s — 对话专用 |

### 验证（cdp_liana_anim_test.js）
`clips=[idle,talk]`、`318 bones`、`talkDur=3.93s`、playTalk 播完自动回 idle 循环 ✓

### 程序化纹理实验 → 已回退（用户决策）
- 做过一版程序化深绿长袍+金边（`_makeDressTexture`/`_makeSkinTexture`/`applyLianaProceduralTextures`），豆包确认可用
- **用户反馈"还是白模好一点，现在是纯绿色的"** → 移除纹理调用 + 清理死代码 helper
- **决策记录**：人物模型明天整体替换，视觉优先级低；白模+动画即当前最优态

### 已知无害错误（已定位）
- 404：`liana_tpose.fbx`/`baruk_walk.fbx`/`margaret_walk.fbx` 探测（baruk/margaret walk 仍未装）
- 403：FBX 内部纹理引用 `D:/tools/playwright/render_odin/source/NPC_*`（Mixamo 已剥离纹理，无害）

### 状态
- ✅ #6 莉安娜动画增强：**功能完成**（上传+3动画+游戏内验证），视觉待明日换模型
- ⏸️ 待办：baruk/margaret walk 动画（同管线，用户指令人物优先级低，暂缓）
- 人物视觉工作按用户指示**停止**（白模保留）

---

## 04:2x 周期 — baruk/margaret walk 动画补全（最后 404 清除）

**决策**：NPC 入场是 1.2m/s 走进步态（index.html 入场流程 `playAnimation(k,'walk')`），缺 walk 会滑步。walk 属**游戏手感**（非视觉决策），用户优先级指向手感 → 顺手补全。

**执行**（复用已打通管线，新脚本 `cdp_mixamo_walk_fetch.js` + `cdp_mixamo_walk_download.js`）：
1. 上传 `baruk_tpose.fbx` → autorig（~20s）→ 下载精确 "Walking"(Walking With A Swagger) → `baruk_walk.fbx`（3.74MB）
2. 上传 `margaret_tpose.fbx`（16MB，Maria With Skin）→ 下载同动画 → `margaret_walk.fbx`（16.1MB）

**教训**：动画卡名必须**严格精确匹配**（`name === 'Walking'`），`/^Walking/` 会误中 "Walking Left Turn"。

**验证**（cdp_walk_verify.js）：
- 4 NPC 全加载；clips：baruk=[idle,talk,**walk**] 1.03s、margaret=[idle,talk,**walk**] 1.03s、rog=[idle,talk,walk]、liana=[idle,talk]
- walk 播放确认（baruk/margaret 动画运行中）
- 服务器 200：baruk_walk 3.74MB / margaret_walk 16.1MB
- **剩余真实 404 仅 `liana_walk.fbx`**（liana 无 walk 属预期探测）

**最终动画矩阵**：
| 角色 | idle | talk | walk |
|------|:---:|:---:|:---:|
| baruk | ✅ | ✅ | ✅ |
| margaret | ✅ | ✅ | ✅ |
| liana | ✅ | ✅ | ✅（追加，stage3 入场需要） |
| rog | ✅ | ✅ | ✅ |
| player | ✅ | — | ✅ |

### 04:3x 追加 — liana_walk 补齐（控制台 100% 干净）

- 查 `STAGE_ENTRANCE_NPC = {1:'rog',2:'baruk',3:'liana',4:'margaret'}` → **liana 在 stage 3 也是走入式入场**，缺 walk 会滑步
- 复用管线上传 `liana_tpose.fbx` → 下载 Walking → `liana_walk.fbx`（5.66MB）
- **最终验证（cdp_clean_404_check.js）**：4 NPC 全 [idle,talk,walk] · `REAL_404: NONE` · `ERRORS: NONE` ✓

### 04:4x 追加 — 骨骼运动深度验证（动画确实在动）

> 曾虚惊一场：初测采样骨骼**位置**得 `movedBones:0`，误判动画未绑定。实为**测试方法错误**——动画主要**旋转**骨骼（本地位置恒定）。改采**四元数**后全部证实：

| 角色 | 动画 | 采样骨 | 最大四元数位移 | 结论 |
|------|------|--------|:---:|:---:|
| liana | talk | 左上臂 | **3.306** | ✅ 大幅手势 |
| liana | idle | 头部/上身 | **3.452** | ✅ 转头环视 |
| margaret | walk | 左臂 | **1.031** | ✅ 摆臂循环 |
| baruk | walk | 左右小腿 | **1.003** | ✅ 迈步踢腿 |
| baruk/margaret/rog | idle | 骨骼 | **1.0+** | ✅ 呼吸/摆动 |

**结论**：Mixamo 动画管线**端到端真实生效**（绑定→播放→骨骼旋转→蒙皮形变），4 NPC 均非"活雕像"。测试脚本：`cdp_bone_real2.js` / `cdp_baruk_walk_cycle.js` / `cdp_idle_check.js`。

### 04:5x 追加 — 对话防打断修复（walk 全齐后暴露的交互 bug）

**发现问题**：给全部 NPC 补上 walk 后，漫游逻辑（timer 3-9s 触发 `playAnimation(k,'walk')`）会**在对话中打断 talk 动画**——实测 playTalk 后 1.5s 内 current 变 walk。

**根因**：index.html 漫游循环无 `current==='talk'` 守卫；此前 rog 有 walk 已潜在存在，全补齐后影响所有角色。

**修复**：漫游循环顶部加守卫——`current==='talk'` 时暂停漫游（重置 timer、清 target、continue），对话结束回 idle 后自然恢复。

**验证**：playTalk 后连续采样 3s，`TALK_SAMPLES: [talk×6]` 不被中断 ✓；全量回归 `REAL_404: NONE` / `ERRORS: NONE` ✓

### 04:36 周期（cron 续跑）— 测试套件全绿

| 套件 | 结果 |
|------|:---:|
| `test_state_machine.py` | **30/30** ✓ |
| `tests/test_endings.py` | **46/46** ✓ |
| `tests/test_dialogue_scenarios.py` | **9 轮 / 0 失言** / 触发结局：无 ✓ |

- 执行方式：`PYTHONIOENCODING=utf-8 python <file>`（pytest 未安装）
- 3D 原型：上一轮 `cdp_clean_404_check.js` 已确认 index.html 无解析错误（浏览器加载零错误）
- **结论**：后端状态机/结局/对话逻辑无回归；本轮无待修复问题

### 04:5x 周期（cron 续跑）— 莉安娜 talk 视觉确认 + 相机/门控/遮挡三连排障

**目标**：给 #6 莉安娜动画增强做**视觉级**验收（此前只有骨骼四元数数据，缺一张"说话手势中"的实拍图）。

**排障三连（都是测试侧问题，不是游戏 bug）**：
1. **相机被 FPS 控制器覆盖** — `fc.setMode('fps')` 会重置 camera 到 `this.pos`（初始 spawn (0,0,-5.5)）并把 yaw 置 π。此前同 evaluate 里 setMode 后立刻读 camPos 读到的是"下一帧未更新"的旧值 → 误以为相机没摆好。**解法**：setMode 后等几帧（600ms）再验证/截图，camera 即落到 fc.pos。
2. **阶段门控把 NPC 重新隐藏** — `fetchGameState` 每 4s 轮询服务器，把 `npcMeshes[k].visible = currentPhase >= NPC_ENTRANCE_STAGE[k]` 重新应用。测试强制 `group.visible=true` 会被轮询覆盖（liana stage=3，服务器 phase 未到则藏起）。**解法**：在 index.html 三个门控点加 `window.__forceNpcVisible === true` 调试开关（沿用 `__forceQuality` 先例，仅自动化测试用，无副作用）。
3. **新手操作指南卡 `g-sub`/`g-card` + 大厅中央守护灵装置遮挡角色** — `.g-card` 是居中"怎么玩·操作指南"卡片（380×762 大卡），另有一个 **3D 守护灵装置**（粉条纹+斜杠圆图标，3D 道具非 DOM）浮在角色上方。**解法**：截图前 CSS 隐藏 `.g-card/.g-sub` 等 UI；相机移到西南角落 (-6.5,0,-5.8) 避开中央装置。

**验收结果**：
- 相机确认停在 fc.pos（(-6.5, 1.6, -5.8)），liana `visible=true`、`current='talk'` 截图时刻仍为 talk。
- **引擎内硬证据**：`cdp_liana_armtrace.js` 采样 Bip001-R-UpperArm 四元数轨迹，talk 全程 0.55s→2.3s 的 delta = **1.137 / 0.823 / 0.702 / 0.712 / 0.963 / 0.772 rad**（持续 ≥40° 大幅摆臂），clip 时长 3.93s，全程 `cur='talk'`。
- **doubao 视觉确认**：画面中 liana 手臂抬起、"确实很像正在说话交流、抬手比划的状态" ✓
- **材质确认**：liana 模型 = 白模（`#cccccc`，无贴图，6 个 skinned mesh）；doubao 描述的"金发/铠甲"是暖光下白模阴影的幻觉。

**结论**：#6 莉安娜动画增强**视觉+数据双重验收通过**。白模 + idle/talk/walk 全部真实生效。测试脚本：`cdp_liana_talk_v5/v6/v7.js`、`cdp_liana_armtrace.js`、`cdp_liana_mat.js`。

### 04:5x 周期（cron 续跑）— 场景完整性核验 + 明日换模管线文档

**场景核验**（`cdp_scene_sweep2.js`）：全场景遍历 mesh 几何/颜色/位置
- 2 桌 + 4 长凳（两侧 ±4.5）✅ 有意摆放（此前误判为"中央重复堆叠"——实为局部坐标重复）
- 中央 4 色球 = **种族关系指示点**（clanDotColors 精灵/矮人/人类/兽人）✅ 有意
- 守护灵悬浮装置、壁灯火焰球、梁柱 ✅ 均为有意道具
- **结论：场景无残留测试几何/垃圾物件**，doubao 所述"彩色测试几何体"为关系点的误读

**明日换模准备**（用户已定明天全换角色模型）：
- 更新 `docs/mixamo-model-guide.md`，新增第八节**自动化管线**（保活 Chrome CDP 9222 → 上传 autorig → 精确动画卡匹配 `name==='Walking'` → Format=FBX Binary `fbx7_2019` + Pose=T-Pose → saveAs 覆盖）+ 第九节**当前资产状态表**（4 NPC 全 [idle,talk,walk]，liana 为 Bip001 白模，非 Sketchfab）
- 说明换模最快路径：上传新模型 → 同角色连下 idle/talk/walk → 覆盖刷新即生效

**新增调试开关**：`window.__forceNpcVisible === true`（index.html 三处阶段门控点，沿用 `__forceQuality` 先例，仅自动化测试用，无副作用）

### 05:0x 周期（cron 续跑）— NPC 脚步声 + 隐藏 403 bug 修复 + rog walk 复核

**1. NPC 脚步声（游戏手感）**：
- `src/audio.js` `step(running, volScale=1)` 增加距离衰减参数
- `index.html` NPC 移动循环：入场（entering）与漫游（walking）各加步距累加器，**每 ~0.6m 一声**，音量随与玩家距离衰减（`1 - d/14`）
- 纯 Web Audio 合成（无外置文件），音频未启动时静默 no-op，安全
- 验证：页面零错误；AudioContext 需用户手势才发声（自动化中静默属预期）

**2. 隐藏 403 bug（重要修复）**：
- `cdp_403_check.js` 发现 4 个 liana FBX **内嵌 Windows 绝对路径纹理引用**（`D:/tools/playwright/render_odin/source/NPC_female_body01_021_.png` 等 6 个），每次加载都触发 `/models/D:/...` → **6×403 控制台噪音**
- 此前的"控制台 100% 干净"只查了 404，**403 一直存在而漏检**（现已加 403 检测）
- 修复：`src/models.js` 加 `THREE.LoadingManager.setURLModifier`，拦截 `[A-Za-z]:[\/]` 绝对路径 URL → 替换为 1x1 透明 GIF data URI（防御式，任何模型带坏路径都不再 403）
- 验证：`cdp_403_check.js` **TOTAL: 0**；`cdp_clean_404_check.js` 全绿（4 NPC 全 [idle,talk,walk]，REAL_404: NONE，ERRORS: NONE）

**3. rog walk 复核（排除假警报）**：
- 旧 `cdp_bone_real2.js` 采样 rog walk d12=0.007 疑似无动画 → 用 `cdp_rog_walk_trace.js` 8 点采样 3.5s：手臂 0.59/0.58 rad、大小腿 0.35~0.68 rad，**全肢体真实运动** ✓
- 结论：旧脚本采样窗太短/相位不佳导致假阴性，非游戏 bug。rog 入场动画正常

### 05:1x 周期（cron 续跑）— 入场朝向修复 + 状态恢复

**发现问题**：NPC 入场（walk-in）只平移不转向——baruk 基转 -π/2 面西墙，入场时朝 (-5,3.5) 走会**横滑入场**；liana 面 +z 走 45° 对角线。

**修复**：index.html 入场分支加**平滑转向移动方向**（`atan2(dx,dz)`，lerp 5*dt），入场自然步态；到达后既有 face-player 逻辑接管转向玩家。

**验证**（`cdp_entrance_facing.js`，先 /api/reset 再推 stage 2）：
- baruk 入场途中 rotY = **-0.416** ≈ 移动方向 atan2(-5,12)=-0.395 ✓（不再 -1.57 横走）
- 到达后 rotY = **2.634** = face-player 转向玩家（atan2(5,-9)=2.63）✓ 既有行为完好
- 回归：0 4xx · 0 错误 · 4 NPC 全 [idle,talk,walk] ✓

**服务器状态**：测试用 /api/reset + 推进后已恢复 stage=4（全员在场）。

### 05:1x 周期（cron 续跑）— 晨间恢复路径整备 + 材质/手感核验

**目的**：确保 12:00 起床后 5 分钟进入游戏即可试玩，恢复路径准确反映当前 3D 状态。

**1. PLAYTEST_CHECKLIST 更新到 08-12 版**：
- 新增 §九「08-12 晨间版新增状态」：WASD 行走 + 4 白模 NPC + 入场朝向 + 脚步声 + 控制台零错误 + 莉安娜抬手动画 + 明日换模提示
- 修正 §八 第 1 条：**开场卡片已 bypass，直接进入第一人称**（实测确认，见下）
- frontmatter 日期 → 08-12

**2. 材质审计**（`cdp_material_audit.js`，201 个网格）：确认建筑材质健康——
- 石墙 8 面带纹理（#8a7f75）、地板 4 块纹理（#6a5a45/#6a625c）、木质 28 块粗糙 0.85~0.9 有金属度微调
- 无残留"纯色盒块"；纯色均为有意的木/铜/彩布材质

**3. 开机流程核验**（`cdp_boot_flow.js`）：开场卡 bypass → 直接 FPS 模式（pos 出生点 0,0,-5.5）→ 4 NPC 全部在场可见 → 零错误 ✓

**4. 移动手感仿真**（`cdp_move_check.js`，合成按键）：W 前进 5.05m/1.5s ≈ 4.0m/s；Shift 跑 5.50m/1.0s 更快；空格跳 y=0.56；零错误 ✓
（Playwright 修饰键需大写 `Shift`，已修脚本）

**服务器状态**：stage=4 未动。

### 05:2x 周期（cron 续跑）— 测试套件全绿 + 玩家模型核验

**1. Python 测试套件复验**（PYTHONIOENCODING=utf-8）：
- `test_state_machine.py`：**30/30 通过** ✓
- `tests/test_endings.py`：**46/46 通过** ✓（含 5 结局隔离性、安慰/挑拨前置）
- `tests/test_dialogue_scenarios.py`：exit 0，9 轮对话 0 失言（该测试用真实 DeepSeek API 模拟玩家，报告"触发结局: 无"属预期——它验证对话机制而非结局）

**2. 玩家模型（#5）TPS 核验**（`cdp_player_model.js`）：C 键切 TPS → 化身 = **REAL_KNIGHT**（占位盒已移除，child=模型 Group）→ idle+walk 双动画加载 → TPS 可见 → **零错误** ✓

**3. NPC 漫游逻辑复查**（index.html 3877-3969）：入场走位→到达 idle 3~9s→家区 1.2m 半径随机小走；talk 时暂停漫游；脚步随距离衰减。逻辑健康，无卡死路径 ✓

**服务器状态**：stage=4 未动。

### 05:2x 周期（cron 续跑）— 测试套件全绿 + 玩家 Knight 渲染确认

**1. Python 测试套件复验**（PYTHONIOENCODING=utf-8）：
- `test_state_machine.py`：**30/30 通过** ✓
- `tests/test_endings.py`：**46/46 通过** ✓（5 结局隔离性、安慰/挑拨前置全过）
- `tests/test_dialogue_scenarios.py`：exit 0，9 轮对话 0 失言（真实 DeepSeek 模拟，报告"触发结局: 无"属预期——它验证对话机制）

**2. 玩家 Knight 模型（#5）渲染确认**：
- 现象：doubao 对 TPS 截图误读"玩家无实体、只有白点"，引发排查
- **结论：Knight 正常渲染**，无游戏 bug。客观证据（`cdp_render_compare.js`）：化身单独渲染 = 3 draw calls / 13,122 tris；完整场景 = 138 calls / 165,926 tris（含化身）；TPS 视角化身躯干区域 **49.3% 亮色像素**（#997d64 = 白模+暖光+ACES 色调映射）
- **方法论教训**（记入日志）：① 排查脚本用 `scene.traverse` 隐藏其他对象时，会**误隐藏目标的子孙网格**（`o !== target` 不排除后代）→ 多个中间脚本得出假阴性；② doubao 对 3D 全场景截图的"未渲染"判断**不可靠**（此前的 liana 验证也是 doubao 但那次成功，说明它不稳定）——判断渲染要用像素探针/渲染统计
- 新增 `window.__renderer` 调试钩子（index.html:1067，只读，与 `__getModelManager` 同风格），供未来像素级自动化
- **决定性数据**（`cdp_center_scan.js` 全帧亮度扫描）：画面中央 (400..1520, 150..800) 亮暖色像素 ~5.3 万（采样 3309×16），质心 (979,472) = 屏幕正中，与 Knight 位置吻合；再加上化身单独渲染 13,122 tris → **Knight 确凿在画面中央**
- **doubao 可靠性结论**：对"白色模型 + 暖光石墙"全场景截图的分割不可靠（连试两次都误报"无实体"），但此前 liana 近景验证它能识别——**今后模型存在性判断一律用像素探针/渲染统计，doubao 仅作辅助**（换模管线文档已含此警示，见下）

**3. 漫游逻辑复查**（index.html 3877-3969）：入场→到达 idle 3~9s→家区 1.2m 小走；talk 时暂停漫游；无卡死路径 ✓

**服务器状态**：stage=4 未动。

### 05:3x 周期（cron 续跑）— props 加固 + 真实 AI 对话端到端验证

**1. props.js 代码自检 + 加固**（优先项 5）：
- 复查 `src/props.js`：4 类道具 FBX（柜/桌/椅/扶手椅）全部加载成功，**19 件已放置**，0 4xx
- 发现隐患：props.js 用裸 `FBXLoader`，没有 models.js 的 LoadingManager URL 拦截——若道具 FBX 也内嵌 Windows 绝对路径纹理（liana 同源隐患）会打隐藏 403
- 修复：加同款 URL 拦截（`[A-Za-z]:[\/]` → 1x1 透明 GIF）
- 验证（`cdp_props_check.js`）：4 道具类型 + 命名网格（GothicCabinet_01_*、WoodenTable_01、WoodenChair_01、ArmChair_01）全在，PROP_4XX: NONE，道具日志正常

**2. 真实 AI 对话端到端验证**（此会话首次，覆盖 `--no-ai` 之外的活体链路）：
- POST /api/chat `{"input":"你好，请问你是谁？","target":"rog"}` → **真实角色回复**："罗格·铁牙。铁牙部落的。你问这个做什么？"（非模板）
- 完整返回：mood/slip_occurred/hints/环境/信任值——**AI 链路（前端契约 → server → 状态机 → DeepSeek）全通**
- 结论：用户清单中"对话全是模板回复"的排查项**确认为非问题**，AI 在线

**3. 服务器状态**：聊天测试污染了 rog 信任（30→31）与默认目标 → 已 `/api/reset` + 推进 ×4 恢复 **干净 stage=4 全员在场**（无测试残留）。

### 05:3x 周期（续）— 60 秒浸泡稳定性测试

**`cdp_soak.js`**：60.4s 持续 W/D 移动 + C 切视角 + 空格跳 + H 帮助面板循环：
- **AVG FPS 163.7 / MIN 130.0**（3s 窗口帧计数差分，性能健康）
- **ERRORS: NONE**（60s 内零累积错误——漫游/切视角/跳/UI 反复触发无异常）

**结论**：3D 原型稳定性与性能达标，可作为 12:00 试玩的最终信心信号。服务器 stage=4 干净。

### 05:3x 周期（续）— 每日决策摘要

用户触发写 `DAILY_DECISION.md`（08-12 05:30 版）：昨晚成果表（模型/动画/手感/材质/0-4xx/AI端到端/测试全绿/60s浸泡）、❓决策点 4 个（换模方案、打磨方向、liana 是否重传建议跳过、手感参数）、今晚计划、风险（换模骨架、doubao 不可靠、服务器内存态）。已写入。

### 05:5x 周期（cron 续跑）— UI 聊天流端到端（用户真实路径）

**`cdp_chat_ui.js`**（优先项 6 冒烟验证的补全）：
- 前置检查：5 个 NPC/守护灵标签全部可见
- 点 rog 标签 → 输入「你是谁？为什么会来这里？」→ Enter → **真实 AI 回复渲染进聊天历史**："罗格（抬头看了一眼）罗格·铁牙。矿工，比你想的多见过几年石头。至于这地方……地底总比太阳底下强……"
- 玩家消息也正确渲染；**零错误**
- 至此覆盖了用户 12:00 的完整操作路径：进入→走动→点标签→对话→收到回复

**服务器状态**：测试会话已清理，`/api/reset`+推进×4 恢复 **stage=4 全员在场、0 互动残留**。

### 06:2x 周期（cron 续跑）— H 帮助面板修复 + 冷启动验证 + 面板切换全绿

**1. 修复真实 UI bug：H 帮助面板不能关闭**（优先项 6 冒烟验证发现）
- 根因：`index.html` 键盘处理里 H 键无条件调 `guidance.showHelp()`（只移除 hidden），第二次按 H 面板不关
- 修复：改为 toggle——`#g-help` 有 `hidden` 类 → showHelp，否则 hideHelp
- 验证（`cdp_hhelp2.js`，class+opacity 双查）：opacity 0→1→0→1，`hasHidden` true→false→true→false，**四次按压完全正确**

**2. 冷启动验证（模拟全新浏览器）**：`cdp_coldstart.js` 清空 localStorage → 刷新 → 直接进第一人称、4 NPC 全员可见、目标面板正确、零错误

**3. 面板切换 V/M/H 三键全部确认（消除此前矛盾）**
- 三个面板隐藏机制不同：`#relationship-panel`/`#memory-panel` 用 display/visibility 类、`#g-help` 用 `.g-overlay.hidden`（opacity:0）→ 用同一套 computed-style 检查必然互相矛盾
- 用 Playwright 权威 `isVisible()` 复测：**V/M 均 [false,true,false,true] TOGGLES_OK**；H 因 opacity 隐藏对 isVisible 恒 true（方法学局限），以 cdp_hhelp2 的 class+opacity 结论为准
- **最终结论：V/M/H 三面板切换全部正常，此前疑云均为测试方法假象，非游戏 bug**

**服务器状态**：本轮全部为浏览器纯前端操作，`/api/state` 复核 stage=4、4 NPC 在场、0 互动残留，未污染。

### 06:3x 周期（cron 续跑）— 12:00 试玩前「一键冒烟」交付

**产出：`cdp_smoke_1200.js`（13 项 PASS/FAIL 总表，一条命令）**
- 覆盖：服务器 stage / 4 NPC 加载在场 / 动画三件套 / FPS 模式 / 目标面板 / 零404(fbx·glb) / 零403 / 零页面错误 / H·V·M 面板开关 / 冷启动干净进入+零错误
- **实测 13/13 全绿**，一次通过
- 合并了此前分散的检查方法学结论：H 用 class（hasHidden），V/M 用 Playwright isVisible——同一脚本内不再互相矛盾
- 附 `试玩前冒烟.bat`（双击即用，须先起 server.py）

**报告更新**：NIGHTLY_REPORT「12:00 怎么开始」段加入一键冒烟用法；动画/模型/手感回归与 `cdp_chat_ui.js` 各归其位

**服务器状态**：`/api/state` 复核 stage=4、4 NPC 在场，冒烟全程无污染。

### 06:3x 周期（续）— 试玩就绪收尾（清单指引 + 实况截图）

- PLAYTEST_CHECKLIST §九 顶部加入「先跑一键冒烟」指引；与 12:00 实况核对 §九 全部条目准确（stage=4 全员在场/白模三动画/0 4xx/H 键指南）
- `cdp_final_shot.js` 实况截图：`shots/state_0615.png`（1920×935）——FPS 视角面向 NPC 聚集区，渲染 35 calls / 68,839 tris / frame 900，**零错误**
- 服务器复核 stage=4、4 NPC 在场，全程无污染

**当前整体状态**：所有优先项（#2 莉安娜动画 / #5 道具模型 / #4 测试套件 / #5 代码自检）此前均已验收；本轮补齐「12:00 试玩前体检」一键入口。**截至 06:35 无遗留阻塞，等待 12:00 试玩反馈。**

**补充（06:38）**：`cdp_smoke_1200.js` 连续两轮运行均 **13/13 全绿且输出一致**（确定性确认，非碰运气）——12:00 一键体检可放心依赖。

### 06:5x 周期（cron 续跑）— 对话测试挂起修复 + 服务器重启热更新 AI 管线 + 冒烟确定性修正

**1. 真实 bug：test_dialogue_scenarios.py 挂起（0 输出，EXIT 被管道 tail 掩盖）**
- 根因：`deepseek-v4-pro`（intent 解析专用模型）**此刻持续返回空内容**（"Expecting value: line 1 column 1"），3 次重试全空后只能随机兜底；且卡死的请求每次耗 30s 超时 → 整测看起来"永远卡住"
- 修复：`src/ai_pipeline.py::parse_intent` 重试序列改为 `[INTENT_MODEL, INTENT_MODEL, REPLY_MODEL]`——末次兜底切 `deepseek-v4-flash`（实测正常）
- 验证：9 轮对话 **0 失言**，EXIT=0 完成；意图多样（probe_conflict 90% / offer_comfort 95% 等），仅 3 轮走设计内随机兜底

**2. 关键发现：游戏服务器与 text-prototype 共用同一份 ai_pipeline**（`server.py` 第 46 行 `sys.path.insert(0, TEXT_PROTO_DIR)`）→ 修复同时惠及 3D 游戏聊天
- 但运行中的服务器（PID 16336）内存里是旧代码 → **重启服务器热更新**，恢复 stage=4
- 重启后真实验证：rog 聊天正常（真实角色回复），冒烟全绿

**3. 冒烟测试 V/M 检查方法学修正（第三次同类课）**
- 现象：重启后 V/M 连续 2 轮 `[false,true,true,true]`（第 2 次按键"关不掉"）——一度疑为真 bug
- 根因：`#relationship-panel`/`#memory-panel` 用 `visibility+opacity` + **0.3s transition** 隐藏；Playwright `isVisible()` 在淡出过渡期间仍返回 true；测试 300ms 等待卡在过渡边界（此前通过是踩线）
- 修复：V/M 改查 `visible` 类（处理器同步切换，无时序依赖）——与 H 面板"查 class"同一原则
- 验证：修正后**连续两轮 13/13 全绿**，确定性确认

**服务器状态**：stage=4、4 NPC 在场、0 互动残留。12:00 试玩链路（修复后 AI 管线 + 确定性冒烟）全部就绪。

### 07:2x 周期（cron 续跑）— 全阵容 AI 验证 + 手感调参速查文档

**1. 全阵容真实 AI 链路验证（此前只测过 rog）**：补 liana/baruk/margaret 各一次短调用
- liana（问日记页）→ 回避式回应，符合"藏着秘密"人设 ✓
- baruk（问矿工密语）→ 冷怼"你连矿坑都没下过"，矮人式防备 ✓
- margaret（问教会立场）→ "罪孽留下的余烬…烧焦的皮肤和沉默的灵魂"，裁判官冷面 ✓
- **结论：4 人 persona 全部正常，无配置 bug；验证后已恢复干净 stage=4**

**2. 新产出：`docs/game-feel-reference.md` 手感调参速查**
- 当前参数全表（moveSpeed 4.0 / runSpeed 7.5 / velY 5.2 / gravity 14 / accel 14 / decel 12 / FOV 50 +9/-5 / 灵敏度）+ 行号
- 「用户反馈 → 改哪里」对照表：快/慢/飘/重/肉/发飘/晕/晃 各自改哪个参数、建议值
- 应用方法：改 `fps_controller.js` → 刷新浏览器即可（前端参数，无需重启服务器）→ 改后跑冒烟回归
- DAILY_DECISION ❓#4 已链接到本文档

**服务器状态**：stage=4、4 NPC 在场、0 互动残留。

**下一步**：等 12:00 试玩反馈。反馈后按 `game-feel-reference.md` 秒级调参 + 冒烟回归；换模则跑 `docs/mixamo-model-guide.md` §八。

### 07:5x 周期（cron 续跑）— 真 bug：UI 聊天超时收不到回复 + 修复

**现象**：重启后的服务器上 `cdp_chat_ui.js` 显示 `NPC_REPLY: NONE (timed out)`，玩家消息渲染正常、零控制台错误；但直连 /api/chat 只花 4.6s。

**根因（两处叠加）**：
1. 前端聊天请求 `AbortSignal.timeout(15000)`（index.html 2734 行）——服务器 AI 路径若 >15s 就被前端掐断，catch 静默降级
2. `parse_intent` 此前 v4-pro 连试 2 次才轮到 flash 兜底；v4-pro 卡顿单次最多 30s（客户端超时）→ 总时长轻易破 15s

**修复**：
- `src/ai_pipeline.py::parse_intent`：重试序列 `[v4-pro, v4-flash, v4-flash]`（第 2 次就切 flash，不浪费在波动中的 pro）+ 每请求 `timeout=8`（单次卡死上限 8s，最坏 3×8=24s）
- `index.html`：前端聊天 abort 超时 **15s → 30s**（留足 AI 余量）

**验证**：
- 重启服务器加载新代码，恢复 stage=4
- 直连 chat 6.3s 正常；**`cdp_chat_ui.js` 全流程通过**（真实 rog 回复渲染进历史，零错误）
- `cdp_smoke_1200.js` 13/13 全绿（index.html 改动无回归）

**服务器状态**：stage=4、4 NPC 在场、0 残留。

**下一步**：试玩时聊天链路已带双保险（flash 兜底 + 8s 上限 + 前端 30s）。等 12:00 反馈。

### 08:2x 周期（cron 续跑）— 一键试玩启动器交付

**产出：`试玩启动.bat`（12:00 主入口）**
- 功能：检查服务器 → 未运行则自动启动（隐藏窗口）→ 恢复 stage=4（reset+advance×4）→ 验证状态 → 打开游戏
- 踩坑记录：① UTF-8 .bat 在 GBK cmd 解析崩 → 改 GBK 编码写入；② `chcp 65001` 与 GBK 文件冲突致中文乱码 → 去掉（默认 GBK 代码页正常显示）；③ `timeout /t 5` 被 Git Bash coreutils 遮蔽 → 改 `ping -n 6 127.0.0.1` 延时
- 完整实测通过：杀服务器 → 跑 bat → 自动起服 + stage=4 全员在场 + 打开游戏
- NIGHTLY_REPORT「12:00 怎么开始」已更新：双击 `试玩启动.bat` 为推荐入口

**服务器状态**：stage=4、4 NPC 在场、0 残留。

**下一步**：等 12:00 反馈。所有自动化入口就绪（试玩启动.bat / 冒烟 / 聊天验证 / 调参速查 / 换模管线）。

### 08:5x 周期（cron 续跑）— 悄悄话模式验证 + 确定性集成测试 16/16

**1. 悄悄话（whisper）模式首次端到端验证**（此前只测过 public 聊天）
- API 测试：whisper 给 liana「撕掉那页日记我帮你保密」→ 真实角色扮演回复（先警惕否认→感谢保密），状态正确进入 `whisper_mode=true, target=liana`
- 集成测试亦含「悄悄话可发」项 ✅ → 双重复核通过

**2. `integration_test.py` 16 项全部通过**（`--no-ai` 确定性模式）
- 覆盖：reset / 4 次推进入场 / 4 NPC 对话 / 悄悄话 / state 结构 / 节奏提示 / reset 后 stage=1 / memories
- 注：先前"零输出"是端口被我的服务器占用 + stdout 块缓冲被超时杀死吞掉——释放端口 + `-u` 无缓冲后正常

**服务器状态**：重启恢复 stage=4、4 NPC 在场、whisper=false 干净。

**下一步**：试玩前覆盖已完整（public/whisper 聊天、确定性回归、冒烟 13/13、一键启动）。等 12:00 反馈。

### 09:2x 周期（cron 续跑）— 悄悄话 UI 全流程验证 + src 语法全检

**1. 悄悄话 UI 端到端（最后一个未覆盖 UI 路径）**：`cdp_whisper_ui.js`
- 点 `#btn-whisper` → 选择提示出现 → 点 baruk 标签 → 按钮变 `🔇 @巴鲁克`
- 发送 → 玩家消息带 `[悄悄话 @巴鲁克]` 前缀 → **真实 baruk 回复**（矿工密语，人设吻合）→ 零错误
- 至此 public/whisper 双聊天路径 UI 全覆盖

**2. 代码语法自检（优先项 5）**：`node --check` 全部 10 个 src JS（atmosphere/audio/fps_controller/guidance/markers/models/perf/props/settings/ui_drag）**全部通过**

**3. 冒烟确认**：08:59 重启后的服务器跑 `cdp_smoke_1200.js` 仍 **13/13 全绿**

**服务器状态**：恢复 stage=4、whisper=false 干净。

**下一步**：试玩前验证全部闭环。后续周期做健康维持（周期性冒烟）+ 接近 12:00 时收尾 NIGHTLY_REPORT 最终版。

### 09:5x 周期（cron 续跑）— NIGHTLY_REPORT 最终版收尾

**产出：`NIGHTLY_REPORT.md` 更新为 2026-08-12 晨间最终版（12:00 回收）**
- 元数据：date → 08-12 09:50，标题 → 晨间最终版
- 晨间摘要补入今晨两处 AI 修复（意图兜底加固 / UI 聊天超时）+ 悄悄话验证 + 一键启动 + 调参速查
- 明日事项更新：候选角色清单（指南§二）+ 手感调参对照表
- 产出汇总表：修重复行号 + 新增 4 项（悄悄话 UI / 一键启动器 / 调参速查 / 原 3 项顺延）

**整体状态**：全部优先项完成并闭环验证。**NIGHTLY_REPORT 已是 12:00 起床最终版**，后续周期做健康维持直到 12:00。

### 10:1x 用户反馈处理（玩家在线）— 杀旧进程 + 恢复开场 + 出生点实证 + 粉色板子定位

**用户反馈**：① 玩家加载到玛格丽特位置 ② 所有 NPC 直接全部到场 ③ 建议启动时杀旧进程 ④ 粉色板子是什么 ⑤ 开场剧情加回去了吗 ⑥ 是否最终版

**1. 出生点实证（`cdp_spawn_probe.js`）**：代码与实测均确认玩家出生在**入口 (0,0,-5.5) 眼高 1.6m 面向殿内 +Z**，无任何代码把玩家挪到玛格丽特 (0,0,5.5)。"加载到玛格丽特位置"的观感源于：stage=4 全员在场 + 玛格丽特站位恰在入口正中 11m，开局第一眼就是她。

**2. 粉色板子定位（`cdp_pink_board.js` + doubao 视觉确认）**：= **NPC 名牌标签**（玛格丽特头顶悬浮的「玛格丽特 Margaret」圆角标签，屏幕正中央 (577,325)）。用途：标识每位 NPC 身份、点击选定对话对象。`.npc-label` 无背景色，暖光下暖白文字读作粉色。

**3. 启动器杀旧进程 + stage 0 开局**：
- 新增 `kill_old_servers.ps1`：杀掉所有残留 `server.py`/`http.server` 进程 + 释放 8080（实测清掉 3 个残留：8200/8199 静态服 + 旧 game 服）
- `试玩启动.bat` 重写（GBK）：**杀旧进程 → 新起服务器 → 只 reset 到 stage 0**（不再 advance×4）→ 验证 → 开浏览器
- 效果：玩家从空殿开始，点「⏭ 等待…」让 NPC 逐个入场（还原设计叙事流）

**4. 恢复开场剧情介绍（黑屏打字）**：
- 恢复 `#opening-overlay` HTML（title/text/cursor/continue/进入大殿按钮）
- 替换 bypass 逻辑为完整开场流程：4 行剧情逐字打字 → 点任意处/Enter 推进 → 末行出现「进入大殿」→ 淡出 + 切入 FPS
- 清理孤儿代码行 + 过时注释

**5. 回归验证**：
- `cdp_opening_regression.js`：**9/9 全绿**（开场可见/打字/进入/出生点/空殿/推进罗格入场/零错误）
- `cdp_smoke_1200.js`：适配开场后 **14/14 全绿**（stage4 全量 + 动画三件套 + FPS + 零404/403 + V/M/H + 冷启动 + 收尾复位 stage 0）

**服务器状态**：stage=0 干净开局状态（冒烟测试收尾已复位）。

**下一步**：回答用户全部问题（最终版状态 / 白模说明 / 火把程序几何 / 名牌用途 / 开场已恢复 / 出生点实证）。

### 11:0x 周期（cron 续跑）— 火焰视觉升级完成 + 修复遮挡火把的面板定向 Bug

**用户反馈**：火把是"手绘几何体"（指火焰像贴图/图标、边缘僵硬），doubao 视觉批评"火焰边缘规整僵硬像卡通标识、余烬是方块小光点"。

**1. 火焰视觉升级（`index.html`，Task #28 完成）**
- 泪滴形火焰：`LatheGeometry`（外焰 + 半尺寸内芯双层）+ 16 粒余烬粒子 + 径向渐变软光晕 Sprite + 金属灯杯（火把/壁灯统一）
- 火焰动画统一驱动：闪烁（三层正弦叠加）+ 光晕呼吸 + 光源强度抖动 + 余烬上升，按画质门控（低档熄壁灯、火把保留 1 灯）
- 修正加色混合在亮墙饱和成白点 → 火焰本体改 `NormalBlending`（橙色保持可读）+ `renderOrder`（光晕→外焰→内芯→余烬）

**2. 关键修复：内墙装饰板定向 Bug（火把被遮挡的根因）**
- 现象：火把火焰在中距离完全不可见（深度测试全灭），近距离可见 → 排查 9 个探针脚本定位
- 根因：`createWallPanel` 用 `PlaneGeometry`（默认 XY 平面/恒定-Z），东西墙装饰板只转了 rotY=0/π → 变成悬浮在殿中央的恒定-Z 竖直面。**兽人区面板 (9.79,2,4.25) 正好挡在相机与东墙火把 (8.5,5) 之间**，火焰被完全遮挡
- 修复：东西墙 5 块面板（精灵×2/矮人/兽人/符文）rotY 改为 ±π/2 → 贴到墙面上
- 附带解决"悬浮木板/装饰板"观感（doubao 视觉确认墙上已无悬浮板）

**3. 回归验证**
- `cdp_flame_verify.js`：**6/6**（注册表 12、LatheGeometry、焰+芯+余烬、余烬动画、低画质门控、零错误）
- doubao 视觉（中距火把）：泪滴形焰 + 白芯橙体 + 边缘柔和 + 光晕自然 + 金属杯/木柄清晰
- 像素统计：火把焰心区橙色 **0% → 47.1%**
- `cdp_opening_regression.js`：**9/9**；`cdp_smoke_1200.js`：**14/14**

**服务器状态**：stage=0 干净。浏览器页面无干扰。

**下一步**：清洁临时诊断脚本/截图；接近 12:00 收尾 NIGHTLY_REPORT。待办顺延：莉安娜动画增强（若 Mixamo 上传成功）、Python 测试套件、代码自检。

---

## 11:2x 周期（11:27）

**1. 火把壁挂支架（修复"火把悬浮"观感）**
- 用户上次反馈火把"像是悬浮"，doubao 视觉也确认南侧火把远处看像悬空
- 新增：金属横臂（圆柱）+ 墙面圆形玫瑰固定盘，4 支火把全部锚定到壁画墙面
- **排障要点**：最初把世界坐标当本地坐标用（火把组在 (x,0,z)），支架被放到殿外 (17,1.45,10) 完全不可见；改成组内相对坐标后立即可见（绿色上色测试 8/8 网格在画面中确认）
- 材质迭代：暗金属在暗墙上隐形 → 加自发光保轮廓 → 中性钢灰避免泛黄像木头；臂高从手柄中段改到金属灯杯下缘（标准壁灯形态，不穿木柄）
- 墙面固定盘改为短圆柱盘（面朝大殿，贴壁画），比扁球更清晰

**2. Python 测试套件（优先级 4 完成）**
- `test_state_machine.py`：**30/30 PASS**
- `integration_test.py --no-ai`：**16/16 全部通过**（确定性模式端到端）

**3. 回归验证**
- `cdp_smoke_1200.js`：**14/14** 🟢（含零 404/403/页面错误）
- `cdp_flame_verify.js`：**6/6**（火焰结构未受支架改动影响）
- 绿色上色测试确认 4 臂 + 4 盘全部在场景中正确渲染、位置正确
- doubao 视觉确认支架已承托金属灯杯（不再是悬浮）

**服务器状态**：stage=0 干净。

**下一步**：11:4x 收尾 —— 更新 NIGHTLY_REPORT 最终版；全部 28 个任务已完成，待办队列清空。

---

## 11:3x 周期（11:33 收尾）

**1. Python 测试套件补全（优先级 4 全部验证）**
- `test_endings.py`：退出码 0（46 项，5 结局可达）
- `test_dialogue_scenarios.py`：3 策略 × 9 轮真实 AI 对话，**0 失言**，无异常结局
- 加上此前：state_machine 30/30 · integration 16/16 —— 全量绿

**2. 代码自检（优先级 5）**
- `src/models.js` / `src/props.js` / `src/fps_controller.js` 全部 `node --check` 语法 OK
- index.html 模块脚本 `node --check` OK（此前已验）

**3. 最终场景级验收（出生点第一视角）**
- 修正出生点朝向（yaw=π 面朝殿内，此前 yaw=0 拍到了南墙）
- doubao 视觉：**三处壁装火把橙色火焰清晰 + 火光暖光投射明确 + 无穿模/无悬浮 + 石殿暖光氛围到位** ✅
- 悬浮白球/半透卡牌为设定内守护灵/封印元素，非 bug

**服务器状态**：stage=0 干净。

**收尾**：全部任务完成，NIGHTLY_REPORT 已更新至 12:00 最终版（19h 节）。

---

## 11:56 收尾核验（会话结束前）

- 服务器 **stage=0 空殿干净**（玩家 12:00 起床直接试玩）
- 关键改动在位：火焰系统（LatheGeometry/createFlameVisual ×5）、火把支架（bracketMat ×3）、面板定向修复（±π/2 旋转变换 ×17）
- NIGHTLY_REPORT 已含 19h 最终节；临时文件 0 残留
- **通宵会话完结**：9 小时自主工作，28 项任务全部完成，测试全绿（30+46+16 状态机/结局/集成 + 9 轮对话 0 失言 + 冒烟 14/14 + 火焰 6/6），场景级 doubao 验收通过

- **12:26 超时核验**：目标时刻 12:00 已过，全部任务已交付；服务器保持 stage=0 待试玩，无新工作可做（不重复已完成项）。通宵会话正式结束。

- **12:56 会话收束**：目标 12:00 已过、全部交付完成，已取消每 30 分钟「自动续跑」循环（7f8b819e），避免空转；夜间主工作流（12:03/02:00/05:00）保留，今晚正常启动。最终交付见 NIGHTLY_REPORT.md。

---

## 13:42 用户反馈处理（背景音乐 + 移除中央板子）

**用户原话**：「不错不错，能加背景音乐吗，还有中间的板子还在，我要去吃饭，大概一个小时」

**1. 移除「中间的板子」= 北墙中央挂毯** ✅
- 定位过程：像素分析确认屏幕中央大片粉色 (240,208,208) → 排除 DOM 覆盖层 → raycast 命中 `PlaneGeometry(3,2.2)` @ (0,2.8,7.45) 带 canvas 贴图 → 定位 `src/atmosphere.js` 的挂毯（`_createTapestryTexture`：暗红底 + 竖条纹 + 金边 + 菱形「圆+竖线」徽记，与 doubao 描述完全吻合）
- 处理：删除挂毯 mesh + 清理未用的 `_createTapestryTexture()`；保留旗帜/盾牌装饰
- 验证：中心粉色像素 0/26000；doubao 确认「远处墙壁中央是裸露复古砖墙，无任何板子/卡牌/挂毯」

**2. 背景音乐（Web Audio 程序化合成，无外置文件）** ✅
- `src/audio.js` 新增 `_buildMusic()`：A 小调持续低音 pad（6 振荡器微失谐 + 低通慢呼吸 LFO）+ 五声音阶稀疏泛音（2.4s 步进调度，30% 休止）+ A1 低频根音脉冲（每 8 步）+ 卷积混响大厅空间感
- 音量分级：master=0.18×musicVol；pad≈0.03、泛音≈0.012、根音≈0.03（低于脚步音效，不抢戏）
- `src/settings.js` 新增「背景音乐音量」滑块（0~1，默认 0.6，localStorage 持久化，input 实时生效）
- `index.html` 设置 onApply 接上 `ambientAudio.musicVolume`
- 验证：AudioContext running、6 pad 振荡器在位、调度器定时器运行、音量数学正确（0.18×0.6=0.108；调滑块 0.25→0.045 实时）、持久化 JSON 含 musicVol、零 JS 错误

**3. 回归验证（非侵入，未动玩家 stage=1 实时会话）** ✅
- 服务器 `/api/state`：stage=1、rog 在场，玩家会话完好（未跑会重置的冒烟脚本）
- 火焰系统：28/28 火焰 mesh 全亮（高画质；此前测试环境 auto-degrade 到 medium 只亮 2/4 壁灯属既有设计，非回归）
- 全部加载零 JS 错误、无 404
- 已知遗留（非本次改动）：NPC 用占位模型（rog 为暗红 0xc4544a 图元，等 Mixamo 换模）

**生效说明**：改动在代码层，玩家刷新页面后生效（用户吃饭回来 reload 即可）。

## 13:50 联机对话修复（好友无法与 NPC 对话）

**现象**：好友通过 Tailscale（`http://100.79.254.94:8080`）打开游戏，页面/模型正常加载，但 NPC 对话无响应。

**根因**：`index.html` 里 `API_BASE = 'http://localhost:8080'` **写死**。好友浏览器里的 `localhost` 指他自己机器 → `/api/chat`、`/api/state` 全部打到自己电脑 → 回落「本地模拟」模式，对话失效。本机自测一切正常（ping 通、rog 正常回复）印证了这一点。

**修复**：`const API_BASE = window.location.origin;` —— API 地址跟随页面来源。本地打开=localhost:8080，好友打开=Tailscale/局域网地址。全库仅此一处写死 localhost（已 grep 确认无其它）。

**验证**：
- 本机 `http://localhost:8080` → origin 正确、`/api/state` stage=1 连接成功、零 JS 错误
- Tailscale 地址下 `window.location.origin` 正确解析为 `http://100.79.254.94:8080`（好友设备经 netstat 确认可达该地址 ESTABLISHED）
- 服务器仍运行中（PID 27684，0.0.0.0:8080）

**玩家须知**：好友需**刷新页面**加载修复后的 JS；本机玩家无需重启服务器（服务器已在跑）。注意 `试玩启动.bat` 会杀服务器 + 重置 stage 0，若想续玩当前进度请勿运行，直接开 `http://localhost:8080` 即可。

## 14:1x 修复：按 E 与 NPC 交互无法输入文字

**现象**：玩家靠近 NPC（如罗格）按 E，输入框没有聚焦，直接打字没反应；提示条写着"按 Enter 说话"但很多人不会按，交互断半截。

**根因（两层）**：
1. E 键交互后**不自动聚焦输入框**（原注释："避免 WASD 被吃；玩家按 Enter 才进输入模式"）——只有 FPS 控制器里 Enter→focus 一条旁路，玩家按 E 后直接打字全部落空。
2. **交互判定半径不一致**：提示条用 `findNearbyNpc(2.2)`，E 键用 `findNearbyNpc(2.0)`——NPC 入场走动中，玩家站在 2.0~2.2 区间时提示显示"按 E"但按了没反应。

**修复**（index.html）：
- E 键选中 NPC 后**自动聚焦输入框**：按 E → 直接打字 → Enter 发送 → Esc 退出。清空移动键状态避免 WASD 被吞；`e.preventDefault()` 阻止触发键 'e' 被当首字符插进输入框。
- 新增共享常量 `INTERACT_RANGE = 2.4`，提示条与 E 键统一用它，杜绝范围漂移。
- 系统提示文案改为"直接输入想说的话，Enter 发送，Esc 退出。"

**验证**（Playwright 端到端）：
- 按 E 后 `document.activeElement === chat-input` ✓
- 直接打字 `value === '你好罗格，这地方为什么这么安静？'`（无多余 'e'）✓
- Enter 发送后罗格正常回复 ✓
- 零 JS 错误 ✓

## 14:2x 修复：背景音"沙沙声"

**现象**：环境音 + 背景音乐里持续有"沙沙/hiss"，用户反馈未消除。

**根因（三处白噪声成分）**：
1. **火堆噪声**：`bandpass 700Hz Q1.5` 的**连续白噪声** @0.012 一直响——中频持续"沙沙"主源。
2. **混响**：音乐 pad/泛音送入全频白噪声脉冲卷积混响，湿声 0.8——每个音都带"shh"尾音，几乎持续。
3. **房间嗡鸣**：`lowpass 160Hz Q0.4` @0.018，中频有余量，略偏"沙"。

**修复**（audio.js）：
- 火堆：连续白噪声压到 0.004 火床（500Hz 窄带），新增 **随机噼啪爆裂**（短噪声脉冲、带通 1.2-3.6kHz、快衰减、35% 留白）替代连续噪声。
- 混响：脉冲响应**一阶低通 1.8kHz 做暗** + 混响返回串 `lowpass 1800` + 湿声 0.8→0.35。
- 嗡鸣：cutoff 160→120Hz、Q 0.4→0.8、gain 0.018→0.012。
- `stop()` 增加 `_crackleTimer` 清理。

**客观验证**（OfflineAudioContext 频谱能量测量）：
- 环境噪声底床高频(>3kHz)占比：8.21% → 0.76%（降 90.7%）
- 混响返回高频占比：~100% → 18.7%（降 81.3%）
- 实时冒烟：启动正常、pad 6 振、音乐/噼啪调度器运行、4 秒零 JS 错误

## 14:5x 修复：试玩启动每次全新开局

**现象**：点击"试玩启动"打开的游戏不是新开局，NPC 全部已在场。

**根因**：存在两个同名 `试玩启动.bat`。用户点击的根目录 `D:\Create by you.demo\试玩启动.bat` 第 [2/4] 步"恢复 stage=4 (4 NPC 全员到场)"——`/api/reset` 后又连发 4 次 `/api/advance`，把游戏推到全员入场的演示态。而 `game-prototypes\试玩启动.bat` 才是"杀旧进程 + stage 0"的版本。

**修复**（根目录 `试玩启动.bat`）：
- 改为与 `game-prototypes\试玩启动.bat` 一致：先 `kill_old_servers.ps1` 杀旧 server → 启动新 server → `/api/reset` 到 stage 0 → 打开浏览器。
- 加入 `chcp 65001` 使中文提示正常显示。
- 两个 launcher 行为统一：每次打开都是全新开局（NPC 依次入场）。

## 14:5x 修复：蹲姿无法测试（Ctrl+W 关标签页）

**现象**：网页版按 Ctrl 蹲 + W 前进被浏览器当作 Ctrl+W 关掉标签页，蹲着走测不了。

**根因**：`fps_controller.js` 蹲姿虽已改 Z 键（注释注明"Ctrl 被浏览器抢键"），但 keydown/keyup 仍残留 `k === 'control'` 触发 crouching；且 FPS 提示条仍写"Ctrl 蹲"，引导玩家按 Ctrl → Ctrl+W 关页。

**修复**（fps_controller.js）：
- 移除 `control` 触发：keydown 只认 `z` 且 `preventDefault`；keyup 只认 `z`。
- 提示条 `Ctrl 蹲` → `Z 蹲`；顶部功能注释同步。
- `node --check` 语法通过；全库无 "Ctrl 蹲" 残留（moveKeys 中 control 仅 preventDefault，无害）。

## 14:5x 新增：游戏内"重新开始"按钮

**需求**：除启动器外，想在网页里直接一键回到全新开局（不必重跑 bat）。

**实现**（src/settings.js）：
- 设置面板新增红色警示按钮 `↺ 重新开始（清空进度）`。
- 点击流程：退出 Pointer Lock → `confirm` 二次确认 → `fetch POST /api/reset` → `location.reload()`（回到 stage 0 全新开局）。
- 用相对路径 `/api/reset`，本机 localhost 与好友 Tailscale 同源访问均有效。

**验证**（Playwright 轻量，未触发重置）：
- 设置面板打开后按钮存在、文案正确 ✓
- 事件绑定正常（element.click() 面板打开）✓
- 零 JS 错误 ✓
- 开场剧情遮罩（#opening-overlay）在片头期间会挡住设置按钮——属既有行为，开场结束后可正常点击。

## 15:1x 调查：所有人物模型"整体一色"根因（暂不改）

**现象**：4 个 NPC（莉安娜/巴鲁克/罗格/玛格丽特）全身都是单一纯色、无纹理细节；当初只有莉安娜"浑身是绿"。

**根因（运行时实测 + FBX 取证）**：
- 所有角色 FBX 来自 mixamo-mini 下载管线，贴图引用是**绝对路径**（`e:/home/app/mixamo-mini/tmp/skins_*.fbx`，本地不存在）。liana_tpose.fbx 18 处盘符引用，rog/player 各 1 处。
- `models.js` 的 `LoadingManager.setURLModifier` 把盘符绝对路径贴图一律换成 1×1 透明 GIF（本为压 403 报错）。
- 结果：材质 `map`=透明 GIF → 贴图失效，只剩材质基础色 `#cccccc`/`#ffffff` + 各 NPC `baseColor` 的**淡自发光染色**（莉安娜绿/巴鲁克黄/罗格红/玛格丽特白）。
- 实测证据：4 NPC 模型加载成功、动画齐全；材质全部 MeshPhongMaterial + `allGifMap: true`；视觉无任何纹理。

**结论**：不是新 bug，与莉安娜当年"全绿"同根因（她的引用最多且染色最扎眼）。属**模型贴图路径管线问题**，非代码 bug。

**用户决定**：先只查不改，等主体方向确认后再定（可选方向：换带贴图角色 / 现有模型上多色材质 / 保持纯色风格）。

**留档脚本**：`D:\tools\playwright\model_color_inspect.js`（运行时读 NPC 材质/贴图源/截图）。
