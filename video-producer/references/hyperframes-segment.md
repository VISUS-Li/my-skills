# HyperFrames Segment Protocol

Use this when producing a single HyperFrames segment.

## Required inputs

Read these before coding:

- `design/art_direction.md`
- `design/design.md`
- `design/tokens.json`
- `script/storyboard.json`
- `script/shotlist.json`
- `assets/asset_manifest.csv`

## Segment files

Create inside `segments/<id>/`:

- `brief.md`: narrative goal, voiceover, visual metaphor, key assets, review criteria.
- `styleframe.md`: final still frame composition before animation.
- `.hyperframes/expanded-prompt.md`: complete scene/timing/transition implementation prompt.
- `segment_report.md`: what was built, checks run, issues, simplifications.

## Expanded prompt contents

Include all of these:

1. Segment goal and emotional beat.
2. Final frame composition.
3. Color roles and tokens.
4. Typography hierarchy and max line counts.
5. Ratio allocation and safe area.
6. Foreground/midground/background layers.
7. Assets and rights status.
8. Camera/shot sequence and edit intent.
9. Motion timing, easing, and transitions.
10. Anti-PPT measures.
11. Validation commands to run.

## Layout-first rule

Implement static end-state first:

1. HTML semantic structure.
2. CSS tokens and final layout.
3. Layering/z-index.
4. Responsive safe area.
5. Then GSAP / timeline animations.

## Richness patterns

Instead of a card + bullets, choose:

- animated diagram with icons and connectors.
- split-screen contrast with two visual worlds.
- data chart build with final insight badge.
- product hero with orbiting feature callouts.
- scroll/timeline with depth layers.
- UI screenshot with masked callouts.
- particle/logo reveal.

## Checks

Run every available check in the environment:

- HyperFrames lint.
- HyperFrames validate.
- HyperFrames inspect.
- Browser preview.
- Render.

If any check fails, fix before finalizing. If preview is visually weak, revise `styleframe.md` or shotlist before adding more animation.
