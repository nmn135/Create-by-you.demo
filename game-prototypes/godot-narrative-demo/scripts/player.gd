extends CharacterBody2D
## 玩家 —— 第七天里的外乡人（占位像素小人）
##
## 这是一个"脚本挂在节点上"的例子：
##   1. 这个脚本挂在 Main 场景里的 Player 节点上（看 scenes/main.tscn）
##   2. Player 是 CharacterBody2D：Godot 的"会移动的物理体"
##   3. 脚本用 _physics_process() 每帧改 velocity，再 move_and_slide()
##   4. 像素小人是用 _draw() 画的（先画个占位，之后换像素图）

const SPEED := 70.0  # 像素/秒 —— 和 Canvas 版 demo 的 AV=70 保持一致

func _physics_process(_delta: float) -> void:
	# 输入：←/→ 用 Godot 内置动作，A/D 直接查物理键
	var dir := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A):
		dir -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D):
		dir += 1.0
	velocity.x = dir * SPEED
	move_and_slide()

func _draw() -> void:
	# 占位像素小人：蓝衣 + 头 + 腰带 + 脚（和 Canvas 版同一套配色）
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), Color("#3b6ea5"))  # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚
