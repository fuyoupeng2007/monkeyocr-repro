#!/usr/bin/env python3
"""Convert the Chinese paper translation (Markdown) into a well-formatted Word file.

Handles the subset of Markdown used in the translation: headings (#..####), tables,
blockquotes (>), bullet/numbered lists, bold/code inline spans, horizontal rules.
CJK-safe: every run gets ascii/hAnsi/eastAsia set to 微软雅黑 so the text renders
correctly on the user's machine.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

CJK = "微软雅黑"


def set_run(run, size=10.5, bold=False, italic=False, color=None, mono=False):
    font = "Consolas" if mono else CJK
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rf = rPr.get_or_add_rFonts()
    rf.set(qn("w:ascii"), font)
    rf.set(qn("w:hAnsi"), font)
    rf.set(qn("w:eastAsia"), CJK if not mono else font)
    if mono:
        # subtle background for inline code
        shd = rPr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): "F3F5F7"})
        rPr.append(shd)


INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def add_inline(p, text, size=10.5, base_bold=False, color=None):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            set_run(p.add_run(part[2:-2]), size=size, bold=True, color=color)
        elif part.startswith("`") and part.endswith("`"):
            set_run(p.add_run(part[1:-1]), size=size - 0.5, mono=True)
        else:
            set_run(p.add_run(part), size=size, bold=base_bold, color=color)


def heading(doc, text, level):
    sizes = {1: 19, 2: 15, 3: 12.5, 4: 11.5}
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(18 if level <= 2 else 12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.3
    p.style = doc.styles["Heading %d" % min(level, 4)]
    # all-black headings; the only decoration is a thin grey rule under level-2 heads
    set_run(p.add_run(text), size=sizes.get(level, 11.5), bold=True)
    if level == 2:
        pPr = p._element.get_or_add_pPr()
        bdr = pPr.makeelement(qn("w:pBdr"), {})
        bdr.append(bdr.makeelement(qn("w:bottom"), {
            qn("w:val"): "single", qn("w:sz"): "4", qn("w:space"): "2",
            qn("w:color"): "BFBFBF"}))
        pPr.append(bdr)
    return p


def para(doc, text, size=10.5, color=None, align=None, indent=0, space_after=6, line=1.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    add_inline(p, text, size=size, color=color)
    return p


def quote(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.6)
    pf.space_before = Pt(6)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.45
    # 说明性引用：缩进 + 灰色细线，正文仍为黑字
    add_inline(p, text, size=9.5)
    pPr = p._element.get_or_add_pPr()
    bdr = pPr.makeelement(qn("w:pBdr"), {})
    left = bdr.makeelement(qn("w:left"), {qn("w:val"): "single", qn("w:sz"): "6",
                                            qn("w:space"): "8", qn("w:color"): "BFBFBF"})
    bdr.append(left)
    pPr.append(bdr)
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    add_inline(p, text)
    return p


def numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.45
    add_inline(p, text)
    return p


def table(doc, rows):
    ncols = max(len(r) for r in rows)
    t = doc.add_table(rows=0, cols=ncols)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j in range(ncols):
            val = row[j] if j < len(row) else ""
            cell = cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, val, size=8.5, base_bold=(i == 0))
    return t


def convert(md_path: Path, out_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()

    # page + base style
    sec = doc.sections[0]
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.3)
    sec.right_margin = Cm(2.3)
    st = doc.styles["Normal"]
    st.font.name = CJK
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), CJK)

    i = 0
    in_table = False
    buf: list[list[str]] = []

    def flush_table():
        nonlocal buf, in_table
        if buf:
            table(doc, buf)
            buf = []
        in_table = False

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # markdown table block
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                i += 1
                continue
            buf.append(cells)
            in_table = True
            i += 1
            continue
        if in_table:
            flush_table()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            p = doc.add_paragraph()
            pPr = p._element.get_or_add_pPr()
            bdr = pPr.makeelement(qn("w:pBdr"), {})
            bdr.append(bdr.makeelement(qn("w:bottom"), {
                qn("w:val"): "single", qn("w:sz"): "6", qn("w:space"): "1", qn("w:color"): "BFBFBF"}))
            pPr.append(bdr)
            p.paragraph_format.space_after = Pt(4)
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            heading(doc, m.group(2).strip(), len(m.group(1)))
            i += 1
            continue

        if stripped.startswith(">"):
            quote(doc, stripped.lstrip("> ").strip())
            i += 1
            continue

        m = re.match(r"^([-*])\s+(.*)$", stripped)
        if m:
            bullet(doc, m.group(2))
            i += 1
            continue

        m = re.match(r"^\d+[\.、]\s+(.*)$", stripped)
        if m:
            numbered(doc, m.group(1))
            i += 1
            continue

        para(doc, stripped)
        i += 1

    if in_table:
        flush_table()

    doc.save(str(out_path))


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(r"D:\haeness\monkeyocr-takeover\deliverables\MonkeyOCR论文_中文全译.md")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path(r"D:\haeness\monkeyocr-takeover\deliverables\MonkeyOCR论文_中文全译.docx")
    convert(src, dst)
    size = dst.stat().st_size
    print(f"written: {dst}  ({size} bytes)")
    d = Document(str(dst))
    print("段落:", len(d.paragraphs), " 表格:", len(d.tables))
    print("标题:", sum(1 for p in d.paragraphs if p.style.name.startswith("Heading")))


if __name__ == "__main__":
    main()
