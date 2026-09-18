#!/usr/bin/env python3
"""Geometric sanity check for the generated deck: does any text overflow its
container or leave the slide? Uses real CJK font metrics (wqy-zenhei) to measure
each paragraph, so it catches the "text spills off the slide" failure mode that a
visual check would catch -- without needing a vision model.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageFont
from pptx import Presentation
from pptx.util import Emu

DEL = Path("/root/autodl-tmp/monkeyocr-repro/outputs/deliverables")
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
EMU_PER_PX = 9525

_cache: dict[int, ImageFont.FreeTypeFont] = {}


def font(size_pt: float):
    px = max(10, int(size_pt * 96 / 72))
    if px not in _cache:
        _cache[px] = ImageFont.truetype(CJK, px)
    return _cache[px]


def main() -> None:
    prs = Presentation(str(DEL / "汇报材料.pptx"))
    W = prs.slide_width / EMU_PER_PX
    H = prs.slide_height / EMU_PER_PX
    problems: list[str] = []
    print(f"slide = {W:.0f} x {H:.0f} px (from {prs.slide_width}x{prs.slide_height} EMU)")

    for idx, slide in enumerate(prs.slides, 1):
        print(f"\n--- slide {idx}")
        for sh in slide.shapes:
            x, y = sh.left / EMU_PER_PX, sh.top / EMU_PER_PX
            w, h = sh.width / EMU_PER_PX, sh.height / EMU_PER_PX
            if x < 0 or y < 0 or x + w > W + 1 or y + h > H + 1:
                problems.append(f"slide{idx}: shape box outside slide: x={x:.0f} y={y:.0f} w={w:.0f} h={h:.0f}")
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            # measure the wrapped text height by summing rendered line heights
            total_h = 0.0
            for p in sh.text_frame.paragraphs:
                txt = "".join(r.text for r in p.runs)
                if not txt.strip():
                    continue
                size = next((r.font.size.pt for r in p.runs if r.font.size), 18)
                f = font(size)
                # wrap to the shape width
                words = list(txt)
                line, lines = "", 1
                for ch in words:
                    if f.getlength(line + ch) > w - 6:
                        lines += 1
                        line = ch
                    else:
                        line += ch
                total_h += lines * (size * 96 / 72) * 1.25 + 6
            bottom = y + total_h
            flag = "OK " if bottom <= H - 6 else "OVERFLOW"
            if bottom > H - 6:
                problems.append(f"slide{idx}: text bottom {bottom:.0f}px exceeds slide {H:.0f}px: "
                                f"{sh.text_frame.text.strip()[:40]!r}")
            print(f"  {flag} box=({x:.0f},{y:.0f},{w:.0f}x{h:.0f}) text_h={total_h:.0f} "
                  f"bottom={bottom:.0f} :: {sh.text_frame.text.strip()[:48]!r}")

    print("\n=== RESULT ===")
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
    else:
        print("no overflow / out-of-slide shapes detected")


if __name__ == "__main__":
    main()
