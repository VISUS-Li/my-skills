# 纯图像长动作（无视频模型）

当用户需要 **≥8s / 约 100–120 唯一帧**、多阶段招式（如龟派气功、御剑长飞、连招），
且**仅有 GenerateImage**（无 I2V / 视频）时使用。

配套 [continuity.md](continuity.md)。若之后有视频模型，优先其 Hard 路径；本文是**纯图像生产路径**。

## 为什么不能一张全表？

一次 GenerateImage 画整张精灵表**不会**产生时间线。格子是并行采样 → 格子越多，身份漂移与姿态瞬移越严重。
表是**导出**（`pack_motion.py`），绝不是动作源。

允许的一次性条带：**仅原型**（≤8 格，轻待机）。生产 = 逐帧，或**按幕行**（见下）。

## 集成流水线（照此做）

```
D0  分级 → 若长 / 多阶段 / 特效 → Mode D-Long（本文）
D1  parts.json + 拓扑 + 色彩锁定 + style_id
D1b 双锚图：character_anchor（+ 可选 vfx_anchor）于 #00FF00
D2  acts.json → expand_stages.py → 编号微阶段（约 100–120 唯一帧）
D3  每幕、每层：
      - 生成 1 条主 take（双参考：[act_anchor 或 global_anchor, prev]）
      - 可选第 2 take 进 candidates/（同阶段）
      - 两边都有时用 pick_candidates.py
D4  qa_frames.py --write-bridges → GenerateImage 桥接（1–3）→ 再 QA
D5  merge_acts.py → 全局 ordered 序列
D6  若分层则 compose_layers.py（角色 + 特效）
D7  pack_motion.py --hold 1（优先真实帧；hold≤2 仅调节奏）
```

脚本（本 skill 的 `scripts/`）：

| 脚本 | 作用 |
|---|---|
| `init_long_action.py` | 脚手架工程 + 复制幕次模板 |
| `expand_stages.py` | `acts.json` → `stages.json` / 分幕阶段列表 |
| `qa_frames.py --write-bridges` | 姿态跳跃报告 + 桥接任务 JSON |
| `pick_candidates.py` | 每槽选跳跃更小的 take |
| `merge_acts.py` | 拼接各幕文件夹 → 全局 `ordered/` |
| `compose_layers.py` | 按帧索引 alpha 合成角色 + 特效 |

## 帧预算（纯图像）

| 目标时长 @ 12fps | 唯一干净姿态 | Hold | 打包 |
|---|---|---|---|
| ~4s（短） | 48–52 | 1 | ~50 |
| **~8–10s（长默认）** | **100–120** | **1** | **100–120** |
| ~10s 更慢读 | 80–100 | 2 | ~160–200 |

**Hold 不加动作。** 优先更多唯一微阶段。

预算按幕拆分（例：龟派气功 ≈ 120）：

| 幕 id | 阶段 | 唯一帧 |
|---|---|---|
| `charge` | 站定 → 双手合掌蓄力 | 24 |
| `form` | 掌心能量球成形变大 | 28 |
| `fire` | 推出光束 + 身体后坐 | 36 |
| `recover` | 余波消散 → 收势 | 24 |
| *(bridges)* | QA 失败对之间 | +8–12 预留 |

## 幕次文件（`acts.json`）

```json
{
  "project": "kamehameha",
  "style_id": "cozy-scrapbook",
  "target_unique_frames": 112,
  "fps": 12,
  "hold": 1,
  "layers": ["character", "vfx"],
  "global_action_family": "kamehameha",
  "acts": [
    {
      "id": "charge",
      "title": "蓄力合掌",
      "unique_frames": 24,
      "action_class": "kamehameha_charge",
      "free_channels": ["arm_angle", "knee_bend", "torso_lean"],
      "vfx": {
        "enabled": true,
        "free_channels": ["seed_scale", "seed_glow_radius"],
        "must_never": ["full beam", "large orb bigger than head"]
      },
      "beat_summary": "hands rise → palms face → small seed appears → seed grows slightly"
    }
  ]
}
```

规则：

- 每幕只有**一个** `action_class`（幕中禁止瞬移到另一类）。
- 第 N 幕最后通过帧是第 N+1 幕第 1 帧的**种子参考**（外加全局锚图）。
- 身份崩了就整幕重生；禁止用混合「修补」。

## 按幕行生成（不是一张巨型表）

每幕可可选生成**不超过 8 格的横向条带**作*草图*，然后**丢弃不作生产**，再用双参考逐格派生。
推荐生产路径：**每个微阶段一次 GenerateImage**。

用行条作中间产物时：

- 最多 **8** 等大格，大块 `#00FF00` 间隙
- 传入 `[character_anchor]`（若有布局导则也可）
- 抽格 → 仅作**候选** → 仍须 QA + 桥接

## 微阶段写法（防跳跃）

对有 `N` 帧的幕，写 `N` 行，每行是 **5–15%** 增量：

```text
charge/01: arms at sides, knees soft
charge/02: arms lift 10° toward chest
...
charge/24: palms nearly touch, seed pea-sized between hands
```

每帧提示包含：

- 风格 Master + Negatives
- 拓扑 + 色彩锁定（INVARIANT）
- **仅本幕** FREE 通道
- `delta only vs previous: …`
- `SINGLE CRISP POSE; NO motion blur / afterimages / multi-exposure`
- 参考：`[global_anchor, previous_accepted]`（第 1 幕第 1 帧：`[global_anchor]`）

每批 ≤4，每批目视 QA。

## 特效分层（光束 / 球体 / 光环必做）

图像模型会把发光能量融进袖子/头发。拆层：

| 层 | 内容 | 锚图 |
|---|---|---|
| `character` | 身体、衣服、肢体 — **无**光束/球（或仅极小接触提示） | `character_anchor` |
| `vfx` | 仅能量种子 / 球 / 光束 / 冲击火花 | `vfx_anchor`（或空绿幕 + 道具） |

两层同帧索引 = 同一节拍。抠图后：

```bash
python scripts/compose_layers.py \
  --character OUT/character/ordered \
  --vfx OUT/vfx/ordered \
  -o OUT/composited/ordered
```

角色提示：蓄力早期写 `NO energy beam, NO glowing orb larger than a pea`。  
特效提示：`NO full body, NO face, only energy prop on #00FF00`。

## 候选池（可选但推荐）

每幕槽位 `k` 最多保留 2 条 take：

```
acts/charge/takes/take_a/frame_01.png
acts/charge/takes/take_b/frame_01.png
```

```bash
python scripts/pick_candidates.py acts/charge/takes -o acts/charge/ordered
```

选出平均相邻 pair-diff 更低（且残影更少）的 take 序列。

## 桥接（QA 失败时强制）

```bash
python scripts/qa_frames.py OUT/ordered \
  --max-scale-jitter 0.25 --max-pair-diff 0.22 --max-ghost 0.35 \
  --write-bridges OUT/bridge_jobs.json
```

对每个 `pose_jump` 对 `(A,B)`，用参考 `[global_anchor, A]` 生成 **1–3** 中间姿态，增量朝向 B。插入、重编号、再 QA。
**禁止**把 `interpolate_sequence.py` 输出当打包格子。

## 打包

```bash
python scripts/pack_motion.py OUT/ordered -o OUT/motion \
  --cell 512 --fps 12 --hold 1 --anchor bottom-center
```

长动作：默认 `--hold 1`。仅当唯一姿态已通过 QA 但播放偏赶时用 `--hold 2`。

## 检查清单（D-Long）

```
- [ ] 确认纯图像（无视频）→ 本协议
- [ ] acts.json 预算合计约 100–120（+ 桥接预留）
- [ ] character_anchor（分层则加 vfx_anchor）
- [ ] 分幕微阶段已展开（expand_stages.py）
- [ ] 双参考；批≤4；拒绝残影
- [ ] QA + 桥接直到 pair-diff 通过
- [ ] 需要时已合成各层
- [ ] pack --hold 1 仅打干净唯一帧
- [ ] 无一键全表当生产源
```

## 模板

- `assets/templates/acts_kamehameha.json` — 龟派气功类
- `assets/templates/acts_sword_fly.json` — 御剑穿云长飞
- `assets/templates/acts_generic_long.json` — 空白 4 幕脚手架

```bash
python scripts/init_long_action.py --template kamehameha --out ./sticker-kit-output/my-move
python scripts/expand_stages.py ./sticker-kit-output/my-move/acts.json
```
