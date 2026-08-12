# 第七天 · Godot 学习版

把 2D 叙事 demo《第七天》搬进 Godot 的第一块砖。**目的不是功能，是让你把场景树/节点/脚本这三件事在手上跑一遍。**

## 打开方式（你的机器）

1. Godot 4.7.1 在：`D:\EDGE\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe`
2. 打开 Godot → **项目管理器 → 导入** → 选中本文件夹的 `project.godot`
3. 打开项目后按 **F5** 运行
4. 操作：**← → / A D** 左右移动（暂时只有左右，和 Canvas 版一致）

## 这个场景树长什么样（核心课）

打开 `scenes/main.tscn`，看左上角"场景"面板——这就是一棵树：

```
Main (Node2D)                        ← 根节点：整个场景就是这棵树
├── Background (ColorRect)           ← 夜空背景（一个填满 320×180 的色块节点）
├── Ground (ColorRect)               ← 地面线（y=158）
├── ClockTower (ColorRect)           ← 钟楼（占位色块，对应 BELL_POS.x=160）
├── Bell (ColorRect)                 ← 那口钟（占位色块）
└── Player (CharacterBody2D)         ← 玩家：带脚本的物理体
    └── CollisionShape2D             ← 玩家的碰撞盒（12×16）
```

**三个要点：**
1. **一切都是节点**——背景、地面、钟楼、钟，连玩家，全是一个个节点，靠父子关系组成一棵树。
2. **脚本挂节点**——`player.gd` 挂在 Player 上，`_physics_process()` 每帧跑，改 `velocity` 再 `move_and_slide()` 就是移动。
3. **谁在上谁先画**——场景面板里**排在上面的节点画在最底层**（Background 在最底下），顺序就是绘制顺序。

## 对应到 Canvas 版 demo

| 这里 | Canvas 版 (`2d-narrative-demo/index.html`) |
|---|---|
| `Main` 根节点 | `SCENES` 状态机 + 主循环 |
| `Player` + `player.gd` | `player` 对象 + 主循环里左右移动那段 |
| `ClockTower`/`Bell` 色块 | `BELL_POS`/`drawBell()` |
| `_physics_process` | 每帧 `loop(dt)` |
| `Input.is_action_pressed` | `keys[...]` 键位表 |

## 下一步（学完这些再往上加）

- [ ] 换正式场景（用 `bg.png`，或先程序化画）
- [ ] NPC 节点 + 站点巡游（对应 `npcs[]`）
- [ ] 对话 UI（CanvasLayer + Control，对应 `#dialogue`）
- [ ] 输入映射（Input Map，把 A/D 也定义成动作，替换物理键直查）
