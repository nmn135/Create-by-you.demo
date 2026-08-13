extends Label
## 第十二课：世界状态 HUD —— 每帧把 GameState 的世界状态报给玩家看
## 挂在 UI 角落的一行小字：第几天、钟响了几声。
## 第十八课：有存档时追加"· 已存档"。
## 以后想加更多世界状态（比如"现在是深夜"），在这里拼进 text 就行。

func _process(_delta: float) -> void:
	text = "第 %d 天 · 钟响 %d 声" % [GameState.day, GameState.bell_rings]
	if GameState.saved:
		text += " · 已存档"
