#!/usr/bin/env python3
"""Build the MonkeyOCR vs MinerU comparison from official OmniDocBench results.

Each model's evaluation is written under a model-specific prefix so the two runs
can never overwrite each other (the official script derives its output name from
the basename of prediction.data_path):

  configs/eval_monkeyocr_120.yaml -> prediction .../eval_inputs/monkeyocr_formal_120
                                     results  result/monkeyocr_formal_120_quick_match_*
  configs/eval_mineru_120.yaml    -> prediction .../eval_inputs/mineru_formal_120
                                     results  result/mineru_formal_120_quick_match_*

Falls back to the historical 'predictions_*' prefix if the model-specific files
are absent, so this keeps working before a re-evaluation is run.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJ = Path("/root/autodl-tmp/monkeyocr-repro")
RES = PROJ / "OmniDocBench" / "result"
OUT = PROJ / "outputs" / "compare"

MODELS = [
    ("MonkeyOCR-3B", ["monkeyocr_formal_120_quick_match", "predictions_quick_match"]),
    ("MinerU-0.9.3", ["mineru_formal_120_quick_match"]),
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


def load(prefixes: list[str]):
    for p in prefixes:
        f = RES / f"{p}_metric_result.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8")), p
    return None, None


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
    labels = [lbl for lbl, _ in MODELS]
    loaded = [load(p) for _, p in MODELS]
    data = [d for d, _ in loaded]
    prefixes = [p for _, p in loaded]

    lines = ["## 4.1 Overall metrics (OmniDocBench v1.0, same 120-page subset)", ""]
    lines.append("| metric | " + " | ".join(labels) + " | change (MinerU vs MonkeyOCR) |")
    lines.append("|---|" + "---|" * (len(labels) + 1))
    summary = {"models": labels, "prefixes": prefixes, "headline": [], "groups": {},
               "per_source": {}, "missing": [], "source_files": [str(p) for p in prefixes]}
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

    # per-page text edit distance -> failure analysis
    per_page = []
    for p in prefixes:
        f = RES / f"{p}_text_block_per_page_edit.json"
        per_page.append(json.loads(f.read_text(encoding="utf-8")) if f and f.exists() else None)
    if all(per_page):
        common = set.intersection(*[set(v) for v in per_page])
        ranked = sorted(common, key=lambda s: -(per_page[0][s] - per_page[1][s]))[:10]
        lines.append("### worst regressions vs MonkeyOCR (text_block edit distance)")
        lines.append("")
        lines.append("| page | " + " | ".join(labels) + " | delta |")
        lines.append("|---|" + "---|" * (len(labels) + 1))
        for s in ranked:
            a, b = per_page[0][s], per_page[1][s]
            lines.append(f"| {s} | {a:.4f} | {b:.4f} | {b - a:+.4f} |")
        lines.append("")
        summary["per_page_worst"] = [
            {"page": s, labels[0]: per_page[0][s], labels[1]: per_page[1][s]} for s in ranked
        ]

    # completeness: how many of the subset pages actually got scored
    expected = None
    gt = PROJ / "data/omnidocbench_v1_0/subsets/formal_120.json"
    if gt.exists():
        try:
            expected = len(json.loads(gt.read_text(encoding="utf-8")))
        except Exception:
            expected = None
    complete = {}
    for lbl, pp in zip(labels, per_page):
        if pp is None:
            complete[lbl] = False
        else:
            scored = sum(1 for v in pp.values() if isinstance(v, (int, float)))
            # a couple of unscored pages are expected (failed parses get an empty
            # prediction and are dropped by the matcher); only a clearly partial
            # run counts as incomplete
            complete[lbl] = bool(expected) and scored >= 0.95 * expected
            summary.setdefault("scored_pages", {})[lbl] = scored
    summary["expected_pages"] = expected
    summary["complete"] = complete
    summary["missing"] = [lbl for lbl, m in zip(labels, data) if not m]

    md = "\n".join(lines)
    (OUT / "comparison_table.md").write_text(md, encoding="utf-8")
    (OUT / "comparison.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    print("SOURCES:", prefixes)
    print("SCORED:", summary.get("scored_pages"), "expected:", expected)
    print("COMPLETE:", complete)
    print("MISSING:", summary["missing"])


if __name__ == "__main__":
    main()
