# Douyin AI Explainer Style Recipe

Use this recipe for Chinese AI/science explainer videos similar to a clean Douyin/Bilibili educational infographic: light background, cartoon-tech diagrams, subtitle-driven narration, fast but readable motion, and many concrete visual metaphors.

## Core look

- **Canvas**: 16:9 first unless the user specifies mobile-first. Use 1280x720 or 1920x1080 at 30 fps.
- **Background**: warm off-white paper or light lab canvas with faint blue-gray perspective grid. Avoid dark premium-tech defaults.
- **Palette**: 60-70% off-white base, 15-20% dark ink/stroke, 15-20% teal/blue/green/yellow educational accents, 3-8% red warning/error accents.
- **Line style**: rounded 2-4 px strokes, soft shadows, clean vector icons, lightly hand-drawn corners. Keep every object in the same illustration family.
- **Texture**: subtle paper grain, grid, tiny particle/dot details. No heavy glow unless it marks a key reveal.
- **Typography**: modern CJK sans for all labels and captions. Use bold Chinese display text for key terms, not generated image text.
- **Captions**: bottom-center black translucent rounded subtitle pill, white text, 1-2 lines, synced to speech. Important keywords may use accent color badges above the caption, not in the subtitle itself.

## Visual primitives

Every 4-8 second scene should include at least four of these, with one as the hero:

- `hero_machine`: AI training box, diffusion machine, CLIP bridge, glyph-guidance module, model cabinet.
- `card_stack`: image examples, before/after outputs, reference cards, mini screenshots.
- `arrow_pipeline`: left-to-right or top-to-bottom process arrows with moving dots.
- `status_badge`: success/fail, error stamp, checkmark, warning triangle, “英文更稳/中文易错” label.
- `neural_graph`: node-link mini-network, embedding grid, classifier/encoder box.
- `comparison_split`: Chinese vs English, semantic vs glyph, old method vs new method.
- `mascot`: small robot/assistant character reacting, pointing, holding a sign, or closing the video.
- `texture_plate`: generated/example image, screenshot plate, document/photo card, product UI.
- `data_or_scale`: balance scale, counter, progress bar, slider, clock, queue, table.

## Motion grammar

Use motion to explain causality, not as decoration:

- `line_draw`: arrows, brackets, and boxes draw on in 0.3-0.8s.
- `card_slide`: cards slide from the direction implied by the process.
- `stamp_hit`: red error or green success badge lands with 0.12s overshoot and short SFX.
- `arrow_pulse`: tiny dots move along arrows to show information flow.
- `machine_process`: inputs enter a machine, progress lights tick, output card emerges.
- `before_after_flip`: failed sample flips or slides into corrected sample.
- `camera_push`: slow push on a key machine or module during explanation.
- `parallax_pan`: foreground labels move faster than background grid during scene transition.
- `diagram_morph`: card stack morphs into table/map/network when explaining an abstraction.
- `rhythm_break`: one clean title card or large phrase after dense diagrams.

Timing defaults: 0.18-0.35s micro interaction, 0.4-0.7s card/label entrance, 0.8-1.6s diagram build, 3-7s explanation scene, 0.2-0.5s silence/drop before a major reveal.

## Story structure for AI model explanations

A reliable structure:

1. **Hook with failure or curiosity**: show the weird output, exaggerate with a red stamp, ask the question.
2. **Visible stakes**: compare “looks right semantically” vs “glyph wrong visually.”
3. **Mental model**: convert the hidden model process into a machine/pipeline.
4. **Mechanism 1**: training/data or representation shown as cards entering a machine.
5. **Mechanism 2**: why Chinese is harder; show glyph density, data imbalance, token/glyph mismatch.
6. **Solution path**: text rendering, glyph guidance, improved model, prompt/composition method.
7. **Takeaway**: summarize with a clean checklist and mascot CTA.

## Chinese text safety

Readable Chinese must be final-rendered as text layers:

- Use HTML/SVG/Canvas/Remotion/Motion Canvas text components with CJK fonts.
- Keep important Chinese labels short: 2-8 characters for badges; 8-16 characters for titles; 1-2 subtitle lines.
- Never ask an image/video model to generate exact Chinese captions, UI labels, subtitles, or diagram labels. Generate the illustration without text, then overlay text.
- For screenshots/examples that must demonstrate wrong Chinese, render the wrong glyphs deliberately as text or import the real reference image with rights noted.
- In prompts for image generation, include “no readable text, blank labels/signs, clean spaces reserved for later Chinese text overlay.”

## Audio style

- Narration is the anchor: fast, clear, friendly, slightly amused, not corporate.
- Music bed: light tech/pop pulse around 105-125 BPM, low enough to duck under voice.
- SFX: tiny UI clicks, data ticks, machine beeps, soft whooshes, red stamp hits, success chimes. Anchor every cue to a visible event.
- Mix target for social: around -14 to -16 LUFS integrated, true peak below -1 dBTP for safer export; platform-native uploads may be hotter but avoid clipping.
- Use short silence/reduced bed before the biggest “aha” or punchline.

## Anti-patterns

- Dark glassmorphism/premium SaaS look for this reference style.
- Full-screen paragraphs or centered PPT cards.
- Random icon sets, random colors, or one-off AI images that do not match the vector universe.
- Chinese text baked into generated images.
- Transitions with no semantic reason.
- BGM only with no UI/SFX rhythm.
