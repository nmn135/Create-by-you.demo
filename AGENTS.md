# 封印之殿（Sealed Hall）— 协作规则

> 本文件是**协作事实**（随 git 同步，双方 AI 都读）。启动命令、资源约定、开发规则在此，比 memory 更硬。

## 项目是什么
以自然语言对话驱动的 3D 叙事游戏原型。玩家在浏览器里自由输入对话，通过说话改变 NPC 关系、揭露秘密、走向不同结局。

## 启动命令（必须）
```bash
cd game-prototypes
pip install openai          # 首次
python server.py            # 启动服务器（端口 8080）
# 浏览器打开 http://localhost:8080
```
- `--no-ai` 参数 = 离线模拟模式（自动化测试用）：`python server.py --no-ai`

## 架构
```
浏览器 Three.js（3d-prototype/index.html，单文件） ←HTTP/JSON→ server.py ←→ text-prototype/ 状态机 + DeepSeek API
```
- **状态机**：`text-prototype/src/state_machine.py`（纯 Python，确定性，不依赖 AI）
- **AI 管线**：`text-prototype/src/ai_pipeline.py`（意图解析 Pro + 回复生成 Flash）
- **3D 前端**：`3d-prototype/index.html`（单文件）+ `3d-prototype/src/*.js` 模块（models/guidance/markers/ui_drag/fps_controller/atmosphere/props/settings）

## 资源约定（禁止违反）
- **模型放** `game-prototypes/assets/models/`：`<角色>_tpose.fbx/.glb` + `<角色>_idle.fbx` + `<角色>_talk.fbx`
- **材质放** `game-prototypes/assets/textures/`
- **禁止删除 assets/ 下任何资源**（模型/纹理是素材库，删了游戏就缺）
- Mixamo 模型必须 **With Skin**（否则只有骨骼无网格，角色不可见）；动画才用 Without Skin
- 素材库备份在 `D:\SealedHallAssets\`（本地，不随 git）

## 测试（改完必须跑）
```bash
cd game-prototypes
python -X utf8 integration_test.py        # 16 项端到端
cd text-prototype
python -X utf8 test_state_machine.py      # 30 项
python -X utf8 tests/test_endings.py      # 46 项
```

## 开发规则
- 中文优先（所有注释/回复/UI）
- 视觉问题用截图 + 豆包视觉确认，不靠猜
- 全视角控制器 `src/fps_controller.js`：C 键 fps↔tps，WASD 移动 + Shift 奔跑 + 空格跳 + Z 蹲 + E 交互 + N 推进
- 输入交互：Enter 进输入模式，Esc 退出清空（避免 WASD 被输入框吃）
- ponytail 原则：最简方案，YAGNI，能抄开源就抄，不写过度工程代码

## 调试钩子（自动化验证用）
- `window.__fpsController`：视角控制器实例（mode/pos/euler）
- `window.__getModelStates()`：各角色模型状态（current 动画/clips）
- `window.__getModelManager()`：模型管理器

## 已知待办
- 更多动作动画（攻击/施法）
- 节点分支对话（骑砍式话题树）
- Electron 本地版（可选）
