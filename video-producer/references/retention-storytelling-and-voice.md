# Retention Storytelling and Voice

Use this when writing Chinese YouTube/Bilibili/Douyin explainer scripts that should feel like a knowledgeable storyteller rather than a textbook.

## Goal

Make the script sound like a real person explaining a fresh story with judgment, suspense, and useful inside context. Do not copy a creator's catchphrases or identity. Reference creators such as 老范讲故事、小白debug、飞天闪客 only as broad pacing/style inspiration.

## Voice defaults

- Use spoken Chinese: short clauses, natural transitions, occasional rhetorical questions.
- Explain less basic textbook background; spend more time on hidden mechanisms, recent dynamics, incentives, conflict, and “为什么现在才爆出来”.
- Add viewpoints, but mark them as analysis, not fact.
- Prefer story verbs: “卡住了、翻车了、绕开了、突然收紧、被迫换路、这才是关键”.
- Avoid corporate tone: “本文将介绍、我们可以看到、从以下几个方面”.
- Avoid **speculative oral fillers** that sound like guesswork: 你想啊、其实吧、我跟你说、这就有意思了. Use **evidence anchors** instead: 原文里、把时间线往回看、公告第X条、很多人只看标题但条款写的是…

For **any scriptwriting** (one event or many), load `references/deep-narrative-investigation.md` automatically — single-story arcs (前尘/秘辛/后果) and multi-point weaving. Oral 口水话 rules are in that reference.

## Hook patterns

Choose one, then make it visual in the first 3 seconds:

1. **Failure hook**: show a broken output or absurd contradiction.
2. **Stakes hook**: “这不是一个小 bug，它可能改变...”
3. **Inside-context hook**: “很多人只看到表面，其实真正的转折点是...”
4. **Misread correction**: “网上很多说法漏掉了一个限定词...”
5. **Timeline shock**: show a fast timeline that suddenly splits.

## Story spine

A strong factual explainer often follows:

1. Hook: one concrete failure, conflict, or surprising claim.
2. Setup: what viewers already think happened.
3. Twist: what is actually more complicated.
4. Proof: source-backed evidence and a visual document/source card.
5. Mechanism: turn the hidden system into a visible machine/diagram.
6. Stakes: why this matters now, especially for Chinese-speaking viewers when relevant.
7. Nuance: what the evidence does **not** prove.
8. Takeaway: one memorable summary, not a bland conclusion.

## Source-backed drama

Drama must come from structure, not fabrication:

- Put the strongest verified detail early.
- Use “限制词” as suspense: “注意，这里它说的不是所有人，而是...”
- Let documents appear on screen as evidence cards, with highlighted clauses.
- If a source is ambiguous, make ambiguity part of the story.

## Story continuity (not news copy)

- **Dwell before jump:** each turn needs mechanism + landing — what it means for the arc — before the next beat.
- **Carry forward:** end a beat with a hook the next beat picks up (“带着这个限定词…”).
- **Callbacks:** reference earlier details so the script feels like one thread tightening.
- **Avoid:** 据悉/据报道/此外/另外/与此同时 as beat openers; fact stacks without so-what.

## Script formatting

For `script/voiceover.md`:

- Mark factual claim IDs inline: `[C001]`.
- Mark opinion lines with `[OPINION]` when they may sound factual.
- Mark visual opportunities with HTML comments when useful: `<!-- VISUAL: red stamp on wrong interpretation -->`.
- Keep paragraphs short: 1-3 spoken sentences.
- Add a references section at the end for editor checking.

## Anti-patterns

- Long definitions before the hook.
- Perfectly neutral but boring encyclopedia paragraphs.
- Source links at the end only, with no claim-to-source mapping.
- Over-explaining basic AI concepts while skipping the new controversy/current state.
- Copying a creator's branded opening, sign-off, or catchphrases.
