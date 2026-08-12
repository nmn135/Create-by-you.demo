---
title: 封印之殿 — 每日决策摘要
date: 2026-08-13
tags: [game-design, sealed-hall, decision]
---

# 封印之殿 每日决策摘要

> **2026-08-13 决策**：放弃 3D 方案，专注 2D 叙事 demo《第七天》。3D 代码/资产/文档已全部删除。

## 当前方向

- **只做**：`game-prototypes/2d-narrative-demo/`（Canvas 2D + Node + DeepSeek，端口 8890）
- **保留**：`text-prototype/`（Python 终端，失言系统逻辑参考）
- **已删**：3D 原型、Mixamo/Sketchfab 资产、server.py、3D 文档

## 2D demo 已修复（用户反馈）

- 画面模糊 → 3× 分辨率渲染（960×540）+ 字体加大
- 对话慢 → DeepSeek 引擎（~3s，doubao 兜底）
- 「游戏坏了」→ 场景背景图丢失（bg.png 被删、新图误存 bd*.png）已改名归位；loadGame 旧档残留修复

## 2026-08-13 深夜自主会话新增

- 第二天场景框架 + 正式 bg_day2.png
- NPC 上轮回复记忆回顾（recap）
- 服务端角色锚定 + fixStageDir 动作主语兜底
- 玩法打磨（气泡截断/防重叠、闲聊频率与台词）
- **骑砍式话题快捷栏 v1**（告别/打听/交易/套话，条件解锁）——节点分支对话的轻量落地
- 对话相机推近（lerp 缓动）

## 待办

- 剧情分支与结局演出（主线尚未收尾）
- 节点分支对话 v2（真正的脚本节点图 + 分支跳转）
- 试玩回归（PLAYTEST_CHECKLIST）
