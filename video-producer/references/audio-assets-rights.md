# Audio Assets and Rights

Use this when sourcing SFX, music, ambience, loops, or voice assets.

## Safe sourcing order
1. User-owned audio or recorded foley.
2. Generated audio with clear usable rights for the target platform.
3. YouTube Audio Library for YouTube-targeted videos, checking attribution and license type.
4. Pixabay / Mixkit / Adobe Audition SFX, checking current license terms.
5. Freesound CC0 or CC-BY only, with attribution recorded when required.
6. Paid libraries such as Epidemic Sound, Artlist, Soundstripe, Envato Elements, or ALIBI only if the user has a valid subscription/license.
7. CapCut/剪映 built-in audio may be used inside those editors when the user confirms platform/license suitability, but do not assume those assets are reusable in an external automated pipeline.

## Required rights fields
Every selected/final audio asset must be recorded in `assets/asset_manifest.csv` and `audio/audio_rights_log.md` with:

- asset_id
- source
- path_or_url
- license
- attribution_required
- commercial_allowed
- platform_restrictions
- evidence_saved
- rights_status

## Rights statuses
Use these exact statuses:
- `self-created`
- `user-owned`
- `generated-rights-ok`
- `youtube-audio-library-ok`
- `royalty-free-ok`
- `cc0-ok`
- `cc-by-attribution-ready`
- `paid-license-ok`
- `needs-check`
- `noncommercial`
- `copyrighted-reference-only`
- `do-not-use-final`

Only `*-ok`, `self-created`, `user-owned`, and `cc-by-attribution-ready` are acceptable for final renders.

## Asset naming
Use consistent file names:

```text
assets/sfx/002_transition_glitch_short_v001.wav
assets/sfx/003_data_tick_motif_v001.wav
assets/music/main_bed_120bpm_v001.wav
assets/audio/voiceover_master_v001.wav
assets/audio/ambience_office_low_v001.wav
```

## CapCut / 剪映 note
剪映/CapCut is useful as a taste reference because its template ecosystem demonstrates dense short-video audio grammar: transition hits, whooshes, trend BGM, subtitle pops, and sticker/UI sounds. For an external automated skill, treat its built-in library as **editor-bound unless the user verifies rights**. Record any exported or reused audio source explicitly.
