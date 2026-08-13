extends Node
## 全局单例（Autoload）—— 所有脚本共享的"世界档案袋"
##
## 任何脚本都能直接写 GameState.xxx 读写，不用传参、不用找节点。
## 注册方式：项目设置 → Autoload → GameState = res://scripts/game_state.gd

# 每个 NPC 的 4 维关系：0=低 1=中 2=高（第十一课）
var relations := {
	"当铺老板": { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"说书人":   { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"神官":     { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"市长":     { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
}

# ---- 世界状态 ----
var day := 1          # 第几天（第十六课起会切到第二天）
var bell_rings := 0   # 钟楼响过几次（数到十三是大事）
var flags := {}       # 剧情旗标：名字 → true
var marks := 0        # 刻痕数 0→1→2→3（第十五~十七课）
var ending := ""      # 结局："留白" / "破局" / "接笔"（空 = 还没结束）
var saved := false    # 第十八课：有没有存档落盘（HUD 用来显示"已存档"）
var reputation := 0   # 还原P7：名声 0~10，帮城里的忙会涨，够高才能解锁某些话

# ---- 还原LLM F3：话会传播 ----
const HEAR_RADIUS := 48.0    # 旁听半径：说话人附近多近的人能"听见"新事实（与 player._eavesdrop 一致）
const GOSSIP_RADIUS := 40.0  # 闲话半径：两个 NPC 多近算"同处一室"、开始传闲话
const GOSSIP_DAY1 := 1.8     # 第一天：共处多久才传一句闲话
const GOSSIP_DAY2 := 1.0     # 第二天：流言传得更快（对应网页版 tickGossip）
var _co_loc := {}            # "A|B" → 累计共处秒数
var _gossip_notified := false # 第一次传开时弹提示

# ---- 还原LLM：自由对话/记忆（F1 占位数据结构，F3 填实）----
var dialogue_history: Array = []          # 最近对话：[{role: "user"|"npc", text}]（发给 LLM 用）
var facts: Array = []                     # 全城记忆：[{text, known_by: [npc名]}]
var npc_heard: Dictionary = {}            # npc名 → [听过的话]
var secrets_known: Array = []             # 玩家已知秘密 id
var npc_secrets_known: Dictionary = {}    # npc名 → [秘密 id]

# 屏幕小提示：Notice 标签在 _ready 时注册上来；还没注册时 notify 是空操作
var notice: Label = null

func has_flag(flag_name: String) -> bool:
	return flags.get(flag_name, false)

func set_flag(flag_name: String) -> void:
	flags[flag_name] = true

func unset_flag(flag_name: String) -> void:
	flags.erase(flag_name)

func add_mark() -> int:
	marks = clampi(marks + 1, 0, 3)
	return marks

func next_day() -> void:
	day += 1

func notify(msg: String) -> void:
	if notice and is_instance_valid(notice):
		notice.show_msg(msg)

# 记一句对话进历史（发给 LLM 用），只留最近 20 句
func log_dialogue(role: String, text: String) -> void:
	dialogue_history.append({ "role": role, "text": text })
	if dialogue_history.size() > 20:
		dialogue_history = dialogue_history.slice(-20)

# ---- 还原LLM：应用 server.js 返回的自由对话结果 ----
# res = {reply, facts[], repDelta, deltas{id:{dim:±1}}, node, secret}
# speaker_cn = 当前对话的 NPC 中文名（新事实讲给谁听）
func apply_llm_result(res: Dictionary, speaker_cn: String) -> void:
	var deltas: Dictionary = res.get("deltas", {})
	for id in deltas:
		var cn := LLMMapper.id_to_cn(str(id))
		if not relations.has(cn):
			continue
		var d: Dictionary = deltas[id]
		for dim in d:
			if relations[cn].has(dim):
				relations[cn][dim] = clampi(int(relations[cn][dim]) + int(d[dim]), 0, 2)
	var rep_delta := int(res.get("repDelta", 0))
	if rep_delta != 0:
		reputation = clampi(reputation + rep_delta, 0, 10)
	var fa: Array = res.get("facts", [])
	if not fa.is_empty():
		remember_facts(fa, speaker_cn)
	var sec := str(res.get("secret", ""))
	if not sec.is_empty():
		learn_secret(sec, speaker_cn)   # 谁告诉你的，谁也知道
	var node := str(res.get("node", ""))
	if not node.is_empty():
		apply_llm_node(node)

# LLM 给的"节点" → 剧情推进（接在现有脚本化触点上）
func apply_llm_node(node: String) -> void:
	if node == "scratch1" and marks == 0:
		bell_rings = maxi(bell_rings, 13)
		add_mark()
		notify("第一道刻痕，浮现在城墙上了。")
		_auto_save()
	elif node == "scratch2":
		set_flag("gossip_spread")
		check_progress()
	elif node == "scratch3":
		set_flag("听懂最后一笔")
		check_progress()
	elif node == "walk_clock":
		notify("市长示意你跟上——往钟楼去。")
	elif node == "author_confessed":
		set_flag("author_confessed")
		notify("你听见了作者的坦白——这座城，是假的。")   # 还原LLM F4：解锁隐藏世界线"坦白之后"

# 新事实入记忆：说话人 + 旁听者都会"听过"它（还原LLM F3：隔墙有耳，听进 memory）
func remember_facts(facts_arr: Array, speaker_cn: String) -> void:
	var listeners: Array = [speaker_cn]
	var speaker_pos := Vector2.INF
	for n in get_tree().get_nodes_in_group("npcs"):
		if n is Node2D and str(n.get("npc_name")) == speaker_cn:
			speaker_pos = n.position
	for n in get_tree().get_nodes_in_group("npcs"):
		if n is Node2D and str(n.get("npc_name")) != speaker_cn:
			if (n.position - speaker_pos).length() <= HEAR_RADIUS:
				listeners.append(str(n.get("npc_name")))
	for ft in facts_arr:
		var s := str(ft).strip_edges()
		if s.is_empty():
			continue
		facts.append({ "text": s, "known_by": listeners.duplicate() })
		for who in listeners:
			var heard: Array = npc_heard.get(who, [])
			if not heard.has(s):
				heard.append(s)
				npc_heard[who] = heard
	if facts.size() > 30:
		facts = facts.slice(-30)

# ---- 还原LLM F3：闲话传播（移植网页版 tickGossip/doGossip/spreadFact）----
func _process(delta: float) -> void:
	_tick_gossip(delta)

func _tick_gossip(delta: float) -> void:
	var npcs := get_tree().get_nodes_in_group("npcs")
	if npcs.size() < 2:
		return
	var threshold: float = GOSSIP_DAY2 if day >= 2 else GOSSIP_DAY1
	for i in npcs.size():
		for j in range(i + 1, npcs.size()):
			var a: Variant = npcs[i]
			var b: Variant = npcs[j]
			if not (a is Node2D) or not (b is Node2D):
				continue
			var key := _pair_key(str(a.get("npc_name")), str(b.get("npc_name")))
			if (a.position - b.position).length() <= GOSSIP_RADIUS:
				_co_loc[key] = _co_loc.get(key, 0.0) + delta
				if _co_loc[key] >= threshold:
					_co_loc[key] = 0.0
					_spread_gossip(str(a.get("npc_name")), str(b.get("npc_name")))
			elif _co_loc.has(key):
				_co_loc[key] = 0.0

func _pair_key(a: String, b: String) -> String:
	if a < b:
		return a + "|" + b
	return b + "|" + a

# 一人知道、一人不知道 → 传过去（每轮只传一条，像闲话一句句说）
func _spread_gossip(a_cn: String, b_cn: String) -> void:
	for f in facts:
		var kb: Array = f.get("known_by", [])
		if kb.has(a_cn) and not kb.has(b_cn):
			_spread_fact(f, b_cn)
			return
		if kb.has(b_cn) and not kb.has(a_cn):
			_spread_fact(f, a_cn)
			return

func _spread_fact(f: Dictionary, npc_cn: String) -> void:
	var kb: Array = f.get("known_by", [])
	if not kb.has(npc_cn):
		kb.append(npc_cn)
	f["known_by"] = kb
	var heard: Array = npc_heard.get(npc_cn, [])
	if not heard.has(str(f.get("text", ""))):
		heard.append(str(f.get("text", "")))
		npc_heard[npc_cn] = heard
	if not _gossip_notified:
		_gossip_notified = true
		notify("闲话在城里传开了。")

# 玩家得知一个秘密（server 用 id：mayor/pawn/bard）。speaker_cn = 谁告诉你的（他也知道）
func learn_secret(secret_id: String, speaker_cn: String = "") -> void:
	if not secrets_known.has(secret_id):
		secrets_known.append(secret_id)
	if not speaker_cn.is_empty():
		var list: Array = npc_secrets_known.get(speaker_cn, [])
		if not list.has(secret_id):
			list.append(secret_id)
			npc_secrets_known[speaker_cn] = list

# 剧情进度检查：每次选项效果结算后调用（dialogue_panel._apply_effect 里接）
#   刻痕1 已现 + 传过一次闲话 → 刻痕2 上墙，天亮切到第二天
#   刻痕2 已现 + 听懂说书人那句"最后一笔" → 刻痕3 浮现
func check_progress() -> void:
	if marks == 1 and has_flag("gossip_spread"):
		add_mark()
		next_day()
		notify("闲话上了墙。天，亮了——第二天。")
		_auto_save()
	if marks == 2 and has_flag("听懂最后一笔"):
		add_mark()
		notify("第三道刻痕浮现：末一笔，等你来写。")
		_auto_save()

# 第十八课：剧情推进到关键节点，顺手把世界状态落盘
func _auto_save() -> void:
	SaveManager.save_game()
