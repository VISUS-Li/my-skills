# Fact-Linked Script System

Use this for news, AI industry analysis, company/product claims, public policy, biographies, rankings, timelines, controversy videos, or any factual explainer.

## Principle

A good video can be口语化、有观点、有戏剧性, but facts cannot be guessed, softened, exaggerated, or misread. Treat every source as evidence with a boundary.

The common failure to avoid: the source says “suspend all access for any foreign national,” but the script says “suspend access for everyone.” This is not a citation problem; it is an interpretation problem. Prevent it by storing what the source literally supports and what it does **not** support.

## Required files

- `research/source_cards.jsonl`: one JSON object per source.
- `research/claim_ledger.csv`: one row per factual claim used or considered.
- `research/factcheck_report.md`: generated/edited review report.
- `script/voiceover.md`: final script with inline claim IDs next to factual sentences.

## Source card schema

Each JSONL line should include:

```json
{"source_id":"S001","title":"","url":"","publisher":"","author":"","published_at":"","retrieved_at":"","source_type":"article/report/filing/paper/video/transcript","reliability":"primary/high/medium/low","key_points":[""],"important_quotes":[{"quote":"short exact quote","supports_claim_ids":["C001"]}],"limits":"what this source does not prove"}
```

## Claim ledger columns

Use at least:

```csv
claim_id,claim,claim_type,source_ids,source_urls,supporting_quote,source_context,interpretation_guardrail,script_sentence,reference_link_text,video_location,risk,verification_status,needs_manual_check,misread_check,notes
```

Definitions:

- `claim`: the precise factual proposition.
- `claim_type`: use `fact` for events/stats; use `relationship` for verified links between entities (cause, incentive, escalation); use `analysis` for `[OPINION]` lines.
- `supporting_quote`: short quote or exact paraphrase from source. Keep it narrow.
- `source_context`: who/what/when/where the source is about.
- `interpretation_guardrail`: what must **not** be inferred from the source.
- `script_sentence`: the actual spoken line or on-screen claim.
- `reference_link_text`: the link/citation text the viewer/editor can use to verify.
- `verification_status`: `verified`, `provisional`, `needs_manual_check`, or `rejected`.
- `misread_check`: explicitly answer: “Could this be overstated, generalized, or inverted?”

## Script citation style

In `script/voiceover.md`, factual lines should carry claim IDs:

```md
但真正要命的不是“模型不会中文”，而是训练和评测链路里，中文经常被当成语义问题处理，可字形本身又是视觉问题。[C012]
```

For public publishing, include a references section that maps claim IDs to source links. Do not overload the spoken line with URLs unless the user asks for visible citations.

## Verification workflow

1. Extract source cards first. Prefer primary sources when available.
2. Create claim rows before writing the final script.
3. Write the script with `[Cxxx]` tags for factual claims.
4. Run `scripts/script_claim_lint.py <project> --fail-under 85`.
5. Manually review high-risk rows, especially legal, policy, financial, medical, safety, and company allegation claims.
6. Only then compile beats.

## Interpretation rules

- Do not convert a scoped claim into a universal claim.
- Do not turn a proposal, allegation, estimate, rumor, or opinion into fact.
- Do not erase qualifiers such as “foreign national,” “according to,” “reported,” “draft,” “as of,” “inside or outside,” or “including.”
- Do not merge two sources into a stronger conclusion unless the inference is labeled as analysis.
- When the script adds an opinion, separate it from the source-backed claim: “我的判断是...” / “这更像是...”.
- For timelines, include dates and avoid implying sequence if dates are unclear.
- If evidence conflicts, show the conflict rather than forcing one clean story.
