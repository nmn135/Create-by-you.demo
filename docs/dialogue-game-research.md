---
title: 对话驱动游戏同类调研 — 封印之殿参考
date: 2026-08-12
tags: [game-design, sealed-hall, dialogue, research, interaction, ai-npc]
status: research
---

# 对话驱动游戏同类调研 —— 封印之殿可借鉴的交互设计与开源实现

> 调研范围：① 除打字外的互动按键设计；② 多 NPC 对话设计；③ 对话驱动世界改变（关系/信任/秘密/后果）；④ GitHub 可借鉴的开源项目。目标：为封印之殿（Three.js 浏览器 + Python 状态机 + DeepSeek AI 的中文对话驱动 3D 叙事原型）整理可直接落地的构思。
>
> 项目现状对照：`AGENTS.md` 已确认现有原型具备 E 交互 / N 推进 / C 切视角 / WASD / Enter 输入模式；待办含「节点分支对话（骑砍式话题树）」。本文在现有 `docs/dialogue-interaction-design.md` 基础上扩展。

---

## 一、互动按键设计：除打字外的交互方式

### 1.1 行业通用惯例（动词 × 对象模型）

从文字冒险到 3D 游戏，非打字交互的内核是**「动词（Verb）作用于对象（Object）」**：接近 → 显示提示 → 互动键 → 对话框 → 推进 → 选分支。

| 层 | 惯例 | 来源 |
|---|---|---|
| 接近提示 | 距离触发，NPC 头顶/准星旁浮现「按 E 交谈」 | Skyrim / 骑砍 / OpenMW |
| 互动键 | E（通用）、空格（推进台词） | Skyrim / 多数 3D RPG |
| 选分支 | 数字键 / 方向键 + 确定 | 骑砍、老式 RPG |
| 自由输入 | 输入框打字 | 封印之殿现有、AI Dungeon |
| 环境交互 | 面向物件「按 E 观察/检查」 | 点选冒险、Disco Elysium |

**关键教训——「看 Look」与「检视 Examine」必须分层**：`LOOK` 是快速默认动作（读招牌/书名），`EXAMINE` 是主动检视、挖更深信息（发现机关）。两者混在一起会让"观察"失去意义。经典 SCUMM 系统的价值在于**把解析器动词做成可点 UI**，玩家不用打字也能表达完整动作；但动词过多拖沓、过少（只剩 USE）摧毁解谜深度。

> 对封印之殿：环境本身是叙事载体（精灵区藤蔓古文字、矮人区矿工暗语）。值得把"面向物件按 E"做成**检视入口**，而不是只当背景摆设——这正是 Disco Elysium 把环境检查变成技能判定的做法（见 1.4）。

### 1.2 对话轮（Dialogue Wheel）的教训——Bethesda 系

- **Skyrim 的菜单式对话**：选项 1~2 个有意义 + 一堆 Yes/No/Neutral/Question 充数，分支浅。
- **Fallout 4 硬编码 4 选项**：引擎强制恰好 4 个回应、且被塞进"是/否/中性/提问"四类，社区 XDI 模组拆掉限制后才支持任意数量 + 全句显示。
- **对话轮的普遍批评**：用「话题概括」代替「完整句子」，玩家不知道角色会说出什么；选项好坏被 UI 标注，削弱决策意义。

> 结论：**选项数量与形式（轮盘 vs 列表 vs 自由文本）应服从内容**，而非被引擎/UI 锁死。封印之殿做"自由输入 + 少量关键分支"的混合，天然避开了 4 选项陷阱。

### 1.3 自由输入类——AI Dungeon

- 玩法即"描述动作 → AI 当 DM 生成回应"，可输入任意动作（不只是对话）。
- **内存靠外部缝合**：Story Cards + Memory Bank，仅在相关时注入上下文；这是 AI 文本 RPG 维持世界状态的核心手段。
- 提供 **undo/rewind**（随时回滚决策）与进度保存/续档。
- 公认局限：LLM 无持久记忆，世界实际只存在于最近几千 token 内；长程角色/物品/地点追踪困难（玩家需要游戏内笔记/日志）。

> 对封印之殿：① 记忆要靠外部结构（你们的状态机 + `已触发事件` 列表）而非指望 LLM 记住；② **回滚本身可以做成机制**（见第五节第 8 条）。

### 1.4 环境交互即叙事——Disco Elysium 与 Pentiment

**Disco Elysium（对话即一切）**：
- 没有战斗系统，一切行动都是"对话系统的高风险延伸"；失败技能检定触发独特名场面而非简单惩罚。
- **24 项技能 = 脑内声音**：技能按等级在对话中插嘴、彼此争吵、提供潜台词与新信息，且**不可全信**。
- **Thought Cabinet（思维内阁）**：对话中的行为模式被观察 → 生成"想法"（面朝下）→ 花现实时间"内化"→ 揭晓效果（Buff/Debuff）。它是游戏的"声誉系统 + 天赋树 + 阵营记录"三合一。玩家可"遗忘"某想法（花技能点），于是**身份养成 = 技能本性 × 主动选择的想法**。

**Pentiment（点选调查式对话）**：
- 探案式对话：访问 NPC 收集证言 → 指控机制（模糊证据、误判后果沉重、无"正确答案"）。
- **字体即身份**：神职用哥特体、抄写室用手写体、印刷匠用印刷体——字体既是美学也是玩法（帮你归因匿名纸条）。
- **背景解锁选项**：开局选教育/经历，游戏中解锁专属对话选项。
- 选项哲学："选项出现 ≠ 该选它"，说错话会负面推进，鼓励真正思考而非穷举分支。

> 对封印之殿：把环境检视做成**技能/感知判定**（看见/嗅到/想起）入口；用**视觉隐喻**（色温、光芒、徽标）表达隐藏状态（对应你们"玩家看不到数值"的设计原则）。

---

## 二、多 NPC 对话设计：目标选择、公开/悄悄话/离间

### 2.1 开源惯例：一对一 + 说话人标识

- **Yarn Spinner / Dialogic / Ren'Py**：几乎全是 `角色名: 台词` + 头像，天然一对一。
- **OpenMW**：激活 NPC → 话题列表窗口（topic 关键字高亮）。
- **封印之殿现有方案**：E 锁定当前 NPC + 说话人头像 + 对话相机推近 + 其他 NPC「⚡连锁反应」插卡。

### 2.2 队伍/群聊对话——BG3 与 AIInfluence

**BG3 队伍对话（Larian 社区方案）**：
- 痛点：先触发者独占台词，其他人"观战"。
- 方案：全员各自选回应 → 骰/投票定谁说出口；**未入选的选择也算态度分**；可选"弃答"把焦点让给队友；长时间没说话的人加权重。
- **baldurs-mouth 实现模型**：`Theater`（场景）+ `scenes/NPCs/lines/dialogues`；分支可挂条件（如"需盗贼黑话"）、技能判定（`deception` + DC，成功/失败各走一场景）。

**骑砍 2 AIInfluence（AI 实时对话模组）**：
- **ALT+T 组群聊**：选择哪些 NPC 加入群聊；ALT+G 结束。
- **偷听系统**：约 14m 内英雄能偷听对话、约 4m 内清晰听到；偷听内容进入其记忆，日后可能演变成动态事件。
- NPC 会主动找玩家搭话；每 NPC 有独立认知风格（对幽默/谎言/恩怨/共情的反应）。

### 2.3 公开 vs 悄悄话 vs 窃听的设计空间（重点）

多款社交/狼人游戏验证了同一核心设计模式：**悄悄话的内容保密，但"正在密谈"这件事可见**——这本身制造猜疑。

| 系统 | 机制 | 可借鉴点 |
|---|---|---|
| The Whisper Game | 有限 Whisper Token；"没人能读内容，但所有人都看到你在密谈" | 悄悄话的次数/资源限制；密谈可见性本身产生剧情张力 |
| Marosia | 在场他人可**概率窃听**；失败则"全场都知道你想偷听" | 窃听成败都要有社交代价；同说话人限次 |
| EpicMafia | 随机/累积泄露：多次密谈后泄露**参与者**而非内容 | 泄露分层：参与者泄露 < 内容泄露；累积风险代替纯随机 |
| 近身距离理论（proxemics） | 社交距离=不知密谈；个人距离=看到两人在密谈但听不到；亲密距离=听得见内容 | 用**距离**做可见性分级，天然适配 3D 场景 |
| Town of Salem 黑mailer | 角色能力绕过密谈隐私（静音、窃听） | 给特定 NPC/守护灵"特权窥听"，形成反制与悬念 |
| polis-darwin | Smallville 系多智能体带 **whisper channel**（悄悄话频道）+ 公开消息 + 隐藏内心三层 | 三层模型：公开台词/密谈/隐藏意图，可做玩家旁观视角 |

> 对封印之殿：你们已定"悄悄话=第三方知道密谈但听不到内容 + 守护灵全知"。可进一步：① 用**距离**做窃听判定（AIInfluence 14m/4m 思路）；② 泄露分层——被偷听的悄悄话先暴露"谁和谁密谈过"、压力大时才暴露内容；③ 守护灵"全知"作为反制特权，制造"密谈未必安全"的悬念。

### 2.4 离间 / 挑拨

离间本质是**在公开对话中对 B 说 A 的坏话/真相**，让 NPC 之间的信任值移动。参考素材：BG3 的队友互评（队友对彼此有态度）、AIInfluence 的"NPC 间背景对话也进记忆"、Smallville 的 reflection（NPC 会归纳对他人的印象并行动）。离间的表现力在于**它同时改三方**：目标对被告发者的信任、告发者暴露自己的动机、以及在场/后来得知者的评价。

---

## 三、对话驱动世界改变：关系、信任、秘密、后果

### 3.1 关系/信任系统的成熟模型

| 模型 | 机制 | 可借鉴点 |
|---|---|---|
| The Necromancer's Tale | Trust 通过「Trust Groups」（工人/学者/军队/贵族…）传播；对一个群体作恶，整组降信任；信任门控对话选项 | **群体传播**：信任不是单个标量 |
| Tyranny | **正负双轴独立**（忠诚 vs 恐惧）：对一个人可以又忠诚又畏惧 | 打破单一"好感度"，支持复杂关系 |
| BG3 | 弹出式 "X 赞同/不赞同"；高信任免检定，低信任逼你掷骰 | **即时反馈 + 信任决定检定难度** |
| Fallout: New Vegas | 阵营声誉分层（Hated→Exalted），每层解锁商人/折扣/任务/结局；对立阵营互斥 | **分层 + 互斥**产生分支结局 |
| 骑砍 2 | Relation（-100~100）门控节点可见性、说服成败、交易价格 | 与你们现有"信任度门槛"一致 |

**核心设计原则**：
1. **意识（Awareness）至关重要**——NPC 只对亲眼所见或传闻所知的事产生态度变化；未被发现的暗中行为不涨声誉，除非后来败露。这保护了悄悄话/暗中行动的意义。
2. **可见后果原则**——声誉若只改隐藏数字而不改 NPC 态度、对话分支、任务、区域解锁或结局，系统就是空的。必须把声誉反馈进对话管理器。
3. **隐藏变量要留线索**——不可见负声誉能开新路线，但玩家感到被"作弊"就会反感；要用环境暗示（如"亵渎"值）预兆其存在。

### 3.2 秘密揭示机制：公开谎言 / 秘密真相 / 压裂阈值

一个高质量的"失言/揭密"模型（来自角色模拟设计文档，多款游戏同构）：

- 每个 NPC 持有 `secret_truth`（真相）、`public_lie`（对外谎言）、`trust_threshold`（揭穿所需压力）。
- NPC **持续维护自己的谎言**（记得自己说过什么），矛盾只在压力下或在不同角色之间暴露。
- 压力来源：被出示的证据、威胁、目睹其他角色崩溃、时间流逝。
- **压力 > 阈值 → 角色"压裂"，吐露真相**。
- 信任动态：帮助+保密 ↑ 信任；威胁+背叛 ↓ 信任，甚至让 NPC 更顽固地说谎。
- A House Divided 补充：不同"bearing"型 NPC 需要不同好感门槛（Reserved 需 +2、Lying 需 +5）；且**好感只在 NPC 知情的行动后才变**。

> 这与你们 `失言公式`（防御等级 + 信任度奖励 + 情绪 + 追问累积 + 痛点短语 − 在场威胁）高度同构——区别是开源模型强调**压力来源（证据/威胁/时间）**与**谎言一致性维护**。建议补上"NPC 维护自己的谎言版本"字段，避免穿帮。

### 3.3 后果与分支结局系统

- **动态事件传播**（AIInfluence）：对话直接生成世界事件，消息在地图真实扩散；NPC 间讨论战况/政治；统治者对事件公开发言；玩家可通过他人插话干预。
- **阵营锚点/不可回头点**（F:NV）：关键任务把你锁进某阵营，剩余内容和结局由承诺决定。
- **结局 = 关系网络的函数**（封印之殿现有设计已如此）：真理之殿 / 血债血偿 / 新火种 / 谁都没被救赎 / 弑神者。
- **Thought Cabinet 式"行为被观察→内化→改变能力"**：这是"对话改变人"的最高形态——不只是关系数值变，而是玩家自己的"定义"在变。

### 3.4 记忆系统的可复用工程结构（Smallville 架构）

Stanford Generative Agents（Smallville）把记忆做成可工程化的三层：

1. **记忆流 Memory Stream**：追加式数据库，每条经验（观察/对话/反思/计划）写入时由 LLM 打重要性分（1-10）。
2. **检索 Retrieval**：打分 = 新近性 × 重要性 × 相关性（语义相似度），取 top-k（排序不硬过滤）。
3. **反思 Reflection**：周期把未处理记忆总结成高层抽象（"甲对乙是什么态度"），形成反思树；触发阈值（如重要性累计 >150）。
4. **计划 Planning**：层级计划（天级 → 小时级），只在被新观察反驳时局部重生成。

> 对封印之殿：你们已有 `对话记忆/事件记忆/情绪快照/谣言` 四类。工程上可抄 Smallville 的**「LLM 打重要分 + 按相关度检索」**：回复生成前，只把"与当前话题相关 + 高重要"的记忆注入 prompt，而不是全量历史。

---

## 四、开源项目清单（GitHub）

### A. 对话引擎 / 分支叙事库

| 项目 | 链接 | 可借鉴点 |
|---|---|---|
| ink / inkjs | github.com/inkle/ink | 节点图（knots/diverts/weave）+ visit_count 访问计数 + 纯 JS 运行时；Disco Elysium 用过 |
| Yarn Spinner 2 | github.com/YarnSpinnerTool/YarnSpinner | 剧本式格式 lines/options/commands，语法最易上手；Unity 向 |
| Twine | tads.org / twinery.org | 网页互动小说，快原型；不适配游戏引擎 |
| Articy:Draft | articydraft.com | AAA 级商业叙事工具，可导出 JSON（需自己写解析器） |
| Dialogue System for Unity | pixelcrushers.com | 商业插件，可**导入 ink/Yarn/Twine/Articy 全部格式**，当作格式转换桥 |
| Talkit | github.com/ajboni/Talkit | 纯 JS 节点图对话编辑器（JointJS），导出 JSON，网页直接可用 |
| @motioneffector/dialogue | github.com/motioneffector/dialogue | TS 轻量分支对话系统：条件、flag、文本插值、历史/撤销、i18n、255 单测 |
| simple-dialogue | github.com/bpkennedy/simple-dialogue | 零依赖 JS 分支对话，`id/message/choices/next` + pre/post 生命周期钩子 |
| EasyVN | github.com/Eshan276/easyvn | TS 浏览器视觉小说引擎，label 跳转 + 分支 |
| Ren'Py | github.com/renpy/renpy | 视觉小说惯例（空格推进/数字选分支） |
| OpenMW | github.com/OpenMW/openmw | 激活距离 + 话题列表窗口；老滚式"话题关键字"交互 |
| OpenMB | github.com/cookgreen/OpenMB | 骑砍 1 开源重写：**文本驱动对话树**（节点 id\|文本\|选项 + 条件/后果） |
| baldurs-mouth | github.com/krainboltgreene/baldurs-mouth | BG3 对话系统的可运行模型：`Theater/scenes/lines`，条件分支 + 技能判定 DC |

### B. AI NPC / 生成式对话框架

| 项目 | 链接 | 可借鉴点 |
|---|---|---|
| generative_agents（Smallville） | github.com/joonspk-research/generative_agents | 记忆流/检索/反思/计划四件套，对话+社交涌现（2023 最经典） |
| ai-town | github.com/a16z-infra/ai-town | MIT 可部署的 AI 小镇 starter kit；Convex 后端，支持本地 Ollama |
| AetherNPC | github.com/3239451861-kirito/aethernpc-story | **LLM 建议、服务端裁决**；FastAPI+Pydantic+SQLite+WebSocket；RAG 知识库 + 会话记忆 + LLM Mock 离线兜底；13 NPC/36 节点/76 选择；附 pytest（≥80% 覆盖）与 DFS 分支可达性测试 |
| not_stone | github.com/weicanie/not_stone | LLM NPC 对话 + 社会系统，与封印之殿场景最贴近（注：仓库访问受限，从二手中转资料核实） |
| Golem | github.com/TreasureProject/Golem | 具身 AI agent 框架：BYO-AI（可接 Claude/本地模型）+ 标准 WebSocket 协议 + 视觉学习，无厂商锁定 |
| WorldX | github.com/YGYOOO/WorldX | TS 文本提示生成 AI 虚拟世界 + 多智能体实时模拟（React/Phaser），token 成本高 |
| polis-darwin | github.com/studiomeyer-io/polis-darwin | Claude+LangGraph 多智能体小镇，含 **whisper channel** 悄悄话频道（V2.0 开源中） |
| ai-rpg-text | github.com/kernelshreyak/ai-rpg-text | AI 文本冒险 RPG，可配置机制 |

### C. 技术栈最接近的（TS/Three/React + AI）

| 项目 | 链接 | 可借鉴点 |
|---|---|---|
| overworld | github.com/luzhenqian/overworld | TS + React Three Fiber，`dialogue/quest` 模块与封印之殿栈最接近 |
| disco-api | github.com/msyavuz/disco-api | 对话数据模型 actor/conversant 可直接照搬 |
| Dialogue-Camera（老滚模组） | github.com/Cassieandstuff/Dialogue-Camera | 推近缓动 + 视线锁定 + 对话禁自由转动 |

### D. 商业/闭源但值得抄设计的

- **Inworld / Convai**：闭源 AI NPC 平台（对话+表情+语音），核心思路是"预设动作集 + LLM 选择 + 记忆/情感状态"。
- **AIInfluence 模组（骑砍 2）**：AI 实时对话 + NPC 记忆（100 游戏日）+ 15 段关系状态 + 偷听/群聊 + 动态事件传播（概念级参考）。
- **The Whisper Game / Marosia / EpicMafia / Town of Salem**：悄悄话可见性与窃听成本的设计样本（见第二节）。

---

## 五、对封印之殿可落地的 8 条具体构思

按"成本/收益"粗略排序，均对齐现有架构（Python 状态机裁决 + AI 生成 + Three.js 前端）：

1. **检视/观察层（Look vs Examine）升级**：现有 E 键只管对话。扩展为**上下文敏感**：走近 NPC→「按 E 交谈」；面向场景物件（浮雕、符文、书架）→「按 E 观察」→ 触发感知旁白，部分物件可接"感知判定"（借鉴 Disco Elysium 技能注入）。成本低，立刻让环境成为叙事载体。

2. **三层对话输入并存，用骑砍式话题树当锚点**：① 自由输入（现有）；② 意图快捷按钮（试探/安慰/挑拨/交易/告别）作导航锚点；③ 关键剧情节点走**节点分支**（数字键选，状态机裁决）。实现可参考 AetherNPC 的"LLM 建议、服务端裁决"分层，或 direct 抄 OpenMB/baldurs-mouth 的条件分支数据结构。

3. **悄悄话的"距离可见性"落地**：公开=全场可听可插话；悄悄话=他人看到你们密谈但听不到内容；**窃听=第三方在一定距离内概率听到片段**（借鉴 AIInfluence 14m/4m + Marosia 概率 + proxemics 分级）。守护灵全知作为"反制特权"保留——密谈并不绝对安全，制造悬念。泄露分层：先露"谁与谁密谈过"，压力大才露内容。

4. **秘密压裂模型补强**：现有 `失言公式` 已经很接近开源的 `public_lie / secret_truth / trust_threshold` 模型。补两点：① 给每个 NPC 维护**"谎言一致性"字段**（自己说过什么版本），避免 AI 穿帮；② 压裂压力不只来自追问，还来自**出示证据、威胁、目睹他人崩溃、时间**。

5. **关系双轴 + 三方同时改值**：把单一"对其他 NPC 态度"拆成**信任/畏惧双轴**（Tyranny 思路），支持"又忠诚又害怕"的复杂关系。实现"告诉 A 一个关于 B 的秘密"时**一次改三个值**：A 对玩家信任↑、B 知情后对玩家信任↓、谣言/知情面扩散到其他 NPC（AIInfluence 动态事件传播的缩小版）。

6. **记忆检索工程化（Smallville 三层）**：现有四类记忆（对话/事件/情绪/谣言）继续保留，但回复生成前**只注入相关记忆**：LLM 给每条记忆打重要性分，按"新近×重要×相关"取 top-k 进 prompt。防长程遗忘、省 token，和现有 `ai_pipeline.py` 天然衔接。

7. **隐藏状态可视化隐喻**：贯彻"玩家看不到数值"原则，但用**体感信号**传达：对话面板情绪徽标（平静/紧绷/愤怒/脆弱）、屏幕色温随关系冷热变化、守护灵光芒强度随"它对你的判断"变化（Pentiment 字体/墨色隐喻 + Disco Elysium 脑内声音的降维版）。

8. **把"反悔"做成机制**：关键分支点允许**撤回一次**（AI Dungeon undo 思路），但代价是**守护灵记住你反悔过**并在最终评判中提及（Thought Cabinet"遗忘有成本"的叙事化）——把系统功能变成世界层叙事。

> 落地优先级建议：1（检视层）→ 7（隐喻）→ 3（悄悄话距离）→ 2（话题树）→ 4（压裂补强）→ 5（双轴）→ 6（记忆检索）→ 8（反悔机制）。1/2/7 接近纯前端，可与现有 3D 原型直接迭代；3/4/5 主要落在 Python 状态机层；6 落在 AI 管线 prompt 工程。

---

## 附：参考来源

**互动按键**
- Skyrim/Fallout 4 对话轮限制与 XDI 模组：forums.nexusmods.com/topic/3955830-solving-the-4-options-dialogue-system/ 、 nexusmods.com/fallout4/mods/27216
- SCUMM 与动词演进：ign.com/articles/2008/10/16/back-to-the-mansion 、 intfiction.org/t/strengths-of-various-forms-of-interactive-storytelling/44348/48
- 文字冒险动词模型：cs.gettysburg.edu/~tneller/cs112/16fa/if.html
- AI Dungeon：en.m.wikipedia.org/wiki/AI_Dungeon_2 、 help.aidungeon.com/faq/what-things-should-i-know
- Disco Elysium Thought Cabinet：discoelysium.com/devblog/2019/09/30/introducing-the-thought-cabinet 、 rockpapershotgun.com/disco-elysium-thought-cabinet-the-thoughts-system-explained ；失败检定：rockpapershotgun.com/combat-failure-and-raising-the-stakes-in-disco-elysium
- Pentiment：trueachievements.com/n51956/pentiment-xbox-dialogue-options 、 languageatplay.de/2023/01/09/the-talking-scripts-of-obsidians-pentiment/

**多 NPC / 悄悄话**
- BG3 队伍对话方案：forums.larian.com/ubbthreads.php?ubb=showthreaded&Number=959506
- baldurs-mouth：github.com/krainboltgreene/baldurs-mouth
- 骑砍 AIInfluence：nexusmods.com/mountandblade2bannerlord/mods/9711 、 steamcommunity.com/sharedfiles/filedetails/changelog/3584621421
- 悄悄话可见性：indiedb.com/games/the-whisper-game/news/the-whisper-game-enters-early-access 、 marosia.com/doku/doku.php?id=communication 、 epicmafia.com/topics/81351 、 fol-archive.netlify.app/t/whispers-deep-analysis-metagame-suggestions/71154

**关系/信任/秘密/后果**
- Necromancer's Tale Trust Groups：indiedb.com/features/trust-and-tension-in-the-necromancers-tale
- BG3 声誉系统设计取舍：tech.yahoo.com/gaming/articles/baldurs-gate-3-writer-says-170000455.html
- 声誉系统设计随笔（可见后果）：sites.wsagames.com/jz15n24/2026/02/27/reputation-system-design%ef%bc%9a-let-the-dialogue-choices-leave-consequences/
- 秘密/压裂模型（角色模拟文档）：raw.githubusercontent.com/kase1111-hash/ASCII-City/refs/heads/main/docs/modules/02-character-simulation.md
- Smallville 架构：deepwiki.com/nmatter1/smallville/1-overview 、 github.com/joonspk-research/generative_agents

**开源项目**
- 对话工具对比：narrativeflow.dev/blog/twine-vs-yarn-spinner-vs-ink-vs-narrativeflow-which-branching-dialogue-tool-is-right-for-your-game/
- Talkit / @motioneffector/dialogue / simple-dialogue：github.com/ajboni/Talkit 、 github.com/motioneffector/dialogue 、 github.com/bpkennedy/simple-dialogue
- AetherNPC：github.com/3239451861-kirito/aethernpc-story
- Golem：github.com/TreasureProject/Golem
- WorldX：github.com/YGYOOO/WorldX
- polis-darwin：github.com/studiomeyer-io/polis-darwin
- ai-town：github.com/a16z-infra/ai-town
