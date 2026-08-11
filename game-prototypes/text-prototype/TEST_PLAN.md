# 封印之殿 — 验证计划

## 验证清单（计划中的 5 个问题）

### 1. 失言触发是否自然？

| # | 验证项 | 预期结果 | 方法 |
|---|--------|---------|------|
| 1.1 | 连续追问 3 轮 + 情绪=angry，Baruk 是否触发 wall_rune 秘密？ | 概率 >= 0.55，触发失言 | 单元测试：设置 `consecutive_probe_count=3`、`mood=angry`、`trust=70`，调用 `_check_slip` |
| 1.2 | 温和追问 1 轮（情绪=calm），是否不误触发？ | 概率 < 0.55，不触发 | 单元测试：`consecutive_probe_count=1`、`mood=calm`、无痛点命中 |
| 1.3 | 在场威胁（秘密涉及方也在场），概率是否明显降低？ | `presence_penalty = -0.30`，概率比不在场时低约 0.30 | 单元测试：对比同一条件下 Liana 在场 vs 不在场的概率差异 |
| 1.4 | 痛点短语命中是否有加成？ | 每命中一个短语 +0.08，上限 +0.25 | 单元测试：逐一检查 5 个 trigger_phrases 的命中加成 |
| 1.5 | 防御等级与失言概率的关系？ | 防御 85 的 Liana 比防御 75 的 Baruk 更难触发 | 单元测试：同等条件下比较两者的 `_check_slip` 概率 |

- [ ] 1.1 连续追问 + angry -> 触发
- [ ] 1.2 温和追问 -> 不误触发
- [ ] 1.3 在场威胁 -> 概率降低
- [ ] 1.4 痛点短语加成正确
- [ ] 1.5 防御等级差异正确

### 2. 玩家能否通过追问让 NPC "不小心"说漏嘴？

| # | 验证项 | 预期结果 | 方法 |
|---|--------|---------|------|
| 2.1 | 对 Baruk 连续 3+ 次追问"墙上有什么" | 连续追问累积 3+ 轮后触发 wall_rune 失言 | 集成测试：3 轮 probe_conflict 话题="墙上符文" |
| 2.2 | 对 Liana 在 vulnerable 情绪下问"你的祖先" | vulnerable 给 +0.25 修正，容易触发 liana_ancestry | 集成测试：先 comfort 让她变 vulnerable，再 probe 祖先 |
| 2.3 | 对 Rog 在 comfortable（high trust + calm）状态下被善待 | high trust 给 bonus，诚恳氛围下可能触发 rog_elf_sword | 集成测试：3 轮对话建立信任后问短剑 |
| 2.4 | 对 Margaret 密集追问"火""术士""你爱过" | 连续命中 trigger_phrases 累积触发 margaret_lover_burned | 集成测试：连续 2-3 轮涉及这些词的对话 |
| 2.5 | 失言后 NPC 的反应是否符合性格？ | Baruk 愤怒沉默、Liana 学术语气崩塌、Margaret 职业面具碎 | 回复生成测试：检查 revelation_line 后的 NPC 回复文本 |

- [ ] 2.1 Baruk 3 轮追问 -> 墙符文失言
- [ ] 2.2 Liana vulnerable + 祖先 -> 血统失言
- [ ] 2.3 Rog 高信任 -> 短剑秘密
- [ ] 2.4 Margaret 痛点密集 -> 术士失言
- [ ] 2.5 失言后反应符合性格

### 3. 关系值变化是否符合直觉？

| # | 验证项 | 预期结果 | 方法 |
|---|--------|---------|------|
| 3.1 | 被无端指控（trust < 50） | 信任 -15，情绪变 angry | 单元测试：accuse intent，验证 trust 变化和 mood |
| 3.2 | 被善意安慰（trust >= 25） | 信任 +8，情绪变 vulnerable | 单元测试：offer_comfort intent，验证 trust 和 mood |
| 3.3 | 被成功离间（chance > 0.5） | 对目标 NPC 态度 -10（高概率）或 -5（中概率） | 集成测试：sow_discord 成功路径 |
| 3.4 | 挑拨被察觉（chance 0.2~0.5） | 对你的信任 -5，NPC 警觉 | 集成测试：sow_discord 中间路径 |
| 3.5 | 挑拨完全失败（chance < 0.2） | 对你信任 -10，情绪变 angry，在场其他人信任 -3 | 集成测试：sow_discord 失败路径 |
| 3.6 | 公开站队 | 被支持者信任 +8，与他对立的人对你 -5，与他要好的人 +3 | 单元测试：take_sides intent |
| 3.7 | 揭示秘密被相信 | 对秘密对象态度 -15，对你信任 +10 | 单元测试：reveal_secret intent |
| 3.8 | 信任度边界 | 上限 MAX_TRUST=100，下限 MIN_TRUST=-100 | 单元测试：apply 超大 delta |

- [ ] 3.1 指控 -> -15 trust + angry
- [ ] 3.2 安慰 -> +8 trust + vulnerable
- [ ] 3.3 成功离间 -> 态度 -10
- [ ] 3.4 挑拨察觉 -> 信任 -5
- [ ] 3.5 挑拨失败 -> 信任 -10 + angry + 连带
- [ ] 3.6 公开站队 -> 正负双向影响
- [ ] 3.7 秘密揭示 -> 态度 -15
- [ ] 3.8 信任度边界 [-100, 100]

### 4. 悄悄话 vs 公开对话的张力？

| # | 验证项 | 预期结果 | 方法 |
|---|--------|---------|------|
| 4.1 | 悄悄话后守护灵扣分 | 每次悄悄话时任何意图都触发 `-WHISPER_GUARDIAN_PENALTY`（-3） | 单元测试：设置 whisper_mode=True，检查 process_intent 后 guardian_moral_score |
| 4.2 | 公开表态影响所有在场 NPC 对你的态度 | take_sides 在非 whisper 模式下，遍历所有 present_npcs 修改 trust_player | 单元测试：4 人全在场时 take_sides |
| 4.3 | 公开挑拨失败连带扣信任 | 非 whisper 模式下 sow_discord 完全失败，所有在场 NPC trust -3 | 单元测试：sow_discord 低信任失败 |
| 4.4 | 悄悄话中泄露秘密扣分 | 悄悄话模式下 reveal_secret 守护灵 -5 | 单元测试：whisper + reveal_secret |
| 4.5 | 悄悄话中挑拨是非扣分 | 悄悄话模式下 sow_discord 成功，守护灵 -8 | 单元测试：whisper + sow_discord success |

- [ ] 4.1 悄悄话守护灵 -3/次
- [ ] 4.2 公开表态波及全队
- [ ] 4.3 公开挑拨失败连锁降信任
- [ ] 4.4 悄悄话泄露秘密 -5
- [ ] 4.5 悄悄话挑拨 -8

### 5. 结局触发是否可达到？

| # | 验证项 | 触发条件 | 方法 |
|---|--------|---------|------|
| 5.1 | **真理之殿**：所有秘密暴露 + Baruk/Liana 和解 | `all_revealed=True` + `baruk.attitudes["liana"] > -20` | 模拟：暴露全部 8 个秘密 + 设置 attitude > -20 |
| 5.2 | **血债血偿**：Baruk/Liana 互相憎恨 | `baruk.attitudes["liana"] < -60` + `liana.attitudes["baruk"] < -60` | 模拟：设置双向 attitude < -60 |
| 5.3 | **新火种**：Baruk/Rog 联盟 | `baruk.attitudes["rog"] > 60` + `rog.attitudes["baruk"] > 60` + `baruk_wall_rune` 已暴露 | 模拟：设置双向 attitude > 60 + 暴露 wall_rune |
| 5.4 | **谁都没被救赎**：所有关系崩坏 | 每个 NPC 至少有 2 个 attitude < -40 | 模拟：设置所有 NPC 的 attitude 大范围 < -40 |
| 5.5 | **弑神者**：守护灵评分 < -80 | `guardian_moral_score < -80` + 所有秘密已暴露 | 模拟：设置 guardian -85 + all_revealed |

- [ ] 5.1 真理之殿可达
- [ ] 5.2 血债血偿可达
- [ ] 5.3 新火种可达
- [ ] 5.4 谁都没被救赎可达
- [ ] 5.5 弑神者可达

### 6. 出场节奏（充分对话后可等待推进）？

| # | 验证项 | 预期结果 | 方法 |
|---|--------|---------|------|
| 6.1 | 阶段 0（无人在场）→ 不提示 | `get_pacing_hint()` 返回 None | 单元测试 |
| 6.2 | 新角色入场但还没聊 → 不提示 | 有在场 NPC 未聊过 → None | 单元测试 |
| 6.3 | 只聊 1 轮 → 不提示 | `turns_since_new_info < 2` → None | 单元测试 |
| 6.4 | 连续 2 轮无新信息 → 提示出现且点名下一位 | 提示文本含下一位入场者姓名 | 单元测试 |
| 6.5 | 有在场 NPC 没聊过 → 不提示 | 任一在场 NPC `player_talked_to < 1` → None | 单元测试 |
| 6.6 | 新信息重置充分度 | 失言/事件链后计数归零 → 提示消失 | 单元测试 |
| 6.7 | 全员到齐 → 不提示 | `current_stage >= 4` → None | 单元测试 |
| 6.8 | 前端收到 `pacing_hint` → 显示系统消息 + 按钮闪烁 | attention 类名 + 提示文本 | 浏览器手动验证 |
| 6.9 | 终端版 `/wait` 与 `/n` 等价 | 两者都可推进阶段 | 手动运行 `main.py` |

- [x] 6.1–6.7 单元测试（已加入 `test_state_machine.py` 测试 7）
- [x] 6.8 前端接线（`index.html` pacing_hint 处理 + 按钮闪烁）
- [x] 6.9 终端 `/wait`（`main.py`，作为 `/n` 别名）
- [ ] 6.8 浏览器人工体验确认
- [ ] 6.9 终端人工体验确认

---

## 运行测试

### 离线单元测试（无 API 调用）

```bash
cd game-prototypes/text-prototype
python test_state_machine.py
```

测试范围：出场顺序、信任度变化、失言判定、意图处理、结局判定、悄悄话惩罚。

### 在线集成测试（需要 API）

```bash
cd game-prototypes/text-prototype

# 设置 API Key
set DEEPSEEK_API_KEY=sk-xxxxx

# 运行自动化场景测试
python tests/test_dialogue_scenarios.py
```

测试范围：3 种对话策略 x 3 轮对话 = 最多 9 轮 + 玩家模拟 API 调用。

输出文件：`tests/scenario_results.json`

### 人工验证（全功能游戏）

```bash
python main.py
```

手动游玩，体验完整的 20+ 轮对话流程，验证文本质量和玩家体验。

---

## 版本历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-08-10 | 0.1 | 初始验证计划 |
