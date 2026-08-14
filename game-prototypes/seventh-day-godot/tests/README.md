# 回归测试（tests/）

从命令行跑，不用打开编辑器。命令都在 `seventh-day-godot/` 目录下执行：

```
"D:/EDGE/Godot_v4.7.1-stable_win64.exe/Godot_v4.7.1-stable_win64_console.exe" --headless --path . res://tests/xxx.tscn
```

| 测试 | 干嘛的 | 需要 server？ | 会动存档吗？ |
|---|---|---|---|
| `test_migrate.gd` | 旧存档迁移：历史反推说话人 + `"<null>"` 清理 + 分桶正确性 | 否 | 否 |
| `test_ending.gd` | 结局入口：标题 / 层二引用玩家台词 / 坦白落盘 / 占位符 + 剧情推进链（闲话上墙→第二天、听懂最后一笔→刻痕3）+ 黄金路径（钟13下→刻痕1→…→刻痕3→结局入口话题真的出现）+ E 键竞态闸门（busy / ending_mode 不得穿透） | 否 | **会写**，但开头备份、结尾自动恢复 |
| `test_e2e.gd` | 端到端：真实 TalkClient → 本地 server（跨 NPC 隔离、meta、离线兜底、世界线分类、endgame） | **是**（127.0.0.1:8890） | 否 |
| `test_anim.gd` | 玩家动画状态机：idle(10帧) → 按方向键 → run_start(2帧不循环) → 播完自动接 run(18帧循环) → 镜像翻转不重启 → 松键回 idle → 可重复触发；顺带验证开场黑幕 pause 解除 | 否 | 否 |

看结果：全部行 `[TAG] PASS`；`SKIP` = 没起 server 被跳过；出现 `FAIL` 就说明哪里坏了。

## 它们守护的两个真实 bug

1. **"市长说神官的台词"**（跨 NPC 对话历史泄漏）：`dialogue_history` 原来全局混存，A 的回复会流进 B 的 LLM 上下文。修复 = 每条历史标说话人 + 取用时按人过滤 + server 双保险。`test_migrate.gd` 和 `test_e2e.gd` 一起守这条线。
2. **存档里的 `"<null>"` 污染**：老代码把 LLM 返回的 `null` 直接 `str()` 成 `"<null>"` 字符串存进 secrets。修复 = 写入时判空 + 读档时清理。`test_migrate.gd` 守这条线。
