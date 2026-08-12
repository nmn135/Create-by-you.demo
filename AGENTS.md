# 封印之殿（Sealed Hall）— 协作规则

> 本文件是**协作事实**（随 git 同步，双方 AI 都读）。启动命令、资源约定、开发规则在此，比 memory 更硬。

## 项目是什么
以自然语言对话驱动的叙事游戏 demo。玩家在 2D 像素画面里与 NPC 自由对话，通过说话改变 NPC 关系、揭露秘密、走向不同结局。

## 当前方向（2026-08-13 起）
- **只做 2D 叙事 demo《第七天》**：`game-prototypes/2d-narrative-demo/`（Canvas 2D + Node 服务 + DeepSeek AI）
- **3D 方案已全部删除**（2026-08-13）：3d-prototype/、server.py、Mixamo/Sketchfab 资产、相关文档均已移除，勿再恢复或引用。

## 启动命令（必须）
```bash
cd game-prototypes/2d-narrative-demo
node server.js        # 启动服务器（端口 8890）
# 浏览器打开 http://localhost:8890
```
- 引擎：DeepSeek `deepseek-chat`（优先读 `DEEPSEEK_API_KEY`，兜底 doubao）
- 详见 `2d-narrative-demo/README.md`

## 架构
```
浏览器 Canvas 2D（2d-narrative-demo/index.html） ←HTTP/JSON→ server.js ←→ DeepSeek API
```
- 对话引擎：`2d-narrative-demo/server.js`（多 NPC persona、意图解析、回复生成）
- 游戏逻辑：`2d-narrative-demo/index.html`（像素渲染、NPC 站点巡游、隔墙有耳、失言演出）

## 文字原型（保留，作状态机参考）
- `text-prototype/`：Python 终端原型，验证失言系统（状态机/AI 管线/结局）。非 3D，保留作逻辑参考。
- 测试：`test_state_machine.py`（30/30）· `tests/test_endings.py`（46/46）

## 资源约定
- 所有 2D demo 资产放 `game-prototypes/2d-narrative-demo/` 内
- 禁止再引入 3D 相关资源（模型/贴图/引擎）

## 开发规则
- 中文优先（所有注释/回复/UI）
- 视觉问题用截图确认，不靠猜
- ponytail 原则：最简方案，YAGNI，不写过度工程代码

## 已知待办
- 2D demo 玩法打磨（NPC 闲聊频率/气泡可读性）
- 节点分支对话（骑砍式话题树）
- 剧情分支与结局演出
