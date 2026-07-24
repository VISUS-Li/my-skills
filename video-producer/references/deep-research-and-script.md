# 深度研究与脚本

当视频需要事实、判断、批评、产品分析、行业语境，或脚本应有「挖过、懂过」的质感（而不是清单罗列）时，在**分镜规划之前**使用本文件。

本文件负责：**何时研究、搜集什么、如何锁定来源、写哪些产物。**  
口播手艺只在 `references/narrative-depth-copy.md`——起草 `outputs/script.md` 时加载。此处不要重复其门槛。

目标：足够的来源锁定 + 事件展开，避免浅评；加上含义/冲击，让观众带走收获——**但不堆重文档**。

## 触发条件

用于：

- AI / 产品 / 工具分析或对比
- 开发者工作流主张（速度、成本、可靠性、失败模式）
- 新闻、公共事件、财经、政策、科技、科学、时事事实
- 用户语言如 深度 / 深搜 / 拆解 / 分析 / 复盘 / 真相 / 为什么
- 读起来像「第一、第二、第三」但缺谱系 + 含义的草稿

纯虚构 motion 测试、logo 短刺、无事实主张的 UI 演示，或用户明确不要研究的脚本，可跳过或保持极简。

## 产物分层

### 深度任务一律要有

```text
research/source_cards.jsonl
research/event_genealogy.md
outputs/script.md
```

`event_genealogy.md` 应足以让陌生人复述 tip → 上游 → 卡点，**并**说出观众收获。演员笔记在需要时写在这里（默认不另开文件）。

### 按需

| 文件 | 何时 |
|---|---|
| `research/claim_ledger.csv` | 大量数字/法律主张，或易误述事实 |
| `research/factcheck_report.md` | 争议、制作期复核，或跳过检查的记录 |
| `script/narrative_thread_map.json` | 长篇或多线；短单事件通常跳过 |
| `research/thread_ledger.csv` | 仅多线 |
| `research/cast_and_incentives.md` | 大卡司会淹没谱系时；否则把卡司折进谱系 |

小任务可将 Source Lock + Genealogy（+ Cast）折进 `outputs/script.md` 的章节。约束不变。

旧别名：`misread_map.md` / `stakeholder_incentives.md` → 当作谱系 + 卡司。

校验骨架（不是文笔质量）：

```bash
python scripts/validate_research_lite.py --project /path/to/project
```

## 研究摄入

不要从口号式判断起笔。搜集到足以把 tip 扩成**连贯故事**，并知道每条硬事实在人类尺度上意味着什么。

**可选广度教练：** 加载 `references/storyteller-fan-craft.md`，并浏览研究宽度表 + `references/storyteller-fan-corpus/CATALOG.md` 里**1–2** 篇匹配字幕。用来决定*该猎哪类材料*（时间线反转、规则底子、卡司压力、对照、机制缝）——不是复用哪句台词。之后分析类口播默认仍经 `narrative-depth-copy.md` 走同一套口语手艺。

尽量按此顺序：

1. Tip 锚点（报道 / 备案 / 产品变更 / 道歉 + 日期）
2. 上游 / 前尘
3. 卡司档案（角色、权力、压力）——多演员时；对陌生公司/创始人也要抓**口播会用到的身份碎片**（谁创办、商业还是实验室、融资量级、公开目标、当前产品状态）
4. 规则底子（标准、合同、锁定期、名单、计费、许可）
5. 主时间线与反转
6. 邻居线（仅当会改读法时）
7. 对照（成对事实 > 感觉）
8. 二手评论（仅作语境；绝不当事实唯一支撑）

每张重要来源卡：

- id、URL/path、title、publisher/author、date
- 对脚本为何重要
- 可用画面：screenshot / table / chart / UI / code / quote / none
- 风险：current / old / disputed / interpretation / anecdote / marketing / blocked
- 谱系角色：tip / upstream / cast / rule / timeline / neighbor / comparator / impact
- **可选含义注：** 若用于口播，这条证据暗示什么（一行）
- **可选 dig 标记：** 节点可能撑起口播里**聚焦展开拍**时标 `dig_worthy`（机制缝、政策变线、卡司反转、常见误读、能改写 tip 读法的邻居）

规则：

- 价格、法律、角色、规格、模型名、基准、新闻：制作时再核。
- 优先官方文档、一手来源、产品 UI、仓库、changelog、备案、论文、截图。
- 弱证据 → 标不确定或删。
- 投诉、匿名爆料、「据悉」转载保留其身份；它们不是判决。
- 不要发明因果；仅在来源支撑时桥接因果。

## 研究整理

### 事件谱系（`research/event_genealogy.md`）

| 字段 | 必填 |
|---|---|
| tip | 冲进视野的是什么 + 日期 |
| upstream | 漏掉的前尘 |
| timeline | 有序拍点 + 反转；标 扣合点 |
| rule_substrate | 卡住故事的规则/合同（若本题无关可写 `none` + 理由） |
| neighbor_strands | 会改读法的平行线（或 `none` + 理由） |
| still_unknown | 未定 |
| ordinary_impact | 落到用户/构建者/消费者何处 |
| dig_worthy | 口播**候选**展开节点（见下方选择标准） |
| viewer_harvest | 口播必须落地的一句带走（白话；不必贴类型标签） |
| cast | 主要演员 + 角色 / 筹码 / 压力（折在这里，除非另开卡司文件） |

写完后，陌生人应能在一分钟内复述来龙去脉，**并**说出 tip 对普通利益相关者意味着什么。

### Dig-worthy 选择（研究标记 → 写稿再判）

研究可标**多个**候选。起草 `outputs/script.md` 时，按下面标准**挑 1–2 处做口播展开**：

- **Tip 中心性** — 这节点是否解释新闻*现在*为何重要？
- **知识产量** — 听众能否学到非显而易见的东西（政策线、邻居名单、卡司反转、机制）？
- **戏剧 / 好奇心** — 谈判、乌龙、误读、行业先例
- **证据强度** — 一手 / 多源 vs 单条「据悉」

**不是名单规则：** 不要因为研究里出现了就每个公司都展开。例：「Apple 智能备案」题，邻居（同批七家 + 端侧首次单列）与规则变线，可能比完整百度专章更重要；百度/阿里出现在它们能解释**为何 tip 以这种方式落地**时。

最终挑选记在脚本附录或 `event_genealogy.md` dig 笔记；跳过的候选 → `factcheck_report.md` 或谱系里一行。

### 主张台账（使用时）

每条事实或评价句需要：来源 id / 显式不确定 / 项目自证 / 删除。

不要越过截图推断。措辞证据 → 叙述措辞。UI 证据 → 叙述 UI。无支撑则不写动机/因果/规模/结果。

每条打算进口播的**数字或列表主张**，加短 `meaning` 注：暗示什么 + 对谁。无含义注 → 先别抬进口播。

### 叙事线地图（使用时）

长篇/多线脚本的可选结构辅助。形态示例：`assets/templates/example_narrative_thread_map.json`。

字段保持精简：tip、genealogy、viewer_harvest、dig_worthy、still_unknown、短 spine。不要把已在谱系或脚本里的卡司/gloss/insight 层再抄一遍。

Spine 阶段是**菜单**，不是必填。短片常见：`tip_stakes` → `dig_expand` → `meaning_impact` → `compress`。

结构上避免：

- 「首先 / 其次 / 最后」当唯一脊柱且无故事线
- 无证据空推测
- 未经展开挣来的口号结论
- 有事实载荷却无含义/冲击进口播的路径

## 来源到画面绑定

**在** `outputs/script.md` 通过口播 Kill Checklist 之后（或用户从纯脚本进入画面工作时），在写 `beat_plan.json` 前/中，给重要句子标证明类型：

`source_screenshot` | `screen_recording` | `code_terminal` | `chart_table` | `timeline_board` | `cast_board` | `metaphor_svg`（可选，勿为了填坑硬造）| `human_context`

研究阶段**不要**仅为满足此列表发明教学隐喻。选定证明之后须在 `segment_spec.json` 里导演（裁切、推进、红框、光标、高亮、来源标签、图表构建等）。

含义句常需要能表现**尺度或对比**的画面，而不只是原样数字卡。

## 移交到脚本

研究锁定足够时：

1. 加载 `references/narrative-depth-copy.md` 与 `references/storyteller-fan-craft.md`；读 **1–2** 篇匹配字幕，标五问（开场 / 还债顺序 / 卡司进场 / 含义 / 深挖收回）。
2. **再选 1–2 个 dig 节点**进口播（见上方标准）；嵌主线，不要机械按演员分章。
3. 按三大硬门槛写 `outputs/script.md`——故事连贯优先；人名经履历/目标/状态进场，不是教辅拆解；口语/TTS 感按 narrative-depth-copy。
4. 运行：
   - `python scripts/validate_research_lite.py --project ...`
   - `python scripts/validate_vo_craft.py --project ...`（教辅拆解 + 元讲解提示）
5. 继续分镜规划，除非用户只要研究/脚本。

研究清单（骨架，不是文风）：

- [ ] 来源卡存在（或 Sources 折进脚本）
- [ ] 谱系存在（文件或折进）；陌生人能复述 tip → 上游 → 卡点 → 带走
- [ ] dig_worthy 候选已标；口播最终 1–2 挑选已记（或明确跳过并写理由）
- [ ] viewer_harvest 已为口播写明（白话句；不必类型 taxonomy）
- [ ] 主张已有来源、标不确定，或已删
- [ ] 主卡司/公司有足够身份碎片做故事进场（或标 unknown）
- [ ] 口播手艺已用 narrative-depth-copy Kill Checklist + `validate_vo_craft.py` 检查
- [ ] 进入分镜规划时已标画面证明类型（不是口播 blocker）
