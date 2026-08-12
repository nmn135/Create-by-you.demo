extends PanelContainer
## 对话面板 —— 第三课：信号；第七课：分支选项
##
## 第七课新招：
##   1. Array[Dictionary] —— 每个选项是一个字典 { label: 按钮文字, reply: 选了之后的话 }
##   2. 动态生成按钮：循环里 Button.new() + add_child()，用完再清掉
##   3. 面板高度跟着内容走：出选项时拉高，平时收回去

signal closed   # 对话结束信号（以后别的系统可以听这个）

@onready var _name_label: Label = $VBox/NameLabel
@onready var _text_label: Label = $VBox/TextLabel
@onready var _choices: VBoxContainer = $VBox/Choices
@onready var _next_button: Button = $VBox/Next

const PANEL_H := 90.0          # 普通对话的面板高度
const PANEL_H_CHOICES := 138.0 # 出选项时的高度（要放下按钮们）

var _lines: Array[String] = []
var _options: Array[Dictionary] = []
var _index := 0
var _showing_reply := false   # 第七课：正在显示某个选项的回复

func _ready() -> void:
	# ★ 信号连接：按钮被按下 → 调 _on_next_pressed()
	_next_button.pressed.connect(_on_next_pressed)

func open(npc_name: String, lines: Array[String], options: Array[Dictionary]) -> void:
	_lines = lines if not lines.is_empty() else ["……"]
	_options = options
	_index = 0
	_showing_reply = false
	_name_label.text = npc_name
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
	for opt in _options:
		var btn := Button.new()
		btn.text = str(opt.get("label", "……"))
		btn.pressed.connect(_on_choice_pressed.bind(opt))
		_choices.add_child(btn)
	_choices.visible = true

func _on_choice_pressed(opt: Dictionary) -> void:
	_set_height(PANEL_H)
	_hide_choices()
	_text_label.text = str(opt.get("reply", "……"))
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true

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
