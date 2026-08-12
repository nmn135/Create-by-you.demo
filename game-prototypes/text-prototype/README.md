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
│   ├── config.py         # API 配置 + 游戏参数
│   ├── game_data.py      # NPC 数据、关系、秘密、对话风格
│   ├── state_machine.py  # 状态机引擎（失言判定、关系变化、结局）
│   ├── ai_pipeline.py    # DeepSeek API（意图解析 Pro + 回复生成 Flash）
│   └── display.py        # 终端彩色输出
└── README.md
```

## AI 管线

```
玩家输入自由文本
  → [DeepSeek V4 Pro] 意图解析（结构化）
  → [纯 Python] 状态机裁决（确定性）
  → [DeepSeek V4 Flash] NPC 回复生成（自然语言）
  → 终端输出 + 关系变化 + 环境反馈
```

## 验证清单

运行后测试以下场景：

- [ ] 失言触发是否自然？（连续追问 3 轮 + 情绪 = angry）
- [ ] 悄悄话 vs 公开对话的张力？
- [ ] 关系值变化是否符合直觉？
- [ ] 结局触发是否可达到？
