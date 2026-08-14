extends Node
## 动画状态机测试：真实驱动 player.gd 的 AnimatedSprite2D
## 验证：idle → （按方向键）→ run_start → （播完）→ run → （松键）→ idle
## 只读存档、不写存档；不连 server。

var _failed: int = 0

func _ready() -> void:
	print("[ANIM] start")
	var scene: PackedScene = load("res://scenes/main.tscn")
	var main := scene.instantiate()
	add_child(main)
	await get_tree().process_frame
	await get_tree().process_frame
	# 开场黑幕 intro 会 get_tree().paused = true 冻结全世界，
	# headless 测试没人按 E 读完它，先手动撤掉（_finish 会 unpause + 自毁）
	var intro := main.get_node_or_null("Intro")
	if intro != null and intro.has_method("_finish"):
		intro.call("_finish")
	get_tree().paused = false   # 双保险：intro 叫别的名字也把树救活
	await get_tree().process_frame
	var player: CharacterBody2D = main.get_node("Player")
	var anim: AnimatedSprite2D = player.get("_anim")
	if anim == null:
		_check("动画精灵存在（帧已就位，不应走静态兜底）", false)
		get_tree().quit()
		return
	_check("初始播 idle", anim.animation == "idle")
	var frames: SpriteFrames = anim.sprite_frames
	_check("idle 有 10 帧", frames.get_frame_count("idle") == 10)
	_check("run_start 有 2 帧", frames.has_animation("run_start") and frames.get_frame_count("run_start") == 2)
	_check("run 有 18 帧", frames.get_frame_count("run") == 18)
	_check("run_start 不循环", not frames.get_animation_loop("run_start"))
	# 模拟按右：应切到启动段（动画切换发生在物理帧，等 physics_frame 而非 process_frame）
	Input.action_press("move_right")
	await _settle()
	_check("按右 → run_start", anim.animation == "run_start")
	_check("朝右不翻转", anim.flip_h == false)
	# 启动段 2 帧 @10fps = 0.2s，播完应自动接 run 循环
	await get_tree().create_timer(0.35).timeout
	_check("启动播完 → 接 run 循环", anim.animation == "run")
	# 模拟按左：镜像翻转，动画不重启
	Input.action_press("move_left")
	Input.action_release("move_right")
	await _settle()
	_check("按左 → 镜像翻转", anim.flip_h == true)
	_check("翻转后仍是 run", anim.animation == "run")
	# 松键 → 回 idle
	Input.action_release("move_left")
	await _settle()
	_check("松键 → 回 idle", anim.animation == "idle")
	# 再按右：从 idle 重新走启动段（验证状态机可重复）
	Input.action_press("move_right")
	await _settle()
	_check("再按右 → 再进 run_start", anim.animation == "run_start")
	Input.action_release("move_right")
	print("[ANIM] DONE failed=%d" % _failed)
	get_tree().quit()

## 留 0.05s（约 3 个物理帧）让 _physics_process 跑完，再回来断言
func _settle() -> void:
	await get_tree().create_timer(0.05).timeout

func _check(name: String, ok: bool) -> void:
	if ok:
		print("[ANIM] PASS  ", name)
	else:
		_failed += 1
		print("[ANIM] FAIL  ", name)
