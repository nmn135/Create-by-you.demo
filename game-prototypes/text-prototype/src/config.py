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

# 型号选择：意图解析用 Pro（高准确度），回复生成用 Flash（便宜、快）
INTENT_MODEL = "deepseek-v4-pro"      # 意图解析
REPLY_MODEL = "deepseek-v4-flash"     # 回复生成

# === 游戏参数 ===
INITIAL_TRUST = 30          # 初始信任度
MAX_TRUST = 100
MIN_TRUST = -100
SLIP_THRESHOLD = 0.55       # 失言概率阈值 (0-1)
WHISPER_GUARDIAN_PENALTY = 3  # 每次悄悄话守护灵扣分
DEBUG_MODE = True           # 是否打印调试信息（关系值变化等）
