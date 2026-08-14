extends CharacterBody2D
## 玩家 —— 第七天里的外乡人（占位像素小人）
##
## 第六课（感应区 Area2D）：
##   不再用"横向距离<20"的土办法判断能不能说话，
##   改成问 NPC："你的感应圈里有人吗？"（player_near）
##   NPC 的 Area2D 用 body_entered/body_exited 信号自己算好了。
##   坑：感应圈放大后可能同时罩住两个 NPC → 感应圈管"行不行"，
##       距离只管"排顺序"（见 _nearby_npc）。

const SPEED := 70.0  # 像素/秒 —— 和 Canvas 版 demo 的 AV=70 保持一致

# ../ 表示"父节点"（Main），所以这是 Main/UI/Prompt —— 屏幕底部那个提示
@onready var _prompt: Label = get_node("../UI/Prompt")
# 对话面板（第三课）：Main/UI/DialoguePanel
@onready var _dialogue: PanelContainer = get_node("../UI/DialoguePanel")
# 动画精灵：_ready 里按帧文件是否就位，决定播动画还是退回静态兜底
var _anim: AnimatedSprite2D
var _moving := false   # 是否有水平输入（动画状态机切换的依据）

func _ready() -> void:
	# 第六课：加入 "player" 组，NPC 的感应区靠它认出"这是玩家"
	add_to_group("player")
	# 玩家动画（AnimatedSprite2D）：待机/跑步帧序列从 assets/player_frames/ 读，
	# 每帧 32×32、脚底贴画布底边。AnimatedSprite2D 和旧 Sprite2D 一样居中，
	# 原点 +16 就是脚底，对齐规则不变。
	_anim = AnimatedSprite2D.new()
	var frames := SpriteFrames.new()
	# Godot 新建 SpriteFrames 自带一个空的 "default" 动画（编辑器占位用），
	# 先摘掉，否则下面 is_empty() 判断永远为假
	if frames.has_animation("default") and frames.get_frame_count("default") == 0:
		frames.remove_animation("default")
	# 帧表布局（assets/player_frames/）：idle 0-9 循环；
	# run 0-1 是启动两帧（只播一次），run 2-19 是跑步循环
	_add_anim(frames, "idle", "idle", 8.0, true, 0, 10)
	_add_anim(frames, "run_start", "run", 10.0, false, 0, 2)
	_add_anim(frames, "run", "run", 10.0, true, 2, 18)
	if frames.get_animation_names().is_empty():
		# 兜底：动画帧还没放进 assets/player_frames/ 时，退回单张静态图，游戏照常能玩
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/player.png")
		add_child(sprite)
		return
	_anim.sprite_frames = frames
	# 启动段播完自动接上跑步循环，见 _on_anim_finished
	_anim.animation_finished.connect(_on_anim_finished)
	_anim.play("idle" if frames.has_animation("idle") else frames.get_animation_names()[0])
	add_child(_anim)

## 注册一段动画：读 assets/player_frames/<前缀>_<i>.png，i 从 from_idx 起最多 count 帧；
## 文件缺失即停（缺帧不崩，最多动画短一点）。loop=false 用于"只播一次"的启动段
func _add_anim(frames: SpriteFrames, anim_name: String, file_prefix: String, speed: float,
		loop: bool = true, from_idx: int = 0, count: int = 32) -> void:
	for i in range(from_idx, from_idx + count):
		var path := "res://assets/player_frames/%s_%d.png" % [file_prefix, i]
		if not ResourceLoader.exists(path):
			break
		if not frames.has_animation(anim_name):
			frames.add_animation(anim_name)
			frames.set_animation_loop(anim_name, loop)
			frames.set_animation_speed(anim_name, speed)
		frames.add_frame(anim_name, load(path))

## 启动段（run_start）只播一次：播完时如果玩家还在跑，接上跑步循环
func _on_anim_finished() -> void:
	if _anim != null and _anim.animation == "run_start" and _moving \
			and _anim.sprite_frames.has_animation("run"):
		_anim.play("run")

func _physics_process(_delta: float) -> void:
	# 第四课：输入映射。代码不再管具体键，只问"这个动作被按了吗"
	# A/← 绑在 move_left，D/→ 绑在 move_right（Project → 项目设置 → 输入映射里改）
	var dir := 0.0
	if Input.is_action_pressed("move_left"):
		dir -= 1.0
	if Input.is_action_pressed("move_right"):
		dir += 1.0
	velocity.x = dir * SPEED
	move_and_slide()
	# 动画切换：有水平输入 → 播启动段（播完自动接跑步循环）并朝移动方向翻转；停下 → 待机
	_moving = dir != 0.0
	if _anim != null:
		if _moving:
			_anim.flip_h = dir < 0.0
			if _anim.animation != "run" and _anim.animation != "run_start":
				_anim.play("run_start" if _anim.sprite_frames.has_animation("run_start") else "run")
		elif _anim.animation != "idle" and _anim.sprite_frames.has_animation("idle"):
			_anim.play("idle")

func _process(_delta: float) -> void:
	_update_prompt()

func _unhandled_input(event: InputEvent) -> void:
	# 第四课：interact 动作（默认绑 E；以后在输入映射里改成别的键即可）
	if event.is_action_pressed("interact"):
		if _dialogue.visible:
			_dialogue.advance()  # 对话开着 → interact 当"下一句"
			return
		var npc := _nearby_npc()
		if npc:
			_eavesdrop(npc)  # 第十三课：说话前先广播"附近有谁在听"
			_dialogue.open(npc.npc_name, npc.lines, npc.options)

func _update_prompt() -> void:
	# 第六课：有人感应到我 → 亮出"E 交谈"，并显示对方名字
	var npc := _nearby_npc()
	if npc:
		_prompt.text = "E 交谈 · " + npc.npc_name
		_prompt.visible = true
	else:
		_prompt.visible = false

# ---- 第十三课：隔墙有耳 ----

# 偷听半径：说话者附近 48px 内的人都能听到（还原LLM F3：与 GameState.HEAR_RADIUS 同源）
func _eavesdrop(speaker: Node2D) -> void:
	var heard_any := false
	for n in get_tree().get_nodes_in_group("npcs"):
		if n == speaker:
			continue
		if (n.position - speaker.position).length() <= GameState.HEAR_RADIUS:
			GameState.set_flag("heard_" + n.npc_name)
			var rel: Dictionary = GameState.relations.get(n.npc_name, {})
			if rel.has("suspect"):
				rel["suspect"] = clampi(int(rel["suspect"]) + 1, 0, 2)
			heard_any = true
	if heard_any:
		GameState.notify("有人竖起了耳朵。")

# 第六课：感应圈负责"行不行"——先筛出感应到玩家的 NPC；
# 距离只负责"排顺序"——同时有好几个在圈里时，选最近的那个。
func _nearby_npc() -> Node2D:
	var best: Node2D = null
	var best_d := INF
	for n in get_tree().get_nodes_in_group("npcs"):
		if n.player_near:
			var d: float = (n.position - position).length()
			if d < best_d:
				best_d = d
				best = n
	return best

# （原 _draw() 占位色块已删 —— 第十二课换成 player.png 精灵图了）
