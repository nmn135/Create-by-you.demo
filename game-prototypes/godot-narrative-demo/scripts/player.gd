extends CharacterBody2D
## 玩家 —— 第七天里的外乡人（占位像素小人）
##
## 第六课（感应区 Area2D）：
##   不再用"横向距离<20"的土办法判断能不能说话，
##   改成问 NPC："你的感应圈里有人吗？"（player_near）
##   NPC 的 Area2D 用 body_entered/body_exited 信号自己算好了。

const SPEED := 70.0  # 像素/秒 —— 和 Canvas 版 demo 的 AV=70 保持一致

# ../ 表示"父节点"（Main），所以这是 Main/UI/Prompt —— 屏幕底部那个提示
@onready var _prompt: Label = get_node("../UI/Prompt")
# 对话面板（第三课）：Main/UI/DialoguePanel
@onready var _dialogue: PanelContainer = get_node("../UI/DialoguePanel")

func _ready() -> void:
	# 第六课：加入 "player" 组，NPC 的感应区靠它认出"这是玩家"
	add_to_group("player")

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
			_dialogue.open(npc.npc_name, npc.lines)

func _update_prompt() -> void:
	# 第六课：有人感应到我 → 亮出"E 交谈"，并显示对方名字
	var npc := _nearby_npc()
	if npc:
		_prompt.text = "E 交谈 · " + npc.npc_name
		_prompt.visible = true
	else:
		_prompt.visible = false

# 第六课：遍历所有 NPC，找"感应圈里有玩家"的那个。
# 距离到底近不近，是 NPC 的 Area2D 用信号帮你算好的，这里不用再量。
func _nearby_npc() -> Node2D:
	for n in get_tree().get_nodes_in_group("npcs"):
		if n.player_near:
			return n
	return null

func _draw() -> void:
	# 占位像素小人：蓝衣 + 头 + 腰带 + 脚（和 Canvas 版同一套配色）
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), Color("#3b6ea5"))  # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚
