import sys
from docx import Document

sys.stdout.reconfigure(encoding="utf-8")

targets = [
    ("deliverables/给导师的汇报_MonkeyOCR复现与MinerU基线.docx", "附录 A"),
    ("deliverables/给你讲明白_这个实验到底做了什么.docx", "四、那 39 页"),
]
for path, key in targets:
    d = Document(path)
    ps = [p.text for p in d.paragraphs]
    idx = next((i for i, t in enumerate(ps) if key in t), None)
    print("=" * 72)
    print("文件:", path.split("/")[-1])
    if idx is not None:
        shown = 0
        for t in ps[idx:idx + 12]:
            if t.strip():
                print("  ", t[:120])
                shown += 1
            if shown >= 6:
                break
    else:
        print("  未找到锚点:", key)
