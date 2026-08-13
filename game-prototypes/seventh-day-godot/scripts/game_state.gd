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
