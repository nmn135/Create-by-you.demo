extends CharacterBody2D
## 玩家 —— 第七天里的外乡人（占位像素小人）
##
## 这节课新增（结合"场景树"一起看）：
##   1. @onready：等树准备好了再取节点引用（get_node 相对路径）
##   2. _process：每帧刷新提示文字
##   3. _unhandled_input：处理"没人接手的"输入事件（E 键）
##   4. 组（group）：get_nodes_in_group("npcs") 找到所有 NPC

const SPEED := 70.0  # 像素/秒 —— 和 Canvas 版 demo 的 AV=70 保持一致

# ../ 表示"父节点"（Main），所以这是 Main/UI/Prompt —— 屏幕底部那个提示
@onready var _prompt: Label = get_node("../UI/Prompt")
# 对话面板（第三课）：Main/UI/DialoguePanel
@onready var _dialogue: PanelContainer = get_node("../UI/DialoguePanel")

func _physics_process(_delta: float) -> void:
	# 输入：←/→ 用 Godot 内置动作，A/D 直接查物理键
	var dir := 0.0
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A):
		dir -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D):
		dir += 1.0
	velocity.x = dir * SPEED
	move_and_slide()

func _process(_delta: float) -> void:
	_update_prompt()

func _unhandled_input(event: InputEvent) -> void:
	# E 键：物理键直查（输入映射以后再讲）
	if event is InputEventKey and event.pressed and not event.echo \
			and event.physical_keycode == KEY_E:
		if _dialogue.visible:
			_dialogue.advance()  # 对话开着 → E 当"下一句"
			return
		var npc := _nearest_npc()
		if npc and _prompt.visible:
			_dialogue.open(npc.npc_name, npc.lines)

func _update_prompt() -> void:
	# 离最近的 NPC 足够近 → 亮出"E 交谈"，并显示对方名字
	var npc := _nearest_npc()
	if npc and abs(npc.position.x - position.x) < 20.0:
		_prompt.text = "E 交谈 · " + npc.npc_name
		_prompt.visible = true
	else:
		_prompt.visible = false

func _nearest_npc() -> Node2D:
	# 遍历 "npcs" 组里的所有节点，找横向距离最近的
	var best: Node2D = null
	var best_d := INF
	for n in get_tree().get_nodes_in_group("npcs"):
		var d: float = abs(n.position.x - position.x)
		if d < best_d:
			best_d = d
			best = n
	return best

func _draw() -> void:
	# 占位像素小人：蓝衣 + 头 + 腰带 + 脚（和 Canvas 版同一套配色）
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), Color("#3b6ea5"))  # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚
