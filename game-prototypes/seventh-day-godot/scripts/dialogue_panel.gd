extends PanelContainer
## 对话面板 —— 第三课：信号；第七课：分支选项；第十一课：关系系统；第十二课：世界状态
##
## 第十一课新招：
##   1. effect —— 选项带"效果"，选了就改变对方 4 维关系（写进 GameState 单例）
##   2. need  —— 选项带"门槛"，关系不够就不出现
##   3. RelLabel —— 面板里实时显示对方四维关系
## 第十二课新招：
##   4. need 里还能写世界状态门槛：{"bell_rings": 2} 钟响过 2 次、{"flag": "名字"} 已点亮旗标
##   5. effect里还能写 {"set_flag": "名字"} —— 选这句，就在 GameState 里留下全城记忆
## 第十三~十七课新招：
##   6. 对话面板左侧显示 NPC 立绘（assets/portraits/<名字>.png，没有就留空）
##   7. 结局流程：选项带 "ending": true 时，改成从 "_ending" 数据里出结局三选一

signal closed   # 对话结束信号（以后别的系统可以听这个）

@onready var _name_label: Label = $HBox/VBox/NameLabel
@onready var _rel_label: Label = $HBox/VBox/RelLabel     # 第十一课：四维关系一行字
@onready var _text_label: Label = $HBox/VBox/TextLabel
@onready var _choices: VBoxContainer = $HBox/VBox/Choices
@onready var _next_button: Button = $HBox/VBox/Next
# 第十七课：立绘。场景里还没加 HBox/Portrait 节点时会是 null，代码里都做了空判断
@onready var _portrait: TextureRect = get_node_or_null("HBox/Portrait")

const PANEL_H := 104.0         # 普通对话的面板高度（第十一课加了一行关系字，撑高了点）
const PANEL_H_CHOICES := 152.0 # 出选项时的高度（要放下按钮们）
const PORTRAIT_DIR := "res://assets/portraits/"

# 第十一课：维度的顺序、中文名、数值翻译
const DIM_ORDER := ["trust", "fear", "like", "suspect"]
const DIM_LABELS := { "trust": "信任", "fear": "恐惧", "like": "好感", "suspect": "怀疑" }
const TIER_WORD := ["低", "中", "高"]

var _lines: Array[String] = []
var _options: Array[Dictionary] = []
var _index := 0
var _npc_name := ""           # 第十一课：现在跟谁说话（改关系要用）
var _showing_reply := false   # 第七课：正在显示某个选项的回复
var _ending: Dictionary = {}  # 第十七课：结局三选一（从 dialogues.json 的 "_ending" 读）

func _ready() -> void:
	# ★ 信号连接：按钮被按下 → 调 _on_next_pressed()
	_next_button.pressed.connect(_on_next_pressed)
	_load_ending()             # 第十七课：结局数据

func open(npc_name: String, lines: Array[String], options: Array[Dictionary]) -> void:
	_lines = lines if not lines.is_empty() else ["……"]
	_options = options
	_index = 0
	_npc_name = npc_name
	_showing_reply = false
	_name_label.text = npc_name
	_refresh_rel()            # 第十一课：打开就显示当前关系
	_update_portrait(npc_name) # 第十七课：换上这位 NPC 的立绘
	_show_current()
	visible = true

func advance() -> void:
	# 玩家按 E 时也叫这个（和点按钮同一招）
	_on_next_pressed()

func _on_next_pressed() -> void:
	if _choices.visible:
		return  # 第七课：有选项在等选择时，E 先无效，得先点一个
	if _showing_reply:
		# 第十七课：结局看完，"继续"就是离开游戏
		if not GameState.ending.is_empty():
			get_tree().quit()
			return
		close()
		return
	_index += 1
	if _index < _lines.size():
		_show_current()
	elif not _options.is_empty():
		_show_choices()   # 主台词说完了，还有选项 → 出岔路口
	else:
		close()

func _show_current() -> void:
	_set_height(PANEL_H)
	_text_label.text = _lines[_index]
	_next_button.text = "继续 [E]"
	_next_button.visible = true
	_hide_choices()

func _show_choices() -> void:
	_set_height(PANEL_H_CHOICES)
	_next_button.visible = false
	_hide_choices()
	# 第七课：循环里给每个选项 new 一个按钮，连到同一个处理函数
	# bind(opt) 把"这是哪个选项"也一起传给回调
	# 第十一课：只有"过门槛"的选项才会出现（_passes_need）
	for opt in _options:
		if not _passes_need(opt):
			continue   # 关系不够，这选项不出现
		var btn := Button.new()
		btn.text = str(opt.get("label", "……"))
		btn.pressed.connect(_on_choice_pressed.bind(opt))
		_choices.add_child(btn)
	# 如果一个能选的都没有，也别卡死——直接当"说完了"
	if _choices.get_child_count() == 0:
		close()
		return
	_choices.visible = true

func _on_choice_pressed(opt: Dictionary) -> void:
	# 第十七课：这是"听懂这座城"的入口 → 不显示普通回复，直接进结局三选一
	if opt.get("ending", false):
		_show_ending_choices()
		return
	_apply_effect(opt.get("effect", {}))   # 第十一课：选完先改关系
	_refresh_rel()                          # 关系变了，刷新那行字
	_set_height(PANEL_H)
	_hide_choices()
	_text_label.text = str(opt.get("reply", "……"))
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true

# ---- 第十一课：关系系统 ----

# 应用选项的效果：
#   {"trust": 1, "suspect": -1} → 关系上下浮动，锁在 0~2（第十一课）
#   {"set_flag": "名字"}        → 点亮世界状态旗标，成为全城的共同记忆（第十二课）
func _apply_effect(effect: Dictionary) -> void:
	if GameState.relations.has(_npc_name):
		var rel: Dictionary = GameState.relations[_npc_name]
		for dim in effect:
			if rel.has(dim):
				rel[dim] = clampi(int(rel[dim]) + int(effect[dim]), 0, 2)
	if effect.has("set_flag"):
		GameState.set_flag(str(effect["set_flag"]))
	GameState.check_progress()   # 第十三课：选完这句话，看看剧情该不该推进（刻痕/天亮）

# 这个选项要不要出现？没写 need 就一直出现；写了就要"过门槛"
# 门槛有两类：
#   关系（第十一课）：     {"trust": 2}              → 对方信任 >= 2
#   世界状态（第十二~十七课）：
#     {"bell_rings": 2}  → 钟楼响过 >= 2 次
#     {"day": 2}         → 已经是第 2 天
#     {"marks": 2}       → 已经有 2 道刻痕
#     {"flag": "名字"}    → 已点亮旗标"名字"
#     {"no_flag": "名字"}  → 还没点亮旗标"名字"
func _passes_need(opt: Dictionary) -> bool:
	var need: Dictionary = opt.get("need", {})
	if need.is_empty():
		return true
	# —— 关系门槛（第十一课）
	var rel: Dictionary = GameState.relations.get(_npc_name, {})
	for dim in ["trust", "fear", "like", "suspect"]:
		if need.has(dim) and int(rel.get(dim, 0)) < int(need[dim]):
			return false
	# —— 世界状态门槛（第十二~十七课）
	if need.has("bell_rings") and GameState.bell_rings < int(need["bell_rings"]):
		return false
	if need.has("day") and GameState.day < int(need["day"]):
		return false
	if need.has("marks") and GameState.marks < int(need["marks"]):
		return false
	if need.has("flag") and not GameState.has_flag(str(need["flag"])):
		return false
	if need.has("no_flag") and GameState.has_flag(str(need["no_flag"])):
		return false
	return true

# 刷新面板上那行四维关系字：信任中 · 恐惧低 · 好感高 · 怀疑低
func _refresh_rel() -> void:
	var rel: Dictionary = GameState.relations.get(_npc_name, {})
	var parts: Array[String] = []
	for dim in DIM_ORDER:
		var v := int(rel.get(dim, 1))
		parts.append("%s%s" % [DIM_LABELS[dim], TIER_WORD[clampi(v, 0, 2)]])
	_rel_label.text = " · ".join(PackedStringArray(parts))

func _hide_choices() -> void:
	_choices.visible = false
	# 旧的选项按钮要清掉：先移出树，再让它自己销毁（下帧）
	for child in _choices.get_children():
		_choices.remove_child(child)
		child.queue_free()

func _set_height(h: float) -> void:
	# 面板是"锚点居中 + 上下 offset"，用 offset 撑出高度
	var half := h * 0.5
	offset_top = -half
	offset_bottom = half

func close() -> void:
	_set_height(PANEL_H)
	_hide_choices()
	if _portrait:
		_portrait.visible = false
	visible = false
	closed.emit()

# ---- 第十七课：立绘 + 结局 ----

# 换立绘：assets/portraits/<名字>.png 存在就显示，没有就先留空（以后放进图片即可）
func _update_portrait(npc_name: String) -> void:
	if _portrait == null:
		return
	var path := PORTRAIT_DIR + npc_name + ".png"
	if ResourceLoader.exists(path):
		_portrait.texture = load(path)
		_portrait.visible = true
	else:
		_portrait.texture = null
		_portrait.visible = false

# 从 dialogues.json 的 "_ending" 键读结局三选一
func _load_ending() -> void:
	var file := FileAccess.open("res://dialogues.json", FileAccess.READ)
	if file == null:
		return
	var data: Variant = JSON.parse_string(file.get_as_text())
	if data is Dictionary and data.has("_ending"):
		_ending = data["_ending"]

# 结局入口：把三个结局变成按钮
func _show_ending_choices() -> void:
	_set_height(PANEL_H_CHOICES)
	_next_button.visible = false
	_hide_choices()
	_text_label.text = str(_ending.get("title", "三道刻痕同时亮起……"))
	for opt in _ending.get("options", []):
		var btn := Button.new()
		btn.text = str(opt.get("label", "……"))
		btn.pressed.connect(_on_ending_chosen.bind(opt))
		_choices.add_child(btn)
	if _choices.get_child_count() == 0:
		close()
		return
	_choices.visible = true

# 玩家挑了一个结局 → 记进 GameState，显示结局文案，"继续"就退出游戏
func _on_ending_chosen(opt: Dictionary) -> void:
	GameState.ending = str(opt.get("label", "留白"))
	_apply_effect(opt.get("effect", {}))
	SaveManager.save_game()   # 第十八课：结局定下了，落盘
	_set_height(PANEL_H)
	_hide_choices()
	_text_label.text = str(opt.get("reply", "……"))
	_next_button.text = "—— 故事完 —— [E]"
	_next_button.visible = true
	_showing_reply = true
