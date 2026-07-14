#!/usr/bin/env python3
"""Build a lightweight static Review Studio bundle from outputs/ contract."""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from beat_store import (  # noqa: E402
    build_micro_timing_from_spec,
    char_count,
    default_segment,
    duration_from_time,
    load_beat_plan,
    load_segment_spec,
    vo_timing_path,
)


def load_text(path: Path, default: str = "") -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else default


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require_inputs(outputs: Path, *, allow_incomplete: bool) -> list[str]:
    missing = [
        rel
        for rel in ("script.md", "beat_plan.json", "segment_spec.json")
        if not (outputs / rel).exists()
    ]
    if allow_incomplete:
        return missing
    return missing


def rel_from(child: Path, parent: Path) -> str:
    try:
        return child.resolve().relative_to(parent.resolve()).as_posix()
    except ValueError:
        return child.as_posix()


def project_root_from_outputs(outputs: Path) -> Path:
    return outputs.parent if outputs.name.lower() == "outputs" else outputs


def sync_runtime_artifacts(project: Path) -> None:
    """Ensure segments/{seg}/vo_timing.json and micro_timing.json exist from beat_plan."""
    seg = default_segment(project)
    beat_plan = load_beat_plan(project)
    spec = load_segment_spec(project)
    vo_beats = []
    total = 0.0
    for beat in beat_plan.get("beats", []):
        if not isinstance(beat, dict):
            continue
        bid = str(beat.get("beat_id") or "")
        t = beat.get("time") or [0, 0]
        start = float(t[0]) if isinstance(t, list) and len(t) >= 1 else 0.0
        dur = duration_from_time(t)
        text = str(beat.get("voice_text") or "")
        vo_beats.append({
            "beat_id": bid,
            "start_sec": round(start, 3),
            "end_sec": round(start + dur, 3),
            "duration_sec": dur,
            "planned_sec": dur,
            "char_count": char_count(text),
            "cps": round(char_count(text) / dur, 2) if dur else 0,
            "source": "beat_plan",
            "locked": False,
        })
        total += dur
    vo_path = vo_timing_path(project, seg)
    if not vo_path.exists():
        vo_path.parent.mkdir(parents=True, exist_ok=True)
        vo_path.write_text(json.dumps({
            "segment_id": seg,
            "total_sec": round(total, 3) or spec.get("duration") or 0,
            "beats": vo_beats,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    micro_path = project / "segments" / seg / "micro_timing.json"
    if not micro_path.exists():
        events = build_micro_timing_from_spec(project, seg)
        micro_path.parent.mkdir(parents=True, exist_ok=True)
        micro_path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    root = args.outputs
    missing = require_inputs(root, allow_incomplete=args.allow_incomplete)
    if missing and not args.allow_incomplete:
        print("ERROR: incomplete review project.")
        for rel in missing:
            print(f"- missing outputs/{rel}")
        return 2

    review = root / "review"
    studio = review / "review-studio"
    studio.mkdir(parents=True, exist_ok=True)

    bundle = {
        "script": load_text(root / "script.md"),
        "beat_plan": load_json(root / "beat_plan.json", {}),
        "segment_spec": load_json(root / "segment_spec.json", {}),
        "audio_cue_sheet": load_json(root / "audio_cue_sheet.json", {}),
        "metrics": load_json(review / "metrics.json", {}),
        "failed_checks": load_text(review / "failed_checks.md"),
        "execution_trace": load_json(review / "execution_trace.json", {"slots": []}),
        "media": {
            "preview": rel_from(review / "preview.mp4", studio) if (review / "preview.mp4").exists() else "",
            "contact_sheet": rel_from(review / "contact_sheet.jpg", studio) if (review / "contact_sheet.jpg").exists() else "",
        },
    }
    (studio / "review_bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    title = html.escape(str(bundle["segment_spec"].get("segment_id") or bundle["beat_plan"].get("title") or "Video Review"))
    index = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} Review Studio</title>
  <style>
    body {{ margin: 0; font-family: Arial, "Microsoft YaHei", sans-serif; background: #101114; color: #f4f4f1; }}
    header {{ padding: 18px 24px; border-bottom: 1px solid #2a2d34; display: flex; gap: 16px; align-items: baseline; }}
    h1 {{ font-size: 20px; margin: 0; }}
    main {{ display: grid; grid-template-columns: minmax(360px, 1.2fr) minmax(320px, .8fr); gap: 18px; padding: 18px; }}
    section {{ background: #17191f; border: 1px solid #2a2d34; border-radius: 8px; padding: 14px; }}
    h2 {{ font-size: 14px; margin: 0 0 12px; color: #9fd8ff; }}
    video, img {{ width: 100%; border-radius: 6px; background: #06070a; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #0c0d11; padding: 10px; border-radius: 6px; max-height: 360px; overflow: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    td, th {{ border-bottom: 1px solid #2a2d34; padding: 7px 6px; text-align: left; vertical-align: top; }}
    .score {{ font-size: 38px; font-weight: 700; }}
    .ok {{ color: #7ee787; }}
    .bad {{ color: #ff8585; }}
    @media (max-width: 860px) {{ main {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{title} Review Studio</h1>
    <span id="style"></span>
  </header>
  <main>
    <section><h2>Preview</h2><video id="preview" controls></video></section>
    <section><h2>Score</h2><div id="score" class="score"></div><pre id="repairs"></pre><pre id="failed"></pre></section>
    <section><h2>Contact Sheet</h2><img id="contact" alt="contact sheet"></section>
    <section><h2>Narration Beats</h2><table id="beats"></table></section>
    <section><h2>Shot Timeline</h2><table id="shots"></table></section>
    <section><h2>Audio Cues</h2><table id="cues"></table></section>
    <section><h2>Delegated Slots</h2><table id="slots"></table></section>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const esc = (s) => String(s ?? "").replace(/[&<>]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));
    function rows(items, cells) {{
      return "<tr>" + cells.map(c => "<th>" + esc(c[0]) + "</th>").join("") + "</tr>" +
        items.map(item => "<tr>" + cells.map(c => "<td>" + esc(c[1](item)) + "</td>").join("") + "</tr>").join("");
    }}
    fetch("review_bundle.json").then(r => r.json()).then(data => {{
      $("style").textContent = data.segment_spec?.style || "";
      if (data.media.preview) $("preview").src = data.media.preview;
      if (data.media.contact_sheet) $("contact").src = data.media.contact_sheet;
      const score = data.metrics?.score ?? "n/a";
      $("score").textContent = score;
      $("score").className = "score " + ((data.metrics?.pass) ? "ok" : "bad");
      $("repairs").textContent = (data.metrics?.repair_suggestions || []).map(x => "- " + x).join("\\n") || "No automated repair suggestions.";
      $("failed").textContent = data.failed_checks || "No failed_checks.md";
      $("beats").innerHTML = rows(data.beat_plan?.beats || [], [
        ["Time", b => (b.time || []).join("-")], ["Keyword", b => b.keyword],
        ["Voice", b => b.voice_text], ["Visual", b => b.visual_owner + " / " + b.visual_action]
      ]);
      $("shots").innerHTML = rows(data.segment_spec?.shots || [], [
        ["Time", s => (s.time || []).join("-")], ["Recipe", s => s.recipe], ["Renderer", s => s.renderer],
        ["Owner", s => s.visual_owner], ["Actions", s => (s.visual_actions || []).map(a => a.type + "@" + a.at).join(", ")]
      ]);
      $("cues").innerHTML = rows(data.audio_cue_sheet?.cues || [], [
        ["At", c => c.at], ["Cue", c => c.type], ["Visual", c => c.visual_action], ["Mix", c => c.mix_note]
      ]);
      const delegated = (data.segment_spec?.shots || []).filter(s => s.delegation).map(s => ({{ shot: s.shot_id, renderer: s.renderer, ...s.delegation }}));
      const traced = (data.execution_trace?.slots || []).map(s => ({{
        shot: s.shot_id || s.shot || "", renderer: s.renderer || "", skill: s.skill || "",
        purpose: s.purpose || s.command || "", acceptance: s.status || s.verification || ""
      }}));
      $("slots").innerHTML = rows([...delegated, ...traced], [
        ["Shot", s => s.shot], ["Renderer", s => s.renderer], ["Skill", s => s.skill],
        ["Purpose", s => s.purpose], ["Acceptance", s => s.acceptance]
      ]);
    }});
  </script>
</body>
</html>
"""
    (studio / "index.html").write_text(index, encoding="utf-8")
    if not missing:
        sync_runtime_artifacts(project_root_from_outputs(root))
    print(f"wrote {studio / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
