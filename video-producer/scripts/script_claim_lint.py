#!/usr/bin/env python3
"""Lint fact-linked scripts and claim ledgers for source-backed video production.

This gate cannot prove truth. It catches workflow failures that commonly lead to
misquotes and overgeneralization: missing source URLs, unsupported script lines,
rejected claims still used in voiceover, weak guardrails, and empty evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {
    "claim_id",
    "claim",
    "claim_type",
    "source_ids",
    "source_urls",
    "supporting_quote",
    "source_context",
    "interpretation_guardrail",
    "script_sentence",
    "reference_link_text",
    "video_location",
    "risk",
    "verification_status",
    "needs_manual_check",
    "misread_check",
}
VALID_STATUSES = {"verified", "provisional", "needs_manual_check", "rejected"}
VALID_RISKS = {"low", "medium", "high", "critical"}
CLAIM_REF_RE = re.compile(r"\[(C\d{3,})\]|\{\{(C\d{3,})\}\}")


def read_claims(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return [], [f"missing {path}"]
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - fieldnames
            if missing:
                errors.append(f"claim ledger missing columns: {', '.join(sorted(missing))}")
            return list(reader), errors
    except Exception as exc:  # noqa: BLE001
        return [], [f"cannot read claim ledger: {exc}"]


def read_source_cards(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    cards: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return cards, [f"missing {path}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            card = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"source_cards.jsonl line {lineno} invalid JSON: {exc}")
            continue
        source_id = str(card.get("source_id", "")).strip()
        if not source_id:
            errors.append(f"source_cards.jsonl line {lineno} missing source_id")
            continue
        cards[source_id] = card
        for key in ["title", "url", "source_type", "reliability", "key_points"]:
            if not card.get(key):
                errors.append(f"source {source_id} missing {key}")
    return cards, errors


def claim_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for match in CLAIM_REF_RE.finditer(text):
        refs.add(match.group(1) or match.group(2))
    return refs


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,|]", value or "") if x.strip()]


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Score fact-linked script, source cards, and claim ledger.")
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--fail-under", type=int, default=85, help="Fail if score is below threshold")
    parser.add_argument("--allow-empty", action="store_true", help="Allow empty claim ledger for non-factual projects")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    claims, claim_errors = read_claims(root / "research" / "claim_ledger.csv")
    cards, card_errors = read_source_cards(root / "research" / "source_cards.jsonl")
    voiceover_path = root / "script" / "voiceover.md"
    voiceover = voiceover_path.read_text(encoding="utf-8") if voiceover_path.exists() else ""

    issues: list[tuple[str, int]] = []
    issues.extend((e, 16) for e in claim_errors)
    issues.extend((e, 8) for e in card_errors)
    if not voiceover_path.exists():
        issues.append(("missing script/voiceover.md", 12))

    if not claims and not args.allow_empty:
        issues.append(("claim ledger has no claim rows; factual videos must be fact-locked before scripting", 30))

    ids_seen: set[str] = set()
    claim_ids = {r.get("claim_id", "").strip() for r in claims if r.get("claim_id")}
    refs_in_voiceover = claim_refs(voiceover)

    for i, row in enumerate(claims, 1):
        cid = row.get("claim_id", "").strip()
        if not cid:
            issues.append((f"claim row {i} missing claim_id", 8))
            continue
        if cid in ids_seen:
            issues.append((f"duplicate claim_id {cid}", 10))
        ids_seen.add(cid)

        status = row.get("verification_status", "").strip().lower()
        risk = row.get("risk", "").strip().lower()
        if status not in VALID_STATUSES:
            issues.append((f"{cid} has invalid verification_status '{status}'", 8))
        if risk and risk not in VALID_RISKS:
            issues.append((f"{cid} has nonstandard risk '{risk}'", 3))
        for key, weight in [
            ("claim", 8),
            ("source_ids", 8),
            ("supporting_quote", 10),
            ("source_context", 5),
            ("interpretation_guardrail", 10),
            ("script_sentence", 6),
            ("misread_check", 8),
        ]:
            if not row.get(key, "").strip():
                issues.append((f"{cid} missing {key}", weight))
        source_ids = split_ids(row.get("source_ids", ""))
        source_urls = split_ids(row.get("source_urls", ""))
        for sid in source_ids:
            if sid not in cards:
                issues.append((f"{cid} references missing source_id {sid}", 8))
        if not source_urls and not source_ids:
            issues.append((f"{cid} has neither source_urls nor source_ids", 10))
        if status == "rejected" and cid in refs_in_voiceover:
            issues.append((f"rejected claim {cid} is still referenced in voiceover", 18))
        if risk in {"high", "critical"} and not truthy(row.get("needs_manual_check", "")) and status != "verified":
            issues.append((f"{cid} is {risk} risk but not marked for manual check or verified", 10))
        if cid in refs_in_voiceover and cid not in row.get("script_sentence", ""):
            # Not fatal: line may be paraphrased, but remind the user to map it.
            issues.append((f"{cid} appears in voiceover but script_sentence does not include its claim id", 3))

    unknown_refs = sorted(refs_in_voiceover - claim_ids)
    if unknown_refs:
        issues.append((f"voiceover references unknown claim IDs: {', '.join(unknown_refs)}", 16))

    used_claims = sorted(refs_in_voiceover & claim_ids)
    if claims and voiceover and not used_claims:
        issues.append(("voiceover has no [Cxxx] claim references even though claim ledger exists", 18))

    # Soft heuristic: source-backed script should have a references section.
    if claims and "References" not in voiceover and "参考" not in voiceover:
        issues.append(("voiceover should include a references section for editor checking", 4))

    penalty = sum(weight for _, weight in issues)
    score = max(0, 100 - penalty)

    report_lines = [
        "# Factcheck Report",
        "",
        f"Score: {score}/100",
        f"Claims: {len(claims)}",
        f"Source cards: {len(cards)}",
        f"Voiceover claim refs: {len(refs_in_voiceover)}",
        "",
    ]
    if issues:
        report_lines.append("## Issues")
        report_lines.extend(f"- [{weight}] {msg}" for msg, weight in issues)
    else:
        report_lines.append("No structural fact-linking issues found. Manual source reading is still required for truth and nuance.")
    report_lines.extend([
        "",
        "## Manual review reminder",
        "Check that every qualifier in the source is preserved in the script: who, where, when, scope, allegation/proposal status, and exceptions.",
    ])
    out = root / "research" / "factcheck_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Fact-link score: {score}/100")
    if issues:
        print("Issues:")
        for msg, weight in issues:
            print(f"- [{weight}] {msg}")
    else:
        print("No structural fact-linking issues found. Manual source review is still required.")
    print(f"Wrote {out}")
    return 1 if score < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
