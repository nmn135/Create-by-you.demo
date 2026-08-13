extends Node2D
## 钟 —— 第九课：Timer + Tween，让钟自己响
##
## 新招：
##   1. Timer：到点自动触发 timeout 信号（这里定时响铃）
##   2. Tween：让属性平滑"动起来"（这里让钟左右摆动）
##   3. await：挂起等一会儿（这里让提示文字自己消失）
## 第十二课：每响一声，写进 GameState 世界状态（bell_rings 计数），提示文字跟着报数

@onready var _timer: Timer = $Timer
@onready var _note: Label = get_node("../UI/BellNote")   # 屏幕中央的提示文字

func _ready() -> void:
	# Timer：每次超时(timeout)就响一次
	_timer.timeout.connect(_ring)
	# 第一次响之前等多久（随机 6~10 秒）
	_timer.wait_time = randf_range(6.0, 10.0)
	_timer.start()

func _ring() -> void:
	Sound.play_bell()   # 第十九课：程序化合成的钟声
	# 第十二课：先把"这次响声"记进世界状态（NPC 对话能读到、HUD 能显示）
	GameState.bell_rings += 1
	# 提示文字跟着报数：第一声是问号，第十三声先打个招呼（真正的戏在第十五课）
	var n := GameState.bell_rings
	if n == 1:
		_note.text = "铛——钟楼自己响了？"
	elif n == 13:
		_note.text = "铛——第十三下了。"
	else:
		_note.text = "铛——第 %d 声了。" % n
	# 第十五课：响满十三下，第一道刻痕浮现（只触发一次）
	if n == 13 and GameState.marks == 0:
		GameState.add_mark()
		GameState.notify("第一道刻痕，浮现在城墙上了。")
		SaveManager.save_game()   # 第十八课：刻痕1 浮现，落盘
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
