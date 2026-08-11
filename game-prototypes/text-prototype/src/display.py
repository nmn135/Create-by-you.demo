"""
封印之殿 文字原型 — 终端显示
彩色文本输出、格式化
"""
import os
import sys
import shutil

# === 颜色代码（ANSI） ===
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"

    # 前景色
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 背景色
    BG_DIM = "\033[48;5;236m"
    BG_GOLD = "\033[48;5;94m"
    BG_DARK_RED = "\033[48;5;52m"
    BG_PURPLE = "\033[48;5;53m"

# === 终端宽度 ===
def terminal_width() -> int:
    return shutil.get_terminal_size().columns

def divider(char: str = "─", color: str = Color.DIM) -> str:
    return color + char * min(terminal_width(), 80) + Color.RESET

def thin_divider() -> str:
    return Color.DIM + "· " * 30 + Color.RESET

# === NPC 颜色主题 ===
NPC_COLORS = {
    "liana": Color.BRIGHT_GREEN,
    "baruk": Color.BRIGHT_YELLOW,
    "margaret": Color.BRIGHT_WHITE,
    "rog": Color.BRIGHT_RED,
    "guardian": Color.BRIGHT_CYAN,
}

NPC_ICONS = {
    "liana": "🧝",
    "baruk": "⚒️",
    "margaret": "✝️",
    "rog": "🪓",
    "guardian": "✨",
}

# === 显示函数 ===

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_title():
    w = min(terminal_width(), 80)
    print(Color.BRIGHT_CYAN + Color.BOLD)
    print("╔" + "═" * (w - 2) + "╗")
    print("║" + "封印之殿 — Sealed Hall".center(w - 4) + "  ║")
    print("║" + "文字原型 v0.1".center(w - 4) + "  ║")
    print("╚" + "═" * (w - 2) + "╝" + Color.RESET)
    print()

def print_narrative(text: str):
    """打印叙事文本（环境描述、事件描述）"""
    print(Color.ITALIC + Color.DIM + text + Color.RESET)
    print()

def print_npc_dialogue(npc_id: str, npc_name: str, text: str, is_whisper: bool = False):
    """打印 NPC 对话"""
    color = NPC_COLORS.get(npc_id, Color.WHITE)
    icon = NPC_ICONS.get(npc_id, "")
    whisper_tag = " [悄悄话]" if is_whisper else ""
    prefix = f"{color}{Color.BOLD}{icon} {npc_name}{whisper_tag}:{Color.RESET}"
    print(prefix)
    print(f"  {text}")
    print()

def print_hint(text: str):
    """打印可视线索"""
    print(Color.DIM + text + Color.RESET)

def print_debug(text: str):
    """打印调试信息"""
    print(Color.DIM + Color.ITALIC + f"  [{text}]" + Color.RESET)

def print_environment(env: dict):
    """打印环境状态"""
    print()
    print(thin_divider())
    print(Color.DIM + f"  ✦ {env['guardian_light']}" + Color.RESET)
    print(Color.DIM + f"  符文: {env['rune_state']}  ·  温度: {env['temperature']}" + Color.RESET)
    print(thin_divider())
    print()

def print_stage_transition(description: str):
    """打印阶段转换"""
    print()
    print(Color.BRIGHT_MAGENTA + "▸ " + description + Color.RESET)
    print()

def print_whisper_mode(target_name: str):
    print()
    print(Color.BRIGHT_MAGENTA + Color.BOLD +
          f"🔇 你将 {target_name} 拉到了一旁——这是悄悄话。" + Color.RESET)
    print(Color.DIM + "其他人注意到你们走开了。但他们听不到你们的对话。" + Color.RESET)
    print(Color.DIM + "但守护灵的光芒在你耳边轻轻波动……它在听。" + Color.RESET)
    print()

def print_ending(narrative: str):
    """打印结局"""
    clear_screen()
    print(Color.BRIGHT_CYAN + Color.BOLD)
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                       终  局                                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(Color.RESET)
    print()
    for line in narrative.strip().split("\n"):
        if line.strip():
            print(Color.BOLD + line.strip() + Color.RESET)
    print()
    print(divider())
    print()

def print_memory_panel(known_secrets: dict, relationships: dict):
    """打印对话记忆面板"""
    print()
    print(Color.BOLD + Color.CYAN + "╔══ 记忆面板 ══════════════════════════════════════════════╗" + Color.RESET)
    print(Color.CYAN + "║" + Color.RESET + " 📋 你现在知道的：".ljust(56) + Color.CYAN + "║" + Color.RESET)

    for npc_id, secrets in known_secrets.items():
        if secrets:
            name = _npc_short_name(npc_id)
            print(Color.CYAN + "║" + Color.RESET + f"   {Color.BOLD}{name}{Color.RESET}:".ljust(58) + Color.CYAN + "║" + Color.RESET)
            for s in secrets[-2:]:  # 最多显示 2 条
                print(Color.CYAN + "║" + Color.RESET + f"     · {s[:40]}...".ljust(58) + Color.CYAN + "║" + Color.RESET)

    print(Color.CYAN + "╚" + "═" * 57 + "╝" + Color.RESET)
    print()

def _npc_short_name(npc_id: str) -> str:
    names = {"liana": "莉安娜(精灵)", "baruk": "巴鲁克(矮人)",
             "margaret": "玛格丽特(牧师)", "rog": "罗格(兽人)", "guardian": "守护灵"}
    return names.get(npc_id, npc_id)

def print_help():
    """打印帮助信息"""
    print(Color.DIM)
    print("  命令提示：")
    print("  /h        查看此帮助")
    print("  /w <NPC>  切换悄悄话模式（与指定 NPC 密谈）")
    print("  /p        切换回公开对话")
    print("  /m        查看记忆面板")
    print("  /e        查看环境状态")
    print("  /n /wait  等待/叫下一位到场者入场（推进阶段）")
    print("  /q        退出游戏")
    print("  直接输入文字 = 对当前对话对象说话")
    print(Color.RESET)

def get_input(prompt: str = "> ") -> str:
    """获取玩家输入"""
    try:
        return input(Color.BRIGHT_GREEN + prompt + Color.RESET).strip()
    except (EOFError, KeyboardInterrupt):
        return "/q"
