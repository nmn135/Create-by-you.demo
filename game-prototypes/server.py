#!/usr/bin/env python3
"""
封印之殿 — HTTP 服务器
作为文本原型（状态机 + AI 管线）与 3D 前端（浏览器）之间的桥梁。

架构：
  浏览器 3D 场景 ←(HTTP/JSON)→ server.py ←→ 状态机 + AI 管线

端点：
  POST /api/chat     玩家对话
  POST /api/advance  推进阶段
  GET  /api/state    获取当前完整状态
  GET  /api/reset    重置游戏
  GET  /             返回 3D 前端 (index.html)
"""

import sys
import os
import json
import argparse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# 修复 Windows 控制台编码问题（GBK 无法显示部分 Unicode 字符）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ================================================================
# 路径设置：让 text-prototype 的 src/ 模块可导入
# ================================================================
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_PROTO_DIR = os.path.join(SERVER_DIR, "text-prototype")
THREE_D_DIR = os.path.join(SERVER_DIR, "3d-prototype")
MODELS_DIR = os.path.join(SERVER_DIR, "assets", "models")
TEXTURES_DIR = os.path.join(SERVER_DIR, "assets", "textures")

sys.path.insert(0, TEXT_PROTO_DIR)

# ================================================================
# 导入游戏核心模块（无 AI 依赖）
# ================================================================
from src.game_data import ALL_NPCS, ENTRANCE_ORDER
from src.state_machine import StateMachine
from src.config import DEEPSEEK_API_KEY, DEBUG_MODE

# ================================================================
# 导入 AI 管线（可选——缺少 openai 包时降级为模拟模式）
# ================================================================
_AI_AVAILABLE = False
try:
    from src.ai_pipeline import parse_intent, generate_npc_reply, generate_guardian_ambient
    _AI_AVAILABLE = True
except Exception as e:
    print(f"  [WARN] AI 管线不可用（缺少依赖）: {e}")
    print(f"         将使用关键词回退 + 模拟回复进行 UI 测试。")

# AI 是否真正可用（包已安装 AND API Key 有效）
_API_KEY_VALID = DEEPSEEK_API_KEY not in ("your-api-key-here", "")
_AI_USABLE = _AI_AVAILABLE and _API_KEY_VALID

# ================================================================
# 全局游戏状态（整个服务器共享一个状态机实例）
# ================================================================
_state_machine = StateMachine()
_default_target = "guardian"  # 当前默认对话对象


# ================================================================
# 辅助函数
# ================================================================

def _resolve_npc(name: str) -> str:
    """根据名字/关键词解析 NPC ID"""
    name = name.lower().strip()
    mapping = {
        "baruk": "baruk", "巴鲁克": "baruk", "矮人": "baruk",
        "liana": "liana", "莉安娜": "liana", "精灵": "liana",
        "margaret": "margaret", "玛格丽特": "margaret", "牧师": "margaret",
        "rog": "rog", "罗格": "rog", "兽人": "rog",
        "guardian": "guardian", "守护灵": "guardian",
    }
    return mapping.get(name, "")


def _get_entrance_line(npc_id: str) -> str:
    """NPC 入场台词"""
    lines = {
        "rog": (
            "（他用力推开石门的最后一寸，粗重地喘着气，"
            "眼睛在殿内扫了一圈，停在了守护灵上）……这是什么地方？你是谁？"
        ),
        "baruk": (
            "（他没有看任何人。他一进门就盯着墙——那些刻痕。"
            "他的下巴绷紧了，然后他慢慢走过去，把粗糙的手掌按在墙面上）"
        ),
        "liana": (
            "（她推开门，仰头看见殿顶的浮雕——那一瞬间，她的嘴张开了。"
            "不是因为美——是因为某种认出。然后她看到了守护灵）"
            "……这建筑……这风格……这是第几纪元？"
        ),
        "margaret": (
            "（她站在门口——她的左手擦过脸上干涸的血迹，右手拿着法杖。"
            "她的眼睛直接锁定了守护灵。她的下巴收紧了一寸）"
        ),
        "guardian": "一千年了。你是第一个无关之人。",
    }
    return lines.get(npc_id, "（沉默地走了进来，环顾四周。）")


def _build_context(sm: StateMachine, target_npc_id: str) -> str:
    """为 AI 管线构建当前对话语境字符串"""
    parts = [
        "当前在场 NPC: " + (
            ", ".join(sm.game.present_npcs)
            if sm.game.present_npcs else "仅守护灵"
        ),
        "对话模式: " + ("悄悄话" if sm.game.whisper_mode else "公开对话"),
    ]
    if target_npc_id:
        defn = sm.get_npc_def(target_npc_id)
        if defn:
            parts.append(f"对话对象: {defn.name}")
    for ri in sm.game.recent_interactions[-5:]:
        parts.append(f"最近: {ri}")
    return "\n".join(parts)


def _build_npc_states(sm: StateMachine) -> dict:
    """构建所有 NPC 状态摘要（供前端 UI 显示）"""
    states = {}
    for npc_id, npc_state in sm.npcs.items():
        if npc_id == "guardian":
            continue  # 守护灵独立处理
        states[npc_id] = {
            "trust": npc_state.trust_player,
            "mood": npc_state.mood,
        }
    return states


def _mock_reply(npc_name: str, player_input: str, mood: str) -> str:
    """当 AI 不可用时的模拟回复（用于 UI 测试）"""
    replies = {
        "calm": f"（{npc_name} 看向了你）你说的，我听到了。",
        "tense": f"（{npc_name} 的表情微微紧绷）……这个问题，让我想一想。",
        "angry": f"（{npc_name} 的眼中闪过一丝怒意）你不该这么问的。",
        "vulnerable": (
            f"（{npc_name} 沉默了一会儿，像是在和自己斗争）"
            f"……有些话，我不知道该不该说。"
        ),
        "hopeful": f"（{npc_name} 嘴角浮起一丝难得的笑意）也许，你是对的。",
    }
    return replies.get(mood, f"（{npc_name} 沉默着，似乎在思考你的话。）")


def _fallback_intent(user_input: str) -> dict:
    """
    AI 不可用时的关键词回退解析。
    与 ai_pipeline._fallback_intent 逻辑一致。
    """
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


# 悄悄话交易关键词（设计文档第六节）
_TRADE_KEYWORDS = ["钱", "钥匙", "信物", "秘密", "承诺", "投票", "站队", "不揭发", "背叛"]


def _contains_trade_keywords(text: str) -> bool:
    """判断玩家输入中是否含悄悄话交易关键词"""
    return any(k in text for k in _TRADE_KEYWORDS)


# ================================================================
# HTTP 请求处理器
# ================================================================

class GameAPIHandler(BaseHTTPRequestHandler):
    """
    处理所有 HTTP 请求的核心处理器。
    每个请求对应一个独立线程（由 ThreadingHTTPServer 管理）。
    """

    # 日志控制（DEBUG_MODE 下打印请求日志）
    def log_message(self, format, *args):
        if DEBUG_MODE:
            super().log_message(format, *args)

    # ================================================================
    # CORS 和通用响应
    # ================================================================

    def _set_cors_headers(self):
        """设置跨域响应头，允许浏览器 HTML 跨域请求"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_path: str):
        """发送 HTML 文件（静态文件服务）"""
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._send_json({"error": "index.html 未找到，请确认 3d-prototype 目录存在"}, 404)

    def _read_body(self) -> dict:
        """读取请求体中的 JSON 数据（兼容多种编码）"""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        # 优先尝试 UTF-8（浏览器标准），失败则尝试其他常见编码
        for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                text = raw.decode(enc)
                return json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return {}

    # ================================================================
    # 路由分发
    # ================================================================

    def do_OPTIONS(self):
        """CORS 预检请求"""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """GET 请求路由"""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/" or path == "/index.html":
            # 静态文件：返回 3D 前端页面
            index_path = os.path.join(THREE_D_DIR, "index.html")
            self._send_html(index_path)

        elif path == "/api/state":
            self._handle_get_state()

        elif path == "/api/memories":
            self._handle_get_memories()

        elif path == "/api/reset":
            self._handle_reset()

        else:
            # 尝试作为 3d-prototype 目录下的静态文件处理（JS/CSS/图片等）
            self._try_serve_static(path)

    def do_POST(self):
        """POST 请求路由"""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/chat":
            self._handle_chat()

        elif path == "/api/advance":
            self._handle_advance()

        elif path == "/api/reset":
            self._handle_reset()

        else:
            self._send_json({"error": f"未知端点: {path}"}, 404)

    # ================================================================
    # 静态文件服务
    # ================================================================

    def _try_serve_static(self, path: str):
        """
        尝试提供静态文件。
        默认从 3d-prototype 目录；/models/ 前缀白名单映射到 assets/models/（模型目录）。
        均包含路径穿越防护。
        """
        # /models/ 前缀 → assets/models/（位于 3d-prototype 之外，需白名单）
        if path.startswith("/models/"):
            self._serve_file(
                os.path.join(MODELS_DIR, os.path.normpath(path[len("/models/"):])),
                MODELS_DIR,
            )
            return

        # /textures/ 前缀 → assets/textures/（CC0 纹理）
        if path.startswith("/textures/"):
            self._serve_file(
                os.path.join(TEXTURES_DIR, os.path.normpath(path[len("/textures/"):])),
                TEXTURES_DIR,
            )
            return

        # 默认：3d-prototype 目录
        safe_path = os.path.normpath(path.lstrip("/"))
        self._serve_file(os.path.join(THREE_D_DIR, safe_path), THREE_D_DIR)

    def _serve_file(self, file_path: str, root_dir: str):
        """读取并返回文件；带路径穿越防护与 MIME 映射。"""
        # 安全检查：确保文件在 root_dir 内
        real = os.path.realpath(file_path)
        root_real = os.path.realpath(root_dir)
        if not real.startswith(root_real):
            self._send_json({"error": "禁止访问"}, 403)
            return

        if not os.path.isfile(file_path):
            self._send_json({"error": "文件未找到"}, 404)
            return

        # 根据扩展名设置 MIME 类型
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".glb": "model/gltf-binary",
            ".gltf": "model/gltf+json",
            ".fbx": "application/octet-stream",
            ".hdr": "application/octet-stream",
            ".wasm": "application/wasm",
            ".woff2": "font/woff2",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_json({"error": f"文件读取失败: {str(e)}"}, 500)

    # ================================================================
    # API: POST /api/chat — 玩家对话
    # ================================================================

    def _handle_chat(self):
        """
        处理玩家自由文本对话。
        流程：输入 → 意图解析 → 状态机裁决 → 回复生成 → JSON 响应
        """
        global _default_target

        body = self._read_body()
        # 兼容前端 {message} 与直接 API 调用 {input} 两种字段名
        user_input = body.get("input", "") or body.get("message", "")
        mode = body.get("mode", "public")        # "public" | "whisper"
        # 兼容前端 {target} 与 API {whisper_target} 两种字段名
        whisper_target = body.get("whisper_target", None) or body.get("target", None)

        if not user_input.strip():
            self._send_json({"error": "请提供 input 或 message 字段"}, 400)
            return

        # 前端连接探测：不进入状态机，避免污染对话节奏计数
        if user_input.strip() == "__ping__":
            self._send_json({"pong": True, "reply": ""})
            return

        sm = _state_machine

        # === 悄悄话模式切换 ===
        if mode == "whisper" and whisper_target:
            if whisper_target in sm.game.present_npcs or whisper_target == "guardian":
                sm.game.whisper_mode = True
                sm.game.whisper_target = whisper_target
                target = whisper_target
            else:
                target = _default_target
        elif mode == "public":
            sm.game.whisper_mode = False
            sm.game.whisper_target = None
            # 公共模式若前端明确指定对话对象，尊重它（前提是该 NPC 在场）
            if whisper_target and whisper_target in sm.game.present_npcs:
                target = whisper_target
                _default_target = whisper_target
            else:
                target = _default_target
        else:
            target = _default_target

        # === 确定对话目标 ===
        defn = sm.get_npc_def(target)
        if not defn:
            if sm.game.present_npcs:
                target = next(iter(sm.game.present_npcs))
                _default_target = target
                defn = sm.get_npc_def(target)
            else:
                target = "guardian"
                _default_target = "guardian"
                defn = sm.get_npc_def("guardian")

        # === 构建语境 ===
        context = _build_context(sm, target)

        # === 1. 意图解析（AI 或关键词回退） ===
        if _AI_USABLE:
            try:
                intent = parse_intent(user_input, context)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"  [SERVER] AI 意图解析失败: {e}，降级为关键词回退")
                intent = _fallback_intent(user_input)
        else:
            intent = _fallback_intent(user_input)

        if DEBUG_MODE:
            print(f"  [SERVER] 意图: {intent.get('intent')} → "
                  f"{intent.get('target_npc') or 'auto'} "
                  f"(conf: {intent.get('confidence', 0):.0%})"
                  + (" [fallback]" if intent.get("fallback") else ""))

        # 意图中的目标覆盖当前目标（仅在公开模式）
        if intent.get("target_npc") and intent["target_npc"] in sm.game.present_npcs:
            if not sm.game.whisper_mode:
                target = intent["target_npc"]
                _default_target = target
                defn = sm.get_npc_def(target)

        intent["target_npc"] = target
        # 悄悄话交易关键词检测：把完整玩家输入作为 terms 传给状态机
        intent.setdefault("terms", user_input)
        # 悄悄话模式下，若输入含交易关键词，强制作为 ask_favor（交易）处理
        if sm.game.whisper_mode and _contains_trade_keywords(user_input):
            intent["intent"] = "ask_favor"

        # === 2. 状态机裁决 ===
        result = sm.process_intent(intent)
        if result.get("result") == "error":
            self._send_json({"error": result.get("message", "处理失败")}, 400)
            return

        # === 3. 生成 NPC 回复 ===
        npc_state = sm.get_npc_state(target)
        current_mood = npc_state.mood if npc_state else "calm"
        env = sm.get_environment_state()

        if _AI_USABLE:
            try:
                reply = generate_npc_reply(
                    npc_name=defn.name,
                    npc_race=defn.race,
                    npc_title=defn.title,
                    talk_style=defn.talk_style,
                    mood=current_mood,
                    response_direction=result.get("response_direction", ""),
                    player_input=user_input,
                    context=context,
                    slip_occurred=result.get("slip_occurred", False),
                    revelation_line=result.get("revelation_line", ""),
                    is_whisper=sm.game.whisper_mode,
                    present_npcs=(
                        list(sm.game.present_npcs)
                        if not sm.game.whisper_mode else []
                    ),
                    guardian_light=env["guardian_light"],
                )
            except Exception as e:
                if DEBUG_MODE:
                    print(f"  [SERVER] AI 回复生成失败: {e}，降级为模拟回复")
                reply = _mock_reply(defn.name, user_input, current_mood)
        else:
            # 模拟模式（无 AI）
            if result.get("slip_occurred"):
                reply = result.get("revelation_line",
                                   f"（{defn.name} 说漏了嘴——那是他不该说的秘密。）")
            else:
                reply = _mock_reply(defn.name, user_input, current_mood)

        # === 4. 检查结局 ===
        ending = sm.check_ending()

        # === 5. 构建完整响应 ===
        # 悄悄话 UI 数据（设计文档第六节）
        whisper_data = {
            "mode": sm.game.whisper_mode,
            "target": sm.game.whisper_target,
        }
        if "whisper_deal_accepted" in result:
            whisper_data["deal_accepted"] = result["whisper_deal_accepted"]
        if result.get("whisper_hesitant"):
            whisper_data["hesitant"] = True
        if result.get("deal_type"):
            whisper_data["deal_type"] = result["deal_type"]
        if sm.game.whisper_mode:
            whisper_data["guardian_notice"] = "守护灵的光芒在你耳边轻轻波动——它在记录。"

        response = {
            "reply": reply,
            "npc_name": defn.name,
            "npc_id": target,
            "mood": current_mood,
            "slip_occurred": result.get("slip_occurred", False),
            "secret_id": result.get("secret_id", None),
            "event_chain": result.get("event_chain", []),
            "environment": env,
            "npc_states": _build_npc_states(sm),
            "hints": sm.get_visible_hints(),
            "ending": ending,
            "present_npcs": list(sm.game.present_npcs),
            "whisper_mode": sm.game.whisper_mode,
            "guardian_score": sm.game.guardian_moral_score,
            "memories": sm.game.player_memories,
            "whisper": whisper_data,
            "pacing_hint": sm.get_pacing_hint(),
        }
        self._send_json(response)

    # ================================================================
    # API: POST /api/advance — 推进阶段
    # ================================================================

    def _handle_advance(self):
        """推进到下一阶段，触发新 NPC 入场"""
        global _default_target
        sm = _state_machine

        new_npc = sm.advance_stage()

        if new_npc is None:
            self._send_json({
                "stage": sm.game.current_stage,
                "message": "所有角色已到场",
                "new_npc": None,
                "present_npcs": list(sm.game.present_npcs),
            })
            return

        stage = sm.game.current_stage
        desc = ENTRANCE_ORDER[stage]["description"]
        defn = sm.get_npc_def(new_npc)
        entrance_line = _get_entrance_line(new_npc) if defn else ""

        # 更新默认对话目标为新入场的 NPC
        _default_target = new_npc

        response = {
            "stage": stage,
            "new_npc": new_npc,
            "npc_name": defn.name if defn else "",
            "entrance_line": entrance_line,
            "description": desc,
            "present_npcs": list(sm.game.present_npcs),
            "environment": sm.get_environment_state(),
            "hints": sm.get_visible_hints(),
            "pacing_hint": sm.get_pacing_hint(),
        }
        self._send_json(response)

    # ================================================================
    # API: GET /api/state — 获取当前完整游戏状态
    # ================================================================

    def _handle_get_state(self):
        """返回完整游戏状态，供前端初始化/调试使用"""
        sm = _state_machine

        # 详细 NPC 状态
        npc_states = {}
        for npc_id, npc_state in sm.npcs.items():
            defn = sm.get_npc_def(npc_id)
            npc_states[npc_id] = {
                "name": defn.name if defn else npc_id,
                "race": defn.race if defn else "",
                "title": defn.title if defn else "",
                "trust_player": npc_state.trust_player,
                "mood": npc_state.mood,
                "attitudes": dict(npc_state.attitudes),
                "revealed_secrets": list(npc_state.revealed_secrets),
            }

        response = {
            "game": {
                "current_stage": sm.game.current_stage,
                "present_npcs": list(sm.game.present_npcs),
                "whisper_mode": sm.game.whisper_mode,
                "whisper_target": sm.game.whisper_target,
                "guardian_moral_score": sm.game.guardian_moral_score,
                "triggered_events": sm.game.triggered_events,
                "recent_interactions": sm.game.recent_interactions[-10:],
                "player_memories": sm.game.player_memories,
                "whisper_deals": sm.game.whisper_deals,
            },
            "npcs": npc_states,
            "environment": sm.get_environment_state(),
            "hints": sm.get_visible_hints(),
            "ending": sm.check_ending(),
            "pacing_hint": sm.get_pacing_hint(),
        }
        self._send_json(response)

    # ================================================================
    # API: GET /api/memories — 获取玩家记忆与在场 NPC
    # ================================================================

    def _handle_get_memories(self):
        """返回玩家记忆列表与在场 NPC（供前端记忆面板展示）"""
        sm = _state_machine
        self._send_json({
            "memories": sm.game.player_memories,
            "present_npcs": list(sm.game.present_npcs),
        })

    # ================================================================
    # API: GET|POST /api/reset — 重置游戏
    # ================================================================

    def _handle_reset(self):
        """重置整个游戏状态，回到初始阶段"""
        global _state_machine, _default_target
        _state_machine = StateMachine()
        _default_target = "guardian"
        self._send_json({
            "message": "游戏已重置",
            "environment": _state_machine.get_environment_state(),
        })


# ================================================================
# 服务器启动入口
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description="封印之殿 — HTTP 游戏服务器"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="HTTP 端口（默认: 8080）",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="监听地址（默认: 0.0.0.0）",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="强制关闭 AI，使用关键词回退 + 模拟回复（确定性模式，用于自动化测试/离线体验）",
    )
    args = parser.parse_args()

    # === --no-ai：强制确定性回退模式（自动化测试不受 AI 意图漂移/延迟影响） ===
    if args.no_ai:
        global _AI_USABLE
        _AI_USABLE = False

    # === API Key 检查 ===
    ai_ready = _AI_USABLE

    if not _API_KEY_VALID:
        print("[WARN] 未检测到 DEEPSEEK_API_KEY 环境变量！")
        print("   服务器将以模拟模式运行（用于 UI 测试）。")
        print("   设置方法: set DEEPSEEK_API_KEY=sk-xxxxx")
        print()
    elif args.no_ai:
        print("[INFO] --no-ai 已指定：AI 强制关闭，使用关键词回退 + 模拟回复。")
        print()
    else:
        print(f"[OK] DEEPSEEK_API_KEY 已配置 ({DEEPSEEK_API_KEY[:8]}...)")
        print()

    # === 启动横幅 ===
    print("=" * 62)
    print("  封印之殿 Server 启动: http://localhost:{}".format(args.port))
    print("=" * 62)
    print("  API:")
    print("    POST /api/chat     — 玩家对话（JSON 输入/输出）")
    print("    POST /api/advance  — 推进阶段，新 NPC 入场")
    print("    GET  /api/state    — 获取当前完整游戏状态")
    print("    POST /api/reset    — 重置游戏")
    print("    GET  /             — 返回 3D 前端页面")
    print(f"  AI 状态: {'[OK] 在线（DeepSeek V4）' if ai_ready else '[WARN] 模拟模式（UI 测试）'}")
    print("=" * 62)

    # === 启动 HTTP 服务 ===
    server = ThreadingHTTPServer((args.host, args.port), GameAPIHandler)
    try:
        print("\n  按 Ctrl+C 停止服务器\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  殿中归于寂静。服务器已关闭。")
        server.server_close()


if __name__ == "__main__":
    main()
