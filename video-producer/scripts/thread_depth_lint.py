#!/usr/bin/env python3
"""Lint deep narrative scripts — single-story arcs and multi-point weaves.

Runs automatically before voiceover approval. Depth is the default; shallow
scripts fail unless --allow-shallow is set (user explicitly opted out).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

PARALLEL_PATTERNS = [
    re.compile(r"第[一二三四五六七八九十\d]+[，,、\.]"),
    re.compile(r"首先.*其次", re.DOTALL),
    re.compile(r"第一.*第二", re.DOTALL),
    re.compile(r"今天(我们)?讲(三个|3个|几个|两|二)点"),
    re.compile(r"接下来(看|讲)第"),
]
SPECULATIVE_ORAL = re.compile(
    r"你想啊|你想想看|你觉得呢|其实吧|我跟你说|这就有意思了|你知道吗|怎么说呢|"
    r"是不是.*疯狂|难道.*吗",
)
RESEARCH_ANCHOR = re.compile(
    r"原文|公告|文件|条款|纪要|时间线|回头看|限定词|官方|来源|写得很清楚|"
    r"把时间线|放一起看|第\s*\d+\s*条|据.*显示|公开.*显示|通报|口径",
)
BRIDGE_HINTS = re.compile(
    r"很多人以为|很多人只看|把时间线|回头看|放一起看|拴在|拖进|同一条|收网|"
    r"前面那个|不是.*而是|关键在于|漏掉.*限定|伏笔|分水岭|条款|原文",
)
ORAL_RHYTHM = re.compile(r"\[pause\]|……|\.{3}|不对，更准确地说")
NEWS_HARD_CUT = re.compile(r"据悉|据报道|消息称|此外[，,]|另外[，,]|与此同时[，,]|值得一提的是[，,]")
HARD_JUMP_OPEN = re.compile(r"^(此外|另外|与此同时|接下来|再说|还有一个)", re.MULTILINE)
LANDING_HINTS = re.compile(
    r"所以到这里|这就是为什么|意味着|才看得懂|一环扣|带着刚才|带着这个|"
    r"就不意外|整条线|同一根链|问题已经不在|真正卡住的",
)
CONTINUITY_HINTS = re.compile(
    r"回到刚才|回到开头|前面那个|同一份|先记住|如果只看到.*加上|"
    r"时间线再往后|再往后推|顺着这条线|带着这个限定词",
)
DWELL_LAYER_KEYS = {"enter", "evidence", "mechanism", "landing"}
PLACEHOLDER_MARKERS = (
    "用户给",
    "示例",
    "必须是关系",
    "一句话：",
    "较少人知道、可证实",
    "观众普遍以为",
    "用一句话描述",
)
THREAD_LEDGER_COLS = {
    "thread_id",
    "from_entity",
    "to_entity",
    "relationship_type",
    "relationship_summary",
    "claim_ids",
    "source_ids",
    "evidence_strength",
    "status",
}


def load_json(path: Path) -> tuple[dict | None, list[str]]:
    if not path.exists():
        return None, [f"missing {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except Exception as exc:  # noqa: BLE001
        return None, [f"invalid JSON in {path}: {exc}"]


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], [f"missing {path}"]
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = THREAD_LEDGER_COLS - set(reader.fieldnames or [])
            errors = []
            if missing:
                errors.append(f"thread_ledger missing columns: {', '.join(sorted(missing))}")
            return list(reader), errors
    except Exception as exc:  # noqa: BLE001
        return [], [f"cannot read thread ledger: {exc}"]


def is_placeholder(text: str) -> bool:
    t = str(text).strip()
    if not t:
        return True
    return any(m in t for m in PLACEHOLDER_MARKERS)


def filled_points(thread_map: dict | None, brief: str) -> list[str]:
    if thread_map:
        points = thread_map.get("user_input_points") or []
        filled = [str(p).strip() for p in points if str(p).strip() and not is_placeholder(str(p))]
        if filled:
            return filled
    hits = re.findall(r"^\s*\d+\.\s*(.+)$", brief, re.MULTILINE)
    return [h.strip() for h in hits if h.strip()]


def substantive_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        r for r in rows
        if str(r.get("relationship_summary", "")).strip()
        and not is_placeholder(str(r.get("relationship_summary", "")))
        and str(r.get("status", "")).strip().lower() in {"verified", "needs_manual_check", "provisional", ""}
    ]


def voiceover_body(voiceover: str) -> str:
    if "## Draft" in voiceover:
        body = voiceover.split("## Draft", 1)[-1]
        for stop in ("## Beat checklist", "## References", "## Arc"):
            if stop in body:
                body = body.split(stop, 1)[0]
        return body
    return voiceover


def count_spine_dwell_issues(spine: list) -> list[tuple[str, int]]:
    issues: list[tuple[str, int]] = []
    major = [p for p in spine if isinstance(p, dict) and p.get("phase") not in (None, "")]
    for phase in major:
        name = str(phase.get("phase", "?"))
        if name in {"hook", "payoff"} or "turn" in name or "prelude" in name or "aftermath" in name:
            landing = str(phase.get("landing_line", "")).strip()
            carry = str(phase.get("carry_forward", "")).strip()
            dwell = phase.get("dwell_layers") or {}
            if is_placeholder(landing):
                issues.append((f"spine.{name} missing landing_line (beat must land before jumping)", 8))
            if name not in {"payoff"} and is_placeholder(carry):
                issues.append((f"spine.{name} missing carry_forward (prevents abrupt cut)", 8))
            if not DWELL_LAYER_KEYS.issubset(set(dwell.keys())):
                issues.append((f"spine.{name} dwell_layers need enter/evidence/mechanism/landing", 6))
            elif any(is_placeholder(str(dwell.get(k, ""))) for k in DWELL_LAYER_KEYS):
                issues.append((f"spine.{name} dwell_layers still placeholder", 5))
    return issues


def count_short_beats(body: str) -> int:
    """Count <!-- BEAT --> sections with fewer than 4 sentence-like units."""
    chunks = re.split(r"<!--\s*BEAT:", body)
    short = 0
    for chunk in chunks[1:]:
        text = re.sub(r"<!--.*?-->", "", chunk, flags=re.DOTALL)
        text = re.sub(r"\[.*?\]", "", text)
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", text) if len(s.strip()) > 8]
        if 0 < len(sentences) < 4:
            short += 1
    return short


def voiceover_is_draft_only(voiceover: str) -> bool:
    draft_markers = ("这里写口播正文", "示例旁白", "<!-- VISUAL: opening hook", "[enter]\n很多人")
    body = voiceover_body(voiceover)
    return any(m in body for m in draft_markers) and len(body.strip()) < 500


def main() -> int:
    parser = argparse.ArgumentParser(description="Score deep narrative depth for script approval.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=80, help="Fail if score below threshold")
    parser.add_argument(
        "--allow-shallow",
        action="store_true",
        help="Allow missing depth artifacts (user explicitly opted out of deep narrative)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues: list[tuple[str, int]] = []

    thread_map, map_errors = load_json(root / "script" / "narrative_thread_map.json")
    issues.extend((e, 10) for e in map_errors)
    thread_rows, ledger_errors = read_csv_rows(root / "research" / "thread_ledger.csv")
    issues.extend((e, 8) for e in ledger_errors)

    brief_path = root / "script" / "creative_brief.md"
    brief = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    voiceover_path = root / "script" / "voiceover.md"
    voiceover = voiceover_path.read_text(encoding="utf-8") if voiceover_path.exists() else ""

    points = filled_points(thread_map, brief)
    scope = str((thread_map or {}).get("story_scope", "")).strip().lower()
    multi = len(points) >= 2 or scope == "multi"
    min_rows = max(2, len(points) - 1) if multi else 3

    if args.allow_shallow:
        print("Shallow mode: skipping depth requirements")
    else:
        if thread_map is None:
            issues.append(("deep narrative requires script/narrative_thread_map.json", 20))
        elif thread_map:
            master = str(thread_map.get("master_thread", "")).strip()
            if is_placeholder(master):
                issues.append(("master_thread is empty or still template placeholder", 16))
            elif master.count("、") >= 2 and not any(k in master for k in ("因为", "链条", "推到", "弧线", "从", "如何")):
                issues.append(("master_thread looks like a topic label, not a story arc or relationship", 12))

            omit = thread_map.get("selective_omit") or []
            if not omit or all(is_placeholder(str(o.get("topic", ""))) for o in omit if isinstance(o, dict)):
                issues.append(("selective_omit required — show what true-but-boring facts you cut", 8))

            layers = thread_map.get("insight_layers") or {}
            secret = str(layers.get("secret", "")).strip()
            if is_placeholder(secret):
                issues.append(("insight_layers.secret required — one verified less-known detail", 12))

            mechanism = str(layers.get("mechanism", "")).strip()
            if is_placeholder(mechanism):
                issues.append(("insight_layers.mechanism is empty or placeholder", 6))

            spine = thread_map.get("spine") or []
            if len(spine) < 3:
                issues.append(("spine needs at least 3 phases (hook, turn, payoff)", 8))
            else:
                issues.extend(count_spine_dwell_issues(spine))

        sub_rows = substantive_rows(thread_rows)
        if len(sub_rows) < min_rows:
            label = "multi-point weave" if multi else "single-story arc"
            issues.append((
                f"{label} needs at least {min_rows} substantive thread_ledger rows (have {len(sub_rows)})",
                16,
            ))

        for row in thread_rows:
            if is_placeholder(str(row.get("relationship_summary", ""))):
                continue
            tid = row.get("thread_id", "?")
            rtype = str(row.get("relationship_type", "")).strip()
            if rtype == "open_question":
                continue
            if not row.get("claim_ids", "").strip():
                issues.append((f"{tid} missing claim_ids (or mark open_question)", 8))
            if not row.get("source_ids", "").strip():
                issues.append((f"{tid} missing source_ids", 6))

    if voiceover_path.exists() and voiceover.strip() and not voiceover_is_draft_only(voiceover):
        body = voiceover_body(voiceover)
        for pat in PARALLEL_PATTERNS:
            if pat.search(voiceover):
                issues.append((f"parallel bullet structure: {pat.pattern}", 14))
                break
        spec_match = SPECULATIVE_ORAL.search(voiceover)
        if spec_match:
            issues.append((
                f"speculative oral phrase detected (sounds like guesswork): «{spec_match.group()}»",
                16,
            ))
        news_match = NEWS_HARD_CUT.search(voiceover)
        if news_match:
            issues.append((
                f"news-report phrasing (breaks story flow): «{news_match.group()}»",
                12,
            ))
        if HARD_JUMP_OPEN.search(body):
            issues.append(("beat opens with hard-cut transition (此外/另外/接下来) — use carry-forward instead", 10))
        if not args.allow_shallow and not LANDING_HINTS.search(voiceover):
            issues.append(("voiceover lacks landing lines (所以到这里/意味着什么/就不意外…)", 10))
        if not args.allow_shallow and len(CONTINUITY_HINTS.findall(voiceover)) < 2:
            issues.append(("need ≥2 continuity devices (回到刚才/带着这个限定词/时间线再往后…)", 8))
        if not args.allow_shallow and not BRIDGE_HINTS.search(voiceover):
            issues.append(("voiceover lacks evidence-anchored bridge language (原文/时间线/条款/很多人只看…)", 10))
        if not args.allow_shallow and not RESEARCH_ANCHOR.search(voiceover):
            issues.append(("voiceover should anchor claims to sources in speech (原文/公告/文件/时间线…)", 8))
        short_beats = count_short_beats(body)
        if short_beats > 0:
            issues.append((f"{short_beats} BEAT block(s) have <4 sentences — dwell before jumping", 10))
        if not ORAL_RHYTHM.search(voiceover):
            issues.append(("add oral rhythm (pause, ……, or 不对更准确地说) sparingly", 3))

    penalty = sum(w for _, w in issues)
    score = max(0, 100 - penalty)

    report = root / "script" / "thread_depth_report.md"
    lines = [
        "# Thread Depth Report",
        "",
        f"Score: {score}/100",
        f"Story scope: {scope or ('multi' if multi else 'single')}",
        f"Input points: {len(points)}",
        f"Thread ledger rows: {len(substantive_rows(thread_rows))} substantive / {len(thread_rows)} total",
        "",
    ]
    if issues:
        lines.append("## Issues")
        lines.extend(f"- [{w}] {msg}" for msg, w in issues)
    else:
        lines.append("Depth structure OK. Manual source verification still required.")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Thread depth score: {score}/100")
    for msg, w in issues:
        print(f"- [{w}] {msg}")
    print(f"Wrote {report}")
    return 1 if score < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
