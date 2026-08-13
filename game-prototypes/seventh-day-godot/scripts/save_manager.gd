extends Node
## 第十八课：存档系统 —— 把 GameState 的世界状态存进 user://save.json
##
## 新招：
##   1. FileAccess —— Godot 的文件读写：WRITE 写盘、READ 读回
##   2. JSON.stringify / JSON.parse_string —— 世界状态 → 文字存盘 → 再变回来
##   3. user:// —— 给"这个玩家"专属的目录（游戏数据放这里，不要放 res://）
##
## 自动存档的时机（都接在剧情推进的关键节点上）：
##   · 钟响第十三下，刻痕1 浮现
##   · 闲话上墙、天亮切到第二天（刻痕2）
##   · 说书人点破"最后一笔"（刻痕3）
##   · 玩家选出结局
## 启动时如果有存档，自动读回，屏幕提示"已读档"。

const SAVE_PATH := "user://save.json"

func _ready() -> void:
	# 启动读档：有存档就恢复世界状态（提示要等主场景就绪后再弹）
	if FileAccess.file_exists(SAVE_PATH):
		if load_game():
			call_deferred("_notify_loaded")

func _notify_loaded() -> void:
	GameState.notify("已读档：第七天，继续。")

# 把世界状态写盘。返回是否成功。
func save_game() -> bool:
	var data := {
		"relations": GameState.relations,
		"day": GameState.day,
		"bell_rings": GameState.bell_rings,
		"flags": GameState.flags,
		"marks": GameState.marks,
		"ending": GameState.ending,
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(data, "\t"))
	GameState.saved = true
	return true

# 读档并写回 GameState。返回是否成功。
func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return false
	var data: Variant = JSON.parse_string(file.get_as_text())
	if not (data is Dictionary):
		return false
	# 关系：以默认表为底，把存档值叠上去——存档里缺的 NPC/维度就用默认值
	var saved_rels: Variant = data.get("relations", {})
	if saved_rels is Dictionary:
		for npc in GameState.relations:
			var saved_npc: Variant = saved_rels.get(npc, {})
			if saved_npc is Dictionary:
				for dim in saved_npc:
					GameState.relations[npc][dim] = clampi(int(saved_npc[dim]), 0, 2)
	GameState.day = int(data.get("day", 1))
	GameState.bell_rings = int(data.get("bell_rings", 0))
	GameState.flags = data.get("flags", {})
	GameState.marks = clampi(int(data.get("marks", 0)), 0, 3)
	GameState.ending = str(data.get("ending", ""))
	GameState.saved = true
	return true
