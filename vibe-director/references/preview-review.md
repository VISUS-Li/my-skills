# Preview Review

Use checkpoints to keep video work reviewable and iterative.

## Checkpoint 1: Script And Structure

Artifacts:

- `script.md`
- `section_plan.md`

Review:

- Hook within 2 seconds.
- Clear promise.
- Sections have narrative roles.
- Chinese narration is concrete and speakable.

## Checkpoint 2: Storyboard

Artifacts:

- `storyboard.json`
- `shotlist.md`
- Optional HTML storyboard preview.

Review:

- Each scene has visual metaphor, shot type, renderer, effect candidates, and duration.
- Every sentence maps to visible action.
- The renderer mix is sensible.

## Checkpoint 3: Single Scene

Artifacts:

- Scene preview.
- `contact-sheet.jpg`.
- `scene_spec.json`.
- If voiced: beat WAVs, `segments/<SEGMENT>/vo_timing.json`, and timing notes.
- `qa.md`.

Review:

- Motion beats match narration.
- Captions are readable and do not cover the main object.
- Visual metaphor is clear.
- Preview duration is within 10 percent of spec.
- If voiced, animation timing follows measured voiceover rather than planned text duration.

## Checkpoint 4: Whole Video

Artifacts:

- `preview.mp4`.
- `verify/montage.jpg`.
- `verify/qa_report.md`.

Review:

- Section motifs work together.
- Motion density is consistent.
- Transitions are intentional.
- No scene feels like a filler slide.

## Rules

- Default: do not go directly to final render.
- If the user requests a fast automated run, still create storyboard and QA artifacts.
- For important videos, ask the user to review storyboard before implementing all scenes.
- Use ask, confirm, execute, self-evaluate, persist.
