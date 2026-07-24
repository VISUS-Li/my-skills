# 镜头语法

写代码前先选命名配方。每个镜头必须有配方、视觉主人、动作列表与转场理由。

## 配方

### `dark_grid_intro`
- 用途：开场钩子、工具/世界观铺垫、开发者悬念。
- 时长：2–4 秒。
- 元素：暗网格、大关键词演员、小证明缩略图、脉冲线。
- 动效/SFX：关键词缩放模糊、网格脉冲、soft pop、短 whoosh。
- 错误：以长字幕开场；太多互相抢戏的词。
- 渲染器：Remotion 或 HyperFrames。

### `light_grid_concept_board`
- 用途：定义、系统图、概念拆分。
- 时长：3–6 秒。
- 元素：亮网格、卡片、箭头、标签、小图标。
- 动效/SFX：卡片抽出、箭头描边、click。
- 错误：静态图解无搭建序列。
- 渲染器：Motion Canvas、SVG/GSAP、HyperFrames。

### `terminal_proof`
- 用途：命令、安装/运行证明、日志、错误。
- 时长：3–7 秒。
- 元素：终端窗、命令行、光标、输出高亮。
- 动效/SFX：打字 tick、行揭示、红框/caret 聚焦、click。
- 错误：终端太小看不清；命令一次性贴完。
- 渲染器：Remotion 或 HyperFrames。

### `editor_code_zoom`
- 用途：代码因果、生成文件、API 调用、配置。
- 时长：3–8 秒。
- 元素：编辑器外壳、文件树、代码高亮、minimap 提示。
- 动效/SFX：推进、行高亮、token 发光、键盘 tick。
- 错误：整份代码文件上屏；无高亮行。
- 渲染器：Remotion、Motion Canvas、SVG/GSAP。

### `screenshot_pushin_redbox`
- 用途：产品证明、UI 证据、网页主张。
- 时长：3–6 秒。
- 元素：截图、浏览器/设备框、红框、光标、标签。
- 动效/SFX：滑入/裁切入、推进、红框描边、click/marker。
- 错误：生截图居中无引导。
- 渲染器：Remotion 或 HyperFrames。

### `phone_chat_sequence`
- 用途：用户工作流、聊天 agent 交互、提示前后对比。
- 时长：4–8 秒。
- 元素：手机 mockup、聊天气泡、输入光标、结果卡。
- 动效/SFX：气泡 pop、打字、发送 click、回答上小 hit。
- 错误：一次太多消息。
- 渲染器：Remotion、HyperFrames。

### `git_graph_growth`
- 用途：分支、合并、版本、快照、协作。
- 时长：4–8 秒。
- 元素：节点、分支线、commit 标签、diff 卡。
- 动效/SFX：node pop、线描、click、轻 stamp。
- 错误：图一开始就画完。
- 渲染器：Motion Canvas、SVG/GSAP、Remotion。

### `timeline_rewind`
- 用途：回滚、历史、因果链、前后时间跳。
- 时长：3–6 秒。
- 元素：时间尺、播放头、幽灵帧、快照卡。
- 动效/SFX：reverse whoosh、刻度 tick、冻结 hit。
- 错误：无清晰前后状态。
- 渲染器：Remotion、Motion Canvas。

### `dashboard_room`
- 用途：指标、产品状态、系统总览。
- 时长：4–8 秒。
- 元素：仪表盘卡、图表、表格、状态 pill、光标。
- 动效/SFX：卡片叠入、count-up、click、soft whoosh。
- 错误：无意义假指标；千篇一律的卡片墙。
- 渲染器：HyperFrames 或 Remotion。

### `critique_wall`
- 用途：指出错配、幻觉、弱主张、坏视频模式。
- 时长：4–7 秒。
- 元素：证据缩略图、红标签、对比线、警告徽章。
- 动效/SFX：marker/click、真实警告用 glitch、low hit。
- 错误：苛刻装饰却无证据。
- 渲染器：HyperFrames、Remotion。

### `data_card_compare`
- 用途：数字、定价、速度、能力对比。
- 时长：3–6 秒。
- 元素：两到三张卡、数字英雄、轴标签、来源标签。
- 动效/SFX：count-up、卡片 snap、soft hit。
- 错误：数字无来源/语境。
- 渲染器：Remotion、HyperFrames。

### `svg_metaphor_scene`
- 用途：抽象机制、心智模型、隐藏系统。
- 时长：4–8 秒。
- 元素：简单隐喻物、SVG 路径、标签、粒子慎用。
- 动效/SFX：路径描、morph、pop、whoosh。
- 错误：隐喻与旁白无关。
- 渲染器：Motion Canvas、SVG/GSAP、HyperFrames。

### `keyword_actor_pop`
- 用途：关键词、钩子短语、对比词、结论词。
- 时长：1–3 秒。
- 元素：一个主导词/短语、小支撑符号。
- 动效/SFX：缩放模糊、snap、soft pop。
- 错误：整句做成巨大文字。
- 渲染器：Remotion、HyperFrames、GSAP。

### `before_after_split`
- 用途：转变、对比、坏/好例子。
- 时长：3–7 秒。
- 元素：分屏、wipe 分割线、标签、同步标注。
- 动效/SFX：wipe、click、胜者 stamp。
- 错误：两边太像；无可见变化。
- 渲染器：Remotion、HyperFrames。

### `workflow_pipeline`
- 用途：工具链、agent 工作流、输入到输出过程。
- 时长：5–10 秒。
- 元素：节点、箭头、小截图、终端/代码插入。
- 动效/SFX：node pop、箭头旅行、click、whoosh。
- 错误：节点太多；无当前步焦点。
- 渲染器：Motion Canvas、SVG/GSAP、Remotion。

### `audio_waveform_sync`
- 用途：展示语音时序、拍点对齐、声音设计。
- 时长：2–5 秒。
- 元素：波形、拍点标记、动作 tick、播放头。
- 动效/SFX：tick、pulse、小 hit。
- 错误：装饰波形与动作无关。
- 渲染器：Remotion、HyperFrames。

### `conclusion_stamp`
- 用途：最终判断、警告、裁决、CTA。
- 时长：2–4 秒。
- 元素：裁决文字、背后证明缩略图、stamp/seal。
- 动效/SFX：bass hit、stamp、短尾音。
- 错误：结论文字却无证明的视觉记忆。
- 渲染器：Remotion、HyperFrames、GSAP。
