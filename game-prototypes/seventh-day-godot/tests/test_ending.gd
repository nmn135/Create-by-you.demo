extends Node
## 回归测试：真实驱动 dialogue_panel 的结局入口 _begin_ending()
## 验证：标题显示、层二引用玩家最近 3 句话、author_confessed 落盘、输入框占位符切换
## 注意：_begin_ending 会真的写 save.json —— 本测试开头备份、结尾恢复，不伤玩家进度。

const SAVE_PATH := "user://save.json"
const BACKUP_PATH := "user://save.json.testbak"

var _failed: int = 0
var _panel: PanelContainer
var _had_backup := false

func _ready() -> void:
	print("[END] start")
	_backup_save()
	await get_tree().process_frame
	var scene: PackedScene = load("res://scenes/main.tscn")
	var main := scene.instantiate()
	add_child(main)
	await get_tree().process_frame
	await get_tree().process_frame
	_panel = main.get_node("UI/DialoguePanel")
	if _panel == null:
		# 节点路径可能不同，打印树帮定位
		print("[END] FAIL 找不到 DialoguePanel")
		get_tree().quit()
		return
	# 模拟玩家一路说过的话（不同 NPC 混着，层二只取玩家台词）
	GameState.dialogue_history = [
		{ "role": "user", "text": "神为什么不回应？", "npc": "神官" },
		{ "role": "npc", "text": "（神官垂目）因为神也认得那三道刻痕。", "npc": "神官" },
		{ "role": "user", "text": "我害怕这座城，可我还是想听懂它。", "npc": "神官" },
		{ "role": "user", "text": "钟楼为什么静了？", "npc": "市长" },
		{ "role": "npc", "text": "（市长压低声音）它只数它自己的数。", "npc": "市长" },
	]
	GameState.marks = 3
	var lines: Array[String] = ["市长看着你。"]
	var opts: Array[Dictionary] = []
	_panel.open("市长", lines, opts)
	_panel._begin_ending()
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	_check("ending_mode 已开启", _panel._ending_mode == true)
	_check("author_confessed 旗标点亮", GameState.has_flag("author_confessed"))
	var text_label: Label = _panel.get_node("HBox/VBox/Scroll/TextLabel")
	var full := text_label.text
	_check("剧场含标题「城把最后一笔」", full.contains("城把最后一笔"))
	_check("层二引用了玩家台词", full.contains("你一路说过——「") and full.contains("神为什么不回应？"))
	_check("层二截断长句", full.contains("我害怕这座城，可我还") and full.contains("…"))
	_check("层二不含 NPC 台词", not full.contains("神官垂目"))
	var input_box: LineEdit = _panel.get_node("HBox/VBox/Input")
	_check("输入框占位符切成结局提示", input_box.placeholder_text.contains("最后一句话"))
	# 存档落盘验证
	var save_text := FileAccess.get_file_as_string("user://save.json")
	_check("存档写入成功", not save_text.is_empty())
	_check("存档含 author_confessed 旗标", save_text.contains("author_confessed"))
	# —— 竞态闸门回归：busy / ending_mode 时 E 键必须无效 ——
	_panel.advance()   # 先跳过打字机（这声 E 是合法的）
	var vis_before: bool = _panel.visible
	var txt_before: String = text_label.text
	_panel._busy = true
	_panel.advance()
	_check("busy 时 E 不关面板不改文本", _panel.visible == vis_before and text_label.text == txt_before)
	_panel._busy = false
	_panel.advance()   # ending_mode 还开着：E 也不能把剧场顶成话题栏
	_check("ending_mode 时 E 不推进剧场", text_label.text == txt_before)
	_panel.close()
	_check("close() 后 ending_mode 复位", _panel._ending_mode == false)
	_panel._ending_mode = true
	_panel.open("市长", lines, opts)
	_check("open() 后 ending_mode 复位", _panel._ending_mode == false)
	_restore_save()
	print("[END] DONE failed=%d" % _failed)
	get_tree().quit()

func _backup_save() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	_had_backup = DirAccess.copy_absolute(
		ProjectSettings.globalize_path(SAVE_PATH),
		ProjectSettings.globalize_path(BACKUP_PATH)) == OK

func _restore_save() -> void:
	if not _had_backup:
		return
	DirAccess.copy_absolute(
		ProjectSettings.globalize_path(BACKUP_PATH),
		ProjectSettings.globalize_path(SAVE_PATH))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(BACKUP_PATH))

func _check(name: String, ok: bool) -> void:
	if ok:
		print("[END] PASS  ", name)
	else:
		_failed += 1
		print("[END] FAIL  ", name)
