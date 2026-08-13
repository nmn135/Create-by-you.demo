extends CharacterBody2D
## NPC —— 站点巡游（对应 Canvas 版 npcs[] 的站点系统）
##
## 第八课（台词搬进 JSON）：
##   lines / options 不再写在场景里，而是启动时从 dialogues.json 读。
##   以后加台词：记事本改 dialogues.json，不用碰 Inspector。

const DIALOGUES_PATH := "res://dialogues.json"   # 第八课：所有台词都在这
const SPRITES_DIR := "res://assets/npcs/"        # 还原P1：自己的像素立绘放这（<名字>.png）

const GROUND_Y := 132.0
@export var npc_name := "说书人"                     # 显示名（也是 JSON 里的钥匙）
@export var body_color := Color("#5A4A7A")           # 衣服颜色
@export var stations: Array[Vector2] = [             # 站点列表（巡逻路线）
	Vector2(90, GROUND_Y),
	Vector2(150, GROUND_Y),
	Vector2(230, GROUND_Y),
]
@export var speed := 32.0   # 像素/秒
@export var dwell := 2.5    # 到站后停留秒数

# 第八课：不再是 @export —— 启动时从 JSON 读进来
var lines: Array[String] = ["……"]        # 台词
var options: Array[Dictionary] = []      # 分支选项 [{label, reply}]

var _target_index := 0
var _waiting := 0.0
var player_near := false   # 第六课：玩家在感应圈里吗？（Area2D 信号在更新它）
var _sprite_loaded := false   # 还原P1：有像素立绘时不再画色块身体

# ---- 还原P1.5（气泡闲话）：头顶冒话 ----
const BUBBLE_MAX_LEN := 18     # 气泡最多显示 18 个字，超了截断加"…"
var _bubble: PanelContainer
var _bubble_label: Label
var _bubble_tween: Tween

func _ready() -> void:
	# 把自己登记进 "npcs" 组，方便玩家/其他系统找到我
	add_to_group("npcs")
	# 出生点 = 第一个站点（否则会从 (0,0) 天花板出生再飞下来）
	position = stations[0]
	# 第八课：读自己的台词（放在信号连接之前，谁先谁后无所谓）
	_load_dialogue()
	# 第六课：把感应区的"有人进来/出去"两个信号，连到下面的方法
	$Area2D.body_entered.connect(_on_area_body_entered)
	$Area2D.body_exited.connect(_on_area_body_exited)
	# 还原P1：有像素立绘就贴图（和玩家一样居中，脚底压到碰撞盒底）
	_try_load_sprite()
	_build_bubble()   # 还原P1.5：头顶气泡（闲话/旁听时冒话）

# 还原P1：assets/npcs/<名字>.png 存在 → 换成像素立绘；没有 → 继续用色块身体
func _try_load_sprite() -> void:
	var path := SPRITES_DIR + npc_name + ".png"
	if ResourceLoader.exists(path):
		var sprite := Sprite2D.new()
		sprite.texture = load(path)
		add_child(sprite)
		_sprite_loaded = true
		queue_redraw()

# 第八课：从 JSON 文件读自己的台词
func _load_dialogue() -> void:
	var file := FileAccess.open(DIALOGUES_PATH, FileAccess.READ)
	if file == null:
		push_error("找不到台词文件：" + DIALOGUES_PATH)
		return
	var data: Variant = JSON.parse_string(file.get_as_text())
	if not data is Dictionary:
		push_error("台词文件格式不对：" + DIALOGUES_PATH)
		return
	if data.has(npc_name):
		var entry: Dictionary = data[npc_name]
		lines = _to_string_array(entry.get("lines", []))
		options = _to_dict_array(entry.get("options", []))

# JSON 读出来的是"万能类型" Variant，转成我们用的定型数组
func _to_string_array(v: Variant) -> Array[String]:
	var out: Array[String] = []
	for item in v:
		out.append(str(item))
	return out

func _to_dict_array(v: Variant) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for item in v:
		out.append(item)
	return out

func _on_area_body_entered(body: Node2D) -> void:
	# 感应圈只对"玩家"这层开着（Area2D 的 mask=1），
	# 进来的本该就是玩家；再用组确认一遍，养成好习惯
	if body.is_in_group("player"):
		player_near = true

func _on_area_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		player_near = false

func _physics_process(delta: float) -> void:
	# 注意：物理体（CharacterBody2D）的移动要在 _physics_process 里做，
	# 因为 move_and_slide() 依赖固定 60 次/秒的物理帧
	if _waiting > 0.0:
		_waiting -= delta
		velocity = Vector2.ZERO  # 停留时别还留着旧速度
		return

	var target: Vector2 = stations[_target_index]
	target.y = GROUND_Y   # 站点只管左右，站多高由常量说了算
	var to_target := target - position

	# 到站了 → 换下一个站点，开始停留
	if to_target.length() < 0.5:
		_target_index = (_target_index + 1) % stations.size()
		_waiting = dwell
		velocity = Vector2.ZERO
		return

	# 朝目标匀速走：velocity = 方向 × 速度；move_and_slide() 负责"撞到就停"
	velocity = to_target.normalized() * speed
	move_and_slide()

func _draw() -> void:
	if _sprite_loaded:
		return  # 还原P1：有像素立绘就不用画色块身体了
	# 像素小人：换个 body_color 就是另一个人
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), body_color)        # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚

# ---- 还原P1.5（气泡闲话）：头顶冒话 ----

# 冒一个说话气泡，几秒后淡出。GameState 在"传闲话/隔墙有耳"时调用。
func show_bubble(text: String, duration: float = 2.5) -> void:
	if _bubble == null or text.strip_edges().is_empty():
		return
	if text.length() > BUBBLE_MAX_LEN:
		text = text.substr(0, BUBBLE_MAX_LEN) + "…"
	_bubble_label.text = text
	_bubble.modulate.a = 1.0
	_bubble.visible = true
	_bubble.reset_size()   # 让 PanelContainer 按文字重新算宽高
	# 顶部居中：气泡左上角 = (负一半宽, 头顶上方)
	_bubble.position = Vector2(-_bubble.size.x * 0.5, -_bubble.size.y - 40.0)
	if _bubble_tween and _bubble_tween.is_valid():
		_bubble_tween.kill()
	_bubble_tween = create_tween()
	_bubble_tween.tween_interval(duration)
	_bubble_tween.tween_property(_bubble, "modulate:a", 0.0, 0.3)
	_bubble_tween.tween_callback(func() -> void:
		_bubble.visible = false
		_bubble.modulate.a = 1.0)

func _build_bubble() -> void:
	_bubble = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.06, 0.09, 0.92)
	sb.set_corner_radius_all(4)
	sb.set_content_margin_all(4)
	sb.border_color = Color(0.75, 0.7, 0.55, 0.6)
	sb.set_border_width_all(1)
	_bubble.add_theme_stylebox_override("panel", sb)
	_bubble_label = Label.new()
	_bubble_label.add_theme_font_size_override("font_size", 8)
	_bubble_label.add_theme_color_override("font_color", Color(0.95, 0.93, 0.85, 1))
	_bubble.add_child(_bubble_label)
	add_child(_bubble)
	_bubble.visible = false
	_bubble.z_index = 5   # 压在立绘上面
