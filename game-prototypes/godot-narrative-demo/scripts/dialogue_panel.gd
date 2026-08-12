extends PanelContainer
## 对话面板 —— 第三课：信号（signal）
##
## 信号 = 节点"喊一声"，谁连了谁响应。
## 本脚本最核心的一行在 _ready() 里：
##   _next_button.pressed.connect(_on_next_pressed)
##   意思是："继续"按钮被按下这个信号 → 连到 _on_next_pressed() 方法

signal closed   # 对话结束信号（以后别的系统可以听这个）

@onready var _name_label: Label = $VBox/NameLabel
@onready var _text_label: Label = $VBox/TextLabel
@onready var _next_button: Button = $VBox/Next

var _lines: Array[String] = []
var _index := 0

func _ready() -> void:
	# ★ 信号连接：按钮被按下 → 调 _on_next_pressed()
	# （等价于在编辑器里：选中 Next → Node 页签 → 双击 pressed → 连到本脚本）
	_next_button.pressed.connect(_on_next_pressed)

func open(npc_name: String, lines: Array[String]) -> void:
	_lines = lines if not lines.is_empty() else ["……"]
	_index = 0
	_name_label.text = npc_name
	_show_current()
	visible = true

func advance() -> void:
	# 玩家按 E 时也叫这个（和点按钮同一招）
	_on_next_pressed()

func _on_next_pressed() -> void:
	_index += 1
	if _index < _lines.size():
		_show_current()
	else:
		close()

func _show_current() -> void:
	_text_label.text = _lines[_index]

func close() -> void:
	visible = false
	closed.emit()
