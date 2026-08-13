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

# ---- 第十二课：世界状态 ----
# 这些是"这座城"的记忆，不属于任何单个 NPC：
var day := 1          # 第几天（以后刻痕剧情会推进到第二天）
var bell_rings := 0   # 钟楼响过几次（数到十三是大事——第十五课用）

# 剧情旗标：字符串名字 → true。选过某句话、听过某个秘密，都在这里留痕。
var flags := {}

func has_flag(flag_name: String) -> bool:
	return flags.get(flag_name, false)

func set_flag(flag_name: String) -> void:
	flags[flag_name] = true

func unset_flag(flag_name: String) -> void:
	flags.erase(flag_name)
