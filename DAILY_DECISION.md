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

## 待办

- 2D demo 玩法打磨
- 节点分支对话
- 剧情分支与结局演出
