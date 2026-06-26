# Tool Routing for AI Explainers

Use this routing for Chinese AI/science explainer videos with many labels, diagrams, captions, and educational motion graphics.

## Primary route

1. Use Remotion, Motion Canvas, HyperFrames, SVG/Canvas, or Manim for the final information layer. These tools keep labels, arrows, diagrams, timing, and captions controllable.
2. Use GPT Image models or other image generators only for visual plates that do not need exact readable text.
3. Use FFmpeg for deterministic assembly, overlays, captions, audio normalization, and social exports.
4. Use ASR such as Whisper or provider speech-to-text to align captions and diagnose pacing.
5. Use TTS or human recording for narration. For Chinese explainers, require pronunciation review of model names, English acronyms, and Chinese technical terms.

## When to use each tool family

- **Remotion**: React/video component system, reusable templates, captions, data-driven batches, social exports.
- **Motion Canvas**: TypeScript vector animation synchronized with voiceover; strong for educational diagrams and code-like motion.
- **Manim**: procedural math/science animations, formulas, geometry, and precise visual transformations.
- **Lottie/Rive/GSAP**: reusable micro-animations, icons, loaders, mascot reactions, confetti, success/fail loops.
- **CapCut/Jianying**: finishing captions, manual rhythm pass, platform-native templates, quick social publishing.
- **Pika/Luma/Kling/Runway/Veo/Seedance/Sora-like video generators**: illustrative B-roll, texture shots, thumbnails, or short cinematic inserts; avoid final text-heavy frames.
- **ElevenLabs/OpenAI/edge-tts/Piper**: narration and alternate voice tests; keep rights and disclosure notes.

## Routing decision

- If the frame contains exact Chinese text, route to code/editor text layers.
- If the frame contains a diagram that must explain logic, route to Remotion/Motion Canvas/Manim/HyperFrames.
- If the frame is mainly mood, metaphor, background, or illustrative B-roll, route to image/video generation.
- If timing must hit narration precisely, route to a programmatic timeline and cue sheet rather than one-shot video generation.

## Avoid

- One-shot text-to-video for dense explainers.
- Prompting an image model to draw long Chinese labels.
- Making each scene in a different app/style without a shared token system.
- Using platform editor audio/SFX without recording rights when final exports will be reused outside that platform.
