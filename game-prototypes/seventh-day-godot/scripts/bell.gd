extends Node2D
## 钟 —— 第九课：Timer + Tween，让钟自己响
##
## 新招：
##   1. Timer：到点自动触发 timeout 信号（这里定时响铃）
##   2. Tween：让属性平滑"动起来"（这里让钟左右摆动）
##   3. await：挂起等一会儿（这里让提示文字自己消失）

@onready var _timer: Timer = $Timer
@onready var _note: Label = get_node("../UI/BellNote")   # 屏幕中央的提示文字

func _ready() -> void:
	# Timer：每次超时(timeout)就响一次
	_timer.timeout.connect(_ring)
	# 第一次响之前等多久（随机 6~10 秒）
	_timer.wait_time = randf_range(6.0, 10.0)
	_timer.start()

func _ring() -> void:
	# Tween：一连串动作，让钟绕着"挂点"摆两下
	# 格式：tween_property(对象, "属性", 目标值, 耗时秒数)
	var tween := create_tween()
	tween.tween_property(self, "rotation", -0.35, 0.05)   # 摆向左边
	tween.tween_property(self, "rotation", 0.35, 0.3)     # 摆向右边
	tween.tween_property(self, "rotation", -0.3, 0.25)    # 再回一点
	tween.tween_property(self, "rotation", 0.0, 0.15)     # 回正
	# 屏幕闪一句提示，2.5 秒后自己消失（await = 在这挂起等一会）
	_note.visible = true
	await get_tree().create_timer(2.5).timeout
	_note.visible = false
	# 安排下一次响（随机 7~12 秒后）
	_timer.wait_time = randf_range(7.0, 12.0)
	_timer.start()
