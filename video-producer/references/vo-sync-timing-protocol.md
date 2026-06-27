# VO Sync & Timing Protocol

**Golden rule for Chinese explainers:** plan at **5 汉字/秒**; **lock composition to measured WAV**, not spreadsheet guesses.

## Planning vs execution

| Stage | Timing source | Rule |
|---|---|---|
| Script draft | char count ÷ 5 | `duration_sec = char_count / 5` |
| narration_beats.csv | planned start/end | 4–6 cps band; flag outliers |
| IndexTTS2 output | **ffprobe per beat** | authoritative for render |
| HyperFrames clips | `vo_timing.json` | one clip per beat, exact duration |
| micro-events | scaled from beat_timeline | map planned → actual VO |

## Forbidden

- ❌ Splitting a segment into N equal clips (e.g. 43s ÷ 7 shots ≈ 6s each)
- ❌ Using `storyboard.json` `duration_sec` without VO measurement
- ❌ Static card visible > **1.5s** with no motion (see density rules)
- ❌ One GSAP tween per 6s clip (fade only)

## Required commands (per segment)

```bash
# After indextts2_generate.py for segment beats
python scripts/measure_segment_vo.py <project> S001
python scripts/build_micro_timing.py <project> S001
python scripts/segment_timing_lint.py <project> S001
```

Outputs:

- `segments/S001/vo_timing.json` — actual start/duration/cps per beat
- `segments/S001/micro_timing.json` — micro-event times aligned to VO
- `segments/S001/s001_vo.wav` — concat of beat WAVs for embedded audio

## HyperFrames duration contract

```html
<div data-composition-id="S001" data-duration="40.763" data-start="0" ...>
<audio id="s001-vo" src="s001_vo.wav" data-start="0"></audio>
<section id="B001" data-start="0" data-duration="4.527" data-track-index="1">
```

- Root `data-duration` = `vo_timing.total_sec`
- Each beat clip: `data-start` / `data-duration` from `vo_timing.beats[]`
- Leave **1ms gap** between adjacent clips on same track to avoid lint overlap

## Micro-event scaling formula

For each event in `beat_timeline.json` with parent beat `B00x`:

```
rel = (event.start_sec - beat_planned_start) / beat_planned_duration
actual_t = beat_actual_start + rel * beat_actual_duration
```

Implement in `scripts/build_micro_timing.py`.

## CPS QC bands

| Metric | Accept | Review | Fail |
|---|---|---|---|
| beat cps | 4.0–6.5 | 3.5–4.0 or 6.5–7.5 | <3.5 or >7.5 |
| clip vs VO drift | ≤0.05s | ≤0.2s | >0.2s |
| segment total | VO ±0.1s | VO ±0.5s | >0.5s |

## Caption sync

- Bottom pill updates **every beat** (not every segment)
- Optional: word-level later via Whisper align — not required if beat-level is tight

## Rebuild cascade

If VO regenerated → rerun measure → micro_timing → regenerate segment HTML → re-render.

Do not patch render only.
