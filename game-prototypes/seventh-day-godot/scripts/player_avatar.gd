extends TextureRect
## HUD 主角小头像（第十九课补丁）
## 读取 assets/portraits/主角.png：生成了就显示，没生成先隐身，不影响界面。

const PORTRAIT_PATH := "res://assets/portraits/主角.png"

func _ready() -> void:
	if ResourceLoader.exists(PORTRAIT_PATH):
		texture = load(PORTRAIT_PATH)
		visible = true
	else:
		visible = false
