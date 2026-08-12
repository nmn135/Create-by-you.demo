# 封印之殿 — 文字原型

纯终端对话驱动游戏原型。验证"失言系统"和"说话改变世界"机制。

## 快速开始

```bash
cd game-prototypes/text-prototype

# 1. 设置 API Key
set DEEPSEEK_API_KEY=sk-xxxxx
# 或在 src/config.py 中直接填写

# 2. 安装依赖
pip install openai

# 3. 运行
python main.py
```

## 命令

| 命令 | 功能 |
|------|------|
| 直接输入文字 | 与当前对话对象说话 |
| `/w baruk` | 切换悄悄话模式（与巴鲁克密谈） |
| `/p` | 切回公开对话 |
| `/m` | 查看记忆面板（已知秘密） |
| `/e` | 查看环境状态 + NPC 数值 |
| `/n` | 推进到下一阶段（等待下一个 NPC 入场） |
| `/h` | 帮助 |
| `/q` | 退出 |

## 结构

```
text-prototype/
├── main.py              # 游戏入口 + 主循环
├── src/
│   ├── config.py         # API 配置 + 游戏参数（统一 deepseek-chat）
│   ├── game_data.py      # NPC 数据、关系、秘密、对话风格
│   ├── state_machine.py  # 状态机引擎（失言判定、关系变化、结局）
│   ├── ai_pipeline.py    # DeepSeek API（意图解析 + 回复生成，读 prompts/*.txt）
│   └── display.py        # 终端彩色输出
├── prompts/
│   ├── intent_parser_v2.txt     # 意图解析 System Prompt v2（唯一真值）
│   ├── reply_generator_v2.txt   # 回复生成 System Prompt v2（17 个模板变量）
│   └── prompt_changelog.md      # Prompt 修改日志
├── tests/
│   ├── test_state_machine.py    # 状态机单元测试（30/30 通过）
│   ├── test_endings.py          # 结局触发测试（46/46 通过）
│   └── test_dialogue_scenarios.py  # 真实 AI 对话场景（3 策略/9 轮）
└── README.md
```

## AI 管线

```
玩家输入自由文本
  → [DeepSeek deepseek-chat] 意图解析（结构化 JSON，~0.3s）
  → [纯 Python] 状态机裁决（确定性：失言判定/关系/结局）
  → [DeepSeek deepseek-chat] NPC 回复生成（自然语言，情绪动态温度）
  → 终端输出 + 关系变化 + 环境反馈
```

> 模型统一使用官方 `deepseek-chat`。历史配置中的 `deepseek-v4-pro` / `deepseek-v4-flash` 不是有效模型名（会导致空响应/卡顿触发整条兜底链），已于 2026-08-13 修复废弃。

## 失言系统（slip-of-tongue）

- 判定：连续追问 + 情绪压力累积，`SLIP_THRESHOLD = 0.55`
- 触发后：`revelation_line` 标志性台词泄出 + 按 NPC 性格选择行为模式 **A（掩饰）/ B（沉默）/ C（破罐破摔）**
- 悄悄话：守护灵扣分 `WHISPER_GUARDIAN_PENALTY = 3`
- 在场感知：非悄悄话下 NPC 会注意到其他 NPC 的反应，涉密措辞更隐晦

## 验证

- `python test_state_machine.py` — 失言判定/关系变化/结局触发/悄悄话惩罚/出场节奏，**30/30 通过**
- `python tests/test_endings.py` — 5 结局全路径 + 状态缺口回归，**46/46 通过**
- `python tests/test_dialogue_scenarios.py` — DeepSeek 真实对话，**3 策略/9 轮/0 失言**（需 `DEEPSEEK_API_KEY`）
