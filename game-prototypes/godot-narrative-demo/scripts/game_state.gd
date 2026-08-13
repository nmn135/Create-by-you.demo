extends Node
## 第十一课：全局单例（Autoload）—— 所有脚本共享的"世界档案袋"
##
## 任何脚本都能直接写 GameState.relations 读写，不用传参、不用找节点。
## 注册方式：项目设置 → Autoload → GameState = res://scripts/game_state.gd

# 每个 NPC 的 4 维关系：0=低 1=中 2=高
var relations := {
	"当铺老板": { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"说书人":   { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"神官":     { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
	"市长":     { "trust": 1, "fear": 1, "like": 1, "suspect": 1 },
}
