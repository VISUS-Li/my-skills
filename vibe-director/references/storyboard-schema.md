# Storyboard Schema

Create `storyboard.json` as the shared contract between director planning, implementation, preview, and QA.

## Schema

```json
{
  "video": {
    "title": "",
    "platform": "douyin | bilibili | x | youtube | other",
    "aspectRatio": "9:16 | 16:9 | 1:1 | 4:5",
    "resolution": "1080x1920",
    "fps": 30,
    "targetDurationSec": 60,
    "stylePreset": "zheda-cat-git-motion | ai-chapingjun-system-explainer | custom",
    "sourceMode": "topic | script | article | srt | notes | existing-storyboard"
  },
  "sections": [
    {
      "id": "sec_01",
      "role": "hook | setup | explanation | contrast | proof | conclusion",
      "narrativeGoal": "",
      "durationSec": 8
    }
  ],
  "scenes": [
    {
      "id": "s001",
      "sectionId": "sec_01",
      "startSec": 0,
      "durationSec": 3.2,
      "narration": "",
      "onScreenText": "",
      "visualMetaphor": "",
      "shotType": "kinetic-title | chat | terminal | diagram | ui-mockup | graph | timeline | comparison | dashboard | caption-focus | code-demo | data-viz",
      "renderer": "hyperframes | remotion | vibe-motion | custom",
      "effectCandidates": [],
      "assetsNeeded": [],
      "sfxCues": [],
      "status": "draft | planned | generated | reviewed | approved | rejected",
      "previewPath": "",
      "notes": ""
    }
  ]
}
```

## Rules

- Every scene must have `visualMetaphor`.
- Every scene must have `renderer`.
- Every scene must have `effectCandidates`; when empty, `notes` must explain why no existing effect fits.
- Every narration sentence must map to visible action.
- Do not allow "captions plus static background" unless it is an extremely short punchline.
- Scene ids must be unique and stable after review begins.
- `startSec + durationSec` should align with adjacent scenes unless the renderer uses its own timeline.
- `status` should move through `draft`, `planned`, `generated`, `reviewed`, and `approved`, or `rejected` when a scene must be redesigned.
- Keep `storyboard.json` synchronized with each `scene_spec.json`.

## Shotlist Columns

For `shotlist.md`, include:

```text
scene | time | narration | visual metaphor | shot type | renderer | effects | assets | review notes
```
