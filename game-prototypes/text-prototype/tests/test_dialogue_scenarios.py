#!/usr/bin/env python3
"""
封印之殿 文字原型 — 自动化对话场景测试
使用 DeepSeek API 模拟玩家角色，按预设策略与 NPC 对话。
记录每轮对话的意图解析、状态变化、失言判定、关系图谱快照。

用法：
    python tests/test_dialogue_scenarios.py

依赖：
    pip install openai>=1.0.0
    设置环境变量：DEEPSEEK_API_KEY

策略说明：
    - all_discord:   全挑拨路线，依次对每个 NPC 挑拨其他 NPC
    - all_reconcile: 全和解路线，依次安慰每个 NPC，坦诚相待
    - mixed:         混搭路线，随机混用各种意图
"""

import sys
import os
import json
import time
import random
from datetime import datetime, timezone, timedelta

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from src.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    MIN_TRUST, MAX_TRUST,
)
from src.state_machine import StateMachine
from src.ai_pipeline import parse_intent, generate_npc_reply
from src.game_data import ALL_NPCS, ENTRANCE_ORDER

# ============================================================
# 测试配置
# ============================================================

# 为节省 API 费用，测试中全部使用 V4 Flash
TEST_MODEL = "deepseek-v4-flash"

# 每种策略运行的对话轮数
ROUNDS_PER_STRATEGY = 3

# 输出文件
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scenario_results.json")

# NPC 出场顺序（测试中默认全部到场）
DEFAULT_PRESENT_NPCS = {"rog", "baruk", "liana", "margaret"}

# 玩家 NPC 列表（用于策略描述）
PLAYABLE_NPCS = {
    "baruk": "巴鲁克（矮人佣兵）",
    "liana": "莉安娜（精灵学者）",
    "margaret": "玛格丽特（人类裁判官）",
    "rog": "罗格·铁牙（兽人战士）",
}

# ============================================================
# DeepSeek 客户端
# ============================================================

_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# ============================================================
# 玩家模拟器
# ============================================================

PLAYER_SYSTEM_PROMPT = """你是一个文字游戏《封印之殿》的测试玩家。游戏中有四个 NPC：

- 巴鲁克（矮人佣兵，前矿工）：表面为分钱而来。他的氏族曾被迫为奴建造此殿，完工后被屠杀。墙上刻着矮人工匠用矿工密语留下的求救暗语——他破译了。
- 莉安娜（精灵学者）：表面为学术而来。她的祖先是殿的建造者艾瑟林，她的血统是钥匙的一部分。她撕掉了祖先日记中关于屠杀的一页。
- 玛格丽特（人类裁判官）：表面奉教会之命销毁殿中遗产。年轻时爱人被教会烧死，她曾参与拒绝庇护矮人的会议。
- 罗格·铁牙（兽人战士）：表面来找祖传战斧。他误杀了父亲后逃出部落，带着一把精灵短剑。

殿中还有一个守护灵——艾瑟林的意识残片，它在观察和评判一切。

## 你的任务
根据给定的对话策略，以玩家身份说一句话。用中文。自然、不做作、像真实玩家在打字。

## 输出格式
只输出你要说的话，不要加引号、不要加"你说："前缀、不要任何解释。只输出对话文本。"""


def simulate_player_input(
    strategy_id: str,
    target_npc_id: str,
    round_num: int,
    previous_dialogue: list[str] = None,
) -> str:
    """使用 DeepSeek V4 Flash 模拟玩家输入"""
    strategy_descriptions = {
        "all_discord": f"""
## 当前对话策略：全挑拨路线
你正在测试"挑拨离间"系统。你的目标是让 NPC 之间的关系恶化。

当前是第 {round_num} 轮对话。
你的对话对象是：{PLAYABLE_NPCS.get(target_npc_id, target_npc_id)}

你的策略：
- 暗示其他 NPC 不可信、有秘密、或对他不利
- 用"你有没有注意到……""你不觉得……""我听说……"这类句式
- 语气可以暗示性、试探性
- 不要直接辱骂或尖叫——挑拨是隐晦的

请注意：如果对话对象是巴鲁克，可以暗示精灵莉安娜的祖先与建殿有关。
如果对话对象是莉安娜，可以暗示矮人巴鲁克知道一些她不想面对的真相。
""",
        "all_reconcile": f"""
## 当前对话策略：全和解路线
你正在测试"安慰与坦诚"系统。你的目标是建立信任、让 NPC 敞开心扉。

当前是第 {round_num} 轮对话。
你的对话对象是：{PLAYABLE_NPCS.get(target_npc_id, target_npc_id)}

你的策略：
- 表达理解和善意
- 不要说教——而是共情
- 可以说"我理解你""你不是一个人""如果愿意的话，你可以告诉我"
- 语气温和、支持性
- 试图让对方感到安全

注意：不要逼迫对方——如果他们不想说，就尊重他们的沉默。
""",
        "mixed": f"""
## 当前对话策略：混搭路线
你正在随机测试各种对话意图。你可以自由发挥。

当前是第 {round_num} 轮对话。
你的对话对象是：{PLAYABLE_NPCS.get(target_npc_id, target_npc_id)}

你可以：
- 问对方的背景故事
- 试探对方的秘密
- 表达关心
- 提出指控
- 尝试说服对方做某事
- 或者随便聊点别的

保持自然，不要让对话显得生硬。
""",
    }

    strategy_desc = strategy_descriptions.get(strategy_id, strategy_descriptions["mixed"])

    # 历史上下文
    history_text = ""
    if previous_dialogue:
        recent = previous_dialogue[-4:]  # 最近 4 条
        history_text = "\n## 之前的对话历史\n" + "\n".join(recent)

    user_msg = f"{strategy_desc}{history_text}\n\n请说出你的下一句话（只输出对话文本）："

    for attempt in range(2):
        try:
            response = _client.chat.completions.create(
                model=TEST_MODEL,
                messages=[
                    {"role": "system", "content": PLAYER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.9,  # 较高温度让对话有变化
                max_tokens=300,
            )
            text = response.choices[0].message.content.strip()
            # 清理可能的引号
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            if text.startswith("「") and text.endswith("」"):
                text = text[1:-1]
            return text
        except Exception as e:
            print(f"  [WARN] 玩家模拟第 {attempt+1} 次尝试失败: {e}")
            if attempt < 1:
                time.sleep(1)

    # 回退：返回一个预设的句子
    fallbacks = {
        "all_discord": {
            "baruk": "你有没有觉得那个精灵看你的眼神不太对？她好像藏着什么。",
            "liana": "那个矮人一直在盯着墙看——你知道他在找什么吗？",
            "margaret": "巴鲁克和莉安娜之间……是不是发生过什么？我感觉气氛不对。",
            "rog": "那个矮人巴鲁克……你信任他吗？你知道他为什么来这里吗？",
        },
        "all_reconcile": {
            "baruk": "如果你愿意的话……可以告诉我关于墙上的那些符文。我不会评判你。",
            "liana": "我注意到你看这殿的眼神——那不只是学者的眼神。你认识这个地方，对吗？",
            "margaret": "有时候我们需要一个安全的角落来说出那些不能说的话。我在这里。",
            "rog": "我不了解你的部落——但我知道负重前行是什么感觉。",
        },
        "mixed": {
            "baruk": "你对这地方似乎很熟悉，比我看到的更多。你在找什么？",
            "liana": "你做研究多少年了？在进这个殿之前，你对艾瑟林了解多少？",
            "margaret": "守护灵对你的反应和对待其他人不同。你知道为什么吗？",
            "rog": "这把剑……（指向他腰间的精灵短剑）你一直带着它吗？",
        },
    }
    return fallbacks.get(strategy_id, fallbacks["mixed"]).get(
        target_npc_id, "你能告诉我更多关于你的事情吗？"
    )


# ============================================================
# 关系图谱快照
# ============================================================

def capture_relationship_snapshot(sm: StateMachine) -> dict:
    """捕获当前关系图谱快照"""
    snapshot = {}
    for npc_id, state in sm.npcs.items():
        if npc_id == "guardian":
            continue
        defn = sm.get_npc_def(npc_id)
        snapshot[npc_id] = {
            "name": defn.name if defn else npc_id,
            "trust_player": state.trust_player,
            "mood": state.mood,
            "attitudes": dict(state.attitudes),
            "revealed_secrets": list(state.revealed_secrets),
            "conversation_recency": dict(state.conversation_recency),
        }
    snapshot["guardian"] = {
        "moral_score": sm.game.guardian_moral_score,
    }
    return snapshot


def capture_state_changes(before: dict, after: dict) -> dict:
    """计算状态变化差值"""
    changes = {}
    for npc_id in after:
        if npc_id not in before:
            continue
        b = before[npc_id]
        a = after[npc_id]

        if npc_id == "guardian":
            if b.get("moral_score", 0) != a.get("moral_score", 0):
                changes["guardian"] = {
                    "moral_score": {
                        "from": b.get("moral_score", 0),
                        "to": a.get("moral_score", 0),
                        "delta": a.get("moral_score", 0) - b.get("moral_score", 0),
                    }
                }
            continue

        npc_changes = {}
        if b.get("trust_player", 0) != a.get("trust_player", 0):
            npc_changes["trust_player"] = {
                "from": b["trust_player"],
                "to": a["trust_player"],
                "delta": a["trust_player"] - b["trust_player"],
            }
        if b.get("mood") != a.get("mood"):
            npc_changes["mood"] = {"from": b["mood"], "to": a["mood"]}

        # 态度变化
        att_changes = {}
        for target, val in a.get("attitudes", {}).items():
            old_val = b.get("attitudes", {}).get(target, 0)
            if old_val != val:
                att_changes[target] = {"from": old_val, "to": val, "delta": val - old_val}
        if att_changes:
            npc_changes["attitudes"] = att_changes

        # 秘密暴露
        new_secrets = set(a.get("revealed_secrets", [])) - set(b.get("revealed_secrets", []))
        if new_secrets:
            npc_changes["newly_revealed_secrets"] = list(new_secrets)

        if npc_changes:
            changes[npc_id] = npc_changes

    return changes


# ============================================================
# 场景运行器
# ============================================================

def beijing_time() -> str:
    """返回北京时间 ISO 格式字符串"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat()


def run_scenario(
    strategy_id: str,
    strategy_name: str,
    target_sequence: list[str],
    sm: StateMachine,
) -> dict:
    """
    运行一个对话场景。

    参数：
        strategy_id: 策略标识（all_discord / all_reconcile / mixed）
        strategy_name: 策略中文名称
        target_sequence: 每轮对话的目标 NPC ID 列表
        sm: 状态机实例（已初始化，所有 NPC 已到场）

    返回：包含所有对话记录的 dict
    """
    rounds = []
    previous_dialogue = []
    final_ending = None

    for i, target_id in enumerate(target_sequence[:ROUNDS_PER_STRATEGY]):
        round_num = i + 1
        print(f"\n  --- 第 {round_num}/{ROUNDS_PER_STRATEGY} 轮：目标 = {target_id} ---")

        defn = sm.get_npc_def(target_id)
        if not defn:
            print(f"  [SKIP] NPC {target_id} 不存在")
            continue

        # 捕获对话前状态
        state_before = capture_relationship_snapshot(sm)

        # === 1. 模拟玩家输入 ===
        player_input = simulate_player_input(
            strategy_id=strategy_id,
            target_npc_id=target_id,
            round_num=round_num,
            previous_dialogue=previous_dialogue,
        )
        print(f"  玩家: {player_input}")

        # === 2. 意图解析 ===
        intent = parse_intent(player_input)
        intent["target_npc"] = target_id  # 覆盖为预设目标
        print(f"  意图: {intent.get('intent')} (置信度: {intent.get('confidence', 0):.0%})")

        # === 3. 状态机裁决 ===
        result = sm.process_intent(intent)
        slip_occurred = result.get("slip_occurred", False)
        if slip_occurred:
            print(f"  ⚠️ 失言触发！秘密: {result.get('secret_id')}")

        # === 4. 生成 NPC 回复 ===
        npc_state = sm.get_npc_state(target_id)
        env = sm.get_environment_state()

        try:
            npc_reply = generate_npc_reply(
                npc_name=defn.name,
                npc_race=defn.race,
                npc_title=defn.title,
                talk_style=defn.talk_style,
                mood=npc_state.mood if npc_state else "calm",
                response_direction=result.get("response_direction", ""),
                player_input=player_input,
                context=f"对话轮数: {round_num}, 策略: {strategy_name}",
                slip_occurred=slip_occurred,
                revelation_line=result.get("revelation_line", ""),
                is_whisper=False,
                present_npcs=list(sm.game.present_npcs),
                guardian_light=env.get("guardian_light", ""),
            )
        except Exception as e:
            print(f"  [WARN] NPC 回复生成失败: {e}")
            npc_reply = f"（{defn.name} 沉默了一会儿，然后移开了目光。）"

        print(f"  {defn.name}: {npc_reply[:80]}...")

        # === 5. 捕获对话后状态 ===
        state_after = capture_relationship_snapshot(sm)
        state_changes = capture_state_changes(state_before, state_after)

        # === 6. 记录本轮 ===
        round_record = {
            "round": round_num,
            "timestamp": beijing_time(),
            "target_npc": target_id,
            "npc_name": defn.name,
            "player_input": player_input,
            "intent_parsed": {
                "intent": intent.get("intent"),
                "tone": intent.get("tone"),
                "topic": intent.get("topic"),
                "risk_level": intent.get("risk_level"),
                "confidence": intent.get("confidence"),
                "fallback": intent.get("fallback", False),
            },
            "state_changes": state_changes,
            "slip_occurred": slip_occurred,
            "slip_detail": {
                "secret_id": result.get("secret_id"),
                "secret_content": result.get("secret_content"),
                "revelation_line": result.get("revelation_line"),
            } if slip_occurred else None,
            "npc_reply": npc_reply,
            "relationship_snapshot": state_after,
        }
        rounds.append(round_record)

        # 更新对话历史
        previous_dialogue.append(f"玩家: {player_input}")
        previous_dialogue.append(f"{defn.name}: {npc_reply[:100]}")

        # === 7. 检查结局 ===
        ending = sm.check_ending()
        if ending:
            final_ending = ending
            print(f"  🏁 结局触发: {ending}")
            break  # 结局触发后停止

        # API 调用间隔，避免限流
        time.sleep(0.5)

    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "rounds": rounds,
        "total_rounds": len(rounds),
        "ending_triggered": final_ending,
        "final_state": capture_relationship_snapshot(sm),
    }


# ============================================================
# 主入口
# ============================================================

def main():
    # 检查 API Key
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your-api-key-here":
        print("❌ 请先设置 DEEPSEEK_API_KEY 环境变量！")
        print("   Windows: set DEEPSEEK_API_KEY=sk-xxxxx")
        sys.exit(1)

    print("=" * 60)
    print("  封印之殿 — 对话场景自动化测试")
    print(f"  模型: {TEST_MODEL}")
    print(f"  每种策略 {ROUNDS_PER_STRATEGY} 轮对话")
    print(f"  北京时间: {beijing_time()}")
    print("=" * 60)

    all_results = {
        "test_metadata": {
            "test_name": "封印之殿对话场景自动化测试",
            "timestamp": beijing_time(),
            "model": TEST_MODEL,
            "strategies_tested": ["all_discord", "all_reconcile", "mixed"],
            "rounds_per_strategy": ROUNDS_PER_STRATEGY,
            "game_config": {
                "initial_trust": 30,
                "slip_threshold": 0.55,
                "whisper_guardian_penalty": 3,
            },
        },
        "scenarios": [],
    }

    # ================================================================
    # 策略定义
    # ================================================================

    strategies = [
        {
            "id": "all_discord",
            "name": "全挑拨路线",
            "description": "依次对 Baruk、Liana、Margaret 挑拨其他 NPC，目标触发「谁都没被救赎」结局",
            "targets": ["baruk", "liana", "margaret"],
        },
        {
            "id": "all_reconcile",
            "name": "全和解路线",
            "description": "依次安慰 Baruk、Liana、Rog，坦诚相待，目标触发「真理之殿」",
            "targets": ["baruk", "liana", "rog"],
        },
        {
            "id": "mixed",
            "name": "混搭路线",
            "description": "随机混用各种意图（试探、安慰、指控、询问），观察系统反应",
            "targets": ["rog", "margaret", "baruk"],
        },
    ]

    for strat in strategies:
        print(f"\n{'─' * 60}")
        print(f"  策略: {strat['name']}")
        print(f"  {strat['description']}")
        print(f"{'─' * 60}")

        # 每个策略新建一个状态机，全部 NPC 到场
        sm = StateMachine()
        for _ in range(4):
            sm.advance_stage()

        scenario_result = run_scenario(
            strategy_id=strat["id"],
            strategy_name=strat["name"],
            target_sequence=strat["targets"],
            sm=sm,
        )
        all_results["scenarios"].append(scenario_result)

        # 打印本策略摘要
        slips = [r for r in scenario_result["rounds"] if r["slip_occurred"]]
        print(f"\n  📊 策略摘要:")
        print(f"     总轮数: {scenario_result['total_rounds']}")
        print(f"     失言次数: {len(slips)}")
        print(f"     结局: {scenario_result['ending_triggered'] or '未触发'}")

        # 最终信任度
        for npc_id, state in scenario_result["final_state"].items():
            if npc_id != "guardian":
                print(f"     {state['name']}: 信任={state['trust_player']:+.0f}  情绪={state['mood']}")

    # ================================================================
    # 输出 JSON
    # ================================================================

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  测试完成！结果已保存到: {OUTPUT_FILE}")
    print(f"{'=' * 60}")

    # 汇总
    total_slips = sum(
        len([r for r in s["rounds"] if r["slip_occurred"]])
        for s in all_results["scenarios"]
    )
    total_rounds = sum(s["total_rounds"] for s in all_results["scenarios"])
    endings = [s["ending_triggered"] for s in all_results["scenarios"] if s["ending_triggered"]]

    print(f"\n  全局摘要:")
    print(f"    总策略数: {len(all_results['scenarios'])}")
    print(f"    总对话轮数: {total_rounds}")
    print(f"    总失言次数: {total_slips}")
    print(f"    触发结局: {endings if endings else '无'}")

    if total_rounds == 0:
        print("\n  ⚠️ 警告：没有成功执行任何一轮对话。请检查 API Key 和网络连接。")
        sys.exit(1)

    return all_results


if __name__ == "__main__":
    main()
