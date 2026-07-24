# 评审量规

在首片预览之后跑评审。目标是决定修这片，还是扩到全片。

## 必查项

1. `first_slice_required`：在 20–30 秒预览存在之前，不做全片实现。
2. `visual_owner_required`：每个旁白拍都有视觉主人。
3. `micro_action_density`：每 0.8–1.5 秒有可见动作。
4. `macro_scene_reset_density`：每 8–12 秒有明显换房/重置。
5. `no_static_text_overuse`：纯文字静帧不超过 1.5 秒。
6. `proof_choreography_required`：截图、代码、终端、浏览器、手机视图用运动或标注导演。
7. `audio_visual_sync_required`：关键视觉动作有音效提示或刻意静音。
8. `subtitle_not_main_visual`：字幕不是唯一信息载体。
9. `review_studio_generated`：预览后存在评审页。
10. `complexity_budget`：首片保持聚焦：一种风格、3–5 个配方、1–3 个渲染器、最多两个委派槽。

## 脚本深度检查（走深度研究路径时）

在扩出首片之前，对照 `outputs/script.md` 与研究锁定。  
**标准与例子：** 仅 `references/narrative-depth-copy.md`。  
**研究骨架：** `references/deep-research-and-script.md` + `scripts/validate_research_lite.py`。

### Blockers（失败 → 全片前先出修复计划）

1. `story_thread_required` — tip → 发生了什么 → 卡点/未知 → 带走；故事连贯，不是话题桶菜单
2. `instant_comprehension_required` — 人/公司/数字在同一话轮内经背景 + 冲击落地；比喻同一口气内讲清
3. `oral_human_feel_required` — 读出声像跟朋友讲；自然反应；TTS 友好标点；不是大纲/讲课腔
4. `no_teaching_deconstruction` — 禁 `你就记` / `别听成黑话` / `别听成` / `你可以把它理解成` / `你就当作` 式专名拆解（见 `validate_vo_craft.py`）
5. `no_meta_vo_commentary` — 正片口播避免 `大白话` / `活人味` / skill 行话（`因果河` / `换轨`）与未解释的口号隐喻（见 `validate_vo_craft.py`）
6. `no_channel_mimicry` — 无点赞/小铃铛/Discord/付费/片尾主持人口头禅

### 强引导（记入 failed_checks；通常不单独挡住高视觉分）

7. `selective_deep_dig` — 按 tip 冲击 / 知识 / 戏剧挑 1–2 处展开；嵌主线，不按演员分章
8. `neighbor_and_rule_when_reframe_tip` — 同批邻居、政策变线、对照在会改读法时写
9. `cast_when_multi_actor` — 演员重要时：角色/权力/压力 + 身份碎片
10. `epistemic_split_preferred` — 混写时分清事实 / 推断 / 未知
11. `no_clever_framework_spine` — 抽象隐喻/分类桶不得取代故事线

第 4–5 项一旦检出是硬内容禁令；第 6–9 项是修复提示，除非它们把上面硬门槛搞垮。

## 风格分

满分 0–100：

- 20：参考风格匹配与连贯视觉世界。
- 20：旁白到画面绑定。
- 15：证明编排与资产可读性。
- 15：运动节奏与微/宏动作密度。
- 10：音画同步。
- 10：字幕与花字支撑场景而不抢戏。
- 10：扩全片的技术就绪度。

过线目标：78。低于 78，修片。低于 65，先修计划再动渲染器代码。

上文脚本深度 **blockers** 即便视觉分很高，也是计划 blocker。

## 修复映射

- 静态：加动作事件、拆长镜头、加运镜。
- 风格弱：改预设、背景、配方、调色板、转场词汇。
- 旁白脱节：每拍绑视觉主人与动作。
- 证明闷：加裁切、红框、光标、缩放、高亮、来源标签。
- 音频弱：给关键视觉动作加有动机的提示。
- 字幕过重：把名词/数字/流程变成视觉演员。
- 慢：缩短镜头时长并加宏重置。
- 过炫：去掉不服务关键词、证明点或转场的效果。
- 过复杂：减少渲染器、合并相似配方，只留明显强于本地实现的委派槽。
- 深度 blockers：按 narrative-depth-copy 三大硬门槛重写口播；按 deep-research-and-script 修研究锁定。
- 行话雾 / 聪明框架 / 僵硬讲课 / 教辅拆解：按故事河 + 履历式专名进场重写；抽 1–2 篇 StorytellerFan 字幕；跑 `validate_vo_craft.py`。
