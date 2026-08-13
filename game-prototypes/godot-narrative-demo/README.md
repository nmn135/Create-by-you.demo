# 第七天 · Godot 学习版

把 2D 叙事 demo《第七天》搬进 Godot 的第一块砖。**目的不是功能，是让你把场景树/节点/脚本这三件事在手上跑一遍。**

## 打开方式（你的机器）

1. Godot 4.7.1 在：`D:\EDGE\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe`
2. 打开 Godot → **项目管理器 → 导入** → 选中本文件夹的 `project.godot`
3. 打开项目后按 **F5** 运行
4. 操作：**← → / A D** 左右移动；靠近 NPC 按 **E**（或空格）打招呼、再按推进对话

## 第一课 · 场景树长什么样（核心课）

打开 `scenes/main.tscn`，看左上角"场景"面板——这就是一棵树：

```
Main (Node2D)                          ← 根节点：整个场景就是这棵树
├── Background (ColorRect)             ← 夜空背景（一个填满 320×180 的色块节点）
├── Ground (ColorRect)                 ← 地面线（y=158）
├── ClockTower (ColorRect)             ← 钟楼（占位色块，对应 BELL_POS.x=160）
├── Bell (ColorRect)                   ← 那口钟（占位色块）
├── Mayor (NPC)                        ← 市长：npc.tscn 的实例 #1
├── Pawn (NPC)                         ← 当铺老板：npc.tscn 的实例 #2
├── Bard (NPC)                         ← 说书人：npc.tscn 的实例 #3
├── Player (CharacterBody2D)           ← 玩家：带脚本的物理体
│   └── CollisionShape2D               ← 玩家的碰撞盒（12×16）
└── UI (CanvasLayer)                   ← 界面层：永远盖在最上面
    └── Prompt (Label)                 ← "E 交谈"提示文字
```

**三个要点：**
1. **一切都是节点**——背景、地面、钟楼、钟，连玩家，全是一个个节点，靠父子关系组成一棵树。
2. **脚本挂节点**——`player.gd` 挂在 Player 上，`_physics_process()` 每帧跑，改 `velocity` 再 `move_and_slide()` 就是移动。
3. **谁在上谁先画**——场景面板里**排在上面的节点画在最底层**（Background 在最底下），顺序就是绘制顺序；而 `UI (CanvasLayer)` 是特殊的"图层"，不管排在哪都画在最上面。

## 第二课 · 场景实例化：种出会走路的 NPC

**核心概念：一个场景 = 一棵可复用的树。** 先写好 `npc.tscn`（一棵只有一个节点、挂着 `npc.gd` 的小树），然后在 `main.tscn` 里用 `instance=` **种三次**，就是三个 NPC。改一次脚本，三个人同时生效——这就是 Godot 做"复制粘贴对象"的正规方式。

每个 NPC 都长这样：

```
Mayor (NPC)                     ← npc.tscn 的实例
├── npc_name = "市长"            ← @export 变量：选中节点，右边 Inspector 面板直接改
├── stations = [(52,150), (150,150), (208,150)]   ← 巡逻站点
├── speed / dwell               ← 走路速度 / 到站停留秒数
└── body_color                  ← 衣服颜色
```

在脚本里新学到的四招：
1. **`@export`**——`@export var speed := 32.0` 会出现在 Inspector 面板里，不写代码就能调参数。选中 `Mayor` 节点，看右边面板，改改 `dwell` 再 F5 试试。
2. **`move_toward()`**——匀速挪向目标，一次只挪一格、不会"飞过去"：`position.x = move_toward(position.x, target.x, speed * delta)`。
3. **计时器写法**——`_waiting` 到站后倒数，减到 0 才继续走（`_process(delta)` 里 `_waiting -= delta`）。
4. **组（group）**——NPC 在 `_ready()` 里 `add_to_group("npcs")`，玩家在 `player.gd` 里 `get_tree().get_nodes_in_group("npcs")` 就能找到他们。这是 Godot 给"同类对象"贴的标签。

玩家的新花样：`@onready var _prompt: Label = get_node("../UI/Prompt")` —— **等树就绪**再取引用，`../` 表示父节点；`_unhandled_input()` 接住 E 键事件（`InputEventKey`，`physical_keycode == KEY_E`）。靠近 NPC 时底部弹出提示，按 E 会得到一句"对话面板下节课做"的占位回应。

## 第三课 · 对话面板 + 信号（signal）

按 E 靠近 NPC → 弹出对话面板 → 逐句看台词 → 看完关闭。

新增：
- `scenes/dialogue_panel.tscn` + `scripts/dialogue_panel.gd` —— 对话面板（挂在 UI 层）
- `npc.gd` 加 `@export var lines: Array[String]` —— 每个 NPC 的台词（Inspector 里写）
- `player.gd`：按 E → `_dialogue.open(npc.npc_name, npc.lines)`

**信号（signal）＝ 节点"喊一声"，谁连了谁响应**。核心一行：

```gdscript
_next_button.pressed.connect(_on_next_pressed)
# "继续按钮被按下"这个信号 → 连到"下一句"方法
```

**踩坑记录（重要）**：场景文件在 Godot 编辑器里开着时，外部直接改文件会被编辑器的保存覆盖。场景开着时，改动要在编辑器里做（如拖拽实例化）。

```
UI (CanvasLayer)                 ← 第三课版
├── Prompt (Label)               ← "E 交谈"提示
└── DialoguePanel (PanelContainer)
    ├── NameLabel                ← NPC 名字
    ├── TextLabel                ← 台词（自动换行）
    └── Next (Button)            ← 继续（pressed → 下一句）
```

## 第四课 · 输入映射（Input Map）

把"具体键"升级成"命名动作"：代码不认识 `KEY_A`/`KEY_E`，只问 `move_left`/`interact` 被按了吗。

`project.godot` 的 `[input]` 定义键位表：

| 动作 | 绑定的键 |
|---|---|
| `move_left` | A、← |
| `move_right` | D、→ |
| `interact` | E、空格（学员亲手加的） |

代码写法：
```gdscript
Input.is_action_pressed("move_left")    # 按住类输入（每帧查）
event.is_action_pressed("interact")     # 事件类输入（_unhandled_input）
```

**改键位的地方**：项目 → 项目设置 → 输入映射。改完不用动代码。⚠️ 改过 `project.godot` 后要**完全退出项目重开**，编辑器才会重新读。

## 第五课 · 碰撞：撞不动，才像活着

让 NPC 从"穿得过的一张贴图"变成"有实体的活人"——玩家走不进 NPC 身体里。

**三个新概念：**

1. **碰撞盒 `CollisionShape2D`** —— 贴在物理体上的"皮肤"，决定占多大面积。玩家身上早就有（12×16 的蓝色框）；这一课给 NPC 也加了一个（10×14，比小人略小一圈，手感更好）。
2. **碰撞层 / 掩码（layer / mask）** —— 游戏物理里最重要的两个数：
   - `layer`（第几层）= 我是谁
   - `mask`（撞谁）= 我会撞到哪些层
   - 玩家 `layer=1` `mask=2`（撞第 2 层 = NPC）；NPC `layer=2` `mask=0`（谁都不撞 → 四个 NPC 不会互挤成一坨）
3. **物理体移动套路** —— 会动的物体统一走：`velocity = 方向 × 速度` + `move_and_slide()`，且必须在 `_physics_process()`（固定 60 次/秒的物理帧）里跑。NPC 从 `Node2D` 升级成 `CharacterBody2D` 后，和玩家共用同一套 API。

```gdscript
velocity = to_target.normalized() * speed   # 想往哪走、走多快
move_and_slide()                            # 走，撞到就停
```

**课后自己动手试：**
- 选中任一 NPC → Inspector 里把 `collision_layer` 改成 1、`collision_mask` 改成 1，F5 看看会发生什么（提示：NPC 开始"堵车"）
- 选中 NPC 下的 `CollisionShape2D`，在场景视图里拖那个蓝色框，调大调小试试手感

## 第六课 · 感应区 Area2D：别再"量距离"了

之前判断"能不能跟 NPC 说话"，用的是土办法：算玩家和 NPC 的**横向距离 < 20**。这招有两个毛病——只比横坐标、而且逻辑散在玩家身上。

这一课换成 Godot 的正规军 **Area2D（感应区）**：每个 NPC 身上挂一个透明的感应圈，玩家走进来触发 `body_entered` 信号、走出去触发 `body_exited` 信号，NPC 自己记下"玩家在不在身边"。

```
NPC (CharacterBody2D)               ← 第六课版
├── CollisionShape2D                ← 实体碰撞盒（第五课，挡玩家的）
└── Area2D (感应区，透明不挡路)
    └── CollisionShape2D            ← CircleShape2D 半径 22 的感应圈
```

NPC 侧（谁进圈、谁出圈，NPC 自己管）：
```gdscript
$Area2D.body_entered.connect(_on_area_body_entered)
func _on_area_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		player_near = true
```

玩家侧（不再量距离，只问结果）：
```gdscript
func _nearby_npc() -> Node2D:
	for n in get_tree().get_nodes_in_group("npcs"):
		if n.player_near:
			return n
	return null
```

**坑：两个 NPC 同时感应到你？** 感应圈调大后，可能有两个 NPC 同时罩住你，`player_near` 同时为 true。如果"见一个就返回"会乱选（按场景树顺序）。正解是分工：**感应圈管"行不行"**（筛出附近的人），**距离只管"选哪个"**（在附近的人里比距离取最近）。见 `_nearby_npc()`：先 `if n.player_near` 筛一遍，再比 `distance_to`。

**为什么这招是万金油**：`body_entered` / `body_exited` 信号是所有"进入区域触发事件"的标准做法——触发剧情、陷阱、传送门、购物半径，全是它。以后做"走进钟楼就响起旁白"，也只是再挂一个 Area2D 的事。

**课后自己动手试**：选中任一 NPC → 展开 `Area2D` → 选中它的 `CollisionShape2D`，在场景视图里把感应圈**拖大拖小**，感受"多大范围才弹 E 提示"。

## 第七课 · 对话分支：说话有了岔路口

普通对话是一字排开往下说；这课给对话加上"岔路口"——说到最后一句，弹出几个选项，你选哪个就接哪句话。

**数据格式升级**：每个 NPC 多了一个 `options`（选项数组），每个选项是一个**字典（Dictionary）**：

```gdscript
options = [
	{ "label": "讲讲刻痕", "reply": "头一道刻痕落下的那夜，钟楼第一次没响。" },
	{ "label": "告辞",     "reply": "我讲的故事里，命都改写过。" },
]
```

- `label` = 屏幕上选项按钮的文字
- `reply` = 点了之后对方接的话

**三个新招：**

1. **字典 `Dictionary`** —— `{ 键: 值 }` 的小盒子，一个格子能装"一组"信息（这里是一对 label/reply）。
2. **动态生成按钮** —— 选项是开会时"现造"的：
   ```gdscript
   for opt in _options:
       var btn := Button.new()
       btn.text = str(opt.get("label", "……"))
       btn.pressed.connect(_on_choice_pressed.bind(opt))
       _choices.add_child(btn)
   ```
   `Button.new()` 在代码里造按钮，`add_child` 挂到界面上；`bind(opt)` 把"这是哪个选项"一起传给回调。
3. **用完清理** —— 每次开会前把旧按钮 `remove_child` + `queue_free` 掉，否则越攒越多。

**流程**：主台词 → 最后一句 → 出选项 → 点了 → 显示 reply → "告辞" 关面板。E 键在有选项等待时会先失效（防止一路按 E 把面板按没）。

**课后动手**：在 Inspector 里选一个 NPC → 展开 `options` → 改 `label` / `reply` 的文字，或 Add Element 加新选项。

## 第八课 · 台词搬进 JSON：数据就该待在文件里

第七课结束时你被 Inspector 手敲字典折磨了一顿——这节课彻底根治：**台词从场景文件里搬出去，放到一个 `dialogues.json`**，NPC 启动时自己读。玩法一行没改，纯"数据搬家"——这就是**重构**。

**`dialogues.json` 长这样**（用记事本就能改）：
```json
{
	"说书人": {
		"lines": ["第七天夜里，城会说话。", "三道刻痕，作者之墨。", "你信命吗？"],
		"options": [
			{ "label": "讲讲刻痕", "reply": "头一道刻痕落下的那夜，钟楼第一次没响。" },
			{ "label": "告辞", "reply": "我讲的故事里，命都改写过。" }
		]
	}
}
```
顶层用 `npc_name` 当钥匙，NPC 启动时按自己的名字去查。JSON 天生就是"字典套数组"，和台词结构一模一样。

**读取代码**（npc.gd 的 `_load_dialogue`）：
```gdscript
var file := FileAccess.open("res://dialogues.json", FileAccess.READ)
var data: Variant = JSON.parse_string(file.get_as_text())
if data.has(npc_name):
	var entry: Dictionary = data[npc_name]
	lines = _to_string_array(entry.get("lines", []))
	options = _to_dict_array(entry.get("options", []))
```

**三个新招：**
1. **`FileAccess`** —— 读文件的入口：`open(路径, READ)` 打开，`get_as_text()` 把整个文件读成字符串。
2. **`JSON.parse_string()`** —— 把 JSON 文本解析成 Godot 的字典/数组。
3. **`Variant` 转定型数组** —— JSON 读出来的是"万能类型"，要转回 `Array[String]` / `Array[Dictionary]`（见 `_to_string_array` / `_to_dict_array`）。

**课后动手**：用记事本打开 `dialogues.json`，给说书人加第四个选项（照着格式抄一行），F5 看看出现没有——全程不用碰 Inspector。

## 常用单词速查（忘了就回来翻）

| 英文 | 意思 | 在哪 |
|---|---|---|
| `Inspector` | 属性面板（右边） | 选中节点后用它改参数 |
| `npc_name` | NPC 显示名 | Inspector |
| `body_color` | 衣服颜色 | Inspector（点色块换色） |
| `stations` | 巡逻站点列表 | Inspector（点箭头展开，`Size`=数量） |
| `speed` | 移动速度（像素/秒） | Inspector |
| `dwell` | 到站停留秒数 | Inspector |
| Rename | 重命名节点 | 右键节点 → Rename |
| Instance Child Scene | 实例化子场景 | 场景面板顶部链子图标 |
| FileSystem | 文件面板（左下） | 从这拖 `.tscn` 进场景 |
| Scene | 场景面板（左上） | 场景树在这 |
| Input Map | 输入映射（键位表） | 项目 → 项目设置 → 输入映射 |
| `is_action_pressed` | "这个动作被按了吗？" | 代码里（`Input.` 或 `event.`） |
| `CollisionShape2D` | 碰撞盒（身体的"皮肤"） | 物理体下面的子节点，设 `shape` |
| `collision_layer` | 我是第几层 | Inspector → 节点 → 碰撞 |
| `collision_mask` | 我会撞到哪些层 | 同上 |
| `_physics_process` | 物理帧（固定 60 次/秒） | 物理体的移动放这 |
| `move_and_slide()` | "走，撞到就停" | 物理体每帧最后调用 |
| `Area2D` | 感应区（透明，不挡路） | 挂在身上，检测"谁进来了" |
| `body_entered` | "有物理体进来了"信号 | `$Area2D.body_entered.connect(...)` |
| `body_exited` | "有物理体出去了"信号 | 同上 |
| `Dictionary` | 字典（{键: 值} 小盒子） | `{ "label": "问刻痕", "reply": "……" }` |
| `Button.new()` | 代码里造一个新按钮 | 循环里动态生成 UI |
| `opt.get("key", 默认值)` | 取字典里的值，没有就返回默认 | `opt.get("label", "……")` |
| `FileAccess.open(路径, READ)` | 打开文件准备读取 | 路径用 `res://` 开头 |
| `get_as_text()` | 把整个文件读成字符串 | `FileAccess` 的方法 |
| `JSON.parse_string(文本)` | JSON 文本 → 字典/数组 | 和 `get_as_text()` 配合 |
| `dialogues.json` | 台词数据文件（记事本可改） | 顶层按 npc_name 查 |

## 对应到 Canvas 版 demo

| 这里 | Canvas 版 (`2d-narrative-demo/index.html`) |
|---|---|
| `Main` 根节点 | `SCENES` 状态机 + 主循环 |
| `Player` + `player.gd` | `player` 对象 + 主循环里左右移动那段 |
| `Mayor`/`Pawn`/`Bard` (NPC) | `npcs[]` + `drawNPC()`/站点巡游 |
| `npc.gd` 的 `stations` | `npc.stations` 站点数组 |
| `ClockTower`/`Bell` 色块 | `BELL_POS`/`drawBell()` |
| `UI` (CanvasLayer) | `#dialogue` / HUD |
| `_physics_process` | 每帧 `loop(dt)` |
| `Input.is_action_pressed` | `keys[...]` 键位表 |
| NPC 的 `Area2D` 感应圈 | 距离判断（`Math.abs(npc.x - player.x) < 40`） |
| `options`（Array[Dictionary]） | 话题快捷栏（节点分支对话 v1） |

## AI 协作环境（godot-mcp，已配好）

Claude Code / Claudian 通过 MCP 直接操作 Godot：

- 服务：`npx @coding-solo/godot-mcp`（Node 版，MCP stdio）
- 注册：`claude mcp add godot --scope user -e GODOT_PATH="D:/EDGE/Godot_v4.7.1-stable_win64.exe/Godot_v4.7.1-stable_win64.exe" -- npx @coding-solo/godot-mcp`
- 工具：`run_project`（跑项目抓输出）、`get_debug_output`（回传报错）、`add_node`/`create_scene`（直接改场景）、`get_godot_version` 等
- **改配置后要重启 Claudian 会话**，MCP 工具才会出现在工具列表里

## 下一步（学完这些再往上加）

- [x] 对话 UI（CanvasLayer + Control，对应 `#dialogue`）——第三课完成 ✅
- [x] 输入映射（Input Map，A/D/E 命名动作）——第四课完成 ✅
- [x] 碰撞：NPC 也带碰撞盒，玩家不能穿人 —— 第五课完成 ✅
- [x] 感应区：Area2D 替代"距离土办法"触发交谈 —— 第六课完成 ✅
- [x] 对话分支：选项 + 动态按钮 —— 第七课完成 ✅
- [x] 第八课：台词搬进 JSON 文件（`dialogues.json`，启动时读）——完成 ✅
- [ ] 换正式场景（用 `bg.png`，或先程序化画）
