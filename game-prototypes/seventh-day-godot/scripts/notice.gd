extends Label
## 屏幕小提示 —— 任何脚本调 GameState.notify("...") 就在屏幕下方闪一行字
##
## 不用在场景里手搓 Timer 节点：用代码 new 一个 Timer 管"显示 2.2 秒后消失"。
## 每个想弹提示的地方（偷听、刻痕浮现、天亮……）都走 GameState.notify。

var _timer: Timer

func _ready() -> void:
	GameState.notice = self   # 把自己注册给 GameState（GameState.notify 就靠这个引用）
	_timer = Timer.new()
	_timer.one_shot = true
	_timer.timeout.connect(func() -> void: visible = false)
	add_child(_timer)
	visible = false

func show_msg(msg: String) -> void:
	text = msg
	visible = true
	_timer.start(2.2)
