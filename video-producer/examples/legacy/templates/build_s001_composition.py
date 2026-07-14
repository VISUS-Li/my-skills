#!/usr/bin/env python3
"""Build the standard Review Studio seekable composition for segment S001.

Project agents may replace the visual design inside this file, but keep this
entry point and the preview contract intact:

- write segments/S001/index.html
- expose window.initComposition
- register window.__timelines["S001"]
- create a paused GSAP timeline that Review Studio seeks with .time(t)
- guard optional selectors before adding tweens
"""
from __future__ import annotations

import json
from pathlib import Path


SEGMENT = "S001"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_duration(root: Path) -> float:
    vo = root / "segments" / SEGMENT / "vo_timing.json"
    if vo.exists():
        try:
            data = json.loads(vo.read_text(encoding="utf-8"))
            duration = data.get("duration_sec") or data.get("total_sec")
            if isinstance(duration, (int, float)) and duration > 0:
                return float(duration)
        except Exception:
            pass

    timeline = root / "script" / "beat_timeline.json"
    if timeline.exists():
        try:
            data = json.loads(timeline.read_text(encoding="utf-8"))
            beats = data.get("beats") or []
            ends = [float(b.get("end_sec", 0)) for b in beats if isinstance(b, dict)]
            if ends:
                return max(ends)
        except Exception:
            pass
    return 15.0


def build_html(duration: float) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{SEGMENT} Composition</title>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #6b7280;
      --paper: #f7f4ef;
      --accent: #e11d48;
      --blue: #2563eb;
      --gold: #f59e0b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      font-family: "Noto Sans SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
      background: var(--paper);
      color: var(--ink);
    }}
    .scene {{
      position: relative;
      width: 100vw;
      height: 100vh;
      opacity: 0;
      background:
        linear-gradient(rgba(37, 99, 235, .08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(37, 99, 235, .08) 1px, transparent 1px),
        radial-gradient(circle at 18% 18%, rgba(245, 158, 11, .18), transparent 24%),
        #f7f4ef;
      background-size: 44px 44px, 44px 44px, auto, auto;
    }}
    .proof-card {{
      position: absolute;
      left: 7vw;
      top: 12vh;
      width: 58vw;
      height: 64vh;
      border: 1px solid rgba(23, 32, 51, .14);
      border-radius: 18px;
      background: rgba(255, 255, 255, .88);
      box-shadow: 0 24px 70px rgba(23, 32, 51, .18);
      padding: 26px;
    }}
    .source-label {{
      font-size: 20px;
      font-weight: 800;
      color: var(--muted);
    }}
    .proof-line {{
      height: 26px;
      margin-top: 24px;
      border-radius: 99px;
      background: #e5e7eb;
    }}
    .proof-line[data-pct] {{
      width: 0%;
      background: linear-gradient(90deg, var(--blue), #38bdf8);
    }}
    .focus-ring {{
      position: absolute;
      left: 11%;
      bottom: 22%;
      width: 48%;
      height: 18%;
      border: 6px solid var(--accent);
      border-radius: 14px;
      opacity: 0;
      pointer-events: none;
      box-shadow: 0 0 0 8px rgba(225, 29, 72, .12);
    }}
    .flower-text {{
      position: absolute;
      right: 8vw;
      top: 22vh;
      max-width: 32vw;
      font-weight: 950;
      line-height: .98;
      letter-spacing: 0;
      opacity: 0;
      color: #111827;
    }}
    .flower-text .small {{
      display: inline-block;
      font-size: clamp(34px, 5vw, 82px);
      color: #334155;
    }}
    .flower-text .hero {{
      display: inline-block;
      font-size: clamp(58px, 9vw, 150px);
      color: var(--accent);
      -webkit-text-stroke: 5px #ffffff;
      text-shadow: 0 12px 26px rgba(225, 29, 72, .24);
    }}
    .side-chip {{
      position: absolute;
      right: 8vw;
      bottom: 14vh;
      opacity: 0;
      font-size: 28px;
      font-weight: 850;
      color: #475569;
    }}
    .composition-error-overlay {{
      position: absolute;
      inset: auto 20px 20px 20px;
      z-index: 100;
      display: none;
      padding: 12px 14px;
      border-radius: 10px;
      background: #7f1d1d;
      color: white;
      font: 14px/1.4 ui-monospace, SFMono-Regular, Consolas, monospace;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>
  <main class="scene" data-composition-id="{SEGMENT}" data-build-entry="scripts/build_s001_composition.py" data-duration-sec="{duration:.3f}">
    <section class="proof-card" data-role="proof" data-must-show-detail="source-label critical-row">
      <div class="source-label">Source / screenshot label</div>
      <div class="proof-line"></div>
      <div class="proof-line" data-pct="72%"></div>
      <div class="proof-line"></div>
      <div class="focus-ring"></div>
    </section>

    <div class="flower-text text-unit" data-text-id="text_wps_backstab" data-sync-phrase="WPS">
      <span class="small">被</span><span class="hero">WPS</span><span class="small">背刺了</span>
    </div>
    <div class="side-chip" data-text-id="text_previous_store">前一句留在旁边</div>
    <div class="composition-error-overlay" id="composition-error-overlay"></div>
  </main>

  <script>
    (() => {{
      const SEGMENT_ID = "{SEGMENT}";
      const DURATION = {duration:.3f};
      const scene = document.querySelector(".scene");
      const errorOverlay = document.getElementById("composition-error-overlay");

      window.__timelines = window.__timelines || {{}};
      window.__compositionErrors = window.__compositionErrors || [];

      function showError(error) {{
        const message = error && error.stack ? error.stack : String(error);
        window.__compositionErrors.push(message);
        if (errorOverlay) {{
          errorOverlay.style.display = "block";
          errorOverlay.textContent = message;
        }}
        console.error("[composition]", message);
      }}

      window.addEventListener("error", (event) => showError(event.error || event.message));
      window.addEventListener("unhandledrejection", (event) => showError(event.reason || event));

      function safeTargets(selector, opts = {{}}) {{
        const targets = gsap.utils.toArray(selector);
        if (!targets.length && opts.required) {{
          showError(new Error(`Required GSAP target not found: ${{selector}}`));
        }}
        return targets;
      }}

      function addFromIfPresent(tl, selector, vars, at) {{
        const targets = safeTargets(selector);
        if (targets.length) tl.from(targets, vars, at);
        return targets;
      }}

      function addToIfPresent(tl, selector, vars, at) {{
        const targets = safeTargets(selector);
        if (targets.length) tl.to(targets, vars, at);
        return targets;
      }}

      window.initComposition = function initComposition() {{
        const tl = gsap.timeline({{ paused: true, defaults: {{ ease: "power3.out" }} }});
        window.__timelines['S001'] = tl;
        window.__timelines[SEGMENT_ID] = tl;

        tl.set(scene, {{ autoAlpha: 1 }}, 0);
        addFromIfPresent(tl, ".proof-card", {{ y: 36, opacity: 0, duration: 0.42 }}, 0.05);
        addToIfPresent(tl, ".proof-line[data-pct]", {{
          width: (index, target) => target.dataset.pct || "0%",
          duration: 0.7,
          ease: "power2.out"
        }}, 0.5);
        addFromIfPresent(tl, ".focus-ring", {{ scale: 0.92, opacity: 0, duration: 0.16 }}, 1.05);
        addToIfPresent(tl, ".focus-ring", {{ opacity: 1, duration: 0.1 }}, 1.05);

        // Keyword enters large; proof card yields a little while preserving must-show details.
        addToIfPresent(tl, ".proof-card", {{ xPercent: -5, scale: 0.96, duration: 0.38 }}, 1.35);
        addFromIfPresent(tl, ".flower-text", {{
          opacity: 0,
          x: 80,
          scale: 1.18,
          filter: "blur(10px)",
          duration: 0.34
        }}, 1.35);
        addToIfPresent(tl, ".flower-text", {{ opacity: 1, x: 0, scale: 1, filter: "blur(0px)", duration: 0.34 }}, 1.35);

        // Previous expressive text stores as a side chip instead of vanishing by default.
        addToIfPresent(tl, ".flower-text", {{ top: "14vh", scale: 0.62, opacity: 0.72, duration: 0.38 }}, 3.0);
        addFromIfPresent(tl, ".side-chip", {{ opacity: 0, y: 18, duration: 0.28 }}, 3.12);
        addToIfPresent(tl, ".side-chip", {{ opacity: 1, y: 0, duration: 0.28 }}, 3.12);

        tl.to({{}}, {{ duration: Math.max(0.1, DURATION - tl.duration()) }});
        tl.pause(0);
        return tl;
      }};

      try {{
        window.initComposition();
      }} catch (error) {{
        showError(error);
      }}
    }})();
  </script>
</body>
</html>
"""


def main() -> int:
    root = project_root()
    out = root / "segments" / SEGMENT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(load_duration(root)), encoding="utf-8")
    print(f"Built {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
