extends CanvasLayer
## 还原P2：开场背景故事 + 引导移动
## 启动时盖全屏黑幕，逐句读开场白，按 E 推进；末句提示操作，读完撤幕恢复游戏。
## 文案在 dialogues.json 的 "_intro" 段，改台词不用碰代码。

const INTRO_PATH := "res://dialogues.json"

var _lines: Array[String] = []
var _index := 0

@onready var _text: Label = $Text
@onready var _hint: Label = $Hint

func _ready() -> void:
	_load_intro()
	if _lines.is_empty():
		hide()
		return
	get_tree().paused = true   # 读开场白时整个世界暂停
	_show_current()

func _process(_delta: float) -> void:
	# 提示字呼吸闪烁，让玩家一眼看到"按 E"
	_hint.modulate.a = 0.7 + 0.3 * sin(Time.get_ticks_msec() * 0.006)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		advance()

func advance() -> void:
	_index += 1
	if _index < _lines.size():
		_show_current()
	else:
		_finish()

func _show_current() -> void:
	_text.text = _lines[_index]
	_hint.text = "按 E 开始" if _index == _lines.size() - 1 else "按 E 继续"

func _finish() -> void:
	get_tree().paused = false
	hide()
	queue_free()

func _load_intro() -> void:
	var file := FileAccess.open(INTRO_PATH, FileAccess.READ)
	if file == null:
		return
	var data: Variant = JSON.parse_string(file.get_as_text())
	if data is Dictionary and data.has("_intro"):
		for item in data["_intro"]:
			_lines.append(str(item))
