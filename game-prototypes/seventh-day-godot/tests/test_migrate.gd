extends Node
## 临时测试：GameState.sanitize_loaded_save() 的旧档迁移 + "<null>" 清理
## 运行：godot --headless --path . res://tests/test_migrate.tscn

var _failed: int = 0

func _ready() -> void:
	print("[MIG] start")
	await get_tree().process_frame
	_test_migrate_history()
	_test_null_cleanup()
	_test_migrate_then_build_body()
	print("[MIG] DONE failed=%d" % _failed)
	get_tree().quit()

func _check(name: String, ok: bool) -> void:
	if ok:
		print("[MIG] PASS  ", name)
	else:
		_failed += 1
		print("[MIG] FAIL  ", name)

# 模拟老存档：说书人聊了一阵 → 换成市长问"钟楼为什么静了？"（正是用户真实存档的片段）
func _test_migrate_history() -> void:
	GameState.dialogue_history = [
		{ "role": "user", "text": "你好" },
		{ "role": "npc", "text": "（说书人眯眼，笑里多了一点认真。）你这话，像听得懂的人说的。" },
		{ "role": "user", "text": "你信命吗？" },
		{ "role": "npc", "text": "我讲的故事里，命都改写过。你也试试？" },   # 无舞台提示 → 靠前后文
		{ "role": "user", "text": "讲讲刻痕" },
		{ "role": "npc", "text": "（说书人指尖划过空气，像在描摹一道看不见的痕。）" },
		{ "role": "user", "text": "钟楼为什么静了？" },
		{ "role": "npc", "text": "（市长指尖在虚空中停顿，像按住一根无形的弦。）" },
	]
	GameState.sanitize_loaded_save()
	var h: Array = GameState.dialogue_history
	_check("说书人台词1（有提示）标对", str(h[1].get("npc", "")) == "说书人")
	_check("说书人台词2（无提示）跟着标对", str(h[3].get("npc", "")) == "说书人")
	_check("玩家台词1归说书人", str(h[2].get("npc", "")) == "说书人")
	_check("市长台词标对", str(h[7].get("npc", "")) == "市长")
	_check("玩家台词3（钟楼问题）归市长", str(h[6].get("npc", "")) == "市长")
	_check("已标记条目不被覆盖", str(h[0].get("npc", "")) == "说书人")

# "<null>" 清理
func _test_null_cleanup() -> void:
	GameState.npc_secrets_known = { "市长": ["<null>"], "说书人": ["<null>", "一个真秘密"] }
	GameState.secrets_known = ["<null>"]
	GameState.sanitize_loaded_save()
	_check("市长秘密列表清空", GameState.npc_secrets_known["市长"].is_empty())
	_check("说书人只留真秘密", GameState.npc_secrets_known["说书人"] == ["一个真秘密"])
	_check("玩家秘密清空", GameState.secrets_known.is_empty())

# 迁移后 build_talk_body 能拿到正确的分桶历史
func _test_migrate_then_build_body() -> void:
	GameState.dialogue_history = [
		{ "role": "user", "text": "神为什么不回应？" },
		{ "role": "npc", "text": "（神官垂目）因为神也认得那三道刻痕。" },
		{ "role": "user", "text": "钟楼响了几声？" },
		{ "role": "npc", "text": "（市长压低声音）十三下。" },
	]
	GameState.sanitize_loaded_save()
	var mayor_body := LLMMapper.build_talk_body("市长", "再说一遍？", false)
	_check("迁移后市长只拿自己的历史（2条）", mayor_body["history"].size() == 2)
	var priest_body := LLMMapper.build_talk_body("神官", "再说一遍？", false)
	_check("迁移后神官只拿自己的历史（2条）", priest_body["history"].size() == 2)
