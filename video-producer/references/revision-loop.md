# Revision Loop

Treat feedback as an instruction to revise the earliest useful artifact, not as a reason to regenerate everything.

## Feedback Mapping

| Feedback | Earliest artifact to revise | Downstream impact |
|---|---|---|
| 观点不对 | `script/creative_brief.md` or `research/research_brief.md` | script, storyboard, shotlist, segments |
| 事实不确定 | `research/claim_ledger.csv` | script lines with claims, captions |
| 口播不像我 | `script/voiceover.md` | storyboard timings, captions, audio |
| 太空洞 / 内容太少 | `script/outline.md` + `script/storyboard.json` | shotlist, assets, segments |
| 分镜像PPT | `script/storyboard.json` + `script/shotlist.json` | visual segments, transitions |
| 色彩不好看 | `design/art_direction.md` + `design/tokens.json` | all visual segments, cover |
| 图标图片太少 | `assets/asset_manifest.csv` + `design/visual_moodboard.json` | affected segments, rights QC |
| 运镜/镜头语言弱 | `script/shotlist.json` | segments, assembly rhythm |
| 动效无聊 | segment `.hyperframes/expanded-prompt.md` | affected segment render |
| 第3段不好 | `segments/003_*/` or its shotlist entries | timeline and final export only |
| 节奏拖沓 | `script/storyboard.json` and `edit/timeline.json` | affected segments and captions |
| 标题封面弱 | `exports/publish_pack.md` and cover brief | no video rebuild unless cover/title style affects visuals |

## Revision Procedure

1. Quote or summarize the feedback.
2. Classify it: content, art direction, palette, typography, layout, shot language, motion, assets, edit rhythm, rights.
3. Identify the smallest upstream artifact to change.
4. Create a versioned draft.
5. Mark impacted stages `needs-revision`.
6. Revise only the impacted artifacts.
7. Run `scripts/validate_project.py`.
8. For visual changes, run `scripts/aesthetic_score.py --fail-under 72`.
9. Present a before/after summary and ask for review only at the relevant checkpoint.

## Version Naming

Use sequential versions, never vague names:

- `voiceover.v002.md`
- `storyboard.v003.json`
- `shotlist.v002.json`
- `art_direction.v002.md`
- `design.v002.md`
- `segments/003_tool_matrix/v002/render.mp4`
