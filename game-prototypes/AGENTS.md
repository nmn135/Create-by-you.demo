# 封印之殿 (Sealed Hall) — Agent Memory Hub

> 任何 AI Agent 进项目第一件事：读这个文件。包含项目全貌、当前状态、可并行任务和关键约定。每次大改动后更新。

## 项目概览
- **类型**：单页 3D 叙事游戏（three.js WebGL）
- **设定**：千年前半神法师艾瑟林设下预言，四族冒险者聚集封印之殿，玩家作为第五人（无关之人）介入，与 NPC 对话推动剧情
- **位置**：`D:\Create by you.demo\game-prototypes\`
- **素材库**：`D:\SealedHallAssets\`

## 目录结构
```
game-prototypes/
├── AGENTS.md             # memory hub（本文件）
├── server.py             # HTTP 服务器（/models/ /textures/ 映射，DeepSeek AI）
├── start_game.bat
├── 3d-prototype/
│   ├── index.html        # 主入口（three.js import map，约 4000 行）
│   ├── old_hall.hdr      # HDR 环境贴图
│   └── src/
│       ├── fps_controller.js  # 视角控制器（overview/fps/tps，WASD）
│       ├── models.js         # 角色模型+动画（FBX/GLB 双格式）
│       ├── guidance.js       # 引导剧情系统（STAGES 多幕主线）
│       ├── settings.js       # 设置面板（O 键）
│       ├── perf.js           # 性能 HUD
│       ├── props.js          # 场景道具加载
│       ├── markers.js        # 场景标记
│       ├── ui_drag.js        # UI 拖拽
│       ├── atmosphere.js     # 大气效果
│       └── audio.js          # Web Audio 环境音（纯合成）
├── assets/
│   ├── models/           # 角色模型+动画+道具
│   ├── textures/         # PBR 材质
│   └── audio/            # 空（音效用 Web Audio 合成）
├── text-prototype/       # AI 对话管线（DeepSeek V4）
└── integration_test.py
```

## 当前状态（2026-08-11 晚）
### 已完成
- 4 NPC 模型 + 玩家 Knight（Mixamo With Skin）+ 动画（idle/talk/walk）
- 莉安娜 Sketchfab GLB（7.8MB Elf Servant）
- 场景材质：四墙统一石墙、木地板、木梁、西墙深色木暗语板
- 全视角控制器（FPS/TPS/俯瞰）、WASD+奔跑+跳跃
- 对话系统（模拟 + DeepSeek AI 在线）
- 引导系统、设置面板、性能 HUD、色温调节
- 吊灯 + 四角壁灯（暖色 PointLight）
- Web Audio 环境音（drone 0.018 / fire 0.012）
- NPC 微走动（Rog 有 walk 动画，其他 idle 滑动）
- git 基线（5 commits，可随时回滚）

### 待用户感受确认
- 墙体颜色 / 火把是否可见（火焰已从 0.1→0.3 半径放大）
- 音频沙沙声（drone gain 0.018）
- 鼠标快速移动是否还闪回（加了 pointerlock 重置）
- 色温是否需要调整

## 好友协作任务（另一台电脑，Tailscale 已连通，勿做需下载的任务）
好友电脑可访问游戏：http://100.79.254.94:8080 （主电脑 Tailscale IP）

| # | 任务 | 交付物 | 说明 |
|---|---|---|---|
| 1 | 游戏测试员 | 测试报告 | 完整玩一遍：开场引导→对话→切视角→情绪→道具；记录卡壳/看不懂/UI 遮挡/bug；格式：`问题+复现步骤+建议` |
| 2 | 剧情/文案创作 | 对话稿/剧情分支 md | NPC 深度对话（罗格/巴鲁克/玛格丽特/莉安娜背景、试探话术、秘密）、多结局分支（按 trust 值）、场景氛围文案 |
| 3 | 音效素材收集（可选） | CC0 音效文件 | 若网络允许再下载：脚步/门/魔法音 |

交付方式：文件放共享目录或直接发用户。

## 多电脑协作（Tailscale）
- 游戏测试地址：http://100.79.254.94:8080
- Tailscale Drive：好友电脑 `tailscale drive share sealed-downloads D:\sealed-downloads`；主电脑 `tailscale drive list` + `net use Z: \\win-oduco8tk731\sealed-downloads` 挂载
- 主电脑 Tailscale IP：100.79.254.94；好友：100.117.160.66
- 素材命名规则见下；下载的素材放 assets/models/ 或 assets/textures/，代码改动走 git

## 关键约定
- **编码**：所有 .js/.html 必须是 UTF-8 无 BOM
- **模型下载**：角色选 With Skin（>5MB=含网格），动画选 Without Skin（<1MB）
- **命名**：`<npc>_tpose.fbx`、`<npc>_idle.fbx`、`_talk.fbx`、`_walk.fbx`
- **存放**：模型→`assets/models/`（`/models/` 映射），纹理→`assets/textures/`（`/textures/` 映射）
- **git**：`git diff --stat` 看改动，`git checkout <file>` 回滚

## 开发命令
```
# 启动游戏
cd D:\Create by you.demo\game-prototypes && python server.py
# 无 AI 模式
python server.py --no-ai
# JS 语法检查
D:\node\node.exe --check 3d-prototype\src\<file>.js
# Edge 调试实例（CDP 9222 端口）
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=D:\edge-dbg-profile --no-first-run http://localhost:8080
```

## 下载管线
工具在 `C:\Users\11988\AppData\Roaming\reasonix\global-workspace\_tools\`：
- `mixamo_dl*.js` — Mixamo 下载
- `sketchfab_dl*.js` — Sketchfab 下载
- `_polyhaven*.py` — Poly Haven 纹理/道具
- `verify_all.js` / `check_login.js` — 登录态检查
使用：先开 Edge 9222 实例（已登录 Mixamo/Sketchfab），再跑对应脚本。

## 关键教训
- ZCode 桌面端曾以 GBK 误读重写项目文件，中文注释被破坏（勿在本项目用 ZCode）
- 角色下载必须选 With Skin（否则只有骨骼）
- npcMeshes 遍历：不要在 npcMeshes 上加属性（Object.entries 会遍历），状态用独立变量
- 豆包视觉不可靠：验证效果用 DOM 状态（#model-status）或像素亮度分析
