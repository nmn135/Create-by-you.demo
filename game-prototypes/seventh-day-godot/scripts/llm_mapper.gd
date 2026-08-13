class_name LLMMapper
## LLMMapper —— 把 GameState 世界状态翻译成 server.js 认识的请求体（还原LLM F1）
## server.js 用英文角色 id（mayor/pawn/bard/priest），Godot 用中文名，这里做映射。
## 记忆字段（heard / npcKnownFacts / secretsKnownBy / playerSecretsKnown）
## F1 先读占位数据（空数组），F3 填实记忆后再升级。

const CN_TO_ID := {
	"市长": "mayor",
	"当铺老板": "pawn",
	"说书人": "bard",
	"神官": "priest",
}

static func npc_id(cn: String) -> String:
	return CN_TO_ID.get(cn, "mayor")

# 组装 /api/talk 的请求体。npc_cn = 当前对话的 NPC 中文名，text = 玩家说的话
static func build_talk_body(npc_cn: String, text: String) -> Dictionary:
	var id := npc_id(npc_cn)
	var relations := {}
	for cn in GameState.relations:
		relations[npc_id(str(cn))] = GameState.relations[cn]
	var sk := {}
	for cn in GameState.npc_secrets_known:
		sk[npc_id(str(cn))] = GameState.npc_secrets_known[cn]
	var body := {
		"npc": id,
		"text": text,
		"history": GameState.dialogue_history.slice(-10),
		"metaMode": false,
		"worldState": _world_state(),
		"relations": relations,
		"heard": GameState.npc_heard.get(npc_cn, []),
		"secretsKnownBy": sk,
		"reputation": GameState.reputation,
		"npcKnownFacts": _known_facts(npc_cn),
		"playerSecretsKnown": GameState.secrets_known,
	}
	return body

# 组装 /api/endgame 的请求体。final_line = 玩家对作者说的最后一句话，ending = 世界线名
static func build_endgame_body(final_line: String, ending: String) -> Dictionary:
	return {
		"finalLine": final_line.left(120),
		"ending": ending,
		"authorConfessed": GameState.has_flag("author_confessed"),
		"worldState": _world_state(),
		"reputation": GameState.reputation,
	}

# 把 GameState 里的刻痕/旗标/天数翻译成 server.js 认识的世界状态
static func _world_state() -> Dictionary:
	var ws := {}
	ws["dayCycle"] = GameState.day
	ws["bellStruck"] = GameState.bell_rings >= 13 or GameState.marks >= 1
	ws["gossipLevel"] = GameState.has_flag("gossip_spread")
	ws["scene"] = "day2" if GameState.day >= 2 else "day1"
	ws["fragments"] = GameState.has_flag("fragments")
	ws["inkDone"] = GameState.marks >= 3
	ws["doorVisible"] = GameState.has_flag("door_visible")
	return ws

# 当前 NPC 记得的事实（≤5 条、每条 ≤40 字，控 token）
static func _known_facts(npc_cn: String) -> Array:
	var heard: Array = GameState.npc_heard.get(npc_cn, [])
	var out: Array = []
	for f in heard:
		if out.size() >= 5:
			break
		var s := str(f)
		if s.length() > 40:
			s = s.left(40) + "…"
		out.append(s)
	return out
