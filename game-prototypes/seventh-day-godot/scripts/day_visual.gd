extends ColorRect
## 还原P5：第二天场景变化 —— 天亮
## 世界状态切到第二天时，天色从黑夜转成黎明（背景 + 城景一起变亮）。

const NIGHT := Color(0.07, 0.08, 0.12, 1.0)
const DAWN := Color(0.30, 0.28, 0.38, 1.0)   # 偏暖的黎明色

var _changed := false

func _process(_delta: float) -> void:
	if _changed or GameState.day < 2:
		return
	_changed = true
	var city := get_node_or_null("../City") as Node2D
	if city:
		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property(self, "color", DAWN, 2.0)
		tw.tween_property(city, "modulate", Color(1.25, 1.22, 1.15, 1.0), 2.0)
	GameState.notify("天亮了。这座城，翻到了第二天。")
