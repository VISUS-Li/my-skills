# `video-plan.json` runtime contract

## Contents

- [Ownership](#ownership)
- [Timing modes](#timing-modes)
- [Voice compilation](#voice-compilation)
- [Scene types](#scene-types)
- [Captions](#captions)
- [Continuous stage](#continuous-stage)
- [Asset paths](#asset-paths)
- [Validation](#validation)

## Ownership

Use `script.md` as the human-editable script and director notes. Use one
`video-plan.json` as the only runtime input to Remotion.

Keep authored and derived fields in the same plan:

- Author `voice.tracks[].beatId`, `src`, `text`, and optional gaps.
- Measure `durationSec` from real media.
- Compile `startSec`, scene boundaries, caption cues, and total duration.
- Author scene-local cues in seconds relative to their scene.

Do not make another persistent beat, scene, audio, or micro-timing file a
runtime authority. `audio/voice/timing.json` is an intermediate measurement
cache and must be compiled into the plan before rendering.

The JSON Schema is `assets/templates/video-plan.schema.json`. The Python
validator additionally checks timing ownership, references, overlaps, bounds,
and safe asset paths.

## Timing modes

- `voice`: Treat measured voice tracks as absolute time. Derive scenes that
  declare `beatIds`.
- `music`: Require `musicBeats`; align authored scene times to that grid.
- `fixed`: Treat the declared video and scene durations as absolute time.

Use seconds in JSON. Convert to frames only inside Remotion using the plan FPS.

## Voice compilation

Place runtime media below `public/` and reference it without the `public/`
prefix:

```json
{
  "voice": {
    "mode": "per-beat",
    "tracks": [
      {
        "beatId": "b001",
        "src": "audio/voice/b001.wav",
        "text": "先说结论。",
        "startSec": 0,
        "durationSec": 1,
        "gapAfterSec": 0.12
      }
    ]
  }
}
```

Run:

```powershell
python scripts/measure_voice.py <project>
python scripts/compile_video_plan.py <project>
python scripts/validate_video_plan.py <project>\video-plan.json --check-assets
```

`measure_voice.py` uses `ffprobe`. It fails on missing media by default. Use
`--allow-missing` only for planning checks that intentionally retain declared
durations.

Scenes that declare `beatIds` receive their absolute start and duration from
the first and last referenced voice tracks. Optional local boundary changes
belong in `scene.timing.startOffsetSec` and `endOffsetSec`.

Set `captions.autoFromVoice` to `true` to compile one caption cue per voiced
beat when precise word timing is unavailable. Replace those cues with ASR/TTS
word timing when word highlighting matters.

## Scene types

The first template ships with:

- `HookScene`
- `TalkScene`
- `ListScene`
- `CompareScene`
- `TimelineScene`
- `BrollScene`
- `TransparentImageScene`
- `ImageSequenceScene`

Scene-specific data belongs in `scene.props`. The root plan stays permissive;
validate scene props beside the component when a scene becomes stable.

Use `BrollScene` for ordinary MP4 footage:

```json
{
  "type": "BrollScene",
  "props": {"src": "media/demo.mp4", "fit": "cover", "muted": true}
}
```

Use `TransparentImageScene` for a single transparent PNG. Use
`ImageSequenceScene` for numbered PNG frames:

```json
{
  "type": "ImageSequenceScene",
  "props": {
    "prefix": "media/sequence/frame_",
    "suffix": ".png",
    "startNumber": 0,
    "digits": 4,
    "imageFps": 30,
    "frameCount": 90
  }
}
```

## Captions

The master renders regular captions once, above every scene. Set
`captions.combineTokensWithinMs` to control page length. Use `plain` for
page-only captions or `word-highlight` with absolute word timings:

```json
{
  "captions": {
    "mode": "word-highlight",
    "combineTokensWithinMs": 1050,
    "cues": [
      {
        "startMs": 0,
        "endMs": 1200,
        "text": "一条时间线",
        "words": [
          {"text": "一条", "startMs": 0, "endMs": 520},
          {"text": "时间线", "startMs": 520, "endMs": 1200}
        ]
      }
    ]
  }
}
```

Word text is whitespace-sensitive. Include any required leading space in
English tokens. Cues without `words` remain valid and render as plain tokens;
do not invent word timing when only sentence timing is known.

## Continuous stage

Use one global `stage.subject` plus a pose schedule when the same presenter,
product, screenshot, or transparent image should survive scene cuts. A scene
opts in with `continuousSubject: true`; setting `scene.pose` also opts in and
provides a schedule keyframe at the scene start.

```json
{
  "stage": {
    "subject": {
      "type": "image",
      "src": "media/presenter.png",
      "label": "Presenter"
    }
  },
  "poses": [
    {"atSec": 0, "pose": "wide-right", "transitionSec": 0},
    {"atSec": 2.8, "pose": "close-left", "transitionSec": 0.55}
  ]
}
```

Built-in poses are `full`, `center`, `close-left`, `close-right`, `wide-left`,
`wide-right`, `card-left`, `card-right`, `offscreen-left`, and
`offscreen-right`. Explicit `poses` override same-time scene-derived poses.
The stage is a global master layer, so adjacent opted-in scenes keep one
continuous subject while scene-local animation still uses local `Sequence`
time.

Add project-specific numeric poses under `stage.poses` instead of changing the
Stage renderer. All values remain frame-interpolated:

```json
{
  "stage": {
    "subject": {
      "type": "video",
      "proxySrc": "media/speaker-720p.mp4",
      "masterSrc": "media/speaker-master.mp4",
      "objectPosition": "50% 42%",
      "audioMode": "muted"
    },
    "poses": {
      "evidence-right": {
        "scale": 1.08,
        "insetT": 12,
        "insetR": 4,
        "insetB": 12,
        "insetL": 54,
        "radius": 28,
        "border": 1,
        "shadow": 1,
        "background": 1
      }
    }
  }
}
```

Studio preview selects `proxySrc`; rendering selects `masterSrc`. The subject
is muted unless `audioMode` is explicitly `media`, so narration remains the
default audio owner. Subjects may also use `type: image` or `type: card`.

Override shared visual tokens under `style.tokens` (`colors`, `typography`,
`spacing`, `radius`, `shadow`, `texture`, and `motion`). Keep the bundled
`Noto Sans SC` and `Space Mono` families unless the project also bundles and
loads its replacement fonts.

## Asset paths

Keep images, video, audio, SVG, and fonts under the generated project's
`public/` directory. Store only safe relative paths in the plan. Do not use
absolute paths or `..`.

An external generator returns an asset, not a competing final timeline.
Integrate its output as a scene, effect, or asset and provide a static or
native Remotion fallback.

## Validation

Run the low-cost checks first:

```powershell
python scripts/validate_video_plan.py <project>\video-plan.json
Push-Location <project>
npm run typecheck
npm run qa:still
npm run render:preview
npm run qa:contact-sheet
Pop-Location
```

Inspect the stills, contact sheet, and preview. Render the final only after checking safe
areas, fonts, media framing, captions, end coverage, and audio balance.
