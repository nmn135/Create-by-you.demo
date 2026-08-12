"""
封印之殿 文字原型 — 配置文件
"""
import os

# === DeepSeek API 配置 ===
# 优先读 DEEPSEEK_API_KEY；未设置时回退到 ANTHROPIC_API_KEY（用户的 DeepSeek key，同一把）
DEEPSEEK_API_KEY = (
    os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("ANTHROPIC_API_KEY")
    or "your-api-key-here"
)
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 型号选择：DeepSeek 官方模型仅 deepseek-chat（V3.2+，快且准）与 deepseek-reasoner（思考型）。
# 意图解析与回复生成统一用 deepseek-chat——实测 ~0.3s 响应、JSON 稳定。
# 注意：历史上用过 "deepseek-v4-pro"/"deepseek-v4-flash"（2026-08-12 曾出现在旧配置），
# 这两个不是有效模型名，会导致空响应/卡顿而触发整条兜底链；已废弃。
INTENT_MODEL = "deepseek-chat"      # 意图解析
REPLY_MODEL = "deepseek-chat"       # 回复生成

# === 游戏参数 ===
INITIAL_TRUST = 30          # 初始信任度
MAX_TRUST = 100
MIN_TRUST = -100
SLIP_THRESHOLD = 0.55       # 失言概率阈值 (0-1)
WHISPER_GUARDIAN_PENALTY = 3  # 每次悄悄话守护灵扣分
DEBUG_MODE = True           # 是否打印调试信息（关系值变化等）
