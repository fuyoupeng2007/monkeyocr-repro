"""Extract the MonkeyOCR paper text so the explanation is grounded in the source.

The reproduction folder ships MonkeyOCR_2025_v1.pdf plus a text extraction; we read
the text file when present and fall back to extracting the PDF with pypdf.
"""
from __future__ import annotations

import sys
from pathlib import Path

CANDIDATES = [
    Path(r"D:\chatgpt\刘禹良团队_入组调研与复现审批\论文\MonkeyOCR_2025_v1.pdf"),
    Path(r"D:\chatgpt\刘禹良团队_入组调研与复现审批\复现工程\MonkeyOCR_2025_v1.pdf"),
    Path(r"D:\haeness\monkeyocr-takeover\sync\MonkeyOCR_2025_v1.txt"),
]
OUT = Path(r"D:\haeness\monkeyocr-takeover\paper_text.txt")


def main() -> int:
    for p in CANDIDATES:
        if not p.exists():
            continue
        if p.suffix.lower() == ".txt":
            text = p.read_text(encoding="utf-8", errors="ignore")
            print(f"read text file: {p} ({len(text)} chars)")
        else:
            try:
                from pypdf import PdfReader
            except ImportError:
                print("pypdf missing")
                return 1
            reader = PdfReader(str(p))
            pages = []
            for i, page in enumerate(reader.pages, 1):
                try:
                    pages.append(f"\n===== PAGE {i} =====\n" + (page.extract_text() or ""))
                except Exception as e:
                    pages.append(f"\n===== PAGE {i} (extract failed: {e}) =====\n")
            text = "\n".join(pages)
            print(f"extracted PDF: {p} -> {len(reader.pages)} pages, {len(text)} chars")
        OUT.write_text(text, encoding="utf-8")
        print("written:", OUT)
        # quick structure probe
        for kw in ["Abstract", "Introduction", "Related Work", "Method", "Experiment",
                   "Conclusion", "OmniDocBench", "TEDS", "Edit Distance", "LMDeploy",
                   "structure-aware", "Relation", "Layout", "Dataset"]:
            hits = text.count(kw)
            if hits:
                print(f"  '{kw}': {hits}")
        return 0
    print("no paper source found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
