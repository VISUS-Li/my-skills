# QA Checklist

Use this checklist before approving a scene preview, full preview, or final render.

## Scene Fail Conditions

A scene fails if:

- A narration sentence has no visual action.
- More than 1.5 seconds pass with no visible motion or meaningful state change.
- On-screen text simply repeats narration without adding structure.
- A static paragraph is the main visual.
- Captions cover the main object.
- Scene duration differs from spec by more than 10 percent.
- Custom code is used while a suitable existing effect or component exists.
- The visual metaphor is unclear.
- The shot does not connect to previous or next shot.
- Text is unreadable on mobile.
- UI labels overlap or overflow.
- The scene feels like a PPT slide instead of time-based motion.

## Whole-Video Checks

The full video must pass:

- Hook appears within the first 2 seconds.
- Each section has a visual motif.
- Motion density is consistent with the style preset.
- No long static slides.
- Captions are readable on mobile.
- SFX cues are declared even if not implemented.
- Renderer choices are justified.
- All previews have contact sheets or equivalent visual review artifacts.
- `storyboard.json` and scene specs stay synchronized.
- `preview.mp4` exists before `final.mp4`.
- Abrupt transitions are intentional and described.
- Asset rights are clear for screenshots, logos, and UI captures.

## Self-Eval Output

For each QA pass, write:

```text
PASS/FAIL:
Failed checks:
Evidence:
Fix plan:
Rerender required:
```
