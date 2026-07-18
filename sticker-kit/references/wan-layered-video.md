# Wan layered-video production

Use this reference for motion jobs when the Wan I2V/FLF2V endpoint is available.
The production unit is **one isolated element × one state segment × one fixed
camera**, not one whole scene and not one generated frame.

## Pipeline

```text
story beats
  → shots and interaction contracts
  → element registry and state timeline
  → endpoint images for each state
  → compile Wan jobs
  → I2V / FLF2V isolated clips
  → chroma/luma matte to stable RGBA sequences
  → deterministic global transforms, z-order, and timing
  → composite MP4 + QA report
```

## Plan before generating

Write `scene_plan.json` with:

1. `project`: duration, FPS, output canvas, style lock, Wan defaults.
2. `shots`: shot-local timeline, one camera rule, background, elements.
3. `elements`: stable identity, z-order, pivot, matte, states.
4. `states`: start/end time, I2V/FLF2V/static mode, endpoint images, local
   motion, playback, and scene transform.
5. `interaction_contracts`: shared event time, participants, contact rule.

Keep **local motion** and **global motion** separate:

- Wan: limb motion, breathing, wing flap, slash arc, facial reaction.
- Compositor: moving across the scene, scale, screen position, z-order, timing.

Tell every Wan actor job: fixed camera, subject centered, no zoom/pan/rotation,
stable scale, no ground or scene. If the model moves both the subject and camera,
the layer cannot be placed reliably.

## Element boundaries

Split by independent motion and occlusion, not by noun alone.

| Situation | Layer decision |
|---|---|
| Warrior holding sword | One `warrior_sword` actor group |
| Dragon body and fire | Separate `dragon` and `dragon_fire` layers |
| Warrior slashes dragon | Separate actors + shared impact time + impact VFX |
| Warrior hugs/carries princess | One temporary `warrior_princess_pair` contact group |
| Castle/hills | Static background plate |
| Trees/clouds/flags | Optional isolated environment loops |

Held props belong to the actor; otherwise attachment drift is likely. Short
contacts can remain separate if an impact flash hides the exact intersection.
Sustained contact, intertwined limbs, carrying, wrestling, or hugging must use a
combined contact group for that state segment.

Do not animate everything. Allocate Wan jobs to foreground actors, expressive
props, atmospheric loops, and VFX. Keep distant geometry static unless its motion
is visible at delivery size.

## State routing

- Use **I2V** when identity and pose class remain stable: tied idle, guard idle,
  defeated breathing, flag waving, tree sway.
- Use **FLF2V** when both endpoint states matter: windup→slash, standing→fallen,
  tied→freed, day→night background transition.
- Split a segment when it contains more than one semantic verb or more than one
  major pose-class change.
- For a long action, chain several short states. Do not ask one clip to attack,
  fall, stand up, walk, and hug.

Make state boundaries visually compatible. End frame of state A should match the
start frame of state B, or use the same image at the boundary. Hide unavoidable
cuts behind impact flashes, smoke, foreground wipes, or a shot cut.

## Interaction contract

For each contact event define:

- event time in the shot;
- participants;
- screen-space contact point;
- facing/direction;
- which layer occludes which;
- reaction delay (usually 0–3 frames);
- optional VFX layer used to mask the contact.

Prompts alone cannot synchronize separately generated actors. The compositor
owns the event time. Phrase each participant prompt relative to the same segment
progress, for example “impact at 73% of the clip”.

## Matte strategy

Wan returns opaque MP4. Always create transparent intermediates after generation.

| Material | Generation background | Matte |
|---|---|---|
| Opaque actor/prop | Uniform chroma color absent from subject | Chroma to alpha |
| Fire/glow/beam | Pure black | Luminance to alpha |
| Smoke/translucent cloth | Chroma plus manual QA; segmentation fallback if needed | Soft matte |

Default chroma is `#00FF00`, but never use green behind a green subject. Choose
blue or magenta based on the locked palette. Require no floor, shadow, reflection,
text, border, or background texture. Preserve a single union crop across the
whole clip; per-frame autocrop causes position jitter.

Use RGBA PNG sequences as the source of truth. Export ProRes 4444 or another
alpha-capable delivery only when required; MP4/H.264 does not preserve alpha.

## Pixel-art guardrails

Video diffusion tends to soften pixel art. Lock the same low-color palette and
pixel grid in endpoint images, forbid anti-aliasing and motion blur, and pass
`cutout_video.py --pixel-grid N` after keying. Use integer-looking compositor
positions and nearest-neighbor resizing for final pixel delivery. Inspect the
result at 100% zoom; regenerate clips with melted outlines or changing palette.

## Commands

```bash
python scripts/init_wan_scene.py --template dragon-rescue --out OUT/dragon-rescue
# Replace placeholder endpoint images and edit scene_plan.json.
python scripts/compile_wan_scene.py OUT/dragon-rescue/scene_plan.json --strict-assets
python scripts/wan_generate.py OUT/dragon-rescue/wan_jobs.json --dry-run
python scripts/wan_generate.py OUT/dragon-rescue/wan_jobs.json

# Batch uses each planned chroma/luma mode and pixel-grid setting.
python scripts/key_wan_jobs.py OUT/dragon-rescue/wan_jobs.json

python scripts/compose_scene.py OUT/dragon-rescue/compiled_scene_plan.json \
  -o OUT/dragon-rescue/renders/final.mp4
```

Read [wan-api.md](wan-api.md) for endpoint fields.

## QA and regeneration

Check each isolated clip before composition:

- identity, colors, topology, and held-prop attachment remain stable;
- no unexpected camera or subject translation;
- start/end frames match the requested state;
- matte has no holes, green/blue spill, opaque background, or clipped motion;
- interaction action peaks at the contract time;
- loops do not pop at the boundary;
- pixel grid/palette do not shimmer.

Regenerate only the failing state. Do not rebuild the whole scene. If contact
still fails after two takes, replace that interval with a contact group or hide
the join behind a designed VFX transition.

## Dragon-rescue beat example

1. `0–3s`: warrior guards; dragon recoils; fire VFX extends; princess tied idle.
2. `3–6s`: warrior FLF slash; dragon FLF hit→defeated; impact VFX at 5.2s.
3. `6–8s`: defeated dragon loop; warrior approaches; princess tied→freed.
4. `8–12s`: swap individual warrior/princess layers for one hugging pair layer.

This is intentionally several short, controllable clips. The visible scene feels
busy because the layers overlap in time, not because one model call invents all
actions at once.
