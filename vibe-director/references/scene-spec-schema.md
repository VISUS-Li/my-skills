# Scene Spec Schema

Create one `scene_spec.json` for each scene before writing scene code.

## Schema

```json
{
  "sceneId": "s001",
  "goal": "",
  "narration": {
    "text": "",
    "emphasisWords": []
  },
  "visual": {
    "metaphor": "",
    "layout": "",
    "background": "",
    "mainObjects": [],
    "secondaryObjects": [],
    "captionStyle": ""
  },
  "motionBeats": [
    {
      "time": "0.0-0.5",
      "action": "",
      "effect": "",
      "sfx": ""
    }
  ],
  "implementation": {
    "renderer": "hyperframes | remotion | vibe-motion | custom",
    "preferredSkills": [],
    "fallback": ""
  },
  "qa": {
    "visualChangeEverySecond": true,
    "narrationMappedToVisual": true,
    "notSlideLike": true,
    "captionReadable": true
  }
}
```

## Rules

- `motionBeats` must cover the whole scene duration with no long unplanned gap.
- Add a visible change every 1 to 1.5 seconds.
- Identify how emphasis words are visually highlighted: spotlight, scale, color, underline, cursor, graph node, UI state, or camera move.
- Include SFX cues even if audio is not implemented in v1.
- Include renderer and fallback. Example: "HyperFrames primary; Remotion fallback if the scene needs shared timeline state."
- `captionStyle` must mention placement, size, contrast, and collision avoidance.
- `mainObjects` should be concrete visual objects, not abstract topics.
- If custom code is chosen, explain why registry effects or component banks are insufficient.
