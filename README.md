# 封印之殿（Sealed Hall）

一个以自然语言对话驱动的 2D 像素叙事游戏 demo。

## 快速开始

- **双击根目录 `启动第七天.bat`**（推荐）——自动检查 Node、启动服务器、打开浏览器
- 或手动启动：
  ```bash
  cd game-prototypes/2d-narrative-demo
  node server.js        # 服务器端口 8890
  ```
- 浏览器访问 <http://localhost:8890>

## 目录结构

- `game-prototypes/2d-narrative-demo/` — **2D 叙事 demo《第七天》**（Canvas 2D + Node + DeepSeek AI，当前主项目）
- `game-prototypes/text-prototype/` — Python 终端文字原型（失言系统/状态机逻辑参考）
- `docs/` — 对话交互设计调研

## 协作

- 协作规则见 [AGENTS.md](AGENTS.md)（随 git 同步，双方 AI 都读）
- 交接文档见 [HANDOFF.md](HANDOFF.md)

> 2026-08-13：3D 方案（3d-prototype、Mixamo 资产等）已全部删除，项目专注 2D 叙事方向。
