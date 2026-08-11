#!/usr/bin/env python3
"""
封印之殿 — 文字原型
纯终端对话驱动游戏。验证"失言系统"和"说话改变世界"机制。
"""
import sys
sys.path.insert(0, ".")

from src.game_data import ALL_NPCS, ENTRANCE_ORDER
from src.state_machine import StateMachine
from src.ai_pipeline import parse_intent, generate_npc_reply, generate_guardian_ambient
from src.config import DEBUG_MODE
from src import display

# ================================================================
# 游戏主循环
# ================================================================

class Game:
    def __init__(self):
        self.sm = StateMachine()
        self.current_target = "guardian"  # 默认对话对象
        self.running = True
        self._pacing_hint_stage = None   # 出场节奏提示已显示过的阶段（每阶段只提示一次）

    def run(self):
        """游戏入口"""
        display.clear_screen()
        display.print_title()
        self._intro()
        self._stage_0()

        while self.running:
            # 检查结局
            ending = self.sm.check_ending()
            if ending:
                self._trigger_ending(ending)
                break

            # 显示环境
            env = self.sm.get_environment_state()
            display.print_environment(env)

            # 显示可视线索
            hints = self.sm.get_visible_hints()
            if hints:
                for h in hints[:3]:  # 最多 3 条
                    display.print_hint(h)
                print()

            # 获取输入
            user_input = display.get_input()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                self._handle_command(user_input)
                continue

            # 普通对话
            self._handle_dialogue(user_input)

            # 出场节奏：充分对话后温和提示可等待推进（每阶段只提示一次，不刷屏）
            hint = self.sm.get_pacing_hint()
            if hint and self._pacing_hint_stage != self.sm.game.current_stage:
                self._pacing_hint_stage = self.sm.game.current_stage
                display.print_narrative(hint)

    # ================================================================
    # 介绍
    # ================================================================

    def _intro(self):
        display.print_narrative("""
黑暗。然后是光。

你睁开眼睛，发现自己站在一座圆形的石殿中。殿顶高得看不到尽头，
墙壁上刻满了陌生文字的浮雕。中央悬浮着一团发光的人形轮廓——
它没有脸，但你能感觉到它在看着你。不，不是在评判你。
更像是在……好奇。

一个声音在你脑海中响起。不是耳朵听到的——是直接刻在意识里的：
""")
        display.print_npc_dialogue("guardian", "守护灵",
            "一千年了。你是第一个无关之人。你不属于矮人的矿道、"
            "精灵的古卷、人类的神殿，也不属于兽人的战场。你是谁？"
        )

    def _stage_0(self):
        """阶段 0：独处"""
        desc = ENTRANCE_ORDER[0]["description"]
        display.print_stage_transition(f"[阶段 0] {desc}")
        display.print_narrative(
            "守护灵的光在你周围流动，像在嗅你的气味。"
            "它的声音再次响起——这次不是在脑海中，而是在空气中。"
        )
        display.print_npc_dialogue("guardian", "守护灵",
            "其他人在路上了。我能感觉到他们——四个灵魂，四种债。"
            "在他们到达之前……你可以问我任何事。或者你可以等待。"
        )
        display.print_help()

    # ================================================================
    # 命令处理
    # ================================================================

    def _handle_command(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "/h":
            display.print_help()

        elif command == "/w":
            npc_id = self._resolve_npc(arg)
            if npc_id and npc_id in self.sm.game.present_npcs:
                self.sm.game.whisper_mode = True
                self.sm.game.whisper_target = npc_id
                self.current_target = npc_id
                defn = self.sm.get_npc_def(npc_id)
                display.print_whisper_mode(defn.name)
            elif npc_id and npc_id not in self.sm.game.present_npcs:
                print(f"  {arg} 还没到场。")
            else:
                print(f"  '/w baruk' — 和巴鲁克悄悄话。可用 NPC: {self.sm.game.present_npcs}")

        elif command == "/p":
            self.sm.game.whisper_mode = False
            self.sm.game.whisper_target = None
            print("  你回到了人群中。所有人都在看着你——他们在猜你刚才在密谈什么。")

        elif command == "/m":
            known = {}
            for npc_id in self.sm.game.present_npcs:
                state = self.sm.npcs[npc_id]
                defn = self.sm.get_npc_def(npc_id)
                if defn and state.revealed_secrets:
                    known[npc_id] = [
                        next((s.content for s in defn.secrets if s.id == sid), "?")
                        for sid in state.revealed_secrets
                    ]
            display.print_memory_panel(known, {})

        elif command == "/e":
            env = self.sm.get_environment_state()
            display.print_environment(env)
            display.print_debug(f"守护灵评分: {env['score']:+.0f}")
            for npc_id in self.sm.game.present_npcs:
                state = self.sm.npcs[npc_id]
                defn = self.sm.get_npc_def(npc_id)
                if defn:
                    display.print_debug(
                        f"{defn.name}: 信任{state.trust_player:+.0f} "
                        f"情绪={state.mood} "
                        f"秘密已暴露={len(state.revealed_secrets)}/{len(defn.secrets)}"
                    )

        elif command in ("/n", "/wait"):
            new_npc = self.sm.advance_stage()
            if new_npc:
                stage = self.sm.game.current_stage
                desc = ENTRANCE_ORDER[stage]["description"]
                defn = self.sm.get_npc_def(new_npc)
                display.print_stage_transition(f"[阶段 {stage}] {desc}")
                if defn:
                    display.print_npc_dialogue(new_npc, defn.name,
                        self._get_entrance_line(new_npc))
                # 环境变化
                env = self.sm.get_environment_state()
                display.print_environment(env)
            else:
                print("  所有人已到场。没有更多人了。")

        elif command == "/q":
            self.running = False
            print("\n  殿门永远在你身后关上了。\n")

        else:
            print(f"  未知命令: {command}。输入 /h 查看帮助。")

    # ================================================================
    # 对话处理
    # ================================================================

    def _handle_dialogue(self, user_input: str):
        """处理玩家自由文本对话"""
        # 确定对话目标
        target = self.current_target
        if self.sm.game.whisper_mode:
            target = self.sm.game.whisper_target

        if target not in self.sm.game.present_npcs and target != "guardian":
            # 尝试在输入中识别目标
            for npc_id in self.sm.game.present_npcs:
                defn = self.sm.get_npc_def(npc_id)
                if defn and defn.name in user_input:
                    target = npc_id
                    self.current_target = npc_id
                    break

        defn = self.sm.get_npc_def(target)
        if not defn:
            if self.sm.game.present_npcs:
                target = next(iter(self.sm.game.present_npcs))
                self.current_target = target
                defn = self.sm.get_npc_def(target)
            else:
                target = "guardian"
                self.current_target = "guardian"
                defn = self.sm.get_npc_def("guardian")

        # === 构建语境 ===
        context_parts = [
            f"当前在场 NPC: {', '.join(self.sm.game.present_npcs)}",
            f"对话对象: {defn.name}",
            f"对话模式: {'悄悄话' if self.sm.game.whisper_mode else '公开对话'}",
        ]
        # 添加最近的交互
        for ri in self.sm.game.recent_interactions[-5:]:
            context_parts.append(f"最近: {ri}")
        context = "\n".join(context_parts)

        # === 1. 意图解析 ===
        if DEBUG_MODE:
            print()
        intent = parse_intent(user_input, context)

        if DEBUG_MODE:
            display.print_debug(f"意图: {intent.get('intent')} → {intent.get('target_npc') or 'auto'} "
                                f"(置信度: {intent.get('confidence', 0):.0%})")
            if intent.get("fallback"):
                display.print_debug("⚠️ 使用关键词回退")

        # 如果 AI 指定了目标和当前目标不同，切换
        if intent.get("target_npc") and intent["target_npc"] in self.sm.game.present_npcs:
            if intent["target_npc"] != target and not self.sm.game.whisper_mode:
                target = intent["target_npc"]
                self.current_target = target
                defn = self.sm.get_npc_def(target)
                if DEBUG_MODE:
                    display.print_debug(f"切换对话对象 → {defn.name}")

        # 确保 target 有效
        intent["target_npc"] = target

        # === 2. 状态机裁决 ===
        result = self.sm.process_intent(intent)

        if result.get("result") == "error":
            print(f"  {result.get('message', '错误')}")
            return

        # === 3. 环境反馈 ===
        env = self.sm.get_environment_state()
        guardian_text = generate_guardian_ambient(
            self.sm.game.guardian_moral_score,
            self.sm.game.recent_interactions
        )
        display.print_narrative(guardian_text)

        # === 4. 生成 NPC 回复 ===
        npc_state = self.sm.get_npc_state(target)
        response = generate_npc_reply(
            npc_name=defn.name,
            npc_race=defn.race,
            npc_title=defn.title,
            talk_style=defn.talk_style,
            mood=npc_state.mood if npc_state else "calm",
            response_direction=result.get("response_direction", ""),
            player_input=user_input,
            context=context,
            slip_occurred=result.get("slip_occurred", False),
            revelation_line=result.get("revelation_line", ""),
            is_whisper=self.sm.game.whisper_mode,
            present_npcs=list(self.sm.game.present_npcs) if not self.sm.game.whisper_mode else [],
            guardian_light=env["guardian_light"],
        )
        display.print_npc_dialogue(target, defn.name, response,
                                   is_whisper=self.sm.game.whisper_mode)

        # === 5. 失言特殊处理 ===
        if result.get("slip_occurred"):
            print()
            display.print_narrative(Color.RED + "⚠️" + Color.RESET +
                f" {defn.name} 说了不该说的话。他的防线在这一瞬间崩塌了。")
            # 如果有涉及的其他 NPC 在场，他们会有反应
            for involved_id in intent.get("involves", []):
                if involved_id in self.sm.game.present_npcs:
                    inv_defn = self.sm.get_npc_def(involved_id)
                    if inv_defn:
                        display.print_npc_dialogue(involved_id, inv_defn.name,
                            self._get_reaction_line(involved_id, result.get("secret_id", "")))

        # === 6. 其他 NPC 自发反应 ===
        if not self.sm.game.whisper_mode and result.get("risk_level") == "high":
            # 高风险对话后，随机一个其他 NPC 插话
            others = [n for n in self.sm.game.present_npcs if n != target and n != "guardian"]
            if others:
                import random
                reactor_id = random.choice(others)
                reactor_defn = self.sm.get_npc_def(reactor_id)
                if reactor_defn:
                    reactor_state = self.sm.npcs[reactor_id]
                    reaction = self._get_random_reaction(reactor_id, target, result)
                    display.print_npc_dialogue(reactor_id, reactor_defn.name, reaction)
                    # 显示 NPC 的微反应
                    display.print_hint(f"（{reactor_defn.name} 说这话时，目光没有离开过 {defn.name}。）")

    # ================================================================
    # 辅助
    # ================================================================

    def _resolve_npc(self, name: str) -> str:
        """根据名字解析 NPC ID"""
        name = name.lower().strip()
        mapping = {
            "baruk": "baruk", "巴鲁克": "baruk", "矮人": "baruk",
            "liana": "liana", "莉安娜": "liana", "精灵": "liana",
            "margaret": "margaret", "玛格丽特": "margaret", "牧师": "margaret",
            "rog": "rog", "罗格": "rog", "兽人": "rog",
            "guardian": "guardian", "守护灵": "guardian",
        }
        return mapping.get(name, "")

    def _get_entrance_line(self, npc_id: str) -> str:
        """NPC 入场台词"""
        lines = {
            "rog": "（他用力推开石门的最后一寸，粗重地喘着气，眼睛在殿内扫了一圈，停在了守护灵上）……这是什么地方？你是谁？",
            "baruk": "（他没有看任何人。他一进门就盯着墙——那些刻痕。他的下巴绷紧了，然后他慢慢走过去，把粗糙的手掌按在墙面上）",
            "liana": "（她推开门，仰头看见殿顶的浮雕——那一瞬间，她的嘴张开了。不是因为美——是因为某种认出。然后她看到了守护灵）……这建筑……这风格……这是第几纪元？",
            "margaret": "（她站在门口——她的左手擦过脸上干涸的血迹，右手拿着法杖。她的眼睛直接锁定了守护灵。她的下巴收紧了一寸）",
        }
        return lines.get(npc_id, "（沉默地走了进来，环顾四周。）")

    def _get_reaction_line(self, npc_id: str, secret_id: str) -> str:
        """NPC 对失言暴露的即时反应"""
        reactions = {
            "liana": {
                "baruk_wall_rune": "（莉安娜的脸颊失去了血色。她没说话——但她的嘴唇轻轻动了一下，像在念一个她不想承认的名字。）",
            },
            "baruk": {
                "liana_ancestry": "（Baruk 慢慢转过了头。他没有表情——但他的手松开了握紧的拳头。不是因为原谅了——是因为他终于听到了。）",
            },
            "margaret": {
                "baruk_wall_rune": "（玛格丽特低下了头。她的法杖敲在石地上，声音空旷——但她没有抬头。）",
            },
        }
        return reactions.get(npc_id, {}).get(secret_id,
            f"（{self.sm.get_npc_def(npc_id).name if self.sm.get_npc_def(npc_id) else '他们'} 的表情微微变化了一瞬。）")

    def _get_random_reaction(self, reactor_id: str, target_id: str, result: dict) -> str:
        """随机 NPC 对高风险对话的反应"""
        reactions = [
            "你们在说什么？",
            "……（目光在你们之间移动，什么都没说）",
            "有些话，也许不该在所有人面前说。",
        ]
        if result.get("slip_occurred"):
            reactions = [
                "你说什么？！",
                "等等——你刚才说什么？",
                "（猛地抬头）……继续。我在听。",
            ]
        import random
        return random.choice(reactions)

    def _trigger_ending(self, ending_id: str):
        """触发结局"""
        narrative = self.sm.get_ending_narrative(ending_id)
        display.print_ending(narrative)

        print("游戏结束。")
        if ending_id == "truth_temple":
            print("🎉 恭喜——你找到了最好的结局：真理之殿。")
        elif ending_id == "new_flame":
            print("🔥 新火种——矮人和兽人的联盟，一个新的纪元开始了。")
        elif ending_id == "godslayer":
            print("⚡ 弑神者。你可以对守护灵说任何话了——但已经没人听了。")
        elif ending_id == "blood_debt":
            print("⚔️ 血债血偿。真相摆在了所有人面前，但没有人准备好了接受它。")
        elif ending_id == "no_redemption":
            print("💔 谁都没有被救赎。你走了——殿中的人留在了彼此的沉默里。")
        print()

        # 等待退出
        display.get_input("按 Enter 退出 > ")
        self.running = False


# ================================================================
# 入口
# ================================================================

if __name__ == "__main__":
    # 检查 API Key
    from src.config import DEEPSEEK_API_KEY
    if DEEPSEEK_API_KEY == "your-api-key-here":
        print("⚠️  请先设置 DEEPSEEK_API_KEY 环境变量！")
        print("   Windows: set DEEPSEEK_API_KEY=sk-xxxxx")
        print("   或在 src/config.py 中直接填写。")
        sys.exit(1)

    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n\n  殿中归于寂静。\n")
