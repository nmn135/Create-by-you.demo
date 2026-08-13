extends Label
## 刻痕墙 —— 跟着 GameState.marks 走，刻痕浮现就在城墙上显字
##
## 第十五~十七课：三道刻痕依次出现，每道一行字。每帧看一眼 marks 是几道，
## 显示对应的话；没有刻痕就整个隐藏。

const MARK_TEXTS := [
	"",                                  # 0：还没有刻痕
	"作者之墨，始于一声钟响。",            # 刻痕1（第十五课）
	"话会传，也会上墙。",                  # 刻痕2（第十六课）
	"末一笔，等你来写。",                  # 刻痕3（第十七课）
]

func _process(_delta: float) -> void:
	var m := clampi(GameState.marks, 0, MARK_TEXTS.size() - 1)
	text = MARK_TEXTS[m]
	visible = m > 0
