# Review Studio

Review Studio is the human/agent review surface for Video Producer. It uses the same `outputs/` contract everywhere — static bundle and full local app both read `outputs/beat_plan.json`.

## Static Review

From a video project directory:

```bash
python <skill>/scripts/score_preview_plan.py --outputs outputs
python <skill>/scripts/build_review_bundle.py --outputs outputs
```

Open:

```text
outputs/review/review-studio/index.html
```

## Full Local App

For interactive beat editing, TTS generation, and timeline inspection:

```bash
pip install -r review-studio/requirements.txt
python review-studio/server/main.py --project D:\videos\my-project --port 8787
```

Open [http://127.0.0.1:8787](http://127.0.0.1:8787).

## Data Contract

| File | Role |
|------|------|
| `outputs/beat_plan.json` | **SSOT** — voice_text, keyword, visual_owner, visual_action |
| `outputs/segment_spec.json` | Shots, visual_actions, renderer delegation |
| `outputs/script.md` | Long-form script; voice block synced on beat edit |
| `segments/{seg}/vo_timing.json` | Measured TTS durations (runtime) |
| `audio/stems/voice/beats/{beat_id}.wav` | TTS stems |
| `outputs/review/preview.mp4` | First-slice preview |

Beat reads/writes are centralized in `scripts/beat_store.py`. There is no legacy `script/narration_beats.csv` path.

## Agent Rule

Generate and edit `outputs/beat_plan.json` directly. Run `build_review_bundle.py` after plan changes. Use the full app when the user needs TTS or live beat editing.
