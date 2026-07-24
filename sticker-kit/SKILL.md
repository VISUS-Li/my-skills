---
name: sticker-kit
description: >-
  规划并制作多风格模切贴纸、分层叙事动画与连续帧安全的动作：分镜与状态时间线、耦合感知的演员组、
  身体驱动的 Wan 图生视频/首尾帧生视频、可执行的互动交接、色度/亮度抠图转透明、确定性合成，
  以及静态 UI 贴纸包；预设风格（默认暖奶油手账，含 8bit 像素、彩色海克斯、扁平矢量、卡哇伊、
  水彩、漫画线稿、新波普、软陶、孔版、粉笔、马克笔、线稿涂鸦、复古等）、身份锁定、接触组、
  发射物分组、位移/根运动归属、特效层，以及纯图像长动作回退（约 100–120 帧，幕次+桥接）。
  在用户需要贴纸、sticker kit、手绘贴纸风、8bit/像素、彩色海克斯、手账 UI、分镜动画、
  多角色场景、Wan 图生视频/首尾帧生视频、元素拆分与合成、透明视频素材、精灵图/帧动画、
  连续帧防跳跃、长动作/龟派气功/御剑、chroma-key 或 sticker-kit 时使用。
---

# Sticker Kit（贴纸包 + 分层 Wan 动画）

制作静态贴纸，或把整场戏规划为**耦合的动画表演片段**：抠成 RGBA 后，按确定性时间线合成。
分层边界跟运动耦合与接触拓扑走，不按名词拆层。

**风格（随时可换）：** [styles.md](styles.md) — 默认 `cozy-scrapbook`

提示词模板：[style-reference.md](style-reference.md)

**连续性 / 防变形（Mode D 必读）：** [continuity.md](continuity.md)

**Wan 分层视频工作流（叙事动画默认路径）：** [references/wan-layered-video.md](references/wan-layered-video.md)

**纯图像长动作（约 100–120 帧，无视频模型）：** [long-action.md](long-action.md)

## 风格切换

1. 默认风格 id：**`cozy-scrapbook`**。
2. 若用户点名其他预设（[styles.md](styles.md) 中的 id 或别名），整单锁定该 `style_id`。
3. 把该预设的 **Master** + **Negatives** 贴进每条生图提示；中途换风格后必须重做 **锚图**。
4. 默认色键为 `#00FF00`；主体自带该色时改用蓝/品红。火焰/辉光用黑底 + 亮度 alpha。

| 用户说法… | 解析为 |
|---|---|
| （未指定）/ 暖奶油 / 手账 | `cozy-scrapbook` |
| 8bit / 像素 | `pixel-8bit` |
| 彩色海克斯 / hex | `hex-colorful` |
| 扁平 / vector | `flat-vector` |
| 卡哇伊 / pastel | `kawaii-pastel` |
| 水彩 | `watercolor` |
| 漫画 | `comic-ink` |
| 波普 / neo-pop | `neo-pop` |
| 软陶 / clay | `clay-soft` |
| 孔版 / riso | `risograph` |
| 粉笔 | `chalk-pastel` |
| 马克笔 | `marker-copic` |
| 线稿涂鸦 | `line-doodle` |
| 复古 / 70s | `retro-vintage` |

## 模式路由

| 用户需求… | 模式 |
|---|---|
| 分析参考视频/截图风格 | A |
| 完整 App 界面 mockup | B |
| 静态贴纸包 | C |
| **多元素叙事 / 可用 Wan** | **D-Wan（动画默认）** |
| 单精灵 / 逐帧生图 / 无 Wan | **D-Frames** |
| **长动作 / 多阶段招式且仅图像** | **D-Long** → [long-action.md](long-action.md) |
| 静态 + 动画 | C 和/或 D-Wan |

默认输出目录：用户指定文件夹，否则 `./sticker-kit-output/`。

## 风格锁定（短）

- 使用 [styles.md](styles.md) 中的活动预设（默认暖奶油手账）
- 贴纸/锚图/帧：用主体上不出现的纯色色键；界面屏：用预设 Screen 背景
- 模切轮廓清晰可读；遵守预设描边 / 白边 / 阴影规则
- 禁止写实；避免玻璃拟态 / 紫霓虹 chrome，除非所选预设明确允许受控高光

---

## Mode A / B / C

- **A：** ffmpeg 抽帧 → 提炼气质 → 映射到最近预设 id + 提示词。
- **B：** 调研 → 带当前风格锁定的 `9:16` 界面屏。
- **C：** 绿幕拼版 → `cutout_assets.py --mode green` → `split_parts.py`。优先一图一主体。

---

## Mode D-Wan — 分层叙事动画

先读 [references/wan-layered-video.md](references/wan-layered-video.md) 与
[references/wan-api.md](references/wan-api.md)。场景计划与互动契约未就绪前，不要开生成。

### D-Wan 0 — 规划故事、镜头、状态

1. 把 brief 拆成故事节拍与镜头；每镜一条机位规则。
2. 写状态时间线。每个状态包含一次语义动词/姿态类过渡，并记录边界上的位置、朝向、缩放、接触状态。
3. 按共享运动链、发射源点、受力、接触拓扑选生成组——不按物体类别。
4. 声明 `motion_space`（`in_place` / `locomotion` / `hybrid` / `compositor`），并为位移/混合状态写 `body_mechanics`。
5. 写可执行的互动/交接字段。仅有散文式 `rule` 无法对齐分别生成的片段。
6. 保存 `scene_plan.json`；默认用故事中立的 generic 模板。

```bash
python scripts/init_wan_scene.py --template generic --out OUT/my-story
python scripts/compile_wan_scene.py OUT/my-story/scene_plan.json
# 创建端点图后，强制校验资产存在：
python scripts/compile_wan_scene.py OUT/my-story/scene_plan.json --strict-assets
```

### D-Wan 1 — 划定正确的元素边界

- 持握/穿戴/骑乘道具与演员同组。
- 与源绑定的发射物：若嘴/喷嘴位置、后坐力、身体发力、发射时序必须一致，则与发射体同组。
- 仅在释放后、或确需独立位移/遮挡/复用/蒙版时，才拆出特效。源点在动则必须有跟踪路径；散文对齐规则不够。
- 短接触用独立演员 + 互动契约同步。
- 持续接触/肢体缠绕：经匹配的接触前端点，进入临时接触组。
- 远处建筑保持静态；只动画那些运动能读出来的层。

### D-Wan 2 — 制作端点图与任务

每张端点图：同一元素画布、同一比例、同一视角、同一身份/色板。色键用主体上没有的统一纯色；发光特效用黑底。

- I2V：稳定姿态类或循环（待机、呼吸、站定反应、接触保持）。
- FLF2V：受控位移、姿态、位置、剪影或接触过渡。
- 锁定机位 = 不做跟踪/回中。位移时让身体在共享元素画布内走位，并表现迈步/重心转移。
- 合成侧 `height` 跨姿态保持稳定。蹲下/倒下时身体在画布内变矮，不要缩小整层。

```bash
python scripts/wan_generate.py OUT/my-story/wan_jobs.json --dry-run
python scripts/wan_generate.py OUT/my-story/wan_jobs.json
```

### D-Wan 3 — 抠图与合成

Wan MP4 无 alpha。每个片段转成 RGBA PNG 序列时，整段用同一联合裁切。禁止按帧各自 autocrop。

```bash
# 批处理按各 job 的 chroma/luma 策略；pixel-8bit 默认 grid 4
python scripts/key_wan_jobs.py OUT/my-story/wan_jobs.json
python scripts/qa_wan_handoffs.py OUT/my-story/compiled_scene_plan.json --save-overlays
# 或手动抠一段：
python scripts/cutout_video.py RAW.mp4 -o RGBA --mode chroma --key-color '#00FF00'
python scripts/compose_scene.py OUT/my-story/compiled_scene_plan.json \
  -o OUT/my-story/renders/final.mp4
```

终渲前先检孤立片段：关节身体驱动、附着物、脚底接触、后坐力/跟随、端点匹配、蒙版、机位稳定是硬门槛。
合成里对每个状态/交接边界逐帧检查。只重生成失败状态。

Wan 失败时停止并保留 `wan_run_report.json`。对受影响节拍重试/重规划、用有动机的切镜/遮挡，或整段改走 D-Frames。
禁止把一张静态演员/接触图塞进运动节拍当成片。

### D-Wan 交付物

交付 `scene_plan.json`、`compiled_scene_plan.json`、`wan_jobs.json`、端点图、
`wan_run_report.json`、原始 Wan MP4 + 元数据、RGBA 序列 + 抠图报告、
`handoff_qa_report.json`（适用时含 overlay）、合成帧，以及 `final.mp4`。

---

## Mode D-Frames — 纯图像连续性回退

部件可能变形时，**禁止**把一次性纯文本精灵表当生产成片。  
**必须**遵循 [continuity.md](continuity.md)：部件清单 → 拓扑句 → 密集阶段 → 双参考 → 目视 QA → 只打包通过帧。

### D0 — 分级 + 帧预算

| 难度 | 方法 | 干净生成帧 | 预览 FPS |
|---|---|---|---|
| 轻 | 微关键 | 24–32 | 10–12 |
| 中 | **分阶段微关键** | **48–52** | 12 |
| **长（纯图像）** | **幕次 + 桥接（+ 特效层）** | **100–120** | 12 |
| 难（若有视频） | I2V 抽干净帧 | 48–120 | 12–15 |

出现任一情况且 **Wan/视频生成不可用** 时走 D-Long：用户要 ≥8s、约 100+ 帧、多阶段技能招、光束/球体特效，或抱怨动作太短/跳。

**禁止**用 `--hold 10` 把 8 个姿态注水成“长动作”。

每帧 = **一个清晰姿态**（无残影）。姿态瞬移为硬失败。

**禁止**用混合/ffmpeg 插帧填表。细节见 [continuity.md](continuity.md)、[long-action.md](long-action.md)。

### D1 — 锚图 + 部件清单

1. 起草 `parts.json` + 拓扑句 + 色彩锁定（[continuity.md](continuity.md)）；记录 `style_id`。
2. 在 `#00FF00` 上生成中性锚图，清单内每个部件**清晰分离**，使用当前风格 Master。
3. 抠图；拒绝部件粘连的锚图。
4. 保存 `anchor_greenscreen.*`、`parts.json`。

### D2 — 派生（防变形 + 防跳跃 + 防残影）

1. 写微阶段 — 每阶段一次 GenerateImage（中等约 48–52；长动作从 `acts.json` 展开）。
2. 每条提示：风格预设 + 拓扑 + 色彩锁定 + 仅 FREE + 仅增量 + 动作类锁定 +  
   **“Single crisp pose only. NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure.”**
3. 参考：先 `[anchor]`，再 `[anchor, previous_accepted]`。
4. 每批 ≤4 张，目视 QA；**拒绝任何残影/多重曝光**；再生后再继续。
5. 要加长：生成更多真实帧或桥接缺口，禁止把两帧混成一格。

### D-Long — 纯图像长动作（摘要）

完整协议：[long-action.md](long-action.md)。

```bash
python scripts/init_long_action.py --template kamehameha --out OUT/my-move
python scripts/expand_stages.py OUT/my-move/acts.json
# 按幕双参考生帧 → 抠图 → ordered
python scripts/qa_frames.py ACT/ordered --max-pair-diff 0.22 --max-ghost 0.35 \
  --write-bridges ACT/bridge_jobs.json
# 从 bridge_jobs.json 生桥接帧 → 插入 → 再 QA
python scripts/merge_acts.py OUT/my-move/acts.json --layer character -o OUT/my-move/ordered
# 若有特效层：
python scripts/compose_layers.py --character OUT/char/ordered --vfx OUT/vfx/ordered \
  -o OUT/composited/ordered
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 1
```

### D3 — 打包（仅干净帧）

```bash
python scripts/cutout_assets.py FRAMES/*greenscreen* --mode green -o OUT/rgba
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 1 --anchor bottom-center
```

`interpolate_sequence.py` **仅预览**；禁止把混合输出打进 `motion/frames` 或 `sheet.png`。  
`--hold 2` 仅用于已通过 QA 的唯一帧调节奏——**不能**替代缺失动作。

交付：`frames/`、`sheet.png`、`manifest.json`、`preview.gif`、`parts.json`（D-Long 另加 `acts.json` / `stages.json`）。

### D4 — 合成端

HyperFrames（默认）或 Remotion 消费 `manifest.json`。单贴纸上下浮动/缩放 → Mode C + easing，不要 Mode D。

---

## 动画检查清单

```
- [ ] 已选模式：有端点视频生成时用 D-Wan
- [ ] 已锁定 style_id（默认 cozy-scrapbook）
- [ ] D-Wan：已写故事节拍 + 镜头 + 元素状态时间线
- [ ] D-Wan：分组遵循共享运动/接触；源绑定发射物已同组
- [ ] D-Wan：每个生成状态声明 motion_space；位移/混合有 body_mechanics
- [ ] D-Wan：合成变换不替代步态、后坐力或动作弧线
- [ ] D-Wan：持续接触有匹配的接触前端点 + 可执行交接
- [ ] D-Wan：qa_wan_handoffs.py 通过中心/缩放/剪影检查
- [ ] D-Wan：状态边界保持位置、地线、朝向、缩放
- [ ] D-Wan：互动事件共享精确时序；机位不跟踪/回中
- [ ] D-Wan：色键不在主体上；发光特效用黑底+亮度
- [ ] D-Wan：单片段通过身体驱动/附着/脚底/蒙版 QA
- [ ] D-Wan：终渲边界通过逐帧瞬移/缩放/消失 QA
- [ ] D-Wan：失败 Wan 任务已重试/重规划，未用静态硬切顶替
- [ ] 已写 parts.json + 拓扑句
- [ ] 锚图展示全部部件，易混淆件可区分
- [ ] 预算：中等约 50 或 D-Long 约 100–120 唯一帧（非 hold 注水）
- [ ] 第 1 帧后尽量使用双参考
- [ ] 每批都有色彩锁定 + 姿态类锁定 + 无残影
- [ ] 无姿态瞬移；无一键全表当生产源
- [ ] qa_frames.py 通过（需要时已生桥接）
- [ ] pack_motion.py 仅打干净帧 @ ~12fps，hold≤2
```

## 脚本

| 脚本 | 作用 |
|---|---|
| `scripts/init_wan_scene.py` | 脚手架分层 Wan 场景 |
| `scripts/compile_wan_scene.py` | 校验耦合/运动/边界/交接契约 → Wan 任务 |
| `scripts/wan_generate.py` | 健康检查 + 重试/续跑 I2V/FLF2V + 运行报告 |
| `scripts/cutout_video.py` | Wan MP4 → 稳定画布 RGBA 帧 |
| `scripts/key_wan_jobs.py` | 批量抠出所有已编译 Wan 任务 |
| `scripts/qa_wan_handoffs.py` | 比较离开演员与接触组入口几何 |
| `scripts/compose_scene.py` | 时间/z/摆放/可见性交接合成 → MP4 |
| `scripts/cutout_assets.py` | 色键 / 白底 → RGBA |
| `scripts/split_parts.py` | 拼版 → 部件 |
| `scripts/qa_frames.py` | 缩放 + 姿态跳跃门槛；`--write-bridges` |
| `scripts/interpolate_sequence.py` | 仅预览的变形（**禁止**打包） |
| `scripts/pack_motion.py` | 对齐 → 精灵表 + manifest + GIF |
| `scripts/init_long_action.py` | 从模板脚手架 D-Long 工程 |
| `scripts/expand_stages.py` | `acts.json` → 编号微阶段 |
| `scripts/pick_candidates.py` | 在 take_a/take_b 中选跳跃更小的一版 |
| `scripts/merge_acts.py` | 拼接各幕 → 全局 ordered |
| `scripts/compose_layers.py` | 角色 + 特效层合成 |

通过本 skill 的绝对路径解析脚本。示例见 [examples.md](examples.md)。
