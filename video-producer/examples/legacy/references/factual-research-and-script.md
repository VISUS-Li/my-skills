# Factual Research And Script

> **DO NOT LOAD for new projects.** Superseded by `references/deep-research-and-script.md`
> (artifact tiers) and `references/narrative-depth-copy.md` (VO gates). Kept for archive only.

Use this for news, finance, technology, social issues, public incidents, science, policy, and documentary-style narration.

## Research Lock

Create:

- `research/source_cards.jsonl`: one source per line with URL, title, date, publisher, type, summary, and usable visual material.
- `research/claim_ledger.csv`: claim ID, claim, source IDs, support quote/context, interpretation guardrail, verification status, risk.
- `research/factcheck_report.md`: what is solid, uncertain, disputed, outdated, or cut.

Do not invent causal links. If evidence is weak, say the uncertainty, frame it as a question, or remove it.

## Script Shape

A mature factual video usually moves through some of these functions:

- hook: the social emotion or contradiction.
- event/site: what happened and where the viewer should mentally stand.
- proof: source screenshots, documents, app pages, public statements.
- mechanism: how the system works or why the consequence follows.
- data/scale: prices, proportions, timeline, market size, trend.
- human impact: how it lands on consumers, workers, families, drivers, patients, users.
- counterpoint/clarification: official response, limitation, uncertainty.
- viewpoint: what judgment or question remains.

Do not force all of them. Use only what the topic needs.

## Voiceover Rules

- Write spoken Chinese, not report prose.
- Put unfamiliar names/numbers in short clauses.
- Attach claim IDs to factual lines in `voiceover.md`.
- Give dense evidence beats enough time and pauses.
- Keep viewpoint lines clear and emotionally honest.

## Source-To-Visual Rules

- Source claims should appear before or with the line that uses them.
- Official pages, app UI, public tables, product pages, and comments need source labels.
- Do not overstate what a screenshot proves. The crop may show wording; the narration must not infer beyond it.
- Current prices, specs, public roles, laws, or breaking news must be verified at production time.
