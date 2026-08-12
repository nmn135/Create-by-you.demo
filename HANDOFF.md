---
title: 封印之殿 — 会话交接文档
date: 2026-08-13
tags: [game-design, sealed-hall, handoff]
---

# 封印之殿 — 会话交接

> 给下一个会话的助手：读完本文件即可无缝接手。项目在 **D 盘**（不在 vault）。
> **2026-08-13 方向变更**：3D 方案已全部删除，当前只做 2D 叙事 demo《第七天》。

## 一、项目位置

- **项目根目录**：`D:\Create by you.demo\`
- 所有操作使用**绝对路径**，因为项目在 vault 之外

## 二、当前进度（2026-08-13）

| 项 | 内容 | 状态 |
|:---:|------|:---:|
| 2D 叙事 demo《第七天》 | Canvas 2D + Node + DeepSeek，端口 8890 | ✅ 主项目 |
| 2D 清晰度修复 | 3× 分辨率渲染（960×540）+ 字体加大 | ✅ |
| 2D 对话引擎 | DeepSeek `deepseek-chat` 优先，doubao 兜底 | ✅ |
| 文字原型 | Python 终端，失言系统/状态机逻辑参考 | ✅ 保留 |
| 3D 方案 | 3d-prototype/、server.py、资产、文档 | ❌ 已删除 |

## 三、启动命令（必须）

```bash
cd D:\Create by you.demo\game-prototypes\2d-narrative-demo
node server.js    # 端口 8890
# 浏览器打开 http://localhost:8890
```

## 四、架构

```
浏览器 Canvas 2D（2d-narrative-demo/index.html） ←HTTP/JSON→ server.js ←→ DeepSeek API
```

- 对话引擎：`2d-narrative-demo/server.js`（多 NPC persona、意图解析、回复生成）
- 游戏逻辑：`2d-narrative-demo/index.html`（像素渲染、NPC 站点巡游、隔墙有耳、失言演出）
- AI 引擎：DeepSeek `deepseek-chat`，key 读 `DEEPSEEK_API_KEY`（`2d-narrative-demo/.env` 或环境变量）

## 五、测试（验收标准）

```bash
cd D:\Create by you.demo\game-prototypes\text-prototype
python -X utf8 test_state_machine.py      # 30/30
python -X utf8 tests/test_endings.py      # 46/46
python -X utf8 tests/test_dialogue_scenarios.py  # 需 DEEPSEEK_API_KEY
```

## 六、关键约定

- **中文优先**（所有注释/回复/UI）
- 3D 方案已删除，**勿再引入 3D 资源或恢复旧文件**
- 2D demo 资产放 `2d-narrative-demo/` 内

## 七、待办

- 2D demo 玩法打磨（NPC 闲聊频率/气泡可读性）
- 节点分支对话（骑砍式话题树）
- 剧情分支与结局演出
