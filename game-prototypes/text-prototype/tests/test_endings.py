#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
封印之殿 文字原型 — 5 结局路线自动化测试
纯离线，不依赖 AI API。针对 src/state_machine.py 的 check_ending() 验证 5 种结局触发条件。

结局一览：
  1. truth_temple   真理之殿 —— 所有秘密暴露 + baruk 对 liana 态度 > -20
  2. blood_debt     血债血偿 —— baruk ↔ liana 互相 < -60
  3. new_flame      新火种   —— baruk ↔ rog 互相 > 60 + baruk_wall_rune 已暴露
  4. no_redemption  谁都没被救赎 —— 每名 NPC 至少有 2 段关系 < -40
  5. godslayer      弑神者   —— guardian_moral_score < -80 + 所有秘密暴露

覆盖：
  1. 直接构造状态法 —— 对每种结局直接构造满足条件的状态，断言 check_ending() 返回正确结局 ID（主测试）
  2. 模拟对话推进法 —— 不调 AI，直接调用 process_intent 用预设意图序列逐步逼近结局（blood_debt 演示）
  3. 冲突检测 —— 验证各结局条件互斥性：一个状态只命中一个结局

运行：
    cd D:\Create by you.demo\game-prototypes\text-prototype
    python -X utf8 tests/test_endings.py
"""
import sys
import os

# 确保项目根目录在 sys.path（脚本位于 tests/，向上找一级）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state_machine import StateMachine
from src.game_data import ALL_NPCS

# ============================================================
# 输出工具（与 test_state_machine.py 风格一致：绿✓红✗）
# ============================================================
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

# 参与结局判定的 4 名 NPC（守护灵不算在内）
PLAYERS = ["baruk", "liana", "margaret", "rog"]

# 结局 ID 与中文名对照
ENDING_NAMES = {
    "truth_temple": "真理之殿",
    "blood_debt": "血债血偿",
    "new_flame": "新火种",
    "no_redemption": "谁都没被救赎",
    "godslayer": "弑神者",
}

def all_revealed(sm: StateMachine) -> bool:
    """所有 4 名 NPC 的秘密是否全部暴露（与 check_ending 内部逻辑一致）"""
    return all(
        len(sm.npcs[n].revealed_secrets) >= len(ALL_NPCS[n].secrets)
        for n in PLAYERS
    )

def reveal_all(sm: StateMachine):
    """直接构造：让 4 名 NPC 的秘密全部暴露"""
    for n in PLAYERS:
        sm.npcs[n].revealed_secrets = {s.id for s in ALL_NPCS[n].secrets}

# ============================================================
# 各结局的独立判定谓词（用于冲突检测，与 check_ending 的条件镜像）
# ============================================================
def cond_truth_temple(sm):
    return (all_revealed(sm)
            and sm.npcs["baruk"].attitudes.get("liana", -100) > -20)

def cond_blood_debt(sm):
    return (sm.npcs["baruk"].attitudes.get("liana", 0) < -60
            and sm.npcs["liana"].attitudes.get("baruk", 0) < -60)

def cond_new_flame(sm):
    return (sm.npcs["baruk"].attitudes.get("rog", 0) > 60
            and sm.npcs["rog"].attitudes.get("baruk", 0) > 60
            and "baruk_wall_rune" in sm.npcs["baruk"].revealed_secrets)

def cond_no_redemption(sm):
    return all(
        sum(1 for v in sm.npcs[n].attitudes.values() if v < -40) >= 2
        for n in PLAYERS
    )

def cond_godslayer(sm):
    return sm.game.guardian_moral_score < -80 and all_revealed(sm)

CONDITIONS = [
    ("truth_temple", cond_truth_temple),
    ("blood_debt", cond_blood_debt),
    ("new_flame", cond_new_flame),
    ("no_redemption", cond_no_redemption),
    ("godslayer", cond_godslayer),
]

def matches_only(sm, expected) -> list:
    """返回所有为真的结局条件 ID；仅当恰好命中 expected 时为 [expected]"""
    return [eid for eid, fn in CONDITIONS if fn(sm)]

def build_ending_state(ending_id: str) -> StateMachine:
    """直接构造满足指定结局的状态（主测试用）"""
    sm = StateMachine()
    if ending_id == "truth_temple":
        reveal_all(sm)
        sm.npcs["baruk"].attitudes["liana"] = 0          # 初始 -30，需 > -20
    elif ending_id == "blood_debt":
        sm.npcs["baruk"].attitudes["liana"] = -70
        sm.npcs["liana"].attitudes["baruk"] = -70
    elif ending_id == "new_flame":
        sm.npcs["baruk"].attitudes["rog"] = 70
        sm.npcs["rog"].attitudes["baruk"] = 70
        sm.npcs["baruk"].revealed_secrets.add("baruk_wall_rune")
    elif ending_id == "no_redemption":
        for n in PLAYERS:
            for other in PLAYERS:
                if other != n:
                    sm.npcs[n].attitudes[other] = -50   # 每人 3 段 < -40
    elif ending_id == "godslayer":
        reveal_all(sm)
        sm.game.guardian_moral_score = -90
        sm.npcs["baruk"].attitudes["liana"] = -50       # 阻止 truth_temple 先触发
    return sm

# ============================================================
# 测试 1：直接构造状态法（离线、无 AI）—— 主测试
# ============================================================
print(bold("\n── 结局测试：直接构造状态法（离线，无 AI）──"))

# 基线：初始状态不应触发任何结局
sm = StateMachine()
test("初始状态无结局", sm.check_ending() is None, f"实际: {sm.check_ending()}")

# 1) 真理之殿
sm = build_ending_state("truth_temple")
test("真理之殿触发", sm.check_ending() == "truth_temple", f"实际: {sm.check_ending()}")
test("真理之殿前置：所有秘密暴露", all_revealed(sm))
test("真理之殿前置：baruk 对 liana 态度 > -20",
     sm.npcs["baruk"].attitudes.get("liana", -100) > -20,
     f"实际: {sm.npcs['baruk'].attitudes.get('liana')}")

# 2) 血债血偿
sm = build_ending_state("blood_debt")
test("血债血偿触发", sm.check_ending() == "blood_debt", f"实际: {sm.check_ending()}")
test("血债血偿前置：baruk 对 liana < -60",
     sm.npcs["baruk"].attitudes.get("liana") < -60,
     f"实际: {sm.npcs['baruk'].attitudes.get('liana')}")
test("血债血偿前置：liana 对 baruk < -60",
     sm.npcs["liana"].attitudes.get("baruk") < -60,
     f"实际: {sm.npcs['liana'].attitudes.get('baruk')}")

# 3) 新火种
sm = build_ending_state("new_flame")
test("新火种触发", sm.check_ending() == "new_flame", f"实际: {sm.check_ending()}")
test("新火种前置：baruk 对 rog > 60",
     sm.npcs["baruk"].attitudes.get("rog") > 60,
     f"实际: {sm.npcs['baruk'].attitudes.get('rog')}")
test("新火种前置：rog 对 baruk > 60",
     sm.npcs["rog"].attitudes.get("baruk") > 60,
     f"实际: {sm.npcs['rog'].attitudes.get('baruk')}")
test("新火种前置：baruk_wall_rune 已暴露",
     "baruk_wall_rune" in sm.npcs["baruk"].revealed_secrets)

# 4) 谁都没被救赎
sm = build_ending_state("no_redemption")
test("谁都没被救赎触发", sm.check_ending() == "no_redemption", f"实际: {sm.check_ending()}")
for n in PLAYERS:
    cnt = sum(1 for v in sm.npcs[n].attitudes.values() if v < -40)
    test(f"谁都没被救赎前置：{n} 有 {cnt} 段关系 < -40", cnt >= 2)

# 5) 弑神者
sm = build_ending_state("godslayer")
test("弑神者触发", sm.check_ending() == "godslayer", f"实际: {sm.check_ending()}")
test("弑神者前置：守护灵道德 < -80", sm.game.guardian_moral_score < -80,
     f"实际: {sm.game.guardian_moral_score}")
test("弑神者前置：所有秘密暴露", all_revealed(sm))
test("弑神者前置：baruk 对 liana ≤ -20（避免 truth_temple 抢先）",
     sm.npcs["baruk"].attitudes.get("liana") <= -20,
     f"实际: {sm.npcs['baruk'].attitudes.get('liana')}")

# ============================================================
# 测试 2：模拟对话推进法（直接调用 process_intent，不调 AI）
# ============================================================
print(bold("\n── 结局测试：模拟对话推进法（无 AI，直接 process_intent）──"))

def make_intent(target, intent_type, involves=None, topic="", tone="neutral", risk="low"):
    return {
        "target_npc": target, "topic": topic, "intent": intent_type,
        "tone": tone, "involves": involves or [], "risk_level": risk,
    }

# ---- 路线 A：血债血偿 —— 揭示秘密路线（确定性、可复现）----
# 思路：先让 NPC 失言让玩家"真正知道"秘密（修复3），再反复揭示压低关系；
#       同时失言引发的连锁反应（事件链）天然加深双方敌意。
sm = StateMachine()
# 步骤 1：让莉安娜失言（学会她的秘密）——先安慰进入 vulnerable，再追问痛点短语
sm.process_intent(make_intent("liana", "offer_comfort", topic="你不必一个人扛"))
sm.process_intent(make_intent("liana", "probe_conflict", involves=[],
                              topic="你的祖先艾瑟林的血统，精灵王室和建殿者", risk="high"))
# 步骤 2：让巴鲁克失言（学会他的秘密）
sm.process_intent(make_intent("baruk", "offer_comfort", topic="活着的人更需要那口气"))
sm.process_intent(make_intent("baruk", "probe_conflict", involves=[],
                              topic="墙上的符文暗语，矿工的求救，你的族人和精灵承诺", risk="high"))
# 此时失言事件链已把 baruk→liana 推到 -65（低于 -60），liana→baruk 仅 -40
test("模拟推进：baruk→liana 已 < -60",
     sm.npcs["baruk"].attitudes.get("liana") < -60,
     f"实际: {sm.npcs['baruk'].attitudes.get('liana')}")
# 只有一侧恶化，不应提前触发血债血偿（需双方互相 < -60）
test("模拟推进：半程未提前触发（liana→baruk 仍 ≥ -60）",
     sm.check_ending() is None, f"实际: {sm.check_ending()}")
# 步骤 3：抬高 Liana 信任到 64+（comfort 5 次：28 → 68）
for _ in range(5):
    sm.process_intent(make_intent("liana", "offer_comfort", topic="你也尽力了"))
# 步骤 4：向 Liana 揭示"巴鲁克的秘密"4 次，每次成功 liana→baruk -15（-15 → -75）
for _ in range(4):
    sm.process_intent(make_intent("liana", "reveal_secret", involves=["baruk"],
                                  topic="关于巴鲁克的真相"))
test("模拟推进：liana→baruk 已 < -60",
     sm.npcs["liana"].attitudes.get("baruk") < -60,
     f"实际: {sm.npcs['liana'].attitudes.get('baruk')}")
ending = sm.check_ending()
test("模拟推进：血债血偿触发", ending == "blood_debt", f"实际: {ending}")

# ---- 记录：挑拨离间公式重平衡后仍需积累，初始状态无法直接离间 Baruk ----
sm2 = StateMachine()
res = sm2.process_intent(make_intent("baruk", "sow_discord", involves=["liana"],
                                     topic="精灵的谎言", tone="insinuating", risk="high"))
test("说明：初始状态挑拨 Baruk 不会成功（新公式仍需积累）",
     res.get("discord_success") is not True,
     f"discord_success: {res.get('discord_success')}")

# ============================================================
# 新增可达性验证 1：安慰 Baruk → baruk→liana 从 -30 升到 > -20（真理之殿通路）
# ============================================================
print(bold("\n── 新增验证：安慰 Baruk 提升 baruk→liana（真理之殿通路）──"))
smc = StateMachine()
for _ in range(3):
    smc.process_intent(make_intent("baruk", "offer_comfort", topic="你不必替他们背着那些怨"))
test("新增：3 次安慰后 baruk→liana 从 -30 升到 > -20",
     smc.npcs["baruk"].attitudes.get("liana") > -20,
     f"实际: {smc.npcs['baruk'].attitudes.get('liana')}")

# ============================================================
# 新增可达性验证 2：挑拨离间从零创造敌意（新公式）
# ============================================================
print(bold("\n── 新增验证：挑拨离间从零创造敌意 ──"))
smd = StateMachine()
# 用抵抗力最低的 Rog（35）挑拨玛格丽特（初始态度 0，可视为"从零"）
for _ in range(4):
    smd.process_intent(make_intent("rog", "offer_comfort", topic="你也累了"))       # 30 → 62
for _ in range(3):
    smd.process_intent(make_intent("margaret", "ask_backstory", involves=["rog"],
                                   topic="关于罗格"))                                 # 建立 recency=3
resd = smd.process_intent(make_intent("rog", "sow_discord", involves=["margaret"],
                                      topic="教会的沉默", tone="insinuating", risk="high"))
test("新增：挑拨 Rog 成功（信任 62 + 近期互动）", resd.get("discord_success") is True,
     f"discord_success: {resd.get('discord_success')}")
test("新增：从零挑拨出敌意（rog→margaret 由 0 转负）",
     smd.npcs["rog"].attitudes.get("margaret") < 0,
     f"实际: {smd.npcs['rog'].attitudes.get('margaret')}")

# ============================================================
# 新增验证 3：新火种（矮人+兽人联盟）流程可达（公开站队 + 安慰建立正向关系）
# ============================================================
print(bold("\n── 新增验证：新火种（baruk↔rog > 60）流程可达 ──"))
sm3 = StateMachine()
for _ in range(4):
    sm3.advance_stage()
# 公开站队：Rog 支持 Baruk ×4 → baruk→rog 25→65
for _ in range(4):
    sm3.process_intent(make_intent("rog", "take_sides", involves=["baruk"], topic="我信你"))
# 公开站队：Baruk 支持 Rog ×4 → rog→baruk 25→65
for _ in range(4):
    sm3.process_intent(make_intent("baruk", "take_sides", involves=["rog"], topic="兄弟"))
# 让 Baruk 进入 vulnerable 以便失言（安慰），再追问墙上符文
sm3.process_intent(make_intent("baruk", "offer_comfort", topic="活着的人更需要那口气"))
sm3.process_intent(make_intent("baruk", "probe_conflict", involves=[],
                               topic="墙上的符文暗语，矿工的求救，你的族人和精灵承诺", risk="high"))
test("新增：新火种前置 baruk→rog > 60",
     sm3.npcs["baruk"].attitudes.get("rog") > 60,
     f"实际: {sm3.npcs['baruk'].attitudes.get('rog')}")
test("新增：新火种前置 rog→baruk > 60",
     sm3.npcs["rog"].attitudes.get("baruk") > 60,
     f"实际: {sm3.npcs['rog'].attitudes.get('baruk')}")
test("新增：baruk_wall_rune 已暴露", "baruk_wall_rune" in sm3.npcs["baruk"].revealed_secrets)
test("新增：新火种触发", sm3.check_ending() == "new_flame", f"实际: {sm3.check_ending()}")

# ============================================================
# 测试 3：冲突检测（互斥性）
# ============================================================
print(bold("\n── 结局测试：冲突检测（互斥性）──"))

# 针对每个结局构造的状态，只应命中自身结局条件
for eid, _ in CONDITIONS:
    sm = build_ending_state(eid)
    hit = matches_only(sm, eid)
    test(f"构造[{ENDING_NAMES[eid]}] 只满足自身条件", hit == [eid],
         f"同时命中的条件: {hit}")
    test(f"构造[{ENDING_NAMES[eid]}] check_ending 返回自身",
         sm.check_ending() == eid, f"实际: {sm.check_ending()}")

# 任务重点：构造满足 truth_temple 的状态，断言它不会同时满足其他结局
sm = build_ending_state("truth_temple")
test("真理之殿状态不同时满足血债血偿", not cond_blood_debt(sm))
test("真理之殿状态不同时满足新火种", not cond_new_flame(sm))
test("真理之殿状态不同时满足谁都没被救赎", not cond_no_redemption(sm))
test("真理之殿状态不同时满足弑神者", not cond_godslayer(sm))

# ============================================================
# 汇总
# ============================================================
print(bold(f"\n{'=' * 60}"))
print(bold(f"  结局测试结果: {green(str(passed))} 通过, {red(str(failed))} 失败"))
print(bold(f"  总计: {passed + failed} 项"))
print(bold(f"{'=' * 60}"))

# 附：状态机设计缺口修复说明（供设计参考）
print(bold("\n── 已修复的状态机缺口（设计参考）──"))
print("  1. 真理之殿：安慰 Baruk 成功时 baruk→liana +5（被善待后怨气松动），")
print("     3 次安慰即可把 -30 升到 > -20（新增验证通过）。")
print("  2. 新火种：站队通路（被支持 NPC 对支持者 +10）与安慰情绪共鸣（+3）叠加，")
print("     baruk↔rog 可从 25 升到 60+，配合失言暴露墙上暗语即可触发（新增验证通过）。")
print("  3. 挑拨离间：公式重平衡（信任 + 抵抗力 + 已有敌意 + 近期互动），")
print("     从零挑拨成为可能但需信任积累；且同一对目标第三次成功后概率 ×0.6 防无限刷。")
print("  4. reveal_secret：新增知识校验——玩家只有真正听过/掌握秘密（失言、记忆、知识来源）")
print("     才可生效；否则被识破为编造（trust -10）。同时新增 known_secret_sources 追踪。")

if failed > 0:
    sys.exit(1)
