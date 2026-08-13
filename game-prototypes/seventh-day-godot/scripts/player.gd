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

func _ready() -> void:
	# 第六课：加入 "player" 组，NPC 的感应区靠它认出"这是玩家"
	add_to_group("player")
	# 第十二课（接画）：把 _draw() 画的占位色块，换成你自己画的 player.png
	# 16×16 图居中贴在角色身上，脚底刚好压到碰撞盒底部（和 NPC 站同一条地平线）
	var sprite := Sprite2D.new()
	sprite.texture = load("res://assets/player.png")
	add_child(sprite)

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

const HEAR_RADIUS := 48.0   # 偷听半径：说话者附近 48px 内的人都能听到

# 跟某人说话时，附近的其他 NPC 会偷听：
#   1. 被偷听的 NPC 记下"听过一耳朵"（他对话里会多出相应选项）
#   2. 偷听让 NPC 对玩家更警觉（怀疑度 +1，锁在 0~2）
#   3. 只要有任何人偷听，屏幕弹一句提示
func _eavesdrop(speaker: Node2D) -> void:
	var heard_any := false
	for n in get_tree().get_nodes_in_group("npcs"):
		if n == speaker:
			continue
		if (n.position - speaker.position).length() <= HEAR_RADIUS:
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
