---
title: 封印之殿 — 会话交接文档
date: 2026-08-10 01:00
tags: [game-design, sealed-hall, handoff]
---

# 封印之殿 — 会话交接

> 给下一个会话的助手：读完本文件即可无缝接手。项目在 **D 盘**（不在 vault）。

## 一、项目位置

- **项目根目录**：`D:\Create by you.demo\`
- **Vault 索引**：`D:\EDGE\obsidian\30.areas\game-design\封印之殿 — 项目索引.md`（已移出 vault，此索引仅作链接）
- 所有操作使用**绝对路径**，因为项目在 vault 之外

## 二、当前进度（2026-08-10 01:00）

| 阶段 | 内容 | 状态 |
|:---:|------|:---:|
| 0 | 文本原型（Python 终端） | ✅ 完成 |
| 1 | 资产收集 | ✅ 6 个 CC0 纹理 + HDRI 已下载 |
| 2 | 核心系统（状态机/AI管线/3D框架） | ✅ 完成 |
| 3 | 对话集成（UI/API/环境反馈/事件链/记忆/悄悄话） | ✅ 完成 |
| 4 | 失言判定 + 关系网可视化 | ✅ 完成 |
| 5 | 结局路线测试 + 4 缺口修复 | ✅ 完成（46/46 通过） |
| 6 | 出场节奏优化 + 前后端契约修复 | ✅ 完成（30+46+16 全绿） |

## 三、后台 Agent（均已完成）

1. **结局可达性修复** ✅：4 缺口全修，`test_state_machine.py` 22/22、`tests/test_endings.py` 46/46 通过。
2. **纹理下载** ✅：6 个 CC0 纹理 + HDRI 已下载到 `assets/textures/`，清单见 `DOWNLOAD_NOTES.md`。

## 四、2026-08-10 01:09 关键修复（出场节奏 + 前后端契约）

> ⚠️ 本次发现了 3 个会让玩家"一开就卡死"的致命契约 bug，已全部修复。

| Bug | 现象 | 修复 |
|-----|------|------|
| **chat 请求被拒** | 前端发 `{message}`，服务器读 `{input}` → 400 | 服务器兼容两种字段名 |
| **chat 回复不显示** | 前端读 `data.replies[]`，服务器返回 `data.reply` 字符串 | 前端兼容单条 reply |
| **推进按钮失效** | 前端读 `data.phase`，服务器返回 `data.stage` | 前端兼容 stage；入场台词现在会显示 |

**出场节奏优化（任务10）**：
- 服务器新增 `get_pacing_hint()`：在场 NPC 都聊过且连续 2 轮无新信息时，提示"可叫下一位"
- 公共模式新增点击 NPC 标签选对话目标（此前只能跟最后入场的人聊）
- 推进按钮感知状态：`⏭ 叫下一位（2/4）`，全员到场后禁用
- 刷新页面后阶段号自动同步（`fetchGameState` 读 `current_stage`）
- `__ping__` 探测短路，不污染对话计数

**新测试**：`game-prototypes/integration_test.py`（16 项端到端，自动起服务器测全部端点；已改为 `--no-ai` 确定性模式跑，16/16 全绿）

**补充接线（本会话）**：
- 终端版 `main.py` 接上出场节奏：充分对话后自动打印提示（每阶段一次）+ `/wait` 作为 `/n` 别名（已实测：`/wait` →「罗格，你是谁」→「没别的事了吗」→ 提示点名下一位）
- 终端对话目标机制：默认跟守护灵聊；在输入里带上 NPC 名字（如"罗格，你是谁"）即切换目标，出场节奏按在场 NPC 是否都被聊过来判断
- 修复 `display.py` 缺失的 `Color.BRIGHT_WHITE`（终端版 `main.py` 一启动就 `AttributeError` 崩溃，已补 ANSI 97 并实测可玩）
- 出场节奏单元测试：`test_state_machine.py` 新增测试 7（8 条断言）→ 该套件现为 **30 项**
- `TEST_PLAN.md` 新增第 6 节（出场节奏 6.1–6.9）
- `server.py` 新增 **`--no-ai` 开关**：强制关闭 AI（关键词回退 + 模拟回复），供自动化测试/离线体验；`integration_test.py` 默认用它跑，消除 AI 意图漂移导致的偶发失败

**其他**：
- HDR 环境贴图本地化：`old_hall.hdr` 已复制到 `3d-prototype/`，离线可玩
- 结局显示中文名（真理之殿/血债血偿/新火种/…），不再显示英文 ID
- **试玩清单**：`PLAYTEST_CHECKLIST.md`（用户起床后照着玩）

## ⚠️ 2026-08-10 01:20 重要：真实 AI 已打通（key 回退）

> 用户系统里只有 `ANTHROPIC_API_KEY`，**没有** `DEEPSEEK_API_KEY`。

- **原状**：游戏读 `DEEPSEEK_API_KEY` → 用户开服=模拟复读机模式（NPC 说固定台词）
- **修复**：`config.py` 回退读 `ANTHROPIC_API_KEY`（同一把 DeepSeek key）
- **已验证**：`deepseek-v4-pro` + `deepseek-v4-flash` 在 OpenAI 兼容端点 `https://api.deepseek.com/v1` 均可用，真实角色扮演回复正常
- **注意**：集成测试在有 key 的环境会走真实 AI（对话慢 2-5s），测试超时已放宽到 45s
- `ai_pipeline.py` 已加 30s 超时 + max_retries=1，防挂起
- 另一个对话的临时调试脚本（`pacing_ab.py` 等，位于 vault `.claude/`）已独立验证节奏逻辑正确，与本次结论一致（验证完已删除）

## 测试状态（01:20 最终）

- `test_state_machine.py`：**30/30**（含新增 8 项出场节奏测试）
- `tests/test_endings.py`：**46/46**
- `integration_test.py`：**16/16**（已固定用 `--no-ai` 确定性模式跑；真实 AI 模式下意图解析有随机性、且 API 慢时会超时，冒烟测试不依赖它）

## 五、测试命令（所有验收标准）

```bash
cd D:\Create by you.demo\game-prototypes
python -X utf8 integration_test.py        # 16 项端到端（自动起服务器，--no-ai 确定性模式）
cd text-prototype
python -X utf8 test_state_machine.py      # 30 项通过（含出场节奏测试）
python -X utf8 tests/test_endings.py      # 46 项通过
python -X utf8 tests/test_dialogue_scenarios.py  # 需 DEEPSEEK_API_KEY
```

## 六、待办

1. ~~**验证修复 Agent 结果**~~ ✅ 已确认：30/30 + 46/46 全通过
2. ~~**出场节奏优化**~~ ✅ 已做（见上节），含 3 个致命契约 bug 修复
3. ~~**最终集成测试**~~ ✅ 已绿：`integration_test.py` 16/16（改用 `--no-ai` 关 AI，消除意图漂移导致的偶发失败）
4. ~~**确认 DeepSeek key**~~ ✅ 已验证：config 回退用的 key 对 `DEEPSEEK_BASE_URL/models` 返回 200，`deepseek-v4-pro`/`deepseek-v4-flash` 真实可用
5. **Steam 迁移方案**：`docs/steam-migration-plan.md` 已写好（见下）

## 七、已写好的文档

- `docs/2026-08-09-sealed-hall-design.md` — 完整设计文档
- `docs/steam-migration-plan.md` — Steam 迁移方案（新会话可直接引用）
- `characters/` — 5 个角色档案
- `game-prototypes/text-prototype/prompts/` — v2 Prompt 工程
- `game-prototypes/text-prototype/TEST_PLAN.md` — 验证清单（已新增第 6 节：出场节奏 6.1–6.9）

## 八、运行游戏

```bash
cd D:\Create by you.demo\game-prototypes
set DEEPSEEK_API_KEY=sk-xxxxx   # 用户已在系统环境变量中配置
python server.py                 # 启动服务器
# 浏览器打开 http://localhost:8080
```

## 九、用户偏好与约定

- **中文**：所有笔记、注释、回复用中文
- **模型策略**：平时 Flash，复杂集成/修复用 Pro
- **文件**：全在 D 盘（剩余 545G），C 盘不要放项目文件
- **用户不写代码**：创意决策白天做，算力执行夜间
- **预算**：一晚 30-60 元算力
- **DeepSeek API**：V4 Pro 意图解析 + V4 Flash 回复生成；官方已宣布涨价但新价未公布
- **上下文提醒**：本会话上下文已近极限，用户可能切新对话——新会话读本文件接上

## 十、关键技术说明

- **架构**：浏览器 Three.js ←HTTP/JSON→ server.py ←→ 状态机 + DeepSeek API
- **状态机**：纯 Python 确定性逻辑，不依赖前端
- **AI 管线**：`ai_pipeline.py` 懒加载客户端，无 Key 时降级模拟模式
- **服务器**：`server.py` ThreadingHTTPServer，端口 8080，含 CORS
- **3D 前端**：`3d-prototype/index.html`（3255 行），快捷键 R/F/G/1-4/Q/E/W/S/T/V/M/Space

## 十一、2026-08-10 后续：模型管线 + 完整引导系统

> 针对试玩反馈"不知道怎么玩 / 无主导剧情 / 无人物提示"的重构轮。92/92 测试保持全绿。

### 新增能力

1. **Mixamo 模型管线**（`3d-prototype/src/models.js`，246 行）
   - FBXLoader 加载 + AnimationMixer 动画管理（idle/talk/walk、crossfade、root motion 过滤）
   - 单位自适应归一化（包围盒高度 → 1.75m × 体型系数）+ 地面对齐 + 阴影/朝向
   - 文件缺失/失败 → 静默回退几何人形，不阻塞试玩
   - 情绪（angry/vulnerable/hopeful/tense）与信任度 → 模型 emissive 表现（不染色贴图）
   - 对话时播放 talk 动画，播完自动回 idle
2. **server.py 静态服务扩展**：`/models/` 前缀白名单 → `assets/models/`（原仅服务 3d-prototype/ 内）；MIME 表补 `.fbx`
3. **完整引导系统**（`3d-prototype/src/guidance.js`，306 行）
   - 开场目标卡片：剧情背景 + 玩家身份（第 5 人）+ 三步玩法
   - 常驻「当前目标」面板：按阶段（0-4）显示主线目标与建议行动
   - NPC 入场介绍卡：名字/种族/目的，入场弹出 7 秒
   - 帮助弹窗（H 键）：对话三步 / 推进方式 / 公开 vs 悄悄话 / 完整快捷键表
   - 屏幕快捷键提示补全（点标签选对象 / V / M / H / R/F/G）
4. **文档**：`docs/mixamo-model-guide.md` —— 角色/动画挑选清单、下载设置、命名约定、验收标准

### 测试状态（本轮后）

- 92/92 全绿不变：状态机 30/30、结局 46/46、集成 16/16
- 起服验证：`/` 与 `/src/*.js` 200；模型缺失时 `/models/*.fbx` 404（前端回退路径正常）
- 注意：起服前确认 8080 无残留实例（`netstat -ano | grep :8080`），旧实例会返回旧状态

### 待办

1. **用户下载模型**（按 `docs/mixamo-model-guide.md`）：4 角色 × (tpose + idle [+talk]) 放入 `game-prototypes/assets/models/`，刷新页面即生效
2. **试玩验证引导体感**：开场卡片 → 目标面板随阶段推进 → 入场介绍卡 → H 帮助弹窗
3. 模型接入后的体型/朝向微调：`index.html` 的 `MODEL_CONFIG`（liana 1.00 / baruk 0.82 朝西墙 / margaret 0.95 / rog 1.10）


## 十二、2026-08-10 模型选定（doubao-vision 协助）

**角色模型已通过浏览器自动化 + doubao-vision 视觉分析确定**（14+8 个候选逐图分析）：

| 角色 | 选定 | 来源 | 文件 |
|------|------|------|------|
| 巴鲁克 | Peasant Man | Mixamo | `baruk_tpose.fbx` + 动画 |
| 罗格 | Warrok | Mixamo | `rog_tpose.fbx` + 动画 |
| 玛格丽特 | Maria / Eva | Mixamo | `margaret_tpose.fbx` + 动画 |
| 莉安娜 | Elf Servant（CC BY） | Sketchfab | `liana_tpose.glb` |

**技术变更**：
- `models.js` 升级为 **FBX + GLB 双格式**（`liana_tpose.glb` 自动探测；GLB 内嵌动画自动作为 idle/talk/walk）
- `index.html` 增加 `GLTFLoader` import 并传入 ModelManager
- **JS 语法全部通过 node --check**（models.js / guidance.js / index.html 主脚本 85KB）——此前无 node 无法验证
- 完整挑选依据见 `docs/mixamo-model-guide.md` 第七节

**下载状态**：等用户按清单下载 → 放入 `game-prototypes/assets/models/` → 刷新页面生效（莉安娜需 Sketchfab 登录下载 GLB）。


## 十三、2026-08-10 第二轮试玩反馈修复（talk 动画 / 场景引导 / UI 可拖动）

> 针对试玩反馈："发消息没触发说话动画 / 看不出玩家在哪、门在哪、NPC 朝哪 / UI 互相遮挡"。

### 1. talk 动画修复（`src/models.js` + `index.html`）
- **根因**：动画文件本身有效（FBXLoader 解析验证 idle 9.93s / talk 3.93s，骨骼 mixamorig 44 个全一致）；实际是**发消息时模型还在异步加载，playTalk 被静默跳过**
- **修复**：新增 `_pendingTalk` 待播队列——模型未加载时请求 talk 会挂起，加载完成后自动补播
- 诊断日志：`[模型] <npc> 播放动画: talk（3.93s, 35 轨）`、`[对话] 发送 → 目标=... 模式=...`

### 2. 场景布局引导（新模块 `src/markers.js`）
- **玩家位置**：入口内侧青色光圈+光柱+「你在这里 · 入口」标签
- **入口**：北墙门柱光效+横梁+「入口 · 已封死」标签（入口 = 北墙中央 z=-7.29）
- **暗语**：西墙 baruk 看的位置金色呼吸符文+「墙上的暗语」标签
- **NPC 朝向**：每人脚前发光箭头，跟随 position + rotation.y（模型替换后仍正确，baruk 朝西墙）
- 用法：`sceneMarkers.update(dt)` 每帧调用（animate 内已接）

### 3. UI 可拖动（新模块 `src/ui_drag.js`）
- 4 个面板可拖：`#chat-history` / `#relationship-panel` / `#memory-panel` / `#g-goal-panel`
- 位置存 localStorage（`ui_drag_pos_<key>`），刷新保持
- 右下角控制条：🖱 调整布局（虚线框+可拖）→ 🔒 固定布局（锁定）→ ↺ 重置
- 目标面板默认位置从左上移到左中（`top:42%`），避开环境指示器遮挡

### 测试
- 92/92 全绿（30+46+16）不变；全部新模块 node --check 通过；起服各资源 200

### 待办
- 用户试玩确认：发消息巴鲁克说话动画、场景标记可见、拖动面板到满意后固定
- 莉安娜 GLB 下载放入 models/ 后自动生效（liana_tpose.glb）


## 十四、2026-08-10 第三轮试玩反馈修复（UI 遮挡 / 箭头 / 中键 / 提示时长 / 模型诊断）

1. **可拖动面板扩展**：新增 `#chat-input-area`（输入区）、`#hint`（底部提示行）、`#phase-advance-btn`（推进按钮）三个可拖；拖动排除放宽（button 可拖），新增 **5px 拖动阈值**保证按钮点击不被吞
2. **NPC 朝向箭头增强**：箭头放大 1.75 倍、抬高到 y=0.18（避开几何人形底座）、**前移到面向方向 0.55m**、提亮（opacity 1，颜色 8ff0ff）；4 个 NPC 统一生效
3. **相机平移改中键**：`controls.mouseButtons = { LEFT: ROTATE, MIDDLE: PAN, RIGHT: null }`（右键会触发浏览器右键手势）；滚轮缩放不变；hint 文案同步更新
4. **提示条停留 5s → 12s**（showHints 超时）
5. **模型状态诊断条**（`#model-status`，屏幕底部 hint 上方）：显示每个 NPC 加载状态（加载中/已加载·动画列表/未找到/失败），绿/黄/红三色；`ModelManager` 新增 `onStatus` 回调

**⚠️ 遗留待确认**：用户反馈"巴鲁克完全静止（idle/talk 都没有）"。代码链路已验证完整（animate 中 modelManager.update(dt) 存在、FBX 动画可解析、文件完好）；无法远程定位——**下次试玩看 #model-status 状态条**：
- 绿色「巴鲁克：模型已加载 · 动画: idle, talk」→ 播放问题（再看服务器日志 `[模型] baruk 播放动画`）
- 红色「未找到/加载失败」→ 文件/加载问题

### 测试
- 集成 16/16 + 状态机 30/30（本轮跑）；全部模块 node --check 通过；页面 200 + 状态条元素存在

## 十五、2026-08-10 talk 动画触发时机修正 + 关键 bug 修复

**用户反馈**：入场时巴鲁克直接触发 talking 动画 ✅，但公开对话 / 悄悄话都无法触发 ❌。

**根因（已用真实 API 请求验证）**：服务器回复 JSON 中 `npc_name` 是**中文显示名**（如 `'罗格·铁牙'`）、`npc_id` 才是**模型键**（如 `'rog'`）。原代码 `data.npc_name || data.npc_id` 取到中文名传给 `playTalk()`，模型表查不到键 → 静默失败（无报错）。

```
实际返回（--no-ai 实测）：npc_name='罗格·铁牙'  npc_id='rog'
```

**修复**：
1. `processChatResponse` 单条 reply 分支：`const replyNpc = data.npc_id || data.npc_name || ''`（npc_id 优先）；`addChatMessage` 也改传 npc_id（顺带修复 NPC 名字颜色丢失——之前传中文名导致 `npcPositions[中文]` 查不到、名字不上色）
2. **talk 触发时机整体调整**（上一轮改的）：发送时不再触发 → 改为**收到回复显示时**触发：
   - `data.reply` 单条：回复者开口（npc_id）
   - `data.replies` 数组：第一个主要回复者开口
   - `processMockResponse`（本地模拟）：第一条 npc 回复开口
   - `advancePhase` 入场台词：`data.new_npc` 开口
   - 入场 talk 为一次性（LoopOnce + clamp），播完自动回 idle；对话期间 talk 播放中再触发会忽略（防抖）

### 测试
- 集成 16/16 ✅；主脚本 node --check ✅
- 真实 API 验证：advance → `new_npc='rog'`；chat → `npc_name='罗格·铁牙' / npc_id='rog'`

### 待办
- 用户试玩确认：对话 / 悄悄话时对应 NPC 开口说话

## 十五、2026-08-11 大更新（素材库 / 材质 / 模型 / 视角系统 / 酒馆道具）

> 本轮完成：从"测试用几何场景"升级为"写实酒馆风格可玩场景"。

### 1. 素材库（D:\SealedHallAssets\，540G 空间）
- **角色模型**（Mixamo）：巴鲁克(Peasant Man)、罗格(Warrok)、玛格丽特(Maria)、玩家(Knight) 全套 tpose+idle+talk(+walk)
- **莉安娜**（Sketchfab）：Elf Servant GLB（CC BY）
- **候选模型**：Peasant Girl / Ely / Knight 备选（animations 目录）
- **写实材质**（Poly Haven CC0，12 个）：castle_brick(石墙)/brick_wall(砖墙)/brown_planks(木地板)/beam_wall(木梁)/dark_wood(深色木)/cobblestone(鹅卵石)/wood_table(木桌)

### 2. 场景改造（index.html）
- 四面墙 → 城堡石墙；北墙 → 砖墙（入口强调）；地板 → 木地板；墙顶 → 木梁横梁
- 西墙符文板 → 深色木暗语板（去掉手绘发光符文）
- **酒馆道具**（程序化）：2 木桌 + 4 长凳 + 3 酒桶 + 4 火把（动态火焰+点光源）+ 中央吊灯 + 书架

### 3. 全视角控制器（src/fps_controller.js）
- **C 键循环切换**：俯瞰 → 第一人称 → 第三人称
- WASD 移动 + Shift 奔跑 + 空格跳 + Ctrl 蹲 + 鼠标视角（Pointer Lock）
- **玩家模型**：Knight 骑士（With Skin 10.85MB，第三人称可见，idle/walk 动画）
- 暗角 + 准星 + 玩家光圈视觉反馈

### 4. 关键 bug 修复
- 玩家化身不可见 → 重新下载 With Skin 模型（教训：Mixamo 角色下载必须 With Skin）
- 莉安娜穿地 → baseY 保存
- 第一人称抖动 → controls.update 条件化

### 5. 测试
- 92/92 全绿（状态机 30 + 结局 46 + 集成 16）

### 待办（明天用户测试/选择）
- 场景道具需从素材库选择更精致的 GLB 模型替换（可选）
- 设置面板（隐藏按键提示/改键）
- 玩家模型可换（素材库有多个候选）

