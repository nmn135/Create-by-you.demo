extends Node
## 端到端集成测试（临时）：真实 TalkClient → 本地 server.js（127.0.0.1:8890）
## 覆盖：
##   1. 跨 NPC 历史隔离（神官历史不流进市长请求；市长历史保留）
##   2. meta 频道保留全部历史
##   3. 离线兜底（连不上 → offline:true）
##   4. Endgame 世界线分类（续写/合卷/抹去/坦白之后）
##   5. 真实 /api/endgame 调用
## 运行：godot --headless --path . res://tests/test_e2e.tscn
## 要求：本地 server.js 正在 8890 运行；否则第 1/2/5 项会标记 SKIP（不判失败）。

var _failed: int = 0
var _skipped: int = 0

func _ready() -> void:
	print("[E2E] start")
	await _test_history_isolation()
	await _test_meta_history()
	await _test_offline_fallback()
	_test_endgame_classify()
	await _test_endgame_api()
	print("[E2E] DONE failed=%d skipped=%d" % [_failed, _skipped])
	get_tree().quit()

func _check(name: String, ok: bool) -> void:
	if ok:
		print("[E2E] PASS  ", name)
	else:
		_failed += 1
		print("[E2E] FAIL  ", name)

func _skip(name: String) -> void:
	_skipped += 1
	print("[E2E] SKIP  ", name)

# 1. 跨 NPC 历史隔离：神官聊完 → 市长请求不带神官历史；市长自己的历史保留
func _test_history_isolation() -> void:
	GameState.dialogue_history = [
		{ "role": "user", "text": "神为什么不回应？", "npc": "神官" },
		{ "role": "npc", "text": "（神官垂目）因为神也认得那三道刻痕。", "npc": "神官" },
		{ "role": "user", "text": "市长，钟楼昨晚响了几声？", "npc": "市长" },
		{ "role": "npc", "text": "（市长压低声音）十三下。", "npc": "市长" },
	]
	var body := LLMMapper.build_talk_body("市长", "你刚才说了什么？再说一遍。", false)
	_check("市长请求只含市长历史（2条）", body["history"].size() == 2)
	var res: Dictionary = await TalkClient.talk(body)
	if res.get("offline", false):
		_skip("真实 LLM 回复（server 不在线？）")
		return
	var reply := str(res.get("reply", ""))
	_check("市长真实回复非空", reply.strip_edges() != "")
	_check("市长回复不带神官口吻（圣火/神坛/垂目）", not (reply.contains("圣火") or reply.contains("神坛") or reply.contains("垂目")))

# 2. meta 频道：保留全部历史（作者记得每句话）
func _test_meta_history() -> void:
	GameState.dialogue_history = [
		{ "role": "user", "text": "神为什么不回应？", "npc": "神官" },
		{ "role": "npc", "text": "（神官垂目）……", "npc": "神官" },
		{ "role": "user", "text": "市长，钟楼响了几声？", "npc": "市长" },
		{ "role": "npc", "text": "（市长压低声音）十三下。", "npc": "市长" },
	]
	var body := LLMMapper.build_talk_body("市长", "作者是谁？", true)
	_check("meta 请求保留全部历史（4条）", body["history"].size() == 4)
	_check("meta 请求 npc=meta", str(body.get("npc", "")) == "meta")
	var res: Dictionary = await TalkClient.talk(body)
	if res.get("offline", false):
		_skip("meta 真实 LLM 回复（server 不在线？）")
		return
	var reply := str(res.get("reply", ""))
	_check("meta 真实回复非空", reply.strip_edges() != "")

# 3. 离线兜底：指向死端口 → offline:true（TalkClient 内部 20 秒超时，死端口会立即拒绝）
func _test_offline_fallback() -> void:
	var old_url: String = TalkClient.BASE_URL
	TalkClient.BASE_URL = "http://127.0.0.1:1"
	var res: Dictionary = await TalkClient.talk(LLMMapper.build_talk_body("市长", "你好", false))
	TalkClient.BASE_URL = old_url
	_check("连不上时返回 offline:true", res.get("offline", false) == true)

# 4. 世界线分类（纯函数，不碰网络）
func _test_endgame_classify() -> void:
	_check("分类：烧毁→抹去", Endgame.classify_ending("把这城烧了吧", false) == "抹去")
	_check("分类：合上→合卷", Endgame.classify_ending("合上这本书", false) == "合卷")
	_check("分类：默认→续写", Endgame.classify_ending("写下去吧", false) == "续写")
	_check("分类：未坦白时说相信→续写（隐藏结局不触发）", Endgame.classify_ending("我相信你", false) == "续写")
	_check("分类：坦白后说相信→坦白之后", Endgame.classify_ending("我相信你", true) == "坦白之后")
	_check("兜底 epilogue 4 条世界线都有文案", Endgame.default_epilogue("抹去") != "" and Endgame.default_epilogue("合卷") != "" and Endgame.default_epilogue("续写") != "" and Endgame.default_epilogue("坦白之后") != "")

# 5. 真实 /api/endgame
func _test_endgame_api() -> void:
	GameState.set_flag("author_confessed")
	var body := LLMMapper.build_endgame_body("谢谢你，作者。这城虽然是假的，但我想陪你写完。", "坦白之后")
	var res: Dictionary = await TalkClient.endgame(body)
	if res.get("offline", false):
		_skip("真实 epilogue（server 不在线？）")
		return
	_check("endgame 真实 epilogue 非空", str(res.get("epilogue", "")).strip_edges() != "")
