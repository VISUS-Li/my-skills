# Deep Narrative Investigation

**Default scriptwriting mode for video-producer.** Load this whenever writing or revising `outline.md` or `voiceover.md` — for **one event or many**, for news, history, profiles, or explainers.

The user should **never** need to say “先跑 thread-weave” or name internal stages. If they ask for 文案 / 口播 / 脚本 / 深度 / 来龙去脉, you automatically:

1. Research beyond the headline
2. Build `thread_ledger.csv` + `narrative_thread_map.json`
3. Write thread-driven 口播稿
4. Run `thread_depth_lint.py` before delivering copy

## Three core failures to avoid

| Failure | Symptom |
|---|---|
| **Parallel explainer** | User gave A/B/C → script has “第一…第二…第三…” with no verified links |
| **Headline reader** | User gave one event → script only restates news + generic background, no 前尘/秘辛/博弈/后果 |
| **News ticker** | Fact after fact with hard cuts — no dwell, no landing, no story glue; reads like 通稿 not 讲故事 |

**Goal:** one **continuous story** — the viewer feels pulled forward, each turn fully landed before the next begins. Facts serve the arc; the arc is not a list of facts.

Load with `fact-linked-script-system.md` and `retention-storytelling-and-voice.md`.

## Auto-routing (agent decides — user does not specify)

| User signal | You do automatically |
|---|---|
| Any 文案 / 口播 / 脚本 request | Full deep narrative path (this doc) |
| One topic, one event | **Single-story arc** mode (see below) |
| Multiple bullets / names / events | **Multi-thread weave** mode |
| “只要大纲 / 不要调研” | Shallow outline only — **explicit opt-out** required |
| Factual topic | Also fact-lock + claim IDs |
| Pure fiction / mood piece | Skip claim ledger; still use master thread + spine |

**Never ask** “要不要跑 thread-weave?” — just do it unless user opted out of depth.

## Required artifacts (always, before final voiceover)

| File | Purpose |
|---|---|
| `research/thread_ledger.csv` | Verified links: between entities **or** between story phases |
| `script/narrative_thread_map.json` | `story_scope`, master thread, insight layers, omissions, spine |
| `research/claim_ledger.csv` | Facts + `claim_type=relationship` for each verified link |

---

## Mode A — Single event / one story (同样要深挖)

User gives **一件事**：某次发布会、某个政策、某个人的一个决定、某场危机。

Do **not** stop at “发生了什么”. Dig:

| Phase | Research question | thread_ledger link types |
|---|---|---|
| **前尘** | 早先埋下了什么伏笔？谁 earlier 做过类似动作？ | `prelude`, `origin` |
| **导火索** | 这次为什么在这个时间点爆发？ | `trigger`, `turning_point` |
| **博弈** | 谁推动、谁阻挠、各自激励是什么？ | `incentive`, `conflict`, `constraint` |
| **转折** | 哪个细节是分水岭？（限定词、措辞、金额、人事） | `turning_point`, `hidden_context` |
| **后果** | 之后改变了什么？短中长期 | `effect`, `aftermath`, `legacy` |
| **秘辛** | 较少人知道但**可证实**的背景 | `hidden_context` + claim_ids |

**Master thread (single-story)** — one sentence naming the **arc**, not the topic label:

> “这期讲的不是 X 事件本身，而是 ______ 如何从 ______ 一路推到现在这一步。”

Example (one event: 某公司突然开源某模型):

- Bad: 5 段百科 — 什么是开源、公司介绍、模型参数、社区反应、总结
- Good: “表面是技术慷慨，实际是在 ______ 压力下来的一次 ______ 换 ______ —— 关键转折是 ______ 那句限定词。”

Minimum `thread_ledger` for single-story: **≥3 substantive rows** (e.g. prelude→trigger, trigger→turn, hidden detail reframes).

---

## Mode B — Multiple points (编织，不是并列)

User bullets are **raw material**, not section headers.

Research **pairs** (A↔B) for: `cause`, `effect`, `incentive`, `conflict`, `alliance`, `escalation`, `turning_point`, `hidden_link`, `open_question`.

Minimum rows: **≥ max(2, N−1)** for N input points.

Master thread names how points sit on **one chain**, not a list.

---

## Shared workflow

### 1 — Inventory (no script yet)

Capture in `narrative_thread_map.json`:

- `story_scope`: `single` | `multi`
- `user_input_points` (1 or many)
- Implied questions: why now? who wins/loses? what do viewers get wrong?
- `narrative_engine` (pick one): misread_correction | incentive_chase | escalation_ladder | two_front_squeeze | hidden_third_party | timeline_pivot | **origin_to_aftermath** (default for single-story)

### 2 — Research links, not summaries

For each link row: `supporting_quote` + `source_ids` in claim ledger, or mark `open_question` / cut.

**Never invent** connection for drama. Insufficient evidence → say on camera or omit.

Link types (use in `thread_ledger.relationship_type`):

`prelude`, `origin`, `trigger`, `cause`, `effect`, `incentive`, `constraint`, `conflict`, `alliance`, `escalation`, `turning_point`, `aftermath`, `legacy`, `hidden_context`, `hidden_link`, `open_question`

### 3 — Master thread + insight layers

```json
"insight_layers": {
  "surface": "观众以为的故事",
  "mechanism": "实际怎么运转",
  "secret": "可证实的、能眼前一亮的细节"
}
```

`secret` **required** — must have claim IDs or be cut. Test: “懂行的人读源也会说没想到这点吗？”

### 4 — Selective depth (anti-啰嗦)

`selective_omit[]` — **required**. Cut true-but-irrelevant dates, side characters, textbook definitions.

Keep: pivots, misreads, proof moments, one sourced “秘辛”.

Target: **one insight per 15–25s**, not chronological completeness.

### 5 — Spine (story order, not bullet order)

| Phase | Single-story | Multi-point |
|---|---|---|
| Hook | Strongest misread or secret hint | Strongest **link**, not weakest bullet |
| Setup | False simplicity | Same |
| Turns | 前尘 → 博弈 → 转折 → 后果 | A↔B link, then B↔C |
| Payoff | One memorable arc sentence | Master thread restated |

**Forbidden:** 第一第二第三 / 首先其次 / 今天讲N个点 / equal time per bullet / Wikipedia sections.

### 5b — Story continuity (anti 新闻稿 / anti 戛然而止)

**News copy vs story copy:**

| 新闻稿感 | 讲故事 / 口播沟通感 |
|---|---|
| 据悉、据报道、此外、另外、与此同时 | 顺着一条线在讲，像在带观众走 |
| 抛一个事实就跳下一段 | 每个拐点 **停住、挖透、收束** 再往下走 |
| 只有 who/what/when | 每层都有 why、对谁有利、意味着什么 |
| 段与段互不引用 | **回调**前文细节：“回到刚才那个限定词…” |
| 信息密度均匀、无节奏 | 该快则快（hook），该慢则慢（转折处多留 2–3 句） |

#### Beat dwell rule (每个拐点必须挖透再跳)

Before leaving any story beat, cover **four layers** in order (plan in `spine[].dwell_layers`, write in voiceover):

| Layer | Job | Min |
|---|---|---|
| `enter` | 从上一节拍 **承接** 进来（不是硬开新段） | 1 句 |
| `evidence` | 可引用的具体细节（日期/主体/原文/数字） | 1–2 句 + `[Cxxx]` |
| `mechanism` | 为什么发生、谁推动/谁受损、博弈或约束 | 1–2 句 |
| `landing` | **收束**：这意味着什么；为下一节拍 **留钩子** | 1 句，必填 |

**`landing_line`** (in `narrative_thread_map.json` spine) — written before scripting. Example:

> “所以问题不在封号本身，而在条款把‘谁能用’的定义悄悄改窄了——后面每一环都从这里长出来。”

**`carry_forward`** — what the **next** beat must pick up (prevents 戛然而止):

> “带着这个限定词，再看第二次收紧就不意外了。”

**Minimum per major beat in voiceover:** 4 spoken sentences covering enter → evidence → mechanism → landing.  
If a beat has only 1–2 fact sentences then jumps → **fail** — expand mechanism or landing, do not add unrelated facts.

#### Continuity devices (mandatory at least 2 in full script)

- **Callback:** 回到刚才 / 前面那个日期 / 同一份文件里另一处
- **Latch:** 如果只看到 A 还说得通，加上 B 整条线才闭合
- **Pending payoff:** 先记住 X——到后面 Y 才看得懂为什么
- **Stakes for viewer:** 这事真正卡住的，是 ______（基于证据，不是空泛感叹）

#### Transition rule (禁止硬切)

**Forbidden openers for a new beat:** 此外 / 另外 / 与此同时 / 接下来 / 再说 / 还有一个

**Use instead:** 所以到这里 / 这就是为什么 / 带着刚才这一点 / 时间线再往后推一步 / 同一根链的下一环是

Each spine phase in JSON must include: `landing_line`, `carry_forward`, `dwell_layers` (all four keys).

---

### 6 — 口播 voiceover

Write as **one continuous telling** — a guided walk through evidence, not a bulletin list.

#### Researched oral voice (use this)

**Sound:** 短句、有节奏、结论先行，每句转折都**挂证据**。

| Device | Example |
|---|---|
| 证据锚点 | “原文里写得很清楚……” “把时间线往回拖一年就看出来了……” |
| 来源并列 | “把公告和那份纪要放一起看，矛盾点在这……” |
| 纠正误读 | “很多人只看标题；但条款限定的是 ______，不是 ______。” |
| 节奏停顿 | `[pause]` / `……` 放在**抛证据前**，不是装神秘 |
| 重复强调 | 重复**关键事实词**（日期、主体、限定词），不重复空泛感叹 |
| 轻修正 | “不对，更准确地说——官方口径是 ______。”（修正方向更精确，不是改口胡编） |

**Bridge lines (mandatory — must cite or point to source):**

- Single: “回头看 ______ 那次动作，伏笔已经在了……[C001]”
- Multi: “A 条款一收紧，B 的 ______ 就被动收缩——这才和 C 对上。[C002]”
- Secret: “很多人漏了原文里那个限定词……[pause] 这才是分水岭。[C003]”

#### Speculative oral voice (forbidden)

These make copy sound like **主观臆想**， not researched conclusion — **do not use**:

- `你想啊` / `你想想看` / `你觉得呢`
- `其实吧` / `我跟你说` / `这就有意思了`
- `说白了`（除非紧接 `[OPINION]` 且前面已摆完证据）
- 空泛反问：“难道不是吗？”“是不是很疯狂？”（无证据承接）
- 无来源的“我觉得/我猜/估计/大概率”（→ 用 `[OPINION]` + 已列证据，或删掉）

**Rule:** 口播可以松，**论断不能飘**。每一句让观众感到“他查过、他对过原文”，不是“他在带我一起猜”。

#### Voiceover block template (each major beat)

```md
<!-- BEAT: turn / thread T002 -->

[enter — 承接上一节拍]
时间线再往后推一步，同一份文件里还有一处容易被跳过。[C002]

[mechanism — 博弈/为什么]
条款改的不是口号，是谁还算“合规用户”——代理层只能跟着收缩。[C002b]

[landing — 收束 + 留钩]
所以到这里，问题已经不在表面公告，而在定义被改窄了；带着这个限定词，后面第二次收紧就不意外了。

<!-- carry → next beat -->
```

#### News-style phrasing (forbidden)

`据悉` `据报道` `消息称` `此外，` `另外，` `与此同时，` `值得一提的是`（无承接时用）

---

## Quality checklist (before delivering 文案)

- [ ] `story_scope` set; master thread is an **arc or relationship**, not a title repeat
- [ ] `thread_ledger` has enough substantive rows (single ≥3, multi ≥ N−1)
- [ ] At least one sourced `secret` in insight_layers
- [ ] `selective_omit` shows editorial control
- [ ] Each spine beat has `landing_line` + `carry_forward` + full `dwell_layers`
- [ ] Voiceover beats have ≥4 sentences (enter/evidence/mechanism/landing) before topic shift
- [ ] ≥2 continuity devices (callback / latch / pending payoff)
- [ ] No news hard-cuts (此外/另外/据悉/与此同时)
- [ ] No parallel 第一/第二 structure
- [ ] Bridges anchor to **sources** (原文/公告/时间线/条款), not speculative fillers
- [ ] No forbidden phrases (你想啊 / 其实吧 / 我跟你说 / …)
- [ ] All links have claim_ids or are `open_question`

Run: `scripts/thread_depth_lint.py <project> --fail-under 80`

## Anti-patterns

| Bad | Good |
|---|---|
| 把用户给的点逐条念完 | 一条主链讲清楚来龙去脉 |
| 单事件只复述新闻通稿 | 前尘 + 博弈 + 秘辛 + 后果，有选择地深 |
| 没来源的“幕后黑手” | “能确认的是 X；Y 尚无实锤” |
| 百科式背景堆满 | 只留服务主链的 2–3 个关键拐点 |
| 书面语、公文腔 | 调研后的口语：短句 + 证据锚点 |
| 新闻稿：此外 A，另外 B，同时 C | 一条线：A 改定义 → 所以 B 收缩 → 这才引出 C |
| 讲一点就跳，没有 landing | 每拐点 landing 收束 + carry_forward 再接下一环 |
| 只有事实陈述 | 事实 + 机制 + 对故事线意味着什么 |

## Examples

**Single event:** “OpenAI 某次 DevDay 发布”

Master thread: “这不是功能更新，是 ______ 战略下，用 ______ 换 ______ 的一步棋；分水岭是 keynote 里那句 ______。”

**Multi-point:** OpenAI 收紧 API / 国内出海 / 封号潮

Master thread: “三条新闻同一根链：合规收紧 → 代理层收缩 → 误读式封号叙事。”
