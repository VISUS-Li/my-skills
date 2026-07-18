# 输出格式契约 v4.0

## 1. 通用规则

所有创作交付必须包含符合 `output-schema.json` 的 JSON 对象。

- `schema_version` 固定为 `4.0`。
- `language` 默认 `zh-CN`。
- 枚举使用英文 snake_case。
- 展示文案、旁白和对白使用用户语言。
- 未知值使用 `null`。
- `story` 永不省略；默认 `{"enabled": false}`。
- `game.dimension` 默认并优先为 `3d`。
- `game.prototype_fidelity` 默认 `rough_graybox`。
- `agent_execution` 永不省略。
- 视频类交付必须包含完整 `narration_contract`、`voiceover_script`、`creative_storyboard` 和 `technical_capture_plan`。

## 2. 顶层字段

```json
{
  "schema_version": "4.0",
  "deliverable_type": "full_production",
  "language": "zh-CN",
  "project": {},
  "game": {},
  "ai_chaos": {},
  "comedy": {},
  "story": {"enabled": false},
  "video": {},
  "agent_execution": {},
  "implementation": {},
  "quality_check": {}
}
```

## 3. 交付类型

- `concept_pack`
- `game_chaos_design`
- `agent_prompt_pack`
- `prototype_plan`
- `video_blueprint`
- `full_production`
- `bug_audit`
- `research_report`

## 4. comedy 新增旁白字段

```json
{
  "tone": "deadpan_visual_contrast",
  "narrator_profile": {
    "perspective": "first_person_creator",
    "persona": "认真做游戏但不断被 AI 结果迫使重新解释现实的普通创作者",
    "delivery": "calm_resigned_precise",
    "language_rules": []
  },
  "voiceover_rules": {
    "min_chars_per_finished_minute": 120,
    "recommended_chars_per_finished_minute": 150,
    "min_spoken_shot_ratio": 0.7,
    "max_silent_gap_sec": 12,
    "exact_text_required": true,
    "optional_lines_forbidden": true
  },
  "transferable_influences": [],
  "contrast_layers": [],
  "authority_rationalization": "",
  "reversal_chain": [],
  "units": [],
  "forbidden_shortcuts": []
}
```

## 5. video

```json
{
  "format": "landscape_main_with_vertical_cutdown",
  "beats": [],
  "capture_shots": [],
  "ui_overlays": [],
  "narration_contract": {},
  "voiceover_script": [],
  "dialogue": [],
  "audio_plan": [],
  "edit_notes": [],
  "creative_storyboard": [],
  "technical_capture_plan": [],
  "cutdowns": []
}
```

### narration_contract

```json
{
  "required": true,
  "perspective": "first_person_creator",
  "target_chars_per_minute_min": 120,
  "target_chars_per_minute_max": 180,
  "target_spoken_runtime_ratio_min": 0.5,
  "target_spoken_runtime_ratio_max": 0.75,
  "min_spoken_shot_ratio": 0.7,
  "max_silent_gap_sec": 12,
  "visual_reveal_hold_sec_min": 0.5,
  "visual_reveal_hold_sec_max": 1.5,
  "exact_text_required": true,
  "placeholder_forbidden": true
}
```

### voiceover_script

```json
{
  "id": "VO01",
  "start_sec": 7,
  "end_sec": 13,
  "speaker": "creator",
  "text": "事情原本没有这么复杂。我只让 AI 做一个勇者救公主的游戏。",
  "function": "setup",
  "delivery": "平静，像在复盘一个普通工作任务",
  "paired_visual": "回到提示词界面"
}
```

`function`：`setup`, `expectation`, `ai_claim_bridge`, `redefinition`, `observation`, `escalation`, `consequence`, `callback`。

禁止把 `text` 写成：`VO1`、`可选 VO`、`待补`、`此处吐槽`。

### creative_storyboard

```json
{
  "shot_id": "S04",
  "start_sec": 31,
  "end_sec": 46,
  "beat_role": "visual_reveal",
  "visual": "玩家抛出木桶，三名守卫同时弃人追桶，锁定线跳到桶上",
  "player_action": "抛桶后原地不动",
  "spoken_content": [
    {
      "speaker": "creator",
      "type": "voiceover",
      "text": "后来我增加了一个木桶。系统第一次遇到了需要判断的情况。",
      "function": "expectation",
      "start_offset_sec": 0,
      "end_offset_sec": 5,
      "delivery": "平静"
    }
  ],
  "silence_hold_sec": 1.0,
  "music": "守卫转向时英雄音乐撤掉",
  "sound_effects": ["木桶滚动", "锁定提示音"],
  "comic_turn": "守卫把无生命木桶当成最近入侵者",
  "transition": "切到守卫围桶，接冷句"
}
```

观众分镜不得出现 `chaos_level_1`、`debug target`、参数名或实现备注。

### technical_capture_plan

```json
{
  "shot_id": "S04",
  "game_state": "chaos_level_1",
  "camera_rig": "third_person_follow",
  "camera_position": "玩家后方 6 米，高 2.5 米",
  "trigger": "木桶进入守卫 6 米搜索半径",
  "required_parameters": ["target_switch_delay=0.08", "barrel_threat_filter=true"],
  "debug_overlay": "拍正式镜头时关闭",
  "reset_method": "按 R 重置桶和守卫",
  "capture_notes": "先录正常版，再录失控版"
}
```

## 6. 分镜密度要求

视频类交付必须：

- 3–6 分钟至少 8 个 `voiceover_script` 项；具体最小值由验证器按时长计算。
- 完整旁白汉字数不低于 `target_duration_sec / 60 × 120`。
- 至少 70% `creative_storyboard` 镜头有 `spoken_content`。
- 无声镜头必须属于 `visual_reveal`、`reaction_hold` 或 `final_button`，且通常不超过 3 秒。
- 任何旁白/对白文本不得包含“可选”“待定”“TBD”“VO1”式占位。

## 7. 其他核心字段

`project`、`game`、`ai_chaos`、`story`、`agent_execution` 和 `implementation` 沿用 v3 的游戏优先约束。剧情不得替代游戏交互；Agent 任务必须包含层级、参数、允许/禁止修改、反例和验收测试。

## 8. quality_check

```json
{
  "game_first": true,
  "three_dimensional_readability": true,
  "rough_prototype_feasible": true,
  "player_agency": true,
  "visual_contrast": true,
  "deadpan_voiceover": true,
  "voiceover_density": true,
  "exact_voiceover_text": true,
  "narrator_continuity": true,
  "creative_technical_separation": true,
  "promise_reveal_structure": true,
  "systemic_escalation": true,
  "agent_specificity": true,
  "reproducible": true,
  "reversal": true,
  "callback": true,
  "story_optional": true,
  "scope_feasible": true,
  "issues": []
}
```

## 9. Hybrid 输出顺序

1. 完整项目 JSON。
2. 喜剧效果与旁白角色说明。
3. 连续完整旁白总稿。
4. 观众成片分镜。
5. 技术拍摄表。
6. Cursor/Agent 任务包。
7. 人工验收清单。
