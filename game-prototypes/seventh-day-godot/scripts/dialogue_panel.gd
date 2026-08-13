extends PanelContainer
## 对话面板 —— 第三课：信号；第七课：分支选项；第十一课：关系系统
##
## 第十一课新招：
##   1. effect —— 选项带"效果"，选了就改变对方 4 维关系（写进 GameState 单例）
##   2. need  —— 选项带"门槛"，关系不够就不出现
##   3. RelLabel —— 面板里实时显示对方四维关系

signal closed   # 对话结束信号（以后别的系统可以听这个）

@onready var _name_label: Label = $VBox/NameLabel
@onready var _rel_label: Label = $VBox/RelLabel     # 第十一课：四维关系一行字
@onready var _text_label: Label = $VBox/TextLabel
@onready var _choices: VBoxContainer = $VBox/Choices
@onready var _next_button: Button = $VBox/Next

const PANEL_H := 104.0         # 普通对话的面板高度（第十一课加了一行关系字，撑高了点）
const PANEL_H_CHOICES := 152.0 # 出选项时的高度（要放下按钮们）

# 第十一课：维度的顺序、中文名、数值翻译
const DIM_ORDER := ["trust", "fear", "like", "suspect"]
const DIM_LABELS := { "trust": "信任", "fear": "恐惧", "like": "好感", "suspect": "怀疑" }
const TIER_WORD := ["低", "中", "高"]

var _lines: Array[String] = []
var _options: Array[Dictionary] = []
var _index := 0
var _npc_name := ""           # 第十一课：现在跟谁说话（改关系要用）
var _showing_reply := false   # 第七课：正在显示某个选项的回复

func _ready() -> void:
	# ★ 信号连接：按钮被按下 → 调 _on_next_pressed()
	_next_button.pressed.connect(_on_next_pressed)

func open(npc_name: String, lines: Array[String], options: Array[Dictionary]) -> void:
	_lines = lines if not lines.is_empty() else ["……"]
	_options = options
	_index = 0
	_npc_name = npc_name
	_showing_reply = false
	_name_label.text = npc_name
	_refresh_rel()            # 第十一课：打开就显示当前关系
	_show_current()
	visible = true

func advance() -> void:
	# 玩家按 E 时也叫这个（和点按钮同一招）
	_on_next_pressed()

func _on_next_pressed() -> void:
	if _choices.visible:
		return  # 第七课：有选项在等选择时，E 先无效，得先点一个
	if _showing_reply:
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
	_apply_effect(opt.get("effect", {}))   # 第十一课：选完先改关系
	_refresh_rel()                          # 关系变了，刷新那行字
	_set_height(PANEL_H)
	_hide_choices()
	_text_label.text = str(opt.get("reply", "……"))
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true

# ---- 第十一课：关系系统 ----

# 应用选项的效果：{"trust": 1, "suspect": -1} → 关系上下浮动，锁在 0~2
func _apply_effect(effect: Dictionary) -> void:
	if not GameState.relations.has(_npc_name):
		return
	var rel: Dictionary = GameState.relations[_npc_name]
	for dim in effect:
		if rel.has(dim):
			rel[dim] = clampi(int(rel[dim]) + int(effect[dim]), 0, 2)

# 这个选项要不要出现？没写 need 就一直出现；写了就要关系达标
func _passes_need(opt: Dictionary) -> bool:
	var need: Dictionary = opt.get("need", {})
	if need.is_empty():
		return true
	var rel: Dictionary = GameState.relations.get(_npc_name, {})
	for dim in need:
		if int(rel.get(dim, 0)) < int(need[dim]):
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
	visible = false
	closed.emit()
