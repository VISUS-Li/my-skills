# Research and Fact Check

## Source Cards

Write one JSON object per line in `research/source_cards.jsonl`:

```json
{"id":"S001","type":"official_doc","title":"...","url":"...","published_at":"YYYY-MM-DD","key_points":["..."],"reliability":"high","rights":"reference-only"}
```

Recommended fields:

- `id`: stable ID such as `S001`.
- `type`: official_doc, paper, news, blog, video, podcast, social, dataset, user_file.
- `title`, `url`, `author`, `published_at`, `accessed_at`.
- `key_points`: concise facts or ideas extracted.
- `reliability`: high, medium, low, unknown.
- `rights`: original, licensed, public-domain, fair-use-risk, reference-only, unknown.

## Claim Ledger

Write `research/claim_ledger.csv` with columns:

```csv
claim_id,claim,source_ids,risk,needs_manual_check,video_location
C001,"...","S001;S003",low,false,"segment 002 voiceover"
```

Rules:

- Every non-obvious factual claim in the voiceover must map to at least one source ID.
- Claims about current events, laws, prices, product features, public figures, statistics, or tool capabilities need high-quality, recent sources.
- Social posts and forum comments can show community sentiment but should not be sole support for factual claims.
- Do not use third-party video/audio/images in final assets unless rights status is explicitly acceptable.

## Research Brief

`research/research_brief.md` should include:

1. Topic and angle.
2. Audience and why they care now.
3. Key facts with source IDs.
4. Open uncertainties.
5. High-risk claims.
6. Visualizable dimensions: comparisons, numbers, timelines, workflows, maps, diagrams.
7. What not to say.
