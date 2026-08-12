extends Node2D
## NPC —— 站点巡游（对应 Canvas 版 npcs[] 的站点系统）
##
## 这节课的三招新武功：
##   1. @export：变量直接在编辑器 Inspector 面板里调
##      （选中 main.tscn 里的任一 NPC 节点，看右边面板）
##   2. move_toward()：匀速走向目标点
##   3. 组（group）：_ready() 里 add_to_group("npcs")，
##      玩家就能用 get_nodes_in_group("npcs") 找到所有 NPC

@export var npc_name := "说书人"                     # 显示名
@export var body_color := Color("#5A4A7A")           # 衣服颜色
@export var stations: Array[Vector2] = [             # 站点列表（巡逻路线）
	Vector2(90, 150),
	Vector2(150, 150),
	Vector2(230, 150),
]
@export var speed := 32.0   # 像素/秒
@export var dwell := 2.5    # 到站后停留秒数

var _target_index := 0
var _waiting := 0.0

func _ready() -> void:
	# 把自己登记进 "npcs" 组，方便玩家/其他系统找到我
	add_to_group("npcs")

func _process(delta: float) -> void:
	# 到站了？先停留 _waiting 秒
	if _waiting > 0.0:
		_waiting -= delta
		return
	# 朝当前目标站点匀速走（move_toward：只往目标挪一格，不会超）
	var target: Vector2 = stations[_target_index]
	position.x = move_toward(position.x, target.x, speed * delta)
	# 到站了 → 换下一个站点，开始停留
	if abs(position.x - target.x) < 0.5:
		_target_index = (_target_index + 1) % stations.size()
		_waiting = dwell

func _draw() -> void:
	# 像素小人：换个 body_color 就是另一个人
	draw_rect(Rect2(-4, -8, 8, 4), Color("#e0b088"))    # 头
	draw_rect(Rect2(-5, -4, 10, 10), body_color)        # 身体
	draw_rect(Rect2(-5, 4, 10, 1), Color("#8a5a2b"))    # 腰带
	draw_rect(Rect2(-5, 6, 4, 2), Color("#4a3827"))     # 左脚
	draw_rect(Rect2(1, 6, 4, 2), Color("#4a3827"))      # 右脚
