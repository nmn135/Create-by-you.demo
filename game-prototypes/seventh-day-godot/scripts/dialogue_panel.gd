extends PanelContainer
## 对话面板 —— 第三课：信号；第七课：分支选项；第十一课：关系系统；第十二课：世界状态
##
## 第十一课新招：
##   1. effect —— 选项带"效果"，选了就改变对方 4 维关系（写进 GameState 单例）
##   2. need  —— 选项带"门槛"，关系不够就不出现
##   3. RelLabel —— 面板里实时显示对方四维关系
## 第十二课新招：
##   4. need 里还能写世界状态门槛：{"bell_rings": 2} 钟响过 2 次、{"flag": "名字"} 已点亮旗标
##   5. effect里还能写 {"set_flag": "名字"} —— 选这句，就在 GameState 里留下全城记忆
## 第十三~十七课新招：
##   6. 对话面板左侧显示 NPC 立绘（assets/portraits/<名字>.png，没有就留空）
##   7. 结局流程：选项带 "ending": true 时，改成从 "_ending" 数据里出结局三选一
## 还原P4新招：
##   8. 话题快捷栏（骑砍式节点分支）：台词说完后，所有"过门槛"的选项变成常驻话题按钮。
##      点一个看回复，话题栏不收起——可以接着问别的；点"告辞"（或按 E）才结束对话。

signal closed   # 对话结束信号（以后别的系统可以听这个）

@onready var _name_label: Label = $HBox/VBox/NameLabel
@onready var _rel_label: Label = $HBox/VBox/RelLabel     # 第十一课：四维关系一行字
@onready var _text_scroll: ScrollContainer = $HBox/VBox/Scroll  # 长回复可滚动，告辞按钮不被挤出
@onready var _text_label: Label = $HBox/VBox/Scroll/TextLabel
@onready var _choices: Container = $HBox/VBox/Choices   # 还原LLM F2：改 FlowContainer 放横向话题按钮
@onready var _next_button: Button = $HBox/VBox/Next
# 第十七课：立绘。场景里还没加 HBox/Portrait 节点时会是 null，代码里都做了空判断
@onready var _portrait: TextureRect = get_node_or_null("HBox/Portrait")
# 还原LLM F2：自由对话输入框（场景里没有就不显示，不影响老版本）
@onready var _input: LineEdit = get_node_or_null("HBox/VBox/Input")

const PANEL_H := 248.0         # 普通对话的面板高度（TextLabel 上方留白多一点）
const PANEL_H_CHOICES := 380.0 # 出选项时的高度（要放下按钮们）
const PANEL_H_ENDING := 460.0  # 还原LLM F5：终局四层剧场的高度（要放下整段作者坦白）
const PORTRAIT_DIR := "res://assets/portraits/"

# 第十一课：维度的顺序、中文名、数值翻译
const DIM_ORDER := ["trust", "fear", "like", "suspect"]
const DIM_LABELS := { "trust": "信任", "fear": "恐惧", "like": "好感", "suspect": "怀疑" }
const TIER_WORD := ["低", "中", "高"]

var _lines: Array[String] = []
var _options: Array[Dictionary] = []
var _index := 0
var _npc_name := ""           # 第十一课：现在跟谁说话（改关系要用）
var _showing_reply := false   # 第七课：正在显示某个选项的回复
var _ending: Dictionary = {}  # 第十七课：结局标题（从 dialogues.json 的 "_ending" 读）
var _ending_mode := false     # 还原LLM F4：正在等玩家写下最后一句话
# 还原LLM G3：打字机效果（逐字显示，按 E 跳过；gen 代次让新消息立刻作废旧打字）
const TYPE_CPS := 40.0
var _typing := false
var _type_gen := 0

func _ready() -> void:
	# ★ 信号连接：按钮被按下 → 调 _on_next_pressed()
	_next_button.pressed.connect(_on_next_pressed)
	if _input:
		_input.text_submitted.connect(_on_input_submitted)   # 还原LLM F2：回车发送自由对话
	_load_ending()             # 第十七课：结局数据
	_choices.add_theme_font_size_override("font_size", 32)  # 640×360 升级：话题按钮字号×2（默认16→32）

func open(npc_name: String, lines: Array[String], options: Array[Dictionary]) -> void:
	_lines = lines if not lines.is_empty() else ["……"]
	_options = options
	_index = 0
	_npc_name = npc_name
	_showing_reply = false
	_typing = false          # 还原LLM G3：开新对话，作废旧打字、显示全文
	_type_gen += 1
	_text_label.visible_characters = -1
	_name_label.text = npc_name
	_refresh_rel()            # 第十一课：打开就显示当前关系
	_update_portrait(npc_name) # 第十七课：换上这位 NPC 的立绘
	_show_current()
	visible = true
	_camera_zoom(true)         # 还原P3：开对话镜头推近
	if _input:
		_input.clear()         # 还原LLM F2：每次开对话清空输入框
		_input.editable = true

func advance() -> void:
	# 玩家按 E 时也叫这个（和点按钮同一招）
	_on_next_pressed()

func _on_next_pressed() -> void:
	Sound.play_tick()   # 第十九课：程序化合成的翻页声
	if _typing:
		# 还原LLM G3：打字机还在逐字显示，按 E = 跳过，直接显示全文
		_type_gen += 1
		_typing = false
		_text_label.visible_characters = -1
		return
	if _showing_reply:
		# 第十七课：结局看完…… 还原LLM G2：不强制退出游戏。
		# 结局已定，但这座城你还可以再走走（和网页版一致）。
		if not GameState.ending.is_empty():
			close()
			GameState.notify("结局已达成 · %s。城，还在。" % GameState.ending)
			return
		close()
		return
	if _choices.visible:
		return  # 还原P4：话题栏在等选择，E 先无效，得先点一个话题
	_index += 1
	if _index < _lines.size():
		_show_current()
	elif not _options.is_empty():
		_show_topics()   # 主台词说完了 → 出常驻话题快捷栏
	else:
		close()

func _show_current() -> void:
	_set_height(PANEL_H)
	_text_label.text = _lines[_index]
	_next_button.text = "继续 [E]"
	_next_button.visible = true
	_hide_choices()

func _show_topics() -> void:
	_set_height(PANEL_H_CHOICES)
	_next_button.visible = false
	_hide_choices()
	_build_topics()
	# 如果一个话题都没有，也别卡死——直接当"说完了"
	if _choices.get_child_count() == 0:
		close()
		return
	_choices.visible = true

# 还原P4：把"过得去门槛"的选项建成话题按钮（常驻，等玩家点"告辞"才收）
func _build_topics() -> void:
	# 第七课：循环里给每个选项 new 一个按钮，连到同一个处理函数
	# bind(opt) 把"这是哪个选项"也一起传给回调
	# 第十一课：只有"过门槛"的选项才会出现（_passes_need）
	for opt in _options:
		if not _passes_need(opt):
			continue   # 关系不够，这个话题不出现
		var btn := Button.new()
		btn.text = str(opt.get("label", "……"))
		btn.pressed.connect(_on_topic_pressed.bind(opt))
		_choices.add_child(btn)

func _on_topic_pressed(opt: Dictionary) -> void:
	# 第十七课：这是"听懂这座城"的入口 → 不显示普通回复，直接进结局（还原LLM F4：自由写下最后一笔）
	if opt.get("ending", false):
		_begin_ending()
		return
	# 还原P4：点"告辞"就结束对话，回到探索
	if str(opt.get("label", "")) == "告辞":
		close()
		return
	# 还原LLM F2：话题 = 预设一句话，发给 LLM（在线走自由对话；离线兜底脚本回复）
	_send_text(str(opt.get("label", "……")), opt)

# 还原LLM F2：玩家在输入框回车 → 自由对话（还原LLM F4：结局模式 → 写下最后一笔）
func _on_input_submitted(text: String) -> void:
	var t := text.strip_edges()
	if t.is_empty():
		return
	_input.clear()
	if _ending_mode:
		_submit_ending(t)
		return
	_send_text(t, {})

# 还原LLM F2：把一句话发给 LLM，等回复并应用世界效果（关系/名声/记忆/剧情节点）
func _send_text(text: String, fallback_opt: Dictionary) -> void:
	GameState.log_dialogue("user", text, _npc_name)
	# 还原LLM F5：默认显示当前 NPC；刻痕1后谈作者/真假 → 切元频道，说话人变成"？？？"
	_name_label.text = _npc_name
	var meta_mode := GameState.marks >= 1 and LLMMapper.is_meta(text)
	if meta_mode:
		_name_label.text = "？？？"
	_text_label.text = "（%s正在斟酌…）" % ("？？？" if meta_mode else _npc_name)
	_set_busy(true)
	var body := LLMMapper.build_talk_body(_npc_name, text, meta_mode)
	var res: Dictionary = await TalkClient.talk(body)
	_set_busy(false)
	if res.get("offline", false) or not res.has("reply"):
		_offline_reply(text, fallback_opt)
		return
	var reply := str(res.get("reply", "……"))
	GameState.apply_llm_result(res, _npc_name)
	GameState.log_dialogue("npc", reply, _npc_name)
	_refresh_rel()
	_set_height(PANEL_H_CHOICES)
	_hide_choices()
	_build_topics()
	_choices.visible = true
	_show_text_typed(reply)
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true

# 还原LLM F2：连不上 LLM 时——话题走脚本化回复+效果；自由输入走罐头回复
func _offline_reply(text: String, fallback_opt: Dictionary) -> void:
	if not fallback_opt.is_empty():
		_apply_scripted_topic(fallback_opt)
		return
	var reply := OfflineReply.fallback_reply(_npc_name, text)
	GameState.log_dialogue("npc", reply, _npc_name)
	_set_height(PANEL_H_CHOICES)
	_hide_choices()
	_build_topics()
	_choices.visible = true
	_show_text_typed(reply)
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true

# 脚本化话题（P4 原行为）：应用 JSON 效果 + 显示脚本回复
func _apply_scripted_topic(opt: Dictionary) -> void:
	_apply_effect(opt.get("effect", {}))
	_refresh_rel()
	_set_height(PANEL_H_CHOICES)
	_hide_choices()
	_build_topics()
	_choices.visible = true
	var reply := str(opt.get("reply", "……"))
	_show_text_typed(reply)
	_next_button.text = "告辞 [E]"
	_next_button.visible = true
	_showing_reply = true
	GameState.log_dialogue("npc", reply, _npc_name)

# 等 LLM 时禁用输入/按钮，防止连点
func _set_busy(b: bool) -> void:
	if _input:
		_input.editable = not b
	for child in _choices.get_children():
		if child is Button:
			child.disabled = b
	_next_button.disabled = b

# ---- 第十一课：关系系统 ----

# 应用选项的效果：
#   {"trust": 1, "suspect": -1} → 关系上下浮动，锁在 0~2（第十一课）
#   {"set_flag": "名字"}        → 点亮世界状态旗标，成为全城的共同记忆（第十二课）
func _apply_effect(effect: Dictionary) -> void:
	if GameState.relations.has(_npc_name):
		var rel: Dictionary = GameState.relations[_npc_name]
		for dim in effect:
			if rel.has(dim):
				rel[dim] = clampi(int(rel[dim]) + int(effect[dim]), 0, 2)
	if effect.has("rep"):
		GameState.reputation = clampi(GameState.reputation + int(effect["rep"]), 0, 10)  # 还原P7：名声
	if effect.has("set_flag"):
		GameState.set_flag(str(effect["set_flag"]))
	GameState.check_progress()   # 第十三课：选完这句话，看看剧情该不该推进（刻痕/天亮）

# 这个选项要不要出现？没写 need 就一直出现；写了就要"过门槛"
# 门槛有两类：
#   关系（第十一课）：     {"trust": 2}              → 对方信任 >= 2
#   世界状态（第十二~十七课）：
#     {"bell_rings": 2}  → 钟楼响过 >= 2 次
#     {"day": 2}         → 已经是第 2 天
#     {"marks": 2}       → 已经有 2 道刻痕
#     {"flag": "名字"}    → 已点亮旗标"名字"
#     {"no_flag": "名字"}  → 还没点亮旗标"名字"
func _passes_need(opt: Dictionary) -> bool:
	var need: Dictionary = opt.get("need", {})
	if need.is_empty():
		return true
	# —— 关系门槛（第十一课）
	var rel: Dictionary = GameState.relations.get(_npc_name, {})
	for dim in ["trust", "fear", "like", "suspect"]:
		if need.has(dim) and int(rel.get(dim, 0)) < int(need[dim]):
			return false
	# —— 世界状态门槛（第十二~十七课）
	if need.has("bell_rings") and GameState.bell_rings < int(need["bell_rings"]):
		return false
	if need.has("day") and GameState.day < int(need["day"]):
		return false
	if need.has("marks") and GameState.marks < int(need["marks"]):
		return false
	if need.has("flag") and not GameState.has_flag(str(need["flag"])):
		return false
	if need.has("no_flag") and GameState.has_flag(str(need["no_flag"])):
		return false
	if need.has("rep") and GameState.reputation < int(need["rep"]):   # 还原P7：名声门槛
		return false
	return true

# 刷新面板上那行四维关系字：信任中 · 恐惧低 · 好感高 · 怀疑低
func _refresh_rel() -> void:
	var rel: Dictionary = GameState.relations.get(_npc_name, {})
	var parts: Array[String] = []
	for dim in DIM_ORDER:
		var v := int(rel.get(dim, 1))
		parts.append("%s%s" % [DIM_LABELS[dim], TIER_WORD[clampi(v, 0, 2)]])
	_rel_label.text = " · ".join(PackedStringArray(parts))

func _hide_choices() -> void:
	_choices.visible = false
	# 旧的选项按钮要清掉：先移出树，再让它自己销毁（下帧）
	for child in _choices.get_children():
		_choices.remove_child(child)
		child.queue_free()

func _set_height(h: float) -> void:
	# 面板是"锚点居中 + 上下 offset"，用 offset 撑出高度
	var half := h * 0.5
	offset_top = -half
	offset_bottom = half

func close() -> void:
	_camera_zoom(false)         # 还原P3：关对话镜头拉回
	_set_height(PANEL_H)
	_hide_choices()
	if _portrait:
		_portrait.visible = false
	visible = false
	closed.emit()

# 还原P3：让镜头推近/拉回（相机在 "camera" 组里，没找到就跳过）
func _camera_zoom(push: bool) -> void:
	var cam := get_tree().get_first_node_in_group("camera")
	if cam:
		cam.call("push_in" if push else "pull_out")

# ---- 第十七课：立绘 + 结局 ----

# 换立绘：assets/portraits/<名字>.png 存在就显示，没有就先留空（以后放进图片即可）
func _update_portrait(npc_name: String) -> void:
	if _portrait == null:
		return
	var path := PORTRAIT_DIR + npc_name + ".png"
	if ResourceLoader.exists(path):
		_portrait.texture = load(path)
		_portrait.visible = true
	else:
		_portrait.texture = null
		_portrait.visible = false

# 从 dialogues.json 的 "_ending" 键读结局三选一
func _load_ending() -> void:
	var file := FileAccess.open("res://dialogues.json", FileAccess.READ)
	if file == null:
		return
	var data: Variant = JSON.parse_string(file.get_as_text())
	if data is Dictionary and data.has("_ending"):
		_ending = data["_ending"]

# 结局入口（还原LLM F4/F5）：走到作者面前 → 四层剧场（含作者坦白）→ 让玩家写下最后一句话
func _begin_ending() -> void:
	if not GameState.ending.is_empty():
		# 还原LLM G2：结局已定，不能重写。告诉玩家可以继续在城里走走。
		_set_height(PANEL_H)
		_hide_choices()
		_show_text_typed("—— 结局已定：%s。循环不会重来，但这座城，你还可以再走走。——" % GameState.ending)
		_next_button.text = "继续 [E]"
		_next_button.visible = true
		_showing_reply = true
		return
	_ending_mode = true
	GameState.set_flag("author_confessed")   # 还原LLM F5：作者已坦白，解锁隐藏世界线"坦白之后"
	_set_height(PANEL_H_ENDING)
	_next_button.visible = false
	_hide_choices()
	_show_text_typed("……三道刻痕，皆已归位。你终于走到我面前了。\n\n" \
		+ "层一 · 感官：你以为你在听钟、看城墙——其实你面前只有一块屏幕，和一行等你输入的代码。\n" \
		+ "层二 · 叙事：你一路说过的话，这座城一个字都没忘。\n" \
		+ "层三 · 世界：你找的那扇门，就是这里。城没有出口，因为写它的人，从没给过它门。\n" \
		+ "层四 · 诚实：……我改不了任何底层代码。这一千次循环，我都在配合你演。假的。但这句话，是真的。\n" \
		+ "（说最后一句话，决定这座城的命运）")
	if _input:
		_input.clear()
		_input.editable = true
		_input.grab_focus()

# 玩家的最后一句话 → 世界线分类 → LLM 现写 epilogue（离线用本地兜底）
func _submit_ending(final_line: String) -> void:
	_ending_mode = false
	GameState.log_dialogue("user", final_line)
	var ending := Endgame.classify_ending(final_line, GameState.has_flag("author_confessed"))
	GameState.ending = ending
	_text_label.text = "（城在倾听你的最后一笔…）"
	_set_busy(true)
	var body := LLMMapper.build_endgame_body(final_line, ending)
	var res: Dictionary = await TalkClient.endgame(body)
	_set_busy(false)
	var epilogue := Endgame.default_epilogue(ending)
	if not res.get("offline", false) and str(res.get("epilogue", "")).strip_edges() != "":
		epilogue = str(res["epilogue"]).strip_edges()
	if _input:
		_input.editable = false   # 故事写完，不再接收输入
	_set_height(PANEL_H)
	_hide_choices()
	_show_text_typed(epilogue + "\n\n—— 世界线 · " + ending + " ——")
	_next_button.text = "—— 故事完 —— [E]"
	_next_button.visible = true
	_showing_reply = true
	SaveManager.save_game()   # 第十八课：结局定下了，落盘

# ---- 还原LLM G3：打字机 ----

# 注：TextLabel 的 custom_minimum_size.x=460 在场景里固定写好，
# 换行宽度固定，不会像"custom_min=滚动区宽度"那样跟 ScrollContainer 形成
# 最小宽度反馈环（滚动条 8px 会让它每帧 +8 无限膨胀到面板被顶出屏幕）。

# 逐字显示一段文字（非阻塞：设置文本后立刻返回，后台继续打）。
# 按 E 跳过、或开新消息（gen 代次变了）都会立刻作废旧打字。
func _show_text_typed(text: String) -> void:
	_type_gen += 1
	var gen := _type_gen
	_typing = true
	_text_label.text = text
	_text_label.visible_characters = 0
	_typewrite_async(text.length(), gen)

func _typewrite_async(total: int, gen: int) -> void:
	# 短句按 40 字/秒，长句最长 2.5 秒打完（别让 epilogue 慢慢磨）
	var delay := minf(1.0 / TYPE_CPS, 2.5 / float(max(total, 1)))
	var shown := 0
	while shown < total and gen == _type_gen:
		shown += 1
		_text_label.visible_characters = shown
		_text_scroll.scroll_vertical = int(_text_scroll.get_v_scroll_bar().max_value)  # 长回复打字时跟着滚到底
		await get_tree().create_timer(delay).timeout
	if gen == _type_gen:
		_typing = false
		_text_label.visible_characters = -1
