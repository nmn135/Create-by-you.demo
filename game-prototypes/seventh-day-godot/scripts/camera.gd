extends Camera2D
## 还原P3：对话相机推近
## 平时缩在默认视角（正好看完整张 320×180 图），开对话时 tween 推近，
## 关对话拉回。推近时跟随玩家，保证主角不会被挤出画面。

const VIEW_W := 320.0
const VIEW_H := 180.0
const DEFAULT_ZOOM := Vector2.ONE
const DIALOGUE_ZOOM := Vector2(1.3, 1.3)

func _ready() -> void:
	add_to_group("camera")
	make_current()
	position = Vector2(VIEW_W * 0.5, VIEW_H * 0.5)
	zoom = DEFAULT_ZOOM

func _process(_delta: float) -> void:
	# 跟随玩家，但镜头不能跑出场景边界
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player:
		position = player.position
		var half := Vector2(VIEW_W, VIEW_H) / (2.0 * zoom)
		position.x = clampf(position.x, half.x, VIEW_W - half.x)
		position.y = clampf(position.y, half.y, VIEW_H - half.y)

func push_in() -> void:
	_tween_zoom(DIALOGUE_ZOOM)

func pull_out() -> void:
	_tween_zoom(DEFAULT_ZOOM)

func _tween_zoom(target: Vector2) -> void:
	var tw := create_tween()
	tw.tween_property(self, "zoom", target, 0.15).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
