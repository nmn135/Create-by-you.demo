class_name Endgame
## Endgame —— 无限结局（还原LLM F4）
## 移植网页版 classifyEnding + DEFAULT_EPILOGUE：
## 玩家对这座城说的最后一句话，确定性分成 4 条世界线；
## LLM 在线时现写 epilogue，离线时用本地兜底文案。

const DEFAULT_EPILOGUE := {
	"续写": "你接过那支笔，蘸尽最后一滴墨，在第七天的末尾写下一行：第八天照常升起。城里的每一个人，都在梦里听见了它。",
	"合卷": "你合上这本没写完的书。城里的人停在原地，脸上挂着第七天的微笑——他们终于不用再被书写，也就永远不会被遗忘。",
	"抹去": "你把那支笔折断。墨水流尽，字迹褪色，城墙像被擦去的草稿一样归于空白。城中无人醒来，也无人死去——故事，停在了空页。",
	"坦白之后": "你说：我相信你。作者愣了很久，然后笑了。假的城，假的循环，假的第七天——却因为这一句真话，第一次真的亮了起来。",
}

# 世界线分类（与网页版同款关键词）
static func classify_ending(text: String, author_confessed: bool) -> String:
	var t := text.strip_edges()
	# 隐藏结局：只在作者坦白（author_confessed）之后，玩家选择拥抱这份"假的真诚"时解锁
	if author_confessed and _has_any(t, ["相信", "拥抱", "我信", "我愿意", "假的真", "真诚", "温暖", "抱抱", "原谅", "继续演", "陪你", "你是真的", "谢谢你"]):
		return "坦白之后"
	if _has_any(t, ["烧", "毁", "删", "清空", "归零", "抹去", "抹掉", "停止", "放映", "消失", "毁灭", "重置", "一把火", "折断"]):
		return "抹去"
	if _has_any(t, ["合上", "合卷", "不写", "放下", "关机", "到此为止", "结束", "离开", "再见", "走吧", "算了"]):
		return "合卷"
	return "续写"

static func default_epilogue(ending: String) -> String:
	return DEFAULT_EPILOGUE.get(ending, DEFAULT_EPILOGUE["续写"])

static func _has_any(t: String, words: Array) -> bool:
	for w in words:
		if t.contains(str(w)):
			return true
	return false
