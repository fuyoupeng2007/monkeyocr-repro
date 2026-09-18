#!/usr/bin/env python3
"""Build the MonkeyOCR vs MinerU 0.9.3 comparison from official OmniDocBench results.

Both runs use the same 120-page stratified subset, the same config, the same
quick_match method:
  OmniDocBench/result/predictions_quick_match_*        MonkeyOCR (formal 120)
  OmniDocBench/result/mineru_formal_120_quick_match_*  MinerU 0.9.3 (formal 120)

Emits Markdown + JSON under outputs/compare/.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJ = Path("/root/autodl-tmp/monkeyocr-repro")
RES = PROJ / "OmniDocBench" / "result"
OUT = PROJ / "outputs" / "compare"

MODELS = [
    ("MonkeyOCR-3B", "predictions_quick_match"),
    ("MinerU-0.9.3", "mineru_formal_120_quick_match"),
]

HEADLINE = [
    ("text_block_edit_dist", ("text_block", "all", "Edit_dist", "ALL_page_avg"), False),
    ("display_formula_edit_dist", ("display_formula", "all", "Edit_dist", "ALL_page_avg"), False),
    ("table_TEDS", ("table", "all", "TEDS", "all"), True),
    ("table_TEDS_structure_only", ("table", "all", "TEDS_structure_only", "all"), True),
    ("table_edit_dist", ("table", "all", "Edit_dist", "ALL_page_avg"), False),
    ("reading_order_edit_dist", ("reading_order", "all", "Edit_dist", "ALL_page_avg"), False),
]

GROUP_KEYS = [
    ("text by language", "text_block", "Edit_dist", "text_language:"),
    ("text by background", "text_block", "Edit_dist", "text_background:"),
    ("text by rotate", "text_block", "Edit_dist", "text_rotate:"),
    ("table by language", "table", "TEDS", "language: table_"),
    ("table by line style", "table", "TEDS", "line:"),
    ("table with span", "table", "TEDS", "with_span:"),
    ("formula by type", "display_formula", "Edit_dist", "formula_type:"),
]

SOURCE_PREFIX = "data_source: "


def load(name: str):
    p = RES / f"{name}_metric_result.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def dig(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def fmt_delta(a, b, higher_better: bool) -> str:
    if a is None or b is None or a == 0:
        return "-"
    rel = (b - a) / abs(a)
    if not higher_better:
        rel = -rel
    return f"{'+' if rel >= 0 else ''}{rel * 100:.1f}%"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = [n for _, n in MODELS]
    labels = [lbl for lbl, _ in MODELS]
    data = [load(n) for n in names]

    lines = ["## 4.1 Overall metrics (OmniDocBench v1.0, same 120-page subset)", ""]
    lines.append("| metric | " + " | ".join(labels) + " | change (MinerU vs MonkeyOCR) |")
    lines.append("|---|" + "---|" * (len(labels) + 1))
    summary = {"models": labels, "headline": [], "groups": {}, "per_source": {}, "missing": []}
    for label, path, hib in HEADLINE:
        vals = [dig(m, path) if m else None for m in data]
        cells = " | ".join(fmt(v) for v in vals)
        delta = fmt_delta(vals[0], vals[1], hib) if len(vals) == 2 else "-"
        lines.append(f"| {label} | {cells} | {delta} |")
        summary["headline"].append({"metric": label, "values": vals, "delta": delta})
    lines.append("")

    for title, sec, metric, prefix in GROUP_KEYS:
        agg = {}
        for m in data:
            g = dig(m, (sec, "group", metric)) if m else None
            if not isinstance(g, dict):
                continue
            for k, v in g.items():
                if k.startswith(prefix) and isinstance(v, (int, float)):
                    agg.setdefault(k, []).append(v)
        if not agg:
            continue
        lines.append(f"### {title} ({metric})")
        lines.append("")
        lines.append("| group | " + " | ".join(labels) + " |")
        lines.append("|---|" + "---|" * len(labels))
        for k, vals in sorted(agg.items()):
            pad = list(vals) + [None] * (len(labels) - len(vals))
            lines.append(f"| {k} | " + " | ".join(fmt(v) for v in pad) + " |")
        lines.append("")
        summary["groups"][title] = agg

    for metric, path in (("text_block", ("text_block", "page", "Edit_dist")),
                         ("display_formula", ("display_formula", "page", "Edit_dist")),
                         ("reading_order", ("reading_order", "page", "Edit_dist")),
                         ("table", ("table", "page", "TEDS"))):
        rows = []
        for m in data:
            page = dig(m, path) if m else None
            rows.append({k[len(SOURCE_PREFIX):]: v for k, v in page.items() if k.startswith(SOURCE_PREFIX)}
                        if page else None)
        if not any(rows):
            continue
        keys = sorted({k for r in rows if r for k in r})
        lines.append(f"### by data source: {metric}")
        lines.append("")
        lines.append("| source | " + " | ".join(labels) + " |")
        lines.append("|---|" + "---|" * len(labels))
        for k in keys:
            lines.append(f"| {k} | " + " | ".join(fmt((r or {}).get(k)) for r in rows) + " |")
        lines.append("")
        summary["per_source"][metric] = [{k: (r or {}).get(k) for k in keys} for r in rows]

    stem_edit = {}
    for lbl, name in zip(labels, names):
        p = RES / f"{name}_text_block_per_page_edit.json"
        if p.exists():
            stem_edit[lbl] = json.loads(p.read_text(encoding="utf-8"))
    if len(stem_edit) == len(labels):
        common = set.intersection(*[set(v) for v in stem_edit.values()])
        ranked = sorted(common, key=lambda s: -(stem_edit[labels[0]][s] - stem_edit[labels[1]][s]))[:10]
        lines.append("### worst regressions vs MonkeyOCR (text_block edit distance)")
        lines.append("")
        lines.append("| page | " + " | ".join(labels) + " | delta |")
        lines.append("|---|" + "---|" * (len(labels) + 1))
        for s in ranked:
            a, b = stem_edit[labels[0]][s], stem_edit[labels[1]][s]
            lines.append(f"| {s} | {a:.4f} | {b:.4f} | {b - a:+.4f} |")
        lines.append("")
        summary["per_page_worst"] = [
            {"page": s, labels[0]: stem_edit[labels[0]][s], labels[1]: stem_edit[labels[1]][s]}
            for s in ranked
        ]

    summary["missing"] = [lbl for lbl, m in zip(labels, data) if not m]
    md = "\n".join(lines)
    (OUT / "comparison_table.md").write_text(md, encoding="utf-8")
    (OUT / "comparison.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    print("MISSING:", summary["missing"])


if __name__ == "__main__":
    main()
