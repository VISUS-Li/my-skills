# Deep Research And Script

Use this **before beat planning** when the video needs facts, judgment, critique, product analysis, industry context, or a script that should feel **discovered and understood**, not listed.

This file owns: **when to research, what to gather, how to lock sources, which artifacts to write.**  
Voiceover craft lives only in `references/narrative-depth-copy.md` — load it when drafting `outputs/script.md`. Do not duplicate its gates here.

Goal: enough source lock + event expansion to prevent shallow commentary, plus meaning/impact so the viewer leaves with a harvest — **without heavy paperwork**.

## Trigger

Use for:

- AI / product / tool analysis or comparison
- Developer workflow claims (speed, cost, reliability, failure modes)
- News, public events, finance, policy, tech, science, current facts
- User language like 深度 / 深搜 / 拆解 / 分析 / 复盘 / 真相 / 为什么
- Drafts that read like「第一、第二、第三」but lack genealogy + meaning

Skip or keep minimal for pure fiction motion tests, logo stings, UI demos with no factual claims, or user scripts that ask for no research.

## Artifact Tiers

### Always (depth jobs)

```text
research/source_cards.jsonl
research/event_genealogy.md
outputs/script.md
```

`event_genealogy.md` should be enough that a stranger can retell tip → upstream → jam **and** state the viewer harvest. Put cast notes here when actors matter (do not require a separate file by default).

### On demand

| File | When |
|---|---|
| `research/claim_ledger.csv` | Many numeric/legal claims, or easy-to-misstate facts |
| `research/factcheck_report.md` | Dispute, production-time recheck, or skipped checks log |
| `script/narrative_thread_map.json` | Long form or multi-strand; short single-event pieces usually skip |
| `research/thread_ledger.csv` | Multi-strand only |
| `research/cast_and_incentives.md` | Large cast that would swamp genealogy; otherwise fold cast into genealogy |

Small jobs may fold Source Lock + Genealogy (+ Cast) into sections inside `outputs/script.md`. Constraints stay the same.

Older aliases: `misread_map.md` / `stakeholder_incentives.md` → treat as genealogy + cast.

Validate skeleton (not prose quality):

```bash
python scripts/validate_research_lite.py --project /path/to/project
```

## Research Intake

Do not start from slogan judgments. Gather enough to expand the tip into a river **and** know what each hard fact means at human scale.

**Optional breadth coach:** load `references/storyteller-fan-craft.md` and skim the research-width table + **1–2** matching transcripts in `references/storyteller-fan-corpus/CATALOG.md`. Use them to decide *what kinds of material to hunt* (timeline reversals, rule substrate, cast pressure, comparators, mechanism cracks) — not what lines to reuse. Analytical VO later defaults to the same oral craft via `narrative-depth-copy.md`.

Prefer this order when possible:

1. Tip anchors (report / filing / product change / apology + dates)
2. Upstream / 前尘
3. Cast dossiers (role, authority, pressure) — when multi-actor; for unknown companies/founders also grab **identity bits VO will need** (who founded, commercial vs lab, funding order-of-magnitude, stated goal, current product status)
4. Rule substrate (standard, contract, lockup, list, billing, license)
5. Main timeline with reversals
6. Neighbor strands (only if they change the reading)
7. Comparators (paired facts > vibes)
8. Secondary commentary (context only; never sole support for a fact)

Each important source card:

- id, URL/path, title, publisher/author, date
- why it matters to the script
- usable visual: screenshot / table / chart / UI / code / quote / none
- risk: current / old / disputed / interpretation / anecdote / marketing / blocked
- genealogy role: tip / upstream / cast / rule / timeline / neighbor / comparator / impact
- **optional meaning note:** one line on what this evidence implies if used on VO
- **optional dig flag:** mark `dig_worthy` when the tip hides a mechanism, incentive crack, calendar lock, or common misread worth a full analogy+expand beat

Rules:

- Prices, laws, roles, specs, model names, benchmarks, news: check at production time.
- Prefer official docs, primary sources, product UI, repo, changelog, filings, papers, screenshots.
- Weak evidence → mark uncertainty or cut.
- Complaints, anonymous leaks, 「据悉」reprints keep their identity; they are not verdicts.
- Do not invent causal links; bridge cause/effect only when sources support it.

## Research Organize

### Event Genealogy (`research/event_genealogy.md`)

| Field | Required |
|---|---|
| tip | What broke into view + date |
| upstream | Missed 前尘 |
| timeline | Ordered beats + reversals; mark 扣合点 |
| rule_substrate | The rule/contract that traps the story（若本题无关可写 `none` + 理由） |
| neighbor_strands | Parallel lines that change reading（或 `none` + 理由） |
| still_unknown | Unsettled |
| ordinary_impact | Where it lands on users/builders/consumers |
| dig_worthy | At most 1–2 nodes (or `none` + 理由 on thin topics) |
| viewer_harvest | One-sentence takeaway the VO must land (plain language; no type label required) |
| cast | Major actors with role / leverage / pressure（fold here unless separate cast file） |

After this file, a stranger can retell 来龙去脉 in under a minute **and** say what the tip means for ordinary stakeholders.

### Claim Ledger (when used)

Every factual or evaluative line needs: source id(s) / explicit uncertainty / project-generated proof / removal.

Do not infer beyond the screenshot. Wording proof → narrate wording. UI proof → narrate UI. No motive/cause/scale/outcome without support.

For each **numeric or list claim** intended for VO, add a short `meaning` note: what it implies + for whom. No meaning note → do not promote that line into spoken script yet.

### Narrative Thread Map (when used)

Optional structure aid for long/multi-strand scripts. Shape example: `assets/templates/example_narrative_thread_map.json`.

Keep fields lean: tip, genealogy, viewer_harvest, dig_worthy, still_unknown, short spine. Do not re-copy cast/gloss/insight layers that already live in genealogy or the script.

Spine phases are a **menu**, not a mandatory fill. Short pieces often: `tip_stakes` → `dig_expand` → `meaning_impact` → `compress`.

Avoid as structure:

- 「首先 / 其次 / 最后」as sole spine with no river
- Empty speculation without proof
- Slogan conclusions not earned by expansion
- Fact payloads with no meaning/impact path into VO

## Source-To-Visual Binding

**After** `outputs/script.md` passes VO kill checklist (or when the user moves from script-only to picture work), tag important lines with proof type before/while writing `beat_plan.json`:

`source_screenshot` | `screen_recording` | `code_terminal` | `chart_table` | `timeline_board` | `cast_board` | `metaphor_svg`（可选，勿为了填坑硬造）| `human_context`

Do **not** invent pedagogical metaphors during research just to satisfy this list. Selected proofs must later be directed in `segment_spec.json` (crop, push-in, redbox, cursor, highlight, source label, chart build, etc.).

Meaning lines often need a visual that shows **scale or contrast**, not only the raw number card.

## Handoff To Script

When research lock is enough:

1. Load `references/narrative-depth-copy.md` and `references/storyteller-fan-craft.md`; read **1–2** matching transcripts and mark the five craft questions (opening / debt order / cast entry / meaning / dig-return).
2. Write `outputs/script.md` against the three hard gates — story continuity first; names enter via résumé/goal/status, not teaching deconstruction.
3. Run:
   - `python scripts/validate_research_lite.py --project ...`
   - `python scripts/validate_vo_craft.py --project ...` (flags teaching-deconstruction anti-patterns)
4. Continue to beat planning unless the user asked for research/script only.

Research checklist (skeleton, not style):

- [ ] Source cards exist (or Sources section folded into script)
- [ ] Genealogy exists (file or folded); stranger can retell tip → upstream → jam → takeaway
- [ ] dig_worthy marked (at most 1–2 seams) or explicitly skipped with reason
- [ ] viewer_harvest stated for VO (plain sentence; no type taxonomy required)
- [ ] Claims either sourced, uncertain, or removed
- [ ] Lead cast/companies have enough identity bits for story entry (or marked unknown)
- [ ] VO craft checked via narrative-depth-copy Kill Checklist + `validate_vo_craft.py`
- [ ] Visual proof types tagged when entering beat planning (not a VO blocker)
