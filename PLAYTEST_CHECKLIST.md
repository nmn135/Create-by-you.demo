---
title: 封印之殿 — 试玩前检查清单
date: 2026-08-13
tags: [game-design, sealed-hall, playtest]
---

# 封印之殿 — 试玩前检查清单（2D 叙事 demo）

> **2026-08-13**：3D 方案已删除，当前试玩目标为 2D 叙事 demo《第七天》。

## 一、启动游戏

```bash
cd D:\Create by you.demo\game-prototypes\2d-narrative-demo
node server.js
```

浏览器打开 **http://localhost:8890**

## 二、试玩重点

1. **画面清晰度**：文字/气泡是否清晰（已 3× 分辨率渲染）
2. **对话速度**：与 NPC 对话是否快（DeepSeek ~3s 端到端）
3. **NPC 闲聊**：NPC 之间自发闲聊（隔墙有耳）——频率/可读性是否合适
4. **失言系统**：连续追问触发 NPC 失言
5. **话题快捷栏**：对话面板顶部话题按钮（告别/打听/交易/套话）——条件解锁是否合理、告别是否正常关闭
6. **对话相机**：进入对话推近 NPC 是否自然、退出是否回位
7. **第二天**：泄密给 NPC 后进入第二天，正式 bg_day2.png 是否正常显示

## 三、如果遇到问题

| 现象 | 处理 |
|------|------|
| 页面打不开 | 确认 `node server.js` 在 8890 端口运行 |
| 对话无回复 | 确认 `DEEPSEEK_API_KEY` 已设置（`2d-narrative-demo/.env` 或环境变量） |
| 对话全是模板回复 | AI 未生效，检查 key/引擎配置 |
