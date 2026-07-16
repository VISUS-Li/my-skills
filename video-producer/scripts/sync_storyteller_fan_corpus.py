#!/usr/bin/env python3
"""Copy StorytellerFan .txt subtitles into the skill corpus with stable IDs."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

SRC_ROOT = Path(r"D:\code\GitHub\my-skills\outputs\subtitles\StorytellerFan")
DST_ROOT = Path(r"D:\code\GitHub\my-skills\video-producer\references\storyteller-fan-corpus")
TX_DIR = DST_ROOT / "transcripts"

THEME_RULES = [
    (["融资", "Pre-IPO", "估值", "募资", "510"], "funding_power"),
    (["条款", "earn-out", "GP", "LP", "对赌", "股权", "一票否决"], "deal_terms"),
    (["后门", "封禁", "禁用", "安全", "核", "切尔诺贝利", "合规", "开源"], "trust_safety_governance"),
    (["跑分", "评测", "Fable", "Mythos", "基准", "benchmark"], "eval_vs_workbench"),
    (["招聘", "天才", "扩张", "裁员"], "org_people"),
    (["商业模式", "遥遥领先", "销量", "定价"], "business_model"),
    (["芯片", "EUV", "制裁", "出口"], "geopolitics_semiconductor"),
    (["起诉", "官司", "专利", "唐坦"], "legal_dispute"),
    (["Agent", "员工", "岗位", "人效"], "labor_ai"),
    (["存储", "涨价", "DRAM", "NAND", "token", "算力"], "cost_infra"),
    (["五层", "拆解", "层层"], "layered_dig"),
]


def tags_for(title: str) -> list[str]:
    t = title or ""
    tags: list[str] = []
    for keys, tag in THEME_RULES:
        if any(k.lower() in t.lower() for k in keys):
            tags.append(tag)
    return tags or ["general_ai_tech"]


def main() -> int:
    TX_DIR.mkdir(parents=True, exist_ok=True)
    summary = json.loads((SRC_ROOT / "_summary.json").read_text(encoding="utf-8"))
    entries: list[dict] = []

    for r in summary["results"]:
        if not r.get("ok"):
            continue
        vid = r["id"]
        title = r["title"]
        files = r.get("files") or {}
        txt_path = Path(files["txt"]) if files.get("txt") else None
        if txt_path is None or not txt_path.exists():
            matches = list(SRC_ROOT.glob(f"*_{vid}.txt"))
            if not matches:
                print("MISSING", vid, title)
                continue
            txt_path = matches[0]
        dst = TX_DIR / f"{vid}.txt"
        shutil.copy2(txt_path, dst)
        text = dst.read_text(encoding="utf-8", errors="replace")
        entries.append(
            {
                "id": vid,
                "title": title,
                "file": f"transcripts/{vid}.txt",
                "chars": len(text),
                "segment_count": r.get("segment_count"),
                "tags": tags_for(title),
                "method": r.get("method"),
            }
        )

    catalog = {
        "source_channel": "@StorytellerFan",
        "purpose": (
            "Portable craft corpus for research breadth/depth and oral VO style. "
            "Study moves; never copy titles, CTAs, catchphrases, or channel branding."
        ),
        "how_to_use": (
            "Load references/storyteller-fan-craft.md first. Then open CATALOG.md "
            "and read 1-2 transcript files matching the topic type. Do not load the whole corpus."
        ),
        "count": len(entries),
        "entries": entries,
    }
    (DST_ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# StorytellerFan Corpus Catalog",
        "",
        "> On-demand only. Read `../storyteller-fan-craft.md` before opening transcripts.",
        "> Learn structure, research widths, dig depth, oral texture — **never** copy intros/outros/CTAs/host branding.",
        "",
        f"Transcripts: **{len(entries)}** files under `transcripts/{{youtube_id}}.txt`.",
        "",
        "## Recommended first reads (by craft move)",
        "",
        "| id | why study |",
        "|---|---|",
        "| `L31KQ21VGQk` | Multi-layer dig；律师/牧师保密类比 + 收回主线 |",
        "| `g20t3FKr49k` | Deal terms / GP-LP / 霸王条款；数字对照后谈含义 |",
        "| `tug90T9FUrE` | Eval vs workbench；跑分追上 ≠ 做事系统 |",
        "| `M8-o9pg2eqU` | 历史/制度隐喻（切尔诺贝利）拉回 AI 监管 |",
        "| `umFhxczfRr8` | 表面销量 vs 真正商业模式 |",
        "| `IbVORK8NX2M` | 大数字 + 含义落地；收购案读法 |",
        "| `T9zqRW4GOq4` | 证据边界：刷屏照片哪些能当证据 |",
        "| `qOFvhTllPhI` | 规则奇葩点（商标/成本）与认知补齐 |",
        "| `00YVzqruxPc` | 融资叙事下的权力与时间线 |",
        "",
        "## Full index",
        "",
        "| id | tags | title |",
        "|---|---|---|",
    ]
    for e in sorted(entries, key=lambda x: x["title"]):
        tags = ", ".join(e["tags"])
        title = e["title"].replace("|", "\\|")
        lines.append(f"| `{e['id']}` | {tags} | {title} |")
    lines.append("")
    (DST_ROOT / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"copied {len(entries)} transcripts -> {TX_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
