#!/usr/bin/env python3
"""Convert MinerU 0.9.3 page output into the Markdown text OmniDocBench reads.

OmniDocBench's end2end dataset (quick_match) loads
    <prediction_dir>/<image_stem>.md
and parses it with utils/extract.py:md_tex_filter, which only understands plain
Markdown + LaTeX: HTML tables, $...$/\[...\] display formulas, ```code``` blocks
and paragraph text. It derives reading order from the character offsets of those
items, so the *document order* of the file is what matters -- not the bbox data.

MinerU's own page Markdown already satisfies that (verified on the 09:43 smoke
output).  We therefore use `<stem>.md` verbatim when present, and fall back to a
`_content_list.json` reconstruction otherwise.  Every manifest entry gets a file,
empty ones included, so the official scorer counts failures as misses instead of
silently dropping pages.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Blocks whose text belongs in the flowing document text.
TEXT_TYPES = {"text", "title", "list", "index", "header", "footer", "page_number", "page_footnote"}


def _clean(text: str) -> str:
    text = (text or "").replace("<|txt_contd|>", "").replace("<|txt_contd|>", "")
    return " ".join(text.split())


def _image_markdown(img_path: str | None, caption: list[str] | None) -> str:
    alt = _clean(" ".join(caption or []))
    return f"![{alt}]({img_path or 'image.jpg'})"


def blocks_to_markdown(blocks: list[dict]) -> str:
    """Reconstruct MinerU page Markdown from its content_list.json."""
    out: list[str] = []
    for b in blocks:
        btype = b.get("type")
        if btype in TEXT_TYPES:
            txt = _clean(b.get("text"))
            if txt:
                out.append(txt)
        elif btype == "equation":
            latex = _clean(b.get("text") or b.get("latex"))
            if latex:
                out.append(f"$$\n{latex}\n$$")
        elif btype == "table":
            body = (b.get("table_body") or "").strip()
            if not body:
                body = _clean(b.get("text"))
            if body:
                # img_caption / table_caption / table_footnote are scored separately
                # by OmniDocBench and are ignored anyway; keep only the table body.
                out.append(body)
            for cap in b.get("table_caption") or []:
                if _clean(cap):
                    out.append(_clean(cap))
            for fn in b.get("table_footnote") or []:
                if _clean(fn):
                    out.append(_clean(fn))
        elif btype == "image":
            out.append(_image_markdown(b.get("img_path"), b.get("img_caption")))
            for fn in b.get("img_footnote") or []:
                if _clean(fn):
                    out.append(_clean(fn))
        elif btype == "interline_equation":
            latex = _clean(b.get("text") or b.get("latex"))
            if latex:
                out.append(f"$$\n{latex}\n$$")
        else:
            txt = _clean(b.get("text"))
            if txt:
                out.append(txt)
    return "\n\n".join(out) + "\n"


def find_page_dir(raw_root: Path, stem: str) -> Path | None:
    """MinerU writes <out>/<pdf_stem>/<auto|ocr>/. Locate it by stem, then by scan."""
    direct = raw_root / stem
    if direct.is_dir():
        return direct
    for cand in raw_root.rglob(stem):
        if cand.is_dir():
            return cand
    return None


def markdown_for_page(page_dir: Path, stem: str) -> tuple[str, str]:
    """Return (markdown_text, source_kind)."""
    if page_dir is None:
        return "", "missing"
    md_candidates = sorted(page_dir.rglob(f"{stem}.md"))
    if not md_candidates:
        md_candidates = sorted(page_dir.rglob("*.md"))
    if md_candidates:
        return md_candidates[0].read_text(encoding="utf-8", errors="replace"), "mineru_md"

    json_candidates = sorted(page_dir.rglob("*content_list.json")) or sorted(page_dir.rglob("*.json"))
    for jc in json_candidates:
        try:
            blocks = json.loads(jc.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(blocks, list):
            return blocks_to_markdown(blocks), "content_list"
    return "", "empty"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True, help="OmniDocBench manifest jsonl")
    ap.add_argument("--raw-root", type=Path, required=True, help="MinerU -o output root")
    ap.add_argument("--pred-dir", type=Path, required=True, help="where <stem>.md must land")
    args = ap.parse_args()

    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    args.pred_dir.mkdir(parents=True, exist_ok=True)

    report = []
    for row in rows:
        stem = Path(Path(row["image_path"]).name).stem
        page_dir = find_page_dir(args.raw_root, stem)
        text, kind = markdown_for_page(page_dir, stem)
        (args.pred_dir / f"{stem}.md").write_text(text, encoding="utf-8")
        report.append({"stem": stem, "source": kind, "chars": len(text),
                       "page_dir": str(page_dir) if page_dir else None})

    counts: dict[str, int] = {}
    for r in report:
        counts[r["source"]] = counts.get(r["source"], 0) + 1
    summary = {"pages": len(report), "sources": counts,
               "empty_pages": [r["stem"] for r in report if r["chars"] == 0]}
    (args.pred_dir.parent / "adapter_report.json").write_text(
        json.dumps({"summary": summary, "detail": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
