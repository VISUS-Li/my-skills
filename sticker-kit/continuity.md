# 连续性与防变形规则（Mode D）

图像模型会跨帧**合并外形相似的部件**（例如锅铲柄被吸进炒锅变成永久锅柄；肢体数量变化；车轮忽有忽无）。
对**任意**主体/动作，把这当作一等故障模式处理。

## 不变项 vs 自由项（关键）

生成前把属性拆成两份列表。每帧提示词都必须包含两者。

| 通道 | 跨帧可变？ | 示例 |
|---|---|---|
| **FREE（仅运动）** | 是 | 关节角、肢体姿态、跳跃高度、武器挥弧、软动作线的压扁/拉伸 |
| **INVARIANT（身份）** | 否 | 部件颜色、描边粗细、服装色、发色、肢体数量、谁是谁、脸部位置、材质 |

**经验法则：** 不是当前动作阶段要求的姿态变化，就不得漂移。  
颜色闪烁（鼠尾草绿车把 → 红色车把）是**硬失败**——丢弃并重生。头发、鞋、武器、载具部件突然换色同理。

色彩锁定写成 hex / 常用名，贴进每条提示：

> Color lock (INVARIANT): hair=#3D3429, jacket=#E85D4C, pants=#5B7C99, shoes=#F5F0E6, sword blade=#C0C6D0, sword grip=#8B5A2B — never recolor.

## 任何动作生成前的强制项

从 [styles.md](styles.md) 锁定 **`style_id`**（默认 `cozy-scrapbook`），整段片段保持一致。中途换风格必须重做锚图。

写一份 **部件清单**（存为 `SUBJECT/parts.json`，并贴进每条提示）：

```json
{
  "subject": "short name",
  "style_id": "cozy-scrapbook",
  "must_always_exist": [
    {"id": "body", "desc": "...", "attach": "core", "color": "#..."},
    {"id": "tool_a", "desc": "SEPARATE movable tool — never fused to body", "attach": "held/resting", "color": "#..."}
  ],
  "must_never_appear": ["extra handles", "second tool", "text labels"],
  "lookalike_warnings": [
    "tool_a.handle must NEVER be redrawn as a body-mounted handle"
  ],
  "color_lock": {
    "part_id": "#hex or named color — INVARIANT"
  },
  "free_channels": ["pose", "limb angles", "weapon swing", "vertical hop"],
  "topology_lock": "exactly N wheels, M handles, K limbs — constant every frame"
}
```

再发明一句一字不改复用的 **拓扑句**，例如：

> Topology lock: ONE wok body + ONE small LEFT rim loop only + ONE separate spatula with its OWN wooden handle; spatula is NEVER a wok handle; wok has NO long side handle.

## 锚图规则（加强）

1. 中性姿态，**清单内每个部件可见且明确分离**。
2. 两部件外形相似时（两根木棍、两根管、天线 vs 剑），在锚图里做成**视觉可区分**（不同颜色/粗细/端帽），避免后续帧互换。
3. 锚图优先「拆解清晰」，而非电影感重叠。
4. 已粘连易混淆件的锚图直接拒绝。

## 帧数与时序（避免过快/跳跃循环）

**默认交付目标：约 48–52 帧**（中等），每帧为**单独生成的单一姿态**。

**多阶段长动作（纯图像）：** 约 **100–120** 唯一帧，见 [long-action.md](long-action.md)——**禁止**用大 `--hold` 注水时长。

**禁止**用混合/变形把两个姿态合成一张图来凑长度。

**禁止**把一整张巨型精灵表当动作源（仅作导出）。

| 难度 | 生成帧（每帧=一个干净姿态） | 预览 FPS | 目标时长 |
|---|---|---|---|
| 轻 | 24–32 | 10–12 | ≥2.5s |
| 中（默认短片） | **48–52** | 12 | ≥4s |
| **长（纯图像，无视频）** | **100–120**（幕次+桥接） | 12 | **≥8–10s** |
| 难（若有 I2V 抽取） | 抽取 48–120 干净帧 | 12–15 | ≥4–10s |

- 宁可多做 GenerateImage 微姿态，也不要在稀疏关键上抬高 FPS。
- 生成前列出**每一个微阶段**；每阶段相对上一帧仅**微小增量**（肢体行程约 5–15%）。
- **姿态类锁定**：每幕选一个动作类（`run_cycle` | `slash` | `kamehameha_charge` | …）。中途换类为**硬失败**。
- 错误跳跃示例（禁止打包）：跑步跨步 → 半空跳跃 → 三点蹲 → 再跑步。
- 光束/球体/光环：用**特效层拆分**（[long-action.md](long-action.md)），避免能量融进身体部件。

## 一帧一姿态（无残影）——硬规则

打包表中每一格必须是**恰好一个不透明主体姿态**。

**生成提示与后期均禁止：**
- 复制身体的运动模糊 / 速度线
- 残影 / 鬼影拖尾 / 多重曝光 / 洋葱皮观感
- 成对 RGBA **混合**插值
- 把 ffmpeg/RIFE 变形帧当**贴纸表**格子

**每帧提示必含：**
> Single crisp pose only. One body, one silhouette. NO motion blur, NO afterimages, NO ghost trail, NO multi-exposure, NO onion-skin.

若生成图已有分层残影：**丢弃并重生**——不要打包。

### 插值 —— 不用于生产贴纸表

| 用途 | 允许？ |
|---|---|
| 最终 `sheet.png` / `frames/`（HyperFrames/Remotion 贴纸） | **否** — 仅真实生成（或 I2V 抽取）的干净帧 |
| 用户明确要求的可选软预览视频 | 可以（标明仅预览；与 `motion/frames` 分开） |

要到约 50 帧：先**生成干净姿态**（或从 I2V 抽取），再可选 **hold 重复**调节奏。  
禁止用混合两张贴纸帧「假造」中间帧——那正是用户反感的残影。

## 用 hold 调节奏（无残影的慢放）

唯一姿态已够密但播放仍偏快时，把每张通过帧**重复 N 次**再前进（hold）。

例：唯一姿态 `A B C` 配 `--hold 2` → 打包顺序 `A A B B C C`。  
播放：播完 A，再播一次 A，再进 B——更慢，每格仍是单一清晰姿态（无残影）。

| 目标 | 唯一干净姿态 | Hold | 打包帧数 |
|---|---|---|---|
| ~50 @ 更慢节奏 | 17–25 | 2–3 | ≈50 |
| ~50 更密动作 | 48–52 | 1 | ≈50 |

```bash
python scripts/pack_motion.py OUT/ordered -o OUT/motion --cell 512 --fps 12 --hold 2
# 25 唯一帧 × hold 2 → 50 打包帧
```

优先 hold 而非混合。仍有跳跃时优先增加唯一姿态；姿态已连续但节奏过快时再用 hold。

## 派生规则（防跳跃）

1. **始终**至少 `reference_image_paths = [anchor]`。
2. 第 2 帧起优先 **`[anchor, previous_accepted_frame]`**（双参考），减轻拓扑漂移。
3. 每条提示必须包含：
   - 风格预设 id + 来自 [styles.md](styles.md) 的 Master/Negatives
   - 拓扑句（原文照贴）
   - **色彩锁定（INVARIANT）** — 列出各部件颜色；写明 “do not recolor”
   - 部件清单简表
   - 明确 FREE 列表：“ONLY change: [pose channels]”
   - 明确：“do not add/remove/merge parts; do not recolor; only FREE channels may change”
   - 相对上一帧的微差（“delta only: spatula rotates +8°, food rises slightly”）
4. 存在易混淆部件时，优先**中等关键集**（每阶段一图），而非精灵行。
5. 精灵行仅用于轻动作**且**清单锁定扎实后；仍须逐格 QA。
6. **小批量**生成（如 4 张），QA 后再继续——不要盲发全部 16 张。

## 成帧后 QA（拒绝并重生）

每帧（或每批）后**读图**检查：

- [ ] 每个 `must_always_exist` 部件都在
- [ ] 未出现 `must_never_appear` 部件
- [ ] 未违反 lookalike 警告（无合并/互换）
- [ ] 肢体/轮子/把手**数量**符合 topology_lock
- [ ] **颜色符合色彩锁定**（无部件换色——尤其易混淆棍/条/柄）
- [ ] 主体比例/机位与上一帧大致一致（包围盒高度 ±20%）
- [ ] **姿态类未变**（仍是同一动作；跑步中途无蹲/跳瞬移）
- [ ] 相对上一帧运动增量**很小**（肢体略动，不是新站姿）
- [ ] 相对上一通过帧仅 FREE 通道变化
- [ ] **无残影** — 单一剪影，无残影/多重曝光层

任一失败：**丢弃**，用更强拓扑 + 色彩锁定 + 双参考 + “delta only from previous frame” + “single crisp pose, no afterimages” 重生。不要打包失败帧。

自动跳跃门槛（剪影差；仍须目视 QA）：

```bash
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35 \
  --write-bridges OUT/bridge_jobs.json
```

若 `frame_N` 与 `frame_N+1` 触发 `--max-pair-diff`：用双参考 `[anchor, frame_N]` 生成 **1–3 桥接帧**（见 `bridge_jobs.json` 提示草稿）后再继续。
**禁止**用 `interpolate_sequence.py` 填生产表缺口。

可选自动尺寸抖动门槛：

```bash
python scripts/qa_frames.py OUT/ordered --max-scale-jitter 0.25
```

剪影高度跳动过大时大声失败（弱代理——永不跳过目视 QA）。

## 已知变形模式（可类推到任意主体）

| 模式 | 示例 | 预防 |
|---|---|---|
| 工具柄 → 身体柄 | 锅铲变成锅柄 | 区分颜色；“SEPARATE tool”；禁止长锅柄 |
| 肢体合并/分裂 | 手臂 2→1 | 拓扑写 “exactly 2 arms” |
| 车轮增减 | 车 4→3 轮 | “exactly 4 wheels every frame” |
| 道具瞬移 | 剑消失 | must_always_exist |
| 风格重启 | 颜色被重定义 | 双参考 + “same palette as anchor” |
| 机位弹出 | 循环中途变焦 | “same scale, same framing” |
| 工具↔身体互换 | 铲柄变锅柄 | 区分颜色；SEPARATE tool；禁止身体长柄 |
| 肢体幻觉 | 载具/工具长出手臂 | 明确 “inanimate / NO arms NO person”；拒帧 |
| 脸部漂移 | 眼睛消失或移位 | 锚图有画脸则列入清单并每帧要求 |
| 锚图意外特征 | 模型给货物画了脸 | 把发明出的特征锁进 `parts.json` 往后——不可忽略 |

## 交付

只打包通过 QA 的帧。交接时注明重生次数，让用户知道连续性被强制执行过。
