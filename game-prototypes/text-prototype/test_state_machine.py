#!/usr/bin/env python3
"""
封印之殿 文字原型 — 状态机离线测试
不依赖 AI API，纯测试状态机逻辑：失言判定、关系变化、结局触发
"""
import sys
sys.path.insert(0, ".")

from src.state_machine import StateMachine
from src.game_data import ALL_NPCS, ENTRANCE_ORDER

def green(s): return f"\033[92m{s}\033[0m"
def red(s): return f"\033[91m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"

passed = 0
failed = 0

def test(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {green('✓')} {name}")
    else:
        failed += 1
        print(f"  {red('✗')} {name} — {detail}")

# ============================================================
# 测试 1：出场顺序
# ============================================================
print(bold("\n── 测试 1：出场顺序 ──"))
sm = StateMachine()

# 初始状态：只有玩家和守护灵
test("初始阶段 = 0", sm.game.current_stage == 0)
test("初始无 NPC 在场", len(sm.game.present_npcs) == 0)

# 推进阶段
npc = sm.advance_stage()
test("阶段1 = Rog", npc == "rog", f"实际: {npc}")
test("Rog 在场", "rog" in sm.game.present_npcs)

npc = sm.advance_stage()
test("阶段2 = Baruk", npc == "baruk", f"实际: {npc}")

npc = sm.advance_stage()
test("阶段3 = Liana", npc == "liana", f"实际: {npc}")

npc = sm.advance_stage()
test("阶段4 = Margaret", npc == "margaret", f"实际: {npc}")

npc = sm.advance_stage()
test("阶段5 = None（全部到场）", npc is None)

# ============================================================
# 测试 2：信任度变化
# ============================================================
print(bold("\n── 测试 2：信任度变化 ──"))
sm = StateMachine()

# 初始化所有 NPC 到场
for _ in range(4):
    sm.advance_stage()

baruk_state = sm.npcs["baruk"]
initial_trust = baruk_state.trust_player

# 询问背景故事（高信任）
sm.apply_trust_change("baruk", 20, "测试")
test("信任度增加", sm.npcs["baruk"].trust_player == initial_trust + 20)

# 指控（低信任）
sm.apply_trust_change("baruk", -30, "测试")
test("信任度减少", sm.npcs["baruk"].trust_player == initial_trust - 10)

# 边界测试
sm.apply_trust_change("baruk", 200, "测试")
test("信任度上限 = 100", sm.npcs["baruk"].trust_player == 100)

sm.apply_trust_change("baruk", -200, "测试")
test("信任度下限 = -100", sm.npcs["baruk"].trust_player == -100)

# ============================================================
# 测试 3：失言判定
# ============================================================
print(bold("\n── 测试 3：失言判定 ──"))
sm = StateMachine()
for _ in range(4):
    sm.advance_stage()

# 场景：高信任 + 连续追问 + 痛点命中 → Baruk 失言
baruk_state = sm.npcs["baruk"]
baruk_state.trust_player = 70  # 高信任
baruk_state.mood = "angry"  # 愤怒情绪（+30%）
baruk_state.consecutive_probe_count["baruk_wall_rune"] = 3  # 追问累积

result = sm._check_slip(
    defn=sm.get_npc_def("baruk"),
    state=baruk_state,
    topic="墙上的符文暗语——那些矮人工匠留下的求救信息",
    trust=70,
    mood="angry"
)
test("Baruk 失言触发（高信任+愤怒+3轮追问+痛点命中）",
     result["slip"],
     f"概率: {result.get('probability', 'N/A')}")

# 场景：低信任 + calm + 无追问 → 不触发
sm2 = StateMachine()
for _ in range(4):
    sm2.advance_stage()
baruk2 = sm2.npcs["baruk"]
baruk2.trust_player = 10
baruk2.mood = "calm"

result2 = sm2._check_slip(
    defn=sm2.get_npc_def("baruk"),
    state=baruk2,
    topic="你好吗",
    trust=10,
    mood="calm"
)
test("Baruk 不触发（低信任+平静+无关话题）", not result2["slip"])

# 场景：Liana 在 vulnerable 时被问及祖先
sm3 = StateMachine()
for _ in range(4):
    sm3.advance_stage()
liana3 = sm3.npcs["liana"]
liana3.trust_player = 60
liana3.mood = "vulnerable"
liana3.consecutive_probe_count["liana_ancestry"] = 2

result3 = sm3._check_slip(
    defn=sm3.get_npc_def("liana"),
    state=liana3,
    topic="你的祖先——艾瑟林——和这座殿的关系",
    trust=60,
    mood="vulnerable"
)
test("Liana 失言触发（vulnerable+痛点命中+2轮追问）",
     result3["slip"],
     f"概率: {result3.get('probability', 'N/A')}")

# ============================================================
# 测试 4：意图处理 — 挑拨离间
# ============================================================
print(bold("\n── 测试 4：挑拨离间 ──"))
sm = StateMachine()
for _ in range(4):
    sm.advance_stage()

# 挑拨公式: chance = ((trust-30)*0.3 + (100-resistance)*0.3 + (-attitude)*0.2) / 100
# 需要 chance > 0.5 才能成功，设计上非常保守（挑拨离间不应容易）

# 测试 4a：挑拨成功——极限条件（极高信任 + 对方已极度憎恨目标）
# Rog: 抵抗力 35 最低, trust=95, attitude to liana=-40
# chance = ((95-30)*0.3 + (100-35)*0.3 + (40*0.2)) / 100 = (19.5+19.5+8)/100 = 0.47 — 仍不够
# 结论：公式天生极保守，需要 trust=100 + attitude=-50 才能触发成功
# 改为测试"被察觉"分支（最常见的设计路径）
rog4 = sm.npcs["rog"]
rog4.trust_player = 50

intent = {
    "target_npc": "rog",
    "topic": "精灵",
    "intent": "sow_discord",
    "tone": "insinuating",
    "involves": ["liana"],
    "risk_level": "high",
}
result = sm.process_intent(intent)
test("挑拨 Rog 被察觉（信任 50 + 抵抗 35）", result.get("discord_success") == False,
     f"信任变更: {sm.npcs['rog'].trust_player}")

# 测试 4b：挑拨完全失败——极低信任下挑拨，NPC 暴怒
sm2 = StateMachine()
for _ in range(4):
    sm2.advance_stage()
marg = sm2.npcs["margaret"]
marg.trust_player = 5  # 极低信任

intent2 = {
    "target_npc": "margaret",
    "topic": "教会",
    "intent": "sow_discord",
    "tone": "insinuating",
    "involves": ["liana"],
    "risk_level": "high",
}
result2 = sm2.process_intent(intent2)
test("挑拨激怒低信任 NPC", marg.mood == "angry",
     f"情绪: {marg.mood}, 信任变化: {marg.trust_player}")
test("挑拨失败信任大降", marg.trust_player <= -3,
     f"信任: {marg.trust_player}")

# ============================================================
# 测试 5：结局判定
# ============================================================
print(bold("\n── 测试 5：结局判定 ──"))
sm = StateMachine()
for _ in range(4):
    sm.advance_stage()

# 初始状态：无结局
ending = sm.check_ending()
test("初始状态无结局", ending is None, f"实际: {ending}")

# 模拟血债血偿
sm.npcs["baruk"].attitudes["liana"] = -70
sm.npcs["liana"].attitudes["baruk"] = -70
ending = sm.check_ending()
test("血债血偿触发", ending == "blood_debt", f"实际: {ending}")

# 模拟新火种
sm2 = StateMachine()
for _ in range(4):
    sm2.advance_stage()
sm2.npcs["baruk"].attitudes["rog"] = 70
sm2.npcs["rog"].attitudes["baruk"] = 70
sm2.npcs["baruk"].revealed_secrets.add("baruk_wall_rune")
ending2 = sm2.check_ending()
test("新火种触发", ending2 == "new_flame", f"实际: {ending2}")

# ============================================================
# 测试 6：悄悄话守护灵惩罚
# ============================================================
print(bold("\n── 测试 6：悄悄话守护灵惩罚 ──"))
sm = StateMachine()
for _ in range(4):
    sm.advance_stage()

sm.game.whisper_mode = True
sm.game.whisper_target = "baruk"
initial_score = sm.game.guardian_moral_score

intent = {
    "target_npc": "baruk",
    "topic": "test",
    "intent": "ask_backstory",
    "tone": "neutral",
    "involves": [],
    "risk_level": "low",
}
sm.process_intent(intent)
test("悄悄话扣守护灵分", sm.game.guardian_moral_score < initial_score,
     f"初始: {initial_score}, 现在: {sm.game.guardian_moral_score}")

# ============================================================
# 测试 7：出场节奏提示（充分对话后可等待推进）
# ============================================================
print(bold("\n── 测试 7：出场节奏提示 ──"))

def _chat(sm, npc_id, n):
    """向 npc_id 连聊 n 轮 ask_backstory（不产生新信息，用于累计充分度）"""
    for _ in range(n):
        sm.process_intent({
            "target_npc": npc_id,
            "topic": "聊聊",
            "intent": "ask_backstory",
            "tone": "neutral",
            "involves": [],
            "risk_level": "low",
        })

# 7a: 阶段 0（无人在场）→ 无提示
sm = StateMachine()
test("阶段0无人在场→无提示", sm.get_pacing_hint() is None)

# 7b: 阶段 1（罗格入场）但还没聊 → 无提示
sm.advance_stage()
test("新角色入场未聊→无提示", sm.get_pacing_hint() is None,
     f"hint={sm.get_pacing_hint()!r}")

# 7c: 只聊 1 轮（充分度不足）→ 无提示
_chat(sm, "rog", 1)
test("只聊1轮→无提示", sm.get_pacing_hint() is None,
     f"hint={sm.get_pacing_hint()!r}")

# 7d: 连续 2 轮无新信息 → 提示出现，且点名下一位入场者（巴鲁克）
_chat(sm, "rog", 1)
hint = sm.get_pacing_hint()
test("连续2轮无新信息→提示出现", hint is not None, f"hint={hint!r}")
test("提示点名下一位入场者", hint is not None and "巴鲁克" in hint,
     f"hint={hint!r}")

# 7e: 有在场 NPC 没聊过 → 无提示（阶段2：罗格+巴鲁克，只聊巴鲁克）
sm2 = StateMachine()
for _ in range(2):
    sm2.advance_stage()
_chat(sm2, "baruk", 3)
test("有NPC没聊过→无提示", sm2.get_pacing_hint() is None,
     f"hint={sm2.get_pacing_hint()!r}")

# 7f: 新信息重置充分度（turns_since_new_info 归零 → 提示消失）
sm.game.turns_since_new_info = 0
test("新信息重置后→提示消失", sm.get_pacing_hint() is None)

# 7g: 全员到齐 → 无提示
sm3 = StateMachine()
for _ in range(4):
    sm3.advance_stage()
_chat(sm3, "rog", 3)
test("全员到齐→无提示", sm3.get_pacing_hint() is None)

# ============================================================
# 汇总
# ============================================================
print(bold(f"\n{'='*50}"))
print(bold(f"  测试结果: {green(str(passed))} 通过, {red(str(failed))} 失败"))
print(bold(f"  总计: {passed + failed} 项"))
print(bold(f"{'='*50}"))

if failed > 0:
    sys.exit(1)
