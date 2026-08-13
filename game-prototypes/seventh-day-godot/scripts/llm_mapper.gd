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
const ID_TO_CN := {
	"mayor": "市长",
	"pawn": "当铺老板",
	"bard": "说书人",
	"priest": "神官",
}

static func npc_id(cn: String) -> String:
	return CN_TO_ID.get(cn, "mayor")

static func id_to_cn(id: String) -> String:
	return ID_TO_CN.get(id, id)

# 还原LLM F5：元话题关键词 —— 谈作者/真假/系统（刻痕1后命中才切 meta 频道）
const META_KEYWORDS := [
	"系统", "代码", "程序", "底层", "世界规则", "重写", "编译", "bug",
	"你在骗", "你在演", "我是玩家", "剧本", "重置", "作者是谁",
	"是你做的", "这一切是假", "谁是作者", "这城是假的",
]

# 这句算不算"元话题"？（触发游戏本体打破第四面墙）
static func is_meta(text: String) -> bool:
	var t := text.to_lower()
	for w in META_KEYWORDS:
		if t.contains(w):
			return true
	return false

# 组装 /api/talk 的请求体。npc_cn = 当前对话的 NPC 中文名，text = 玩家说的话
# meta_mode = true 时切到"游戏本体"（npc=meta），对应网页版 PERSONAS.meta
static func build_talk_body(npc_cn: String, text: String, meta_mode: bool = false) -> Dictionary:
	var id := npc_id(npc_cn)
	var relations := {}
	for cn in GameState.relations:
		relations[npc_id(str(cn))] = GameState.relations[cn]
	var sk := {}
	for cn in GameState.npc_secrets_known:
		sk[npc_id(str(cn))] = GameState.npc_secrets_known[cn]
	var body := {
		"npc": "meta" if meta_mode else id,
		"text": text,
		"history": GameState.dialogue_history.slice(-10),
		"metaMode": meta_mode,
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
# 还原LLM F3：对齐网页版语义——"你的记忆" = facts 里他知道的；"你听说" = heard 里听过的
static func _known_facts(npc_cn: String) -> Array:
	var out: Array = []
	for f in GameState.facts:
		if out.size() >= 5:
			break
		if f.get("known_by", []).has(npc_cn):
			var s := str(f.get("text", "")).strip_edges()
			if s.is_empty():
				continue
			if s.length() > 40:
				s = s.left(40) + "…"
			out.append(s)
	return out
