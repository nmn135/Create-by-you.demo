extends CharacterBody2D
## NPC —— 站点巡游（对应 Canvas 版 npcs[] 的站点系统）
##
## 第六课（感应区 Area2D）新招：
##   1. 每个 NPC 挂一个透明感应圈（Area2D + CircleShape2D）
##   2. 玩家走进来 → body_entered 信号 → player_near = true
##      玩家走出去 → body_exited 信号 → player_near = false
##   3. 玩家不再"算距离"，直接问：谁感应到我了？（player_near）

@export var npc_name := "说书人"                     # 显示名
@export var body_color := Color("#5A4A7A")           # 衣服颜色
@export var stations: Array[Vector2] = [             # 站点列表（巡逻路线）
	Vector2(90, 150),
	Vector2(150, 150),
	Vector2(230, 150),
]
@export var speed := 32.0   # 像素/秒
@export var dwell := 2.5    # 到站后停留秒数
@export var lines: Array[String] = ["……"]   # 台词（第三课：对话面板）
@export var options: Array[Dictionary] = []   # 第七课：分支选项 [{label, reply}]

var _target_index := 0
var _waiting := 0.0
var player_near := false   # 第六课：玩家在感应圈里吗？（Area2D 信号在更新它）

func _ready() -> void:
	# 把自己登记进 "npcs" 组，方便玩家/其他系统找到我
	add_to_group("npcs")
	# 出生点 = 第一个站点（否则会从 (0,0) 天花板出生再飞下来）
	position = stations[0]
	# 第六课：把感应区的"有人进来/出去"两个信号，连到下面的方法
	$Area2D.body_entered.connect(_on_area_body_entered)
	$Area2D.body_exited.connect(_on_area_body_exited)

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
	# 像素小人：换个 body_color 就是另一个人
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), body_color)        # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚
