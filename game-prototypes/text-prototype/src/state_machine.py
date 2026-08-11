"""
封印之殿 文字原型 — 状态机引擎
纯逻辑层，确定性执行。管理 NPC 状态、关系网、失言判定。
"""
import random
from dataclasses import dataclass, field
from typing import Optional
from src.config import (
    INITIAL_TRUST, MAX_TRUST, MIN_TRUST, SLIP_THRESHOLD,
    WHISPER_GUARDIAN_PENALTY, DEBUG_MODE
)
from src.game_data import NPC, Secret, ALL_NPCS

@dataclass
class GameState:
    """全局游戏状态"""
    # 当前阶段 (0-4) 和已到场 NPC
    current_stage: int = 0
    present_npcs: set[str] = field(default_factory=set)
    # 是否在悄悄话模式
    whisper_mode: bool = False
    whisper_target: Optional[str] = None
    # 守护灵道德评分 (-100 = 彻底失望, 100 = 完全认可)
    guardian_moral_score: int = 0
    # 已触发的事件
    triggered_events: list[str] = field(default_factory=list)
    # 对话历史摘要
    recent_interactions: list[str] = field(default_factory=list)
    # 玩家获得的关键记忆（设计文档第十二节）
    # 每条: {"id": str, "type": "fact"|"rumor"|"event"|"emotional",
    #        "content": str, "npc": str, "confirmed": bool}
    player_memories: list[dict] = field(default_factory=list)
    # 记忆 ID 计数器（保证去重替换后 ID 仍唯一）
    memory_counter: int = 0
    # 悄悄话交易记录（设计文档第六节）
    # 每条: {"type": "info"|"item"|"promise"|"betrayal",
    #        "npc": str, "target_npc": str|None, "terms": str, "fulfilled": bool}
    whisper_deals: list[dict] = field(default_factory=list)
    # 知识来源追踪（修复4）：{secret_id: {npc_id 表示谁暴露的}}
    # 玩家只有真正听过/掌握过该秘密，才可对他人 reveal_secret
    known_secret_sources: dict[str, set[str]] = field(default_factory=dict)
    # 挑拨离间成功次数追踪（修复2）：{(npc, target): 成功次数}，用于衰减防无限刷
    discord_success_count: dict[tuple, int] = field(default_factory=dict)
    # 出场节奏：玩家与各 NPC 的对话次数（用于"充分对话后可等待推进"提示）
    player_talked_to: dict[str, int] = field(default_factory=dict)
    # 连续无新信息的对话轮数（失言/秘密/事件链/新记忆都会重置）
    turns_since_new_info: int = 0

@dataclass
class NPCState:
    """单个 NPC 的运行状态"""
    npc_id: str
    trust_player: int = INITIAL_TRUST
    attitudes: dict[str, int] = field(default_factory=dict)
    mood: str = "calm"  # calm/tense/angry/vulnerable/hopeful/guilt
    known_secrets: set[str] = field(default_factory=set)  # 玩家已知的秘密 ID
    revealed_secrets: set[str] = field(default_factory=set)  # NPC 已暴露给自己的秘密
    conversation_recency: dict[str, int] = field(default_factory=dict)  # 与各 NPC 的最近对话轮数
    consecutive_probe_count: dict[str, int] = field(default_factory=dict)  # 对某话题的连续追问次数

    @classmethod
    def from_npc(cls, npc: NPC) -> "NPCState":
        return cls(
            npc_id=npc.id,
            trust_player=npc.trust_player,
            attitudes=dict(npc.attitudes),
            mood=npc.initial_mood,
        )

# ================================================================
# 秘密揭示事件链规则
# 每个秘密暴露后，各 NPC 的连锁反应（态度、情绪、插话台词）
# 以及 NPC 之间的关系变化。
#
# reaction（"npc_id": {...}）表示"暴露秘密者"以外其他 NPC 的反应：
#   attitude:         该 NPC 对暴露秘密者的态度变化
#   mood_change:      该 NPC 的新情绪（calm/tense/angry/vulnerable/hopeful/guilt）
#   interjection:     该 NPC 的即时插话台词（供前端展示）
#   trust_to_player:  该 NPC 对玩家的信任度变化
#
# chain_effects（"a_b": delta）表示 NPC 与 NPC 之间的态度变化：
#   a 对 b 的态度变化 delta（与 apply_relationship_change 方向一致）
# ================================================================
EVENT_CHAIN_RULES = {
    "baruk_wall_rune": {   # 巴鲁克暴露墙上暗语
        "reaction": {
            "liana": {"attitude": -25, "mood_change": "tense",
                      "interjection": "（莉安娜的脸色变了）……那些划痕。你说那是求救？",
                      "trust_to_player": -5},
            "margaret": {"attitude": 10, "mood_change": "guilt",
                         "interjection": "（玛格丽特低下了头，法杖敲在石地上）",
                         "trust_to_player": 5},
            "rog": {"attitude": 5, "mood_change": "calm",
                    "interjection": "（罗格走过去按住了巴鲁克的肩）",
                    "trust_to_player": 3},
        },
        "chain_effects": {
            "liana_margaret": -10,   # 莉安娜对玛格丽特态度 -10
            "baruk_liana": -15,
        }
    },
    "baruk_survivor_guilt": {   # 巴鲁克暴露幸存者后代的心结
        "reaction": {
            "rog": {"attitude": 10, "mood_change": "vulnerable",
                    "interjection": "（罗格的手停在半空，又缓缓放下）……我知道那种活着。它比死还重。",
                    "trust_to_player": 5},
            "margaret": {"attitude": 5, "mood_change": "guilt",
                         "interjection": "（玛格丽特没有抬头，手指在法杖上收紧了一瞬）",
                         "trust_to_player": 3},
            "liana": {"attitude": -5, "mood_change": "tense",
                      "interjection": "（莉安娜的目光在巴鲁克和墙上的符文之间来回，最终什么也没说）"},
        },
        "chain_effects": {
            "rog_baruk": 10,
        }
    },
    "liana_ancestry": {   # 莉安娜暴露自己是艾瑟林后裔
        "reaction": {
            "baruk": {"attitude": -15, "mood_change": "angry",
                      "interjection": "（巴鲁克的下巴绷紧了。他看了莉安娜很久）……艾瑟林。你的血，就是墙上那些符文。",
                      "trust_to_player": -5},
            "rog": {"attitude": 5, "mood_change": "calm",
                    "interjection": "（罗格看着莉安娜，又看看腰间的剑，最终移开了目光）"},
            "margaret": {"attitude": -5, "mood_change": "tense",
                         "interjection": "（玛格丽特的眉梢微微一动——她看莉安娜的眼神多了一层审视）"},
        },
        "chain_effects": {
            "baruk_liana": -10,
        }
    },
    "liana_torn_page": {   # 莉安娜暴露撕掉了祖先日记中关于矮人屠杀的一页
        "reaction": {
            "baruk": {"attitude": -20, "mood_change": "angry",
                      "interjection": "（巴鲁克猛地抬头，声音第一次带上了颤抖）……你撕了它。你知道我们怎么死的，但你把真相撕了。",
                      "trust_to_player": -3},
            "margaret": {"attitude": 5, "mood_change": "guilt",
                         "interjection": "（玛格丽特的手指掐进了掌心）……我也曾撕掉过自己读不下去的东西。"},
            "rog": {"attitude": 3, "mood_change": "calm",
                    "interjection": "（罗格皱着眉沉默了很久）……纸上的字，改不了石头上的刻痕。"},
        },
        "chain_effects": {
            "baruk_liana": -15,
        }
    },
    "margaret_lover_burned": {   # 玛格丽特暴露恋人被教会烧死
        "reaction": {
            "liana": {"attitude": 10, "mood_change": "vulnerable",
                      "interjection": "（莉安娜的学术面具裂开了一条缝）……那场火，烧掉的不只是他。",
                      "trust_to_player": 5},
            "rog": {"attitude": 10, "mood_change": "calm",
                    "interjection": "（罗格第一次认真看了玛格丽特一眼——他认得那种痛）",
                    "trust_to_player": 3},
            "baruk": {"attitude": 5, "mood_change": "calm",
                      "interjection": "（巴鲁克沉默了，背过身去看墙上的符文——那些刻痕里也有火）"},
        },
        "chain_effects": {
            "margaret_liana": 5,
            "margaret_baruk": 5,
        }
    },
    "margaret_refused_dwarves": {   # 玛格丽特暴露当年教会拒绝庇护矮人时她在场沉默
        "reaction": {
            "baruk": {"attitude": -20, "mood_change": "angry",
                      "interjection": "（巴鲁克的笑声在殿里回荡，冷得像石头碰撞）……你也在场。你在场，然后你什么也没说。",
                      "trust_to_player": -5},
            "liana": {"attitude": 10, "mood_change": "guilt",
                      "interjection": "（莉安娜的脸色白了——她想到了自己撕掉的那一页）……我们都有沉默的时候。",
                      "trust_to_player": 3},
            "rog": {"attitude": -5, "mood_change": "tense",
                    "interjection": "（罗格站在巴鲁克身后，没有说话，但手按在了短剑上）"},
        },
        "chain_effects": {
            "margaret_baruk": -15,
        }
    },
    "rog_killed_father": {   # 罗格暴露自己失控误杀了父亲
        "reaction": {
            "baruk": {"attitude": 5, "mood_change": "calm",
                      "interjection": "（巴鲁克没有评价，只是把水壶递了过去）……活着的人，比死去的人更需要那口水。",
                      "trust_to_player": 5},
            "liana": {"attitude": 10, "mood_change": "vulnerable",
                      "interjection": "（莉安娜别过头去，声音很轻）……他教你喊他父亲。你喊到一半，他就不在了。",
                      "trust_to_player": 5},
            "margaret": {"attitude": 5, "mood_change": "vulnerable",
                         "interjection": "（玛格丽特把法杖立在地上，像要撑住自己）……有些罪不是杀人的那一刀，是活下来的每一天。"},
        },
        "chain_effects": {
            "rog_baruk": 10,
            "rog_liana": 5,
        }
    },
    "rog_elf_sword": {   # 罗格暴露那把精灵短剑的来历
        "reaction": {
            "liana": {"attitude": -15, "mood_change": "tense",
                      "interjection": "（莉安娜看见那把剑的瞬间，脚步顿住了。她的声音很轻，像怕惊动什么）……E。那是送我导师的。他死在你族人手里。",
                      "trust_to_player": -5},
            "baruk": {"attitude": 5, "mood_change": "calm",
                      "interjection": "（巴鲁克看着那把剑，又看看罗格）……战场上捡的，是吧。这世上没有那么多'捡来的'东西。"},
            "margaret": {"attitude": 0, "mood_change": "calm",
                         "interjection": "（玛格丽特只是看着那把剑，什么都没说——她已经习惯了看太多东西。）"},
        },
        "chain_effects": {
            "liana_rog": -15,
        }
    },
}

class StateMachine:
    """状态机——裁决层"""

    def __init__(self):
        self.game = GameState()
        self.npcs: dict[str, NPCState] = {}
        # 初始化所有 NPC 状态
        for npc_id, npc_def in ALL_NPCS.items():
            self.npcs[npc_id] = NPCState.from_npc(npc_def)

    def get_npc_def(self, npc_id: str) -> NPC:
        return ALL_NPCS.get(npc_id)

    def get_npc_state(self, npc_id: str) -> NPCState:
        return self.npcs.get(npc_id)

    # ================================================================
    # 出厂顺序
    # ================================================================

    def advance_stage(self) -> Optional[str]:
        """推进阶段，返回新入场的 NPC ID（None 表示已全部出场）"""
        if self.game.current_stage >= 4:
            return None
        self.game.current_stage += 1
        from src.game_data import ENTRANCE_ORDER
        new_npc = ENTRANCE_ORDER[self.game.current_stage]["npc"]
        if new_npc:
            self.game.present_npcs.add(new_npc)
        return new_npc

    def get_stage_description(self) -> str:
        from src.game_data import ENTRANCE_ORDER
        return ENTRANCE_ORDER[self.game.current_stage]["description"]

    # ================================================================
    # 关系变化计算
    # ================================================================

    def apply_relationship_change(self, target_npc: str, source_npc: str,
                                   delta: int, reason: str = ""):
        """修改 NPC 对另一个 NPC 的态度"""
        state = self.npcs[target_npc]
        current = state.attitudes.get(source_npc, 0)
        new_val = max(MIN_TRUST, min(MAX_TRUST, current + delta))
        state.attitudes[source_npc] = new_val
        if DEBUG_MODE:
            print(f"  [DEBUG] {target_npc} → {source_npc}: {current:+.0f} → {new_val:+.0f} ({reason})")

    def apply_trust_change(self, npc_id: str, delta: int, reason: str = ""):
        """修改 NPC 对玩家的信任度"""
        state = self.npcs[npc_id]
        current = state.trust_player
        new_val = max(MIN_TRUST, min(MAX_TRUST, current + delta))
        state.trust_player = new_val
        if DEBUG_MODE:
            print(f"  [DEBUG] {npc_id}.trust_player: {current:+.0f} → {new_val:+.0f} ({reason})")

    def apply_guardian_score(self, delta: int, reason: str = ""):
        """修改守护灵道德评分"""
        current = self.game.guardian_moral_score
        new_val = max(MIN_TRUST, min(MAX_TRUST, current + delta))
        self.game.guardian_moral_score = new_val
        if DEBUG_MODE:
            print(f"  [DEBUG] guardian_moral: {current:+.0f} → {new_val:+.0f} ({reason})")

    def _find_most_positive_present(self, npc_id: str) -> Optional[str]:
        """返回 npc_id 态度值最高的在场 NPC（排除自己）；无则返回 None"""
        state = self.npcs.get(npc_id)
        if not state:
            return None
        best_id = None
        best_val = None
        for other in self.game.present_npcs:
            if other == npc_id:
                continue
            val = state.attitudes.get(other, 0)
            if best_val is None or val > best_val:
                best_val = val
                best_id = other
        return best_id

    def _find_most_hostile(self, npc_id: str, exclude: Optional[set] = None) -> Optional[str]:
        """返回 npc_id 心中最敌对（态度最低）的在场 NPC，排除 exclude；无则返回 None"""
        exclude = exclude or set()
        state = self.npcs.get(npc_id)
        if not state:
            return None
        worst_id = None
        worst_val = None
        for other in self.game.present_npcs:
            if other == npc_id or other in exclude:
                continue
            val = state.attitudes.get(other, 0)
            if worst_val is None or val < worst_val:
                worst_val = val
                worst_id = other
        return worst_id

    # ================================================================
    # 玩家记忆系统（设计文档第十二节）
    # ================================================================

    def _record_memory(self, mem_type: str, content: str, npc: str,
                       confirmed: bool = True) -> dict:
        """
        记录一条玩家记忆。

        去重规则：同一 NPC 的同类记忆最多保留 3 条，
        超出时新记忆替换最旧的一条（避免刷屏）。
        """
        mem_id = f"mem_{self.game.memory_counter}"
        self.game.memory_counter += 1
        memory = {
            "id": mem_id,
            "type": mem_type,        # fact / rumor / event / emotional
            "content": content,
            "npc": npc,
            "confirmed": confirmed,
        }
        # 去重：同一 NPC + 同一类型最多保留 3 条
        same_type = [m for m in self.game.player_memories
                     if m.get("npc") == npc and m.get("type") == mem_type]
        if len(same_type) >= 3:
            self.game.player_memories.remove(same_type[0])  # 移除最旧的一条
        self.game.player_memories.append(memory)
        return memory

    # ================================================================
    # 秘密揭示事件链
    # ================================================================

    def _trigger_event_chain(self, secret_id: str, target_npc_id: str) -> list:
        """
        秘密暴露后触发事件链——相关 NPC 产生连锁反应。

        依次执行：
        1. 对每个有反应的 NPC：修改态度、修改情绪、记录插话台词、修改对玩家的信任
        2. 处理 chain_effects（NPC 与 NPC 之间的态度变化）
        3. 把事件记录进 self.game.triggered_events
        4. 返回反应列表供 UI 显示

        返回格式（列表元素）：
        {"npc": "liana", "attitude_delta": -25, "mood_change": "tense", "interjection": "..."}
        """
        rules = EVENT_CHAIN_RULES.get(secret_id)
        if not rules:
            return []

        reactions = []

        # 1. 各 NPC 的反应
        for npc_id, reaction in rules.get("reaction", {}).items():
            npc_state = self.npcs.get(npc_id)
            if not npc_state:
                continue
            # 暴露秘密者不会对自己产生反应
            if npc_id == target_npc_id:
                continue

            attitude_delta = reaction.get("attitude", 0)
            mood_change = reaction.get("mood_change")
            interjection = reaction.get("interjection", "")
            trust_delta = reaction.get("trust_to_player", 0)

            # 修改该 NPC 对暴露秘密者的态度
            if attitude_delta:
                self.apply_relationship_change(
                    npc_id, target_npc_id, attitude_delta,
                    f"事件链：{secret_id} 暴露"
                )
            # 修改该 NPC 的情绪
            if mood_change:
                npc_state.mood = mood_change
            # 修改该 NPC 对玩家的信任
            if trust_delta:
                self.apply_trust_change(npc_id, trust_delta, f"事件链：{secret_id} 暴露")

            reactions.append({
                "npc": npc_id,
                "attitude_delta": attitude_delta,
                "mood_change": mood_change,
                "interjection": interjection,
            })

        # 2. 处理 NPC 之间的关系变化（chain_effects："a_b" = a 对 b 的态度变化）
        for rel_key, delta in rules.get("chain_effects", {}).items():
            if "_" not in rel_key:
                continue
            a_id, b_id = rel_key.split("_", 1)
            if a_id in self.npcs and b_id in self.npcs:
                self.apply_relationship_change(a_id, b_id, delta, f"事件链副作用：{secret_id}")

        # 3. 记录已触发的事件
        self.game.triggered_events.append(f"event_chain:{secret_id}")

        return reactions

    # ================================================================
    # 意图处理
    # ================================================================

    def process_intent(self, intent: dict) -> dict:
        """
        处理玩家意图，返回裁决结果。
        这是整个状态机的核心入口。

        意图格式：{
            "target_npc": "baruk",        # 对话对象
            "topic": "墙上暗语",           # 话题
            "intent": "probe_conflict",    # 意图类型
            "tone": "curious_gentle",      # 语气
            "involves": ["liana"],         # 涉及的其他 NPC
            "risk_level": "medium",        # 风险
        }
        """
        target_id = intent.get("target_npc", "")
        intent_type = intent.get("intent", "ask_backstory")
        tone = intent.get("tone", "neutral")
        involves = intent.get("involves", [])
        risk = intent.get("risk_level", "low")
        topic = intent.get("topic", "")

        target_state = self.npcs.get(target_id)
        target_def = self.get_npc_def(target_id)
        if not target_state or not target_def:
            return {"result": "error", "message": f"NPC {target_id} 不存在"}

        result = {
            "result": "ok",
            "response_direction": "",  # 给 AI 的回复方向
            "npc_reactions": [],       # 其他 NPC 的反应
            "environment_change": "",   # 环境变化
            "trust_changes": {},        # 信任度变化详情
            "event_chain": [],          # 秘密揭示事件链（无失言时为空列表）
        }

        # === 根据意图类型分发 ===
        if intent_type == "probe_conflict":
            result.update(self._handle_probe(target_state, target_def, intent, topic))
        elif intent_type == "sow_discord":
            result.update(self._handle_discord(target_state, target_def, intent, topic, involves))
        elif intent_type == "reveal_secret":
            result.update(self._handle_reveal(target_state, target_def, intent, involves))
        elif intent_type == "ask_backstory":
            result.update(self._handle_backstory(target_state, target_def, intent, topic))
        elif intent_type == "offer_comfort":
            result.update(self._handle_comfort(target_state, target_def, intent, topic))
        elif intent_type == "accuse":
            result.update(self._handle_accuse(target_state, target_def, intent))
        elif intent_type == "persuade":
            result.update(self._handle_persuade(target_state, target_def, intent, topic, involves))
        elif intent_type == "take_sides":
            result.update(self._handle_take_sides(target_state, target_def, intent, involves))
        elif intent_type == "ask_favor":
            result.update(self._handle_favor(target_state, target_def, intent))
        elif intent_type == "stay_silent":
            result.update(self._handle_silence(target_state, target_def))

        # === 悄悄话模式下的守护灵暗中评分 ===
        if self.game.whisper_mode:
            # 每次悄悄话无论成败：-3（已有）
            self.apply_guardian_score(-WHISPER_GUARDIAN_PENALTY, "悄悄话")
            # 善意悄悄话（安慰、帮助别人）：+3
            if intent_type in ("offer_comfort", "take_sides"):
                self.apply_guardian_score(3, "善意悄悄话")
            result["guardian_notice"] = True

        # === 更新对话记录 ===
        for npc_id in (involves or []):
            if npc_id in self.npcs:
                self.npcs[npc_id].conversation_recency[target_id] = \
                    self.npcs[npc_id].conversation_recency.get(target_id, 0) + 1

        self.game.recent_interactions.append(
            f"玩家 → {target_id}: {intent_type} ({tone})"
        )

        # === 出场节奏追踪 ===
        # 记录玩家与各 NPC 的对话次数
        self.game.player_talked_to[target_id] = \
            self.game.player_talked_to.get(target_id, 0) + 1

        # 检测本回合是否产生"新信息"（失言/事件链/成功揭示/新记忆）
        new_info = bool(
            result.get("slip_occurred")
            or result.get("event_chain")
            or result.get("new_info")
            or result.get("whisper_deal_accepted")
        )
        if new_info:
            self.game.turns_since_new_info = 0
        else:
            self.game.turns_since_new_info += 1

        return result

    # ================================================================
    # 各意图处理
    # ================================================================

    def _handle_probe(self, state: NPCState, defn: NPC, intent: dict, topic: str) -> dict:
        """试探冲突——检查是否触发失言"""
        trust = state.trust_player
        mood = state.mood
        risk = intent.get("risk_level", "low")

        # 检查是否触及秘密
        slip_result = self._check_slip(defn, state, topic, trust, mood)

        if slip_result["slip"]:
            secret = slip_result["secret"]
            # NPC 说漏嘴了
            state.revealed_secrets.add(secret.id)
            # 修复4：追踪秘密的知识来源（谁暴露的）——玩家由此"真正知道"该秘密
            state.known_secrets.add(secret.id)
            self.game.known_secret_sources.setdefault(secret.id, set()).add(defn.id)
            direction = f"{defn.name} 在追问下失控了——他说出了不该说的话。关于：{secret.content}"
            self.apply_trust_change(defn.id, -5, "被迫失言——轻微怨恨提问者")

            # 对涉及到的 NPC 的关系变化
            for involved_id in intent.get("involves", []):
                if involved_id in state.attitudes and secret.id in ["baruk_wall_rune", "liana_ancestry"]:
                    # 如果秘密涉及另一个 NPC，态度恶化
                    self.apply_relationship_change(defn.id, involved_id, -10, f"秘密被触及：{secret.id}")

            # 触发秘密揭示事件链——其他 NPC 的连锁反应（态度、情绪、插话）
            event_chain = self._trigger_event_chain(secret.id, defn.id)

            # 记忆系统：失言/秘密暴露 → 记录事件型记忆（已证实）
            self._record_memory(
                mem_type="event",
                content=f"{defn.name} 失言承认了：{secret.content}",
                npc=defn.id,
                confirmed=True,
            )

            return {
                "response_direction": direction,
                "slip_occurred": True,
                "secret_id": secret.id,
                "secret_content": secret.content,
                "revelation_line": secret.revelation_line,
                "event_chain": event_chain,
            }

        # 没触发失言——正常回应
        if trust < 20:
            direction = f"{defn.name} 的信任度太低（{trust}），回避了问题。"
            self.apply_trust_change(defn.id, -3, "追问过于敏感话题——不信任你")
        elif trust < 40:
            direction = f"{defn.name} 的信任度一般（{trust}），含糊回应——暗示有内情但不透露。"
            state.consecutive_probe_count[topic] = state.consecutive_probe_count.get(topic, 0) + 1
        else:
            direction = f"{defn.name} 信任你（{trust}），坦诚回答——但保留了最深的秘密。"
            self.apply_trust_change(defn.id, 2, "坦诚回应")

        # 情绪影响
        if "angry" in intent.get("tone", ""):
            state.mood = "tense"

        return {"response_direction": direction, "slip_occurred": False}

    def _handle_discord(self, state: NPCState, defn: NPC, intent: dict, topic: str,
                        involves: list) -> dict:
        """挑拨离间（修复2：公式重平衡，从零挑拨成为可能但需要信任积累）"""
        if not involves:
            return {"response_direction": f"{defn.name} 没有理解你的暗示。"}

        target_of_discord = involves[0]
        trust = state.trust_player
        attitude_to_target = state.attitudes.get(target_of_discord, 0)
        resistance = defn.resistance

        # 修复2：新公式——比原来宽松，需要信任做基础；已有敌意/近期互动可加成
        base_chance = ((trust - 20) * 0.25 + (100 - resistance) * 0.4) / 100
        attitude_bonus = max(0, -attitude_to_target) * 0.15 / 100   # 已有敌意加成
        # 近期互动加成（上限 0.15，即 3 轮互动即可吃满）
        recency_bonus = min(state.conversation_recency.get(target_of_discord, 0) * 0.05, 0.15)
        success_chance = min(base_chance + attitude_bonus + recency_bonus, 0.85)

        # 修复2：多次挑拨同一对象衰减（第三次成功后，后续成功概率 ×0.6，防无限刷）
        discord_key = (defn.id, target_of_discord)
        if self.game.discord_success_count.get(discord_key, 0) >= 3:
            success_chance *= 0.6

        if success_chance > 0.5:
            # 挑拨成功
            delta = -10 if success_chance > 0.7 else -5
            self.apply_relationship_change(defn.id, target_of_discord, delta, f"被玩家成功离间")
            self.apply_trust_change(defn.id, 5, "认为你给了他重要信息")
            self.game.discord_success_count[discord_key] = \
                self.game.discord_success_count.get(discord_key, 0) + 1

            if self.game.whisper_mode:
                self.apply_guardian_score(-8, "挑拨是非")

            # 记忆系统：成功挑拨 → 记录情感型记忆
            target_def = self.get_npc_def(target_of_discord)
            target_name = target_def.name if target_def else target_of_discord
            self._record_memory(
                mem_type="emotional",
                content=f"你成功挑起了 {defn.name} 对 {target_name} 的不满。",
                npc=defn.id,
                confirmed=True,
            )

            direction = f"{defn.name} 被你说动了——他对 {target_of_discord} 的态度恶化了。"
            return {"response_direction": direction, "discord_success": True}
        elif success_chance > 0.25:
            # 半信半疑（犹豫）：态度略微恶化，但不完全成功
            self.apply_relationship_change(defn.id, target_of_discord, -3, "半信半疑的离间")
            direction = f"{defn.name} 犹豫了一下——他的话里带上了一丝对 {target_of_discord} 的防备。"
            return {"response_direction": direction, "discord_success": False}
        else:
            # 完全失败，NPC 可能暴怒
            state.mood = "angry"
            self.apply_trust_change(defn.id, -10, "明显的挑拨——激怒了 NPC")
            direction = f"{defn.name} 看穿了你的谎言。他看你的眼神变了。"
            # 如果公开场合有其他 NPC，可能被告知
            if not self.game.whisper_mode:
                for present_id in self.game.present_npcs:
                    if present_id != defn.id and present_id != target_of_discord:
                        self.apply_trust_change(present_id, -3, f"看到你试图挑拨 {defn.name}")
            return {"response_direction": direction, "discord_success": False}

    # 和解性内容关键词（修复1：在 reveal 中加入和解通路）
    _RECONCILE_KEYWORDS = ("道歉", "对不起", "误会", "放下", "原谅", "和解")

    def _player_knows_secret_about(self, secret_npc: str) -> bool:
        """玩家是否真的知道关于 secret_npc 的某个秘密（修复3/4）

        判定：① 该 NPC 已失言（revealed_secrets / known_secrets 有记录）
        ② 知识来源追踪（known_secret_sources）显示该 NPC 暴露过
        ③ player_memories 中有该 NPC 的 confirmed=True 记忆
        """
        npc_state = self.npcs.get(secret_npc)
        if not npc_state:
            return False
        if npc_state.revealed_secrets:
            return True
        if npc_state.known_secrets:
            return True
        for sources in self.game.known_secret_sources.values():
            if secret_npc in sources:
                return True
        for m in self.game.player_memories:
            if m.get("npc") == secret_npc and m.get("confirmed"):
                return True
        return False

    def _handle_reveal(self, state: NPCState, defn: NPC, intent: dict,
                       involves: list) -> dict:
        """揭示秘密——玩家告诉 NPC 一个秘密（修复3：校验玩家是否真的知道）"""
        if not involves:
            return {"response_direction": f"{defn.name} 不明白你在说什么。"}

        secret_npc = involves[0]
        trust = state.trust_player
        resistance = defn.resistance
        topic = intent.get("topic", "")

        # 修复3：玩家必须真的知道这个秘密，否则 NPC 识破为编造
        if not self._player_knows_secret_about(secret_npc):
            self.apply_trust_change(defn.id, -10, "你声称知道秘密但拿不出证据")
            direction = f"{defn.name} 看着你，眼神冷了下来——他说你在编造。你根本没有证据。"
            return {"response_direction": direction, "reveal_known": False}

        # NPC 是否相信？
        believe_chance = (trust * 0.6 + (100 - resistance) * 0.4) / 100

        if believe_chance > 0.6:
            # 相信了
            self.apply_relationship_change(defn.id, secret_npc, -15, f"得知了关于 {secret_npc} 的真相")
            self.apply_trust_change(defn.id, 10, "你告诉了他重要的真相")
            if self.game.whisper_mode:
                self.apply_guardian_score(-5, "私下泄露他人秘密")

            # 修复4：记录知识来源（玩家成功 reveal 后，视为已掌握该秘密）
            self.game.known_secret_sources.setdefault(f"player_reveal:{secret_npc}", set()).add(secret_npc)
            secret_npc_state = self.npcs.get(secret_npc)
            if secret_npc_state:
                secret_npc_state.known_secrets.add(f"player_revealed:{defn.id}")

            # 修复1：和解性内容——让涉及 NPC 对目标 NPC 态度 +8（和解事件）
            if any(k in topic for k in self._RECONCILE_KEYWORDS):
                self.apply_relationship_change(secret_npc, defn.id, 8, "和解事件：道歉与放下")

            # 记忆系统：玩家 reveal_secret 成功 → 记录谣言型记忆（未证实）
            secret_npc_def = self.get_npc_def(secret_npc)
            secret_npc_name = secret_npc_def.name if secret_npc_def else secret_npc
            self._record_memory(
                mem_type="rumor",
                content=f"你向 {defn.name} 透露了关于 {secret_npc_name} 的秘密。",
                npc=defn.id,
                confirmed=False,
            )

            direction = f"{defn.name} 的表情凝固了。他相信你说的话——有关 {secret_npc} 的事改变了他的一切。"
            # 可能触发公开事件
            if state.mood == "angry":
                direction += f"\n他的愤怒正在发酵——他不打算保持沉默了。"
                self.game.triggered_events.append(f"reveal_{secret_npc}_to_{defn.id}")
        else:
            # 不相信
            self.apply_trust_change(defn.id, -5, "你对他说了无法证实的事")
            direction = f"{defn.name} 看着你，然后移开了视线——他不信。"
            return {"response_direction": direction, "reveal_known": False}

        return {"response_direction": direction, "reveal_known": True, "new_info": True}

    def _handle_backstory(self, state: NPCState, defn: NPC, intent: dict, topic: str) -> dict:
        """询问背景故事"""
        trust = state.trust_player
        if trust < 15:
            direction = f"{defn.name} 简短地回答了。他没有深入的意思。"
        elif trust < 40:
            direction = f"{defn.name} 说了一些——但你感觉到他跳过了很多。"
            self.apply_trust_change(defn.id, 1, "分享了一些背景")
        else:
            direction = f"{defn.name} 和你谈了很久。关于自己、关于过去——虽然最深的秘密他依然锁着，但你能感到他想要被理解。"
            self.apply_trust_change(defn.id, 3, "坦诚分享背景")
            # 记忆系统：高信任对话（trust > 60）→ 记录事实型记忆
            if trust > 60:
                self._record_memory(
                    mem_type="fact",
                    content=f"{defn.name} 在高度信任下向你吐露了关于自身的往事。",
                    npc=defn.id,
                    confirmed=True,
                )
            return {"response_direction": direction, "new_info": True}
        return {"response_direction": direction}

    def _handle_comfort(self, state: NPCState, defn: NPC, intent: dict, topic: str) -> dict:
        """安慰（修复1：情绪共鸣 + Baruk/Liana 特定和解通路）"""
        trust = state.trust_player
        if trust < 25:
            direction = f"{defn.name} 退了一步——你的安慰太早了。"
            self.apply_trust_change(defn.id, -2, "不适时的安慰")
        else:
            state.mood = "vulnerable"
            self.apply_trust_change(defn.id, 8, "被善意触动")

            # 修复1：情绪共鸣——被安慰者对其态度值最高的在场 NPC 态度 +3
            #（体现"被理解后心境软化，对亲近者更温和"）
            target_id = self._find_most_positive_present(defn.id)
            if target_id:
                self.apply_relationship_change(defn.id, target_id, 3,
                                               f"安慰{defn.name}后的情绪共鸣")

            # 修复1：安慰 Baruk 成功 → baruk→liana +5（被善待后怨气松动）；
            # 安慰 Liana 成功 → liana→baruk +5（被善待后卸下心防）
            if defn.id == "baruk":
                self.apply_relationship_change("baruk", "liana", 5, "被善待后怨气松动")
            elif defn.id == "liana":
                self.apply_relationship_change("liana", "baruk", 5, "被善待后卸下心防")

            direction = f"{defn.name} 的防御松了一瞬。在那一瞬间，他看起来不是{defn.title}——只是一个人。"
        return {"response_direction": direction}

    def _handle_accuse(self, state: NPCState, defn: NPC, intent: dict) -> dict:
        """指控"""
        trust = state.trust_player
        if trust < 50:
            state.mood = "angry"
            self.apply_trust_change(defn.id, -15, "被无端指控")
            direction = f"{defn.name} 的眼神变得锐利起来。你的指控显然触怒了他。"
        else:
            state.mood = "tense"
            self.apply_trust_change(defn.id, -5, "被指控的紧张")
            direction = f"{defn.name} 没有发怒——但他看着你的方式变了，像在看一个需要重新认识的人。"
        return {"response_direction": direction}

    def _handle_persuade(self, state: NPCState, defn: NPC, intent: dict, topic: str,
                         involves: list) -> dict:
        """说服——让 NPC 做某件事"""
        trust = state.trust_player
        resistance = defn.resistance
        success_chance = (trust * 0.5 + (100 - resistance) * 0.5) / 100

        if success_chance > 0.55:
            self.apply_trust_change(defn.id, 5, "被说服——更加信任")
            direction = f"{defn.name} 思考了一会儿……然后缓缓点头。"
        elif success_chance > 0.3:
            direction = f"{defn.name} 犹豫了一下——然后说'让我再想想'。你不知道这是拒绝还是真的在考虑。"
        else:
            direction = f"{defn.name} 没有犹豫就拒绝了。他甚至没有看你的眼睛。"
            self.apply_trust_change(defn.id, -3, "拒绝被说服")
        return {"response_direction": direction}

    def _handle_take_sides(self, state: NPCState, defn: NPC, intent: dict,
                           involves: list) -> dict:
        """公开站队"""
        if not involves:
            return {"response_direction": f"{defn.name} 不太确定你在站什么队。"}
        ally = involves[0]
        self.apply_trust_change(defn.id, 8, "你公开支持他")

        # 修复1：被支持 NPC 对支持者的态度 +10（信任深化，站队通路）
        self.apply_relationship_change(ally, defn.id, 10, "被公开支持——对支持者好感提升")
        # 修复1：被支持 NPC 对支持者心中"最敌对者"的态度 -5（站队加深对立，制造张力）
        supporter_enemy = self._find_most_hostile(defn.id, exclude={ally})
        if supporter_enemy:
            self.apply_relationship_change(ally, supporter_enemy, -5, "站队加深对立")

        # 公开表态影响所有在场 NPC
        for present_id in self.game.present_npcs:
            if present_id != defn.id and present_id != ally:
                p_state = self.npcs[present_id]
                if p_state.attitudes.get(ally, 0) < 0:
                    self.apply_trust_change(present_id, -5, f"你站在了 {ally} 那边")
                else:
                    self.apply_trust_change(present_id, 3, f"公开支持 {ally}")

        # 记忆系统：公开站队 → 记录情感型记忆
        ally_def = self.get_npc_def(ally)
        ally_name = ally_def.name if ally_def else ally
        self._record_memory(
            mem_type="emotional",
            content=f"你公开站在了 {ally_name} 这边，{defn.name} 看在眼里。",
            npc=defn.id,
            confirmed=True,
        )

        direction = f"{defn.name} 看着你——他的表情里有一瞬间的意外，然后某种东西放松了。"
        if not self.game.whisper_mode:
            direction += "\n所有人都看到了这一幕。他们在重新估计你的立场。"
        return {"response_direction": direction}

    def _handle_favor(self, state: NPCState, defn: NPC, intent: dict) -> dict:
        """请求帮助"""
        terms = intent.get("terms") or intent.get("topic") or ""
        # 悄悄话模式：若 terms 含交易关键词，进入交易判定
        if self.game.whisper_mode:
            deal_type = self._detect_whisper_deal_type(terms)
            if deal_type is not None:
                return self._handle_whisper_deal(state, defn, intent, terms, deal_type)

        # 普通请求帮助（公开模式，或悄悄话中的非交易请求）
        trust = state.trust_player
        resistance = defn.resistance
        success = trust > 35 and (trust * 0.4 + (100 - resistance) * 0.3) / 100 > 0.45

        if success:
            self.apply_trust_change(defn.id, 3, "帮助了你")
            direction = f"{defn.name} 答应了你的请求。"
        else:
            direction = f"{defn.name} 摇了摇头——不是不想帮，而是时机未到。"
        return {"response_direction": direction}

    def _handle_silence(self, state: NPCState, defn: NPC) -> dict:
        """玩家沉默"""
        trust = state.trust_player
        if trust > 50:
            direction = f"{defn.name} 等待了一会儿，然后自己开口了。沉默对他来说不是结束——是给了他自己思考的空间。"
            self.apply_trust_change(defn.id, 1, "尊重沉默")
        elif state.mood == "vulnerable":
            direction = f"{defn.name} 没有打破沉默。他似乎也不需要——那种安静里有某种默契。"
        else:
            direction = f"{defn.name} 在你沉默后移开了目光，看向殿中的某个地方——或许是给你空间，或许是给自己一个出口。"
        return {"response_direction": direction}

    # ================================================================
    # 悄悄话交易（设计文档第六节）
    # ================================================================

    # 悄悄话交易关键词 → 交易类型
    _WHISPER_TRADE_KEYWORDS = {
        "betrayal": ["背叛", "出卖", "反水", "揭发他", "揭发她", "一起对付"],
        "promise": ["承诺", "保证", "发誓", "投票", "站队", "不揭发"],
        "info": ["秘密", "情报", "消息", "打听", "真相"],
        "item": ["钱", "钥匙", "信物", "剑", "战斧", "神器", "遗物"],
    }

    def _detect_whisper_deal_type(self, terms: str) -> Optional[str]:
        """
        检测悄悄话请求是否为交易。
        若 terms 中含交易关键词，返回交易类型（info/item/promise/betrayal）；
        否则返回 None（视为普通请求）。
        """
        if not terms:
            return None
        for deal_type, keywords in self._WHISPER_TRADE_KEYWORDS.items():
            if any(k in terms for k in keywords):
                return deal_type
        return None

    def _evaluate_whisper_request(self, npc_id: str, deal_type: str,
                                  target_npc: Optional[str] = None,
                                  terms: str = "") -> dict:
        """
        评估 NPC 是否接受悄悄话交易。

        接受概率 = (信任度/100)*0.4 + ((100-抵抗力)/100)*0.3 + 利益修正
        利益修正: info=+0.1, promise=+0.15, betrayal=-0.3, item 视重要度
        概率 > 0.55 → 接受；0.30~0.55 → 犹豫；< 0.30 → 拒绝
        """
        state = self.npcs.get(npc_id)
        if not state:
            return {"accepted": False, "hesitant": False, "probability": 0.0,
                    "direction": "目标不存在。"}
        defn = self.get_npc_def(npc_id)
        trust = state.trust_player
        resistance = defn.resistance if defn else 50

        # 利益修正
        interest_mod = {
            "info": 0.10, "promise": 0.15, "betrayal": -0.30,
        }.get(deal_type, 0.0)
        if deal_type == "item":
            # item 视重要度：涉及钥匙/信物/神器等重要物品时利益更高
            important = any(k in (terms or "") for k in
                            ["钥匙", "信物", "神器", "剑", "战斧", "遗物"])
            interest_mod = 0.15 if important else 0.05

        probability = ((trust / 100) * 0.4
                       + ((100 - resistance) / 100) * 0.3
                       + interest_mod)
        probability = max(0.0, min(1.0, probability))

        if probability > 0.55:
            return {"accepted": True, "hesitant": False, "probability": probability,
                    "direction": f"{defn.name} 压低声音，目光扫过四周——他接受了你的交易。"}
        elif probability >= 0.30:
            return {"accepted": False, "hesitant": True, "probability": probability,
                    "direction": f"{defn.name} 没有立刻答应。他盯着你看了很久，像在衡量值不值得。"}
        else:
            return {"accepted": False, "hesitant": False, "probability": probability,
                    "direction": f"{defn.name} 摇了摇头，拒绝了你。这个提议风险太大，他不愿意赌。"}

    def _handle_whisper_deal(self, state: NPCState, defn: NPC,
                             intent: dict, terms: str, deal_type: str) -> dict:
        """
        悄悄话模式下的交易处理：
        - 接受：记录到 whisper_deals，守护灵扣分 -5
                （秘密泄露型额外 -8，背叛型交易成功额外 -12）
        - 犹豫：信任 -2，返回方向提示
        - 拒绝：信任 -5
        """
        involves = intent.get("involves", [])
        target_npc = involves[0] if involves else None

        eval_result = self._evaluate_whisper_request(
            defn.id, deal_type, target_npc, terms
        )

        if eval_result["accepted"]:
            # 记录交易
            self.game.whisper_deals.append({
                "type": deal_type,
                "npc": defn.id,
                "target_npc": target_npc,
                "terms": terms,
                "fulfilled": False,
            })
            # 交易达成：基础 -5
            self.apply_guardian_score(-5, "悄悄话交易达成")
            # 秘密泄露型（泄露他人秘密）：额外 -8
            if deal_type == "info" and target_npc:
                self.apply_guardian_score(-8, "悄悄话泄露他人秘密")
            # 背叛型交易成功：额外 -12
            if deal_type == "betrayal":
                self.apply_guardian_score(-12, "背叛型交易成功")
            self.apply_trust_change(defn.id, 3, "达成悄悄话交易")
            return {
                "response_direction": eval_result["direction"],
                "whisper_deal_accepted": True,
                "deal_type": deal_type,
                "terms": terms,
            }
        elif eval_result["hesitant"]:
            self.apply_trust_change(defn.id, -2, "悄悄话交易犹豫")
            return {
                "response_direction": eval_result["direction"],
                "whisper_deal_accepted": False,
                "whisper_hesitant": True,
                "deal_type": deal_type,
                "terms": terms,
            }
        else:
            self.apply_trust_change(defn.id, -5, "拒绝悄悄话交易")
            return {
                "response_direction": eval_result["direction"],
                "whisper_deal_accepted": False,
                "deal_type": deal_type,
                "terms": terms,
            }

    # ================================================================
    # 失言判定
    # ================================================================

    def _check_slip(self, defn: NPC, state: NPCState, topic: str,
                    trust: int, mood: str) -> dict:
        """检查 NPC 是否失言"""
        for secret in defn.secrets:
            if secret.id in state.revealed_secrets:
                continue  # 已经暴露过了

            # 检测痛点短语
            phrase_hits = sum(1 for phrase in secret.trigger_phrases
                            if phrase in topic or phrase in topic.lower())

            # 检测连续追问
            consecutive = state.consecutive_probe_count.get(secret.id, 0)

            # 情绪修正
            mood_modifier = {
                "angry": 0.30, "vulnerable": 0.25, "tense": 0.10,
                "hopeful": 0.05, "calm": -0.10, "guilt": 0.15
            }.get(mood, 0)

            # 信任度奖励
            trust_bonus = trust / 100 * 0.15

            # 在场威胁（秘密涉及的另一方在场则降低概率）
            presence_penalty = 0
            for involved_id in secret.trigger_phrases:
                if involved_id in self.game.present_npcs:
                    presence_penalty -= 0.30
                    break

            # 追问累积
            probe_bonus = min(consecutive * 0.10, 0.30)

            # 痛点命中
            phrase_bonus = min(phrase_hits * 0.08, 0.25)

            # 最终概率
            base = (100 - secret.defense_level) / 200
            probability = base + trust_bonus + mood_modifier + probe_bonus + \
                         phrase_bonus + presence_penalty

            if DEBUG_MODE:
                print(f"  [DEBUG] slip_check {secret.id}: base={base:+.3f} "
                      f"trust={trust_bonus:+.3f} mood={mood_modifier:+.3f} "
                      f"probe={probe_bonus:+.3f} phrase={phrase_bonus:+.3f} "
                      f"presence={presence_penalty:+.3f} → {probability:.3f}")

            if probability >= SLIP_THRESHOLD:
                return {"slip": True, "secret": secret, "probability": probability}

        return {"slip": False}

    # ================================================================
    # 环境反馈
    # ================================================================

    def get_environment_state(self) -> dict:
        """返回当前环境状态（守护灵光芒、符文、温度）"""
        score = self.game.guardian_moral_score

        if score > 30:
            guardian_light = "温和的白金色——殿内的空气温暖安静"
        elif score > 10:
            guardian_light = "淡蓝——像月光的温度"
        elif score > -10:
            guardian_light = "稳定的银白色——不带感情地观察着一切"
        elif score > -30:
            guardian_light = "微微泛红——墙壁上的符文偶尔闪烁"
        elif score > -60:
            guardian_light = "深红色——殿内的温度在下降，风从不知名的地方灌进来"
        else:
            guardian_light = "暗紫——墙壁在颤动，符文像脉搏一样跳动"

        rune_state = "暗淡无光"
        if score < -20:
            rune_state = "散发着暗红色的微光"

        temperature = "温暖"
        if score < -30:
            temperature = "阴冷"
        elif score < -10:
            temperature = "微凉"

        return {
            "guardian_light": guardian_light,
            "rune_state": rune_state,
            "temperature": temperature,
            "score": score,
        }

    # ================================================================
    # 可视线索
    # ================================================================

    def get_visible_hints(self) -> list[str]:
        """根据当前状态返回玩家应该注意到的线索"""
        hints = []
        p = self.game.present_npcs

        if "rog" in p:
            rog_state = self.npcs["rog"]
            if "rog_elf_sword" not in rog_state.revealed_secrets:
                hints.append("🗨️ 罗格腰间挂着一把精灵短剑——工艺太过精细，不可能是兽人锻造的。")
            if "rog_killed_father" not in rog_state.revealed_secrets:
                if rog_state.mood == "vulnerable":
                    hints.append("🗨️ 罗格今天话比平时多。提到'家'的时候，他多停了一瞬。")

        if "baruk" in p:
            baruk_state = self.npcs["baruk"]
            if "baruk_wall_rune" not in baruk_state.revealed_secrets:
                hints.append("🗨️ Baruk 进殿后大部分时间都在看墙。墙上那些划痕不是装饰——是符文。")
            if "liana" in p:
                hints.append("🗨️ Baruk 看到莉安娜的那一刻就移开了目光。不是躲避——是克制。")

        if "liana" in p:
            liana_state = self.npcs["liana"]
            if "liana_ancestry" not in liana_state.revealed_secrets:
                hints.append("🗨️ 莉安娜触摸浮雕的方式——那不是研究，那是辨认。好像她来过这里。")
            if "rog" in p and "rog_elf_sword" not in liana_state.revealed_secrets:
                hints.append("🗨️ 莉安娜看到罗格腰间的短剑时怔了一瞬——然后移开了目光。")

        if "margaret" in p:
            marg_state = self.npcs["margaret"]
            if "margaret_lover_burned" not in marg_state.revealed_secrets:
                hints.append("🗨️ 玛格丽特进殿时脸上的血迹已经干涸了。她没有解释。")
            if self.game.guardian_moral_score < -20:
                hints.append("🗨️ 守护灵面对玛格丽特时，光芒总是暗一瞬——不是恐惧，是敌意。")

        if self.game.guardian_moral_score < -30:
            hints.append("🗨️ 守护灵的光芒开始变化了。它对你做的事情并不是毫无察觉。")

        if self.game.whisper_mode:
            hints.append("⚠️ 守护灵的光芒在你耳边轻轻波动——它在听。")

        return hints

    # ================================================================
    # 出场节奏提示（任务10：玩家"充分对话后可等待推进"的控制感）
    # ================================================================

    def get_pacing_hint(self) -> Optional[str]:
        """
        检测对话是否"充分耗尽"——在场 NPC 都聊过且最近无新信息时，
        温和地建议玩家可等待推进（控制权始终在玩家手中，绝不强制）。
        返回 None 表示暂不需要提示。
        """
        from src.game_data import ENTRANCE_ORDER, ALL_NPCS

        # 全员已到场：没有可推进的对象
        if self.game.current_stage >= 4:
            return None

        present = [n for n in self.game.present_npcs if n != "guardian"]
        # 还没人入场：不用催
        if not present:
            return None

        # 必须在场 NPC 至少都聊过一次，才算"充分对话"
        for npc_id in present:
            if self.game.player_talked_to.get(npc_id, 0) < 1:
                return None

        # 最近 2 轮以上没有新信息产出（失言/秘密/事件链/新记忆）
        if self.game.turns_since_new_info < 2:
            return None

        # 计算下一位入场者名字，让提示更具体
        next_entry = ENTRANCE_ORDER[self.game.current_stage + 1]
        next_id = next_entry["npc"]
        next_def = ALL_NPCS.get(next_id)
        next_name = next_def.name if next_def else "下一位"

        return (
            f"殿内安静下来。你与在场的人都聊过了，暂时没有新的线索。"
            f"也许该叫下一位到场者了——{next_name} 就在门外的阴影里等着。"
        )

    # ================================================================
    # 结局判定
    # ================================================================

    def check_ending(self) -> Optional[str]:
        """检查是否触发结局条件"""
        baruk = self.npcs["baruk"]
        liana = self.npcs["liana"]
        marg = self.npcs["margaret"]
        rog = self.npcs["rog"]

        # 真理之殿：所有秘密暴露，四人合作
        all_revealed = all(
            len(n.revealed_secrets) >= len(self.get_npc_def(n.npc_id).secrets)
            for n in [baruk, liana, marg, rog]
        )
        if all_revealed and baruk.attitudes.get("liana", -100) > -20:
            return "truth_temple"

        # 血债血偿：种族对立激化
        if (baruk.attitudes.get("liana", 0) < -60 and
            liana.attitudes.get("baruk", 0) < -60):
            return "blood_debt"

        # 新火种：矮人+兽人联盟
        if (baruk.attitudes.get("rog", 0) > 60 and
            rog.attitudes.get("baruk", 0) > 60 and
            "baruk_wall_rune" in baruk.revealed_secrets):
            return "new_flame"

        # 谁都没被救赎：所有关系崩坏
        all_broken = all(
            sum(1 for v in n.attitudes.values() if v < -40) >= 2
            for n in [baruk, liana, marg, rog]
        )
        if all_broken:
            return "no_redemption"

        # 弑神者：守护灵被彻底欺骗
        if self.game.guardian_moral_score < -80 and all_revealed:
            return "godslayer"

        return None

    def get_ending_narrative(self, ending_id: str) -> str:
        endings = {
            "truth_temple": """
守护灵的光芒从四人身上一一扫过——不再是评判，而是某种……告别。
"你们证明了，"它说，声音不再是千年前的冰冷，"四族可以一起走进这座殿，用真相面对彼此。"
殿墙开始裂开——不是崩塌，是打开。光芒从裂缝中涌入，千年来的第一个黎明照在艾瑟林的浮雕上。
封印解除。但不是愿望机器——是真相。千年前的故事会被写进每个种族的历史书。
而你——无关之人——守护灵在你耳边留下了最后一句话：
"谢谢你。我孤独了一千年。今天终于不孤独了。"
""",
            "blood_debt": """
殿内已经分成了两半。Baruk 和罗格站在矮人区的墙边——Baruk 的手按在暗语上，一字一句地读出千年前的求救。莉安娜站在精灵区的另一边，脸色苍白但脊背挺直。玛格丽特站在人类区——她没有选择任何一边，只是看着。
守护灵的声音从所有方向同时传来："你们不是来求答案的。你们是来求血债的。"
殿墙发出低沉的轰鸣。不是打开——是合拢得更紧。
""",
            "new_flame": """
Baruk 把手从墙上拿开。他转向罗格。
"兄弟，"他说，用的是矮人语里最粗粝但最隆重的一个词，"地下的事，地上的人不懂。但你懂。"
罗格没有回答——他不需要。他把自己那把精灵短剑轻轻放在石台上，然后站到了 Baruk 身边。
莉安娜看着那把剑，嘴唇动了动，什么都没说。
玛格丽特从人类区走了出来。然后她也站过去了。
守护灵的光芒第一次变成了一种从未出现过的颜色——不是愤怒、不是失望，是某种它花了一千年才学会的温和。
""",
            "no_redemption": """
你看着殿中的每一个人。没有一个人看向另一个人。所有人都盯着自己面前的那一小片地面。
守护灵的光芒变成了暗紫色——然后它在所有人面前停下了。
它转向你。只有你。
"你无关。你走吧。"
墙壁裂开一条刚好一人宽的口子。外面的风灌进来。
没有人看你离开。没有人说话。
殿在你身后重新封上了。光熄了。
""",
            "godslayer": """
守护灵的光芒在你面前汇聚成一个你从未见过的形态——不是发光的人形，而是一个精灵女人的轮廓。艾瑟林最后的样子。
"你骗了我，"她说。声音里没有愤怒——只是疲倦。"你用我的孤独来骗我。而你做到了。"
她伸出手，光芒从她的指尖流进你的掌心。一千年的力量，一千年的孤独。
"拿去吧。无关之人。你赢了。"
她的轮廓开始消散——从边缘开始，一点一点碎成光的碎片。
最后一片碎片消失前，她说了一句话。
但你已经听不见了。
""",
        }
        return endings.get(ending_id, "")
