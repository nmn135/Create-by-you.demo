class_name OfflineReply
## OfflineReply —— 自由对话的离线兜底（还原LLM F2）
## 移植网页版 fallbackReply + detectTone：
## 连不上 LLM 时，按语气给一句罐头回复，让游戏永远能玩下去。

static func detect_tone(text: String) -> String:
	var t := text.to_lower()
	# 剧本外/元话题 → meta
	for w in ["系统", "代码", "程序", "底层", "世界规则", "重写", "编译", "bug", "你在骗", "你在演", "我是玩家", "ai", "人工智能", "剧本", "作者", "刻痕", "重置"]:
		if t.contains(w):
			return "meta"
	# 敌意
	for w in ["滚", "杀", "烧", "毁", "威胁", "闭嘴", "去死", "蠢", "白痴", "懦夫"]:
		if t.contains(w):
			return "敌意"
	# 友好
	for w in ["谢谢", "帮忙", "喜欢", "朋友", "相信", "你好"]:
		if t.contains(w):
			return "友好"
	return ""

static func fallback_reply(npc_cn: String, text: String) -> String:
	var tone := detect_tone(text)
	if tone == "meta":
		return "（%s忽然顿住，直直看着你。）……这句话，不在我该知道的范围内。" % npc_cn
	match npc_cn:
		"市长":
			match tone:
				"敌意": return "（市长笑意不改，眼神冷了几分。）本官警告你，这座城经不起第二个纵火犯。"
				"友好": return "（市长微微点头。）识大体的人，本官愿意多给几分面子。"
				_: return "（市长抚着怀表，不置可否。）第七天的事，没什么新鲜的可说。"
		"当铺老板":
			match tone:
				"敌意": return "（当铺老板把算盘往怀里一拢。）这单生意，恕不奉陪。"
				"友好": return "（当铺老板来了兴致。）这买卖有的谈。你想知道点什么？"
				_: return "（当铺老板敲了敲柜台。）话是好话，就是还不值钱。"
		"说书人":
			match tone:
				"敌意": return "（说书人笑得更欢了。）火烧起来的时候，故事才最好听。你这话，够劲儿。"
				"友好": return "（说书人眯眼，笑里多了一点认真。）你这话，像听得懂的人说的。"
				_: return "（说书人摇头晃脑，话里有话。）这话，一半是真的。另一半，也是真的。"
		"神官":
			match tone:
				"敌意": return "（神官垂目，圣火晃了晃。）亵渎之言，不必说出口。"
				"友好": return "（神官微微颔首。）虔诚的心，圣火认得。"
				_: return "（神官望着圣火。）第七天，神还沉默。"
	return "……"
