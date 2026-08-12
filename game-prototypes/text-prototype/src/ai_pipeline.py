"""
封印之殿 文字原型 — AI 管线
DeepSeek API 调用：意图解析（V4 Pro）+ 回复生成（V4 Flash）
"""
import json
import time
from src.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    INTENT_MODEL, REPLY_MODEL, DEBUG_MODE
)

# === 客户端懒加载 ===
# API Key 缺失时不在导入期崩溃，调用时才报错（由调用方降级处理）
_client = None
_client_error = None

def _get_client():
    """延迟创建 OpenAI 客户端；Key 无效时抛出带提示的异常"""
    global _client, _client_error
    if _client is not None:
        return _client
    if _client_error is not None:
        raise _client_error
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
        _client_error = RuntimeError(
            "DEEPSEEK_API_KEY 未设置。请设置环境变量或在 src/config.py 中填写。"
        )
        raise _client_error
    try:
        from openai import OpenAI
        # 30s 超时：DeepSeek 偶发慢响应，超时让服务器快速降级，避免玩家无限等待
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=30.0,
            max_retries=1,
        )
        return _client
    except Exception as e:
        _client_error = e
        raise

# ================================================================
# 意图解析器 (DeepSeek V4 Pro — 高质量)
# ================================================================

INTENT_SYSTEM_PROMPT = """你是一个对话意图解析器。玩家的输入是自然语言，你需要从中提取结构化信息。

## 意图类型（10 种）
- ask_backstory: 询问 NPC 的背景、经历、目的
- probe_conflict: 试探 NPC 与其他人的矛盾、紧张关系、秘密
- reveal_secret: 向 NPC 透露一个秘密（关于你自己或其他人）
- persuade: 说服 NPC 做某事
- accuse: 指控 NPC 撒谎或隐瞒
- take_sides: 公开表态支持某个人
- sow_discord: 试图离间 NPC 之间的关系
- offer_comfort: 安慰、表达善意
- ask_favor: 请求帮助或物品
- stay_silent: 玩家选择不回应或沉默

## 语气
- curious_gentle: 好奇但温和
- testing_reaction: 试探对方反应
- accusatory: 指控性
- insinuating: 暗示性、挑拨
- supportive: 支持、善良
- neutral: 中性
- confrontational: 对抗

## 输出格式（纯 JSON，不要 markdown 包裹）
{
  "target_npc": "baruk|liana|margaret|rog|guardian",
  "topic": "话题关键词（中文）",
  "intent": "意图类型",
  "tone": "语气",
  "involves": ["涉及的其他 NPC ID"],
  "risk_level": "low|medium|high",
  "confidence": 0.0-1.0
}

## 注意
- target_npc 必须是玩家对话的主要对象（不是被谈论的对象）
- involves 是被提到、涉及的 NPC（最多 2 个）
- risk_level: low=日常对话, medium=可能引起不快, high=可能激怒对方
- 如果无法确定 target_npc，设为空字符串
- 如果玩家没有明确指谁，且之前对话已经建立了语境，根据语境判断
"""

def parse_intent(user_input: str, context: str = "") -> dict:
    """
    解析玩家输入为结构化意图。
    使用 DeepSeek V4 Pro 保证理解准确度。
    """
    messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "system", "content": f"当前语境：{context}"})
    messages.append({"role": "user", "content": user_input})

    # 第 1 次用 INTENT_MODEL（v4-pro，质量高）；v4-pro 08-12 实测持续空响应/卡顿，
    # 故第 2 次起切 REPLY_MODEL（v4-flash）兜底，并给每次请求 8s 超时上限——
    # 防止单次卡死拖过前端 15s abort（UI 聊天曾因此收不到回复）。
    models = [INTENT_MODEL, REPLY_MODEL, REPLY_MODEL]
    for attempt in range(3):
        try:
            response = _get_client().chat.completions.create(
                model=models[attempt],
                messages=messages,
                temperature=0.1,  # 低温度保证稳定
                max_tokens=300,
                timeout=8,
            )
            text = response.choices[0].message.content.strip()
            # 清理可能的 markdown 包裹
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            result = json.loads(text)
            return _validate_intent(result)
        except (json.JSONDecodeError, Exception) as e:
            if DEBUG_MODE:
                print(f"  [DEBUG] Intent parse attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(1)
            else:
                return _fallback_intent(user_input)

def _validate_intent(result: dict) -> dict:
    """验证和补全意图"""
    valid_intents = [
        "ask_backstory", "probe_conflict", "reveal_secret", "persuade",
        "accuse", "take_sides", "sow_discord", "offer_comfort",
        "ask_favor", "stay_silent"
    ]
    valid_tones = [
        "curious_gentle", "testing_reaction", "accusatory", "insinuating",
        "supportive", "neutral", "confrontational"
    ]
    valid_npcs = ["baruk", "liana", "margaret", "rog", "guardian", ""]
    valid_risks = ["low", "medium", "high"]

    result.setdefault("intent", "ask_backstory")
    if result["intent"] not in valid_intents:
        result["intent"] = "ask_backstory"

    result.setdefault("tone", "neutral")
    if result["tone"] not in valid_tones:
        result["tone"] = "neutral"

    result.setdefault("target_npc", "")
    if result["target_npc"] not in valid_npcs:
        result["target_npc"] = ""

    result.setdefault("involves", [])
    result["involves"] = [n for n in result.get("involves", []) if n in valid_npcs and n != result["target_npc"]]

    result.setdefault("risk_level", "medium")
    if result["risk_level"] not in valid_risks:
        result["risk_level"] = "medium"

    result.setdefault("confidence", 0.5)
    result.setdefault("topic", "")
    result.setdefault("urgency", 2)
    if not isinstance(result.get("urgency"), (int, float)) or result["urgency"] < 1 or result["urgency"] > 5:
        result["urgency"] = max(1, min(5, int(result.get("urgency", 2) or 2)))
    result.setdefault("reasoning", "")

    return result

def _fallback_intent(user_input: str) -> dict:
    """AI 解析失败时的回退——基于关键词的简单匹配"""
    text = user_input.lower()
    intent = "ask_backstory"
    tone = "neutral"

    if any(w in text for w in ["挑拨", "离间", "小心他", "防着", "背后"]):
        intent = "sow_discord"
        tone = "insinuating"
    elif any(w in text for w in ["骗", "撒谎", "隐瞒", "真相", "到底"]):
        intent = "accuse"
        tone = "accusatory"
    elif any(w in text for w in ["帮你", "告诉我", "说吧", "你知道"]):
        intent = "probe_conflict"
        tone = "testing_reaction"
    elif any(w in text for w in ["没事", "抱歉", "理解", "不难过", "不怪"]):
        intent = "offer_comfort"
        tone = "supportive"
    elif any(w in text for w in ["站你", "支持", "帮你说话"]):
        intent = "take_sides"
        tone = "supportive"

    # 识别目标 NPC
    target = ""
    for keyword, npc_id in [
        ("baruk", "baruk"), ("巴鲁克", "baruk"), ("矮人", "baruk"),
        ("莉安娜", "liana"), ("liana", "liana"), ("精灵", "liana"),
        ("玛格丽特", "margaret"), ("margaret", "margaret"), ("牧师", "margaret"),
        ("罗格", "rog"), ("rog", "rog"), ("兽人", "rog"),
        ("守护灵", "guardian"), ("guardian", "guardian"),
    ]:
        if keyword in text:
            target = npc_id
            break

    return {
        "target_npc": target,
        "topic": user_input[:20],
        "intent": intent,
        "tone": tone,
        "involves": [],
        "risk_level": "medium",
        "confidence": 0.3,
        "fallback": True,
    }

# ================================================================
# 回复生成器 (DeepSeek V4 Flash — 便宜、快)
# ================================================================

# 情绪→温度映射：不同情绪下语言可预测性不同
# 愤怒时更高温度 = 更多"失言"和情绪爆发的可能
# 平静时更低温度 = 语言稳定、可预测
MOOD_TEMPERATURE = {
    "calm": 0.7,        # 平静：适中偏低，语言稳定不跳跃
    "tense": 0.6,       # 紧张：低温度，措辞谨慎不随机
    "angry": 0.9,       # 愤怒：高温度，语言更不可预测
    "vulnerable": 0.85, # 脆弱：偏高温度，防御松动后话可能出人意料
    "hopeful": 0.8,     # 希望：默认温度，语言自然流畅
}

def generate_npc_reply(
    npc_name: str,
    npc_race: str,
    npc_title: str,
    talk_style: str,
    mood: str,
    response_direction: str,
    player_input: str,
    context: str = "",
    slip_occurred: bool = False,
    revelation_line: str = "",
    is_whisper: bool = False,
    present_npcs: list[str] = None,
    guardian_light: str = "",
) -> str:
    """
    生成 NPC 的自然语言回复。
    使用 DeepSeek V4 Flash 保证速度和成本。
    """
    mood_colors = {
        "calm": "平静的，有条理的",
        "tense": "紧张的，语言变得简短直接",
        "angry": "愤怒的，声音可能更低而不是更高，措辞更加锐利",
        "vulnerable": "脆弱的，防御在松动——这是他说真话的时刻",
        "hopeful": "带着一丝希望，语气温和",
    }

    whisper_note = ""
    if is_whisper:
        whisper_note = """
⚠️ 这是悄悄话——只有你和玩家能听到。你不会大声说出你的秘密。
但你的肢体语言仍然会被其他人看到——他们会注意到你在和玩家密谈。
"""

    slip_note = ""
    if slip_occurred and revelation_line:
        slip_note = f"""
⚠️ 你刚才失言了——你不小心说出了你一直在隐藏的事。
你的标志性台词应该是："{revelation_line}"
在这句话之后，你才意识到自己说了什么——你的表情、语气都会有一瞬间的崩塌。
然后你可以选择：① 试图收回（掩饰） ② 沉默（放弃） ③ 继续说下去（破罐破摔）
"""

    audience = f"在场的其他人：{', '.join(present_npcs or [])}" if (present_npcs and not is_whisper) else ""

    system_prompt = f"""你是 {npc_name}，一个{npc_race}{npc_title}。

## 你的说话风格
{talk_style}

## 当前状态
- 情绪：{mood_colors.get(mood, '正常的')}
- 回复方向：{response_direction}
- 环境：{guardian_light or '大殿内安静，守护灵的光芒稳定地悬浮在中央'}

{whisper_note}
{slip_note}
{audience}

## 回复要求
- 2-5 句话，不要超过 100 字
- 自然的对话节奏——不是念剧本，是活人在说话
- 允许停顿、沉默、不完整句子——像真正的对话
- 允许微动作描述（用括号）：（他/她 + 动作）
- 不使用 markdown
- 使用中文
- 你绝不会说"作为XX种族的XX身份"——你会以角色的方式自然地反应

## ⚠️ 最关键
- 你永远不会知道"秘密已被设定好"——你的秘密对你自己来说是真实经历，不是数据
- 只有在 slip_occurred=true 时才说出你的标志性台词——那是你最深的秘密
- 平时的对话中你可以暗示、回避、转移话题——但绝不能直接说出来
"""

    user_msg = f"玩家说：「{player_input}」\n\n请以 {npc_name} 的身份回应。"

    for attempt in range(2):
        try:
            response = _get_client().chat.completions.create(
                model=REPLY_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=MOOD_TEMPERATURE.get(mood, 0.8),  # 根据情绪动态调整温度
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if DEBUG_MODE:
                print(f"  [DEBUG] Reply generation attempt {attempt+1} failed: {e}")
            if attempt < 1:
                time.sleep(1)

    return f"（{npc_name} 沉默了一会儿，似乎有话要说，但最终只是移开了目光。）"

# ================================================================
# 快捷方法
# ================================================================

def generate_guardian_ambient(guardian_score: int, recent_events: list[str]) -> str:
    """生成守护灵的环境描述（非对话，叙事文本）"""
    system_prompt = """你是守护灵的叙事者。用 1-2 句话描述守护灵在当前时刻的状态。
描述应该是诗意的、像刻在石板上一样简洁有力。
守护灵不直接说话——你描述它的光、温度、空气的变化。"""

    user_msg = f"守护灵道德评分：{guardian_score}。最近的事件：{'; '.join(recent_events[-3:] or ['无'])}。描述当前时刻的守护灵。"

    try:
        response = _get_client().chat.completions.create(
            model=REPLY_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # 回退
        if guardian_score > 30:
            return "守护灵的光芒温和地照耀着——像一层薄薄的白金色丝绸覆盖在每一块石头上。"
        elif guardian_score > -10:
            return "守护灵悬浮在中央，光芒稳定而沉默。它在观察。"
        elif guardian_score > -40:
            return "守护灵的光芒已经泛红。殿内的空气开始变冷。墙壁上的符文偶尔闪一下——像是不安的脉搏。"
        else:
            return "整座殿都在低鸣。守护灵的光不再是光——更像是一种颜色的愤怒。暗紫色的波纹从中央向外扩散，触及每一面墙，每一个灵魂。"
