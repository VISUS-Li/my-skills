# 音画同步语法

音效必须有画面动机。若没有可见动作，用静音或口播重音，不要乱加 SFX。

## 提示映射

- `keyword_pop` -> `soft_pop`
- `redbox_focus` -> `click` or `marker`
- `terminal_typing` -> `keyboard_tick`
- `code_highlight` -> `soft_click` or `tick`
- `cursor_click` -> `click`
- `card_stack_enter` -> `soft_whoosh`
- `dashboard_count_up` -> `tick_rise`
- `git_node_pop` -> `node_pop`
- `branch_draw` -> `line_whoosh`
- `major_transition` -> `whip` or `whoosh`
- `timeline_rewind` -> `reverse_whoosh`
- `error_or_warning` -> `glitch` or `low_hit`
- `important_conclusion` -> `bass_hit` or `stamp`
- `phone_message_send` -> `send_click`
- `audio_waveform_marker` -> `tick`

## 时机规则

- 提示起始落在视觉动作前后 0.03–0.08 秒内。
- SFX 要 duck 在人声之下；绝不要盖住中文口播的辅音。
- 大转场尽量留 0.15–0.35 秒呼吸空档，放在该句前后。
- 花字跟关键词重音一起出，不要等整句说完再出。
- 字幕可以略早于人声；花字与证据高亮应对准说出的关键词。
- 严肃转折、人情冲击，或画面信息已经很密时，用静音。

## 提示密度

- 开发者演示：轻–中；大量小 click/tick，少用 bass hit。
- 系统讲解：中–高；click 与卡片 whoosh；glitch 只用于警告。
- Git/技术教学：精确；node pop 与打字 tick，不要随机电影感轰鸣。

## 常见翻车

- 没有视觉动作却有 SFX：删掉。
- 小词却用大 hit：降级为 click 或静音。
- 密句底下还在打字 tick：降音量或缩短。
- 每次转场同一 whoosh：轮换 click、snap、wipe、静音，或共用物体运动。
