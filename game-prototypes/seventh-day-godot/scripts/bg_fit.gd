extends Sprite2D
## 背景自适应：不管 bg.png 画多大（320×180 / 640×360 / 1024×576…），
## 都会自动缩放成"正好覆盖整个世界"（世界是 320×180）。
## 换图之后什么都不用改，启动时自动贴合。

const VIEW_W := 320.0   # 世界宽度（世界坐标）
const VIEW_H := 180.0   # 世界高度

func _ready() -> void:
	_fit()

func _fit() -> void:
	if texture:
		scale = Vector2(VIEW_W / texture.get_width(), VIEW_H / texture.get_height())
