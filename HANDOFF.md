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
| 场景图 | 修复丢失的 bg.png；新增正式 bg_day2.png（第二天） | ✅ |
| 第二天场景框架 | SCENES 状态机（day7/day2），正式图自动替换程序化元素 | ✅ |
| 上轮记忆回顾 | NPC 对话窗口显示上次最后说的话（recap + 存档） | ✅ |
| 角色锚定 | 服务端 persona 锚定 + fixStageDir 动作主语兜底 | ✅ |
| 玩法打磨 | 气泡截断/防重叠/对比度，闲聊频率与台词扩充 | ✅ |
| 节点分支对话 | v1：骑砍式话题快捷栏（告别/打听/交易/套话，条件解锁） | ✅ |
| 对话相机 | 对话推近 NPC（lerp 缓动） | ✅ |
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
- 游戏逻辑：`2d-narrative-demo/index.html`（像素渲染、NPC 站点巡游、隔墙有耳、失言演出、话题快捷栏、对话相机）
- AI 引擎：DeepSeek `deepseek-chat`，key 读 `DEEPSEEK_API_KEY`（`2d-narrative-demo/.env` 或环境变量）

## 五、测试（验收标准）

```bash
cd D:\Create by you.demo\game-prototypes\text-prototype
python -X utf8 test_state_machine.py      # 30/30
python -X utf8 tests/test_endings.py      # 46/46
python -X utf8 tests/test_dialogue_scenarios.py  # 需 DEEPSEEK_API_KEY
```

2D demo 回归（DOM/Canvas 桩，无需浏览器）：

```bash
cd D:\Create by you.demo\game-prototypes\2d-narrative-demo
node _harness.js                          # 24/24
```

## 六、关键约定

- **中文优先**（所有注释/回复/UI）
- 3D 方案已删除，**勿再引入 3D 资源或恢复旧文件**
- 2D demo 资产放 `2d-narrative-demo/` 内
- 调试钩子在 `window.__game`（含 debugOpenDialogue/debugResetSecrets/cam 等）
- `_harness.js` 是 DOM/Canvas 桩回归测试，改动 index.html 后跑一遍

## 七、待办

- 剧情分支与结局演出（主线尚未收尾）
- 节点分支对话 v2（真正的脚本节点图 + 分支跳转，替代"话题路由 AI"）
- 试玩后按 PLAYTEST_CHECKLIST 回归
