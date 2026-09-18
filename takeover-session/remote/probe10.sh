#!/bin/bash
cd /root/autodl-tmp/monkeyocr-repro || exit 1
echo "=== MonkeyOCR prediction vs GT structure (page 1 of subset) ==="
/root/autodl-tmp/conda_envs/monkeyocr/bin/python - <<'PY'
import json
gt = json.load(open("data/omnidocbench_v1_0/subsets/formal_120.json", encoding="utf-8"))
print("GT type:", type(gt), "len:", len(gt))
page = gt[0]
print("GT page keys:", list(page.keys()))
for k, v in page.items():
    if isinstance(v, str):
        print(f"  {k}: str len={len(v)} :: {v[:300]!r}")
    else:
        print(f"  {k}: {type(v)} -> {str(v)[:300]}")
PY
echo
echo "=== OmniDocBench end2end dataset loader expectations ==="
sed -n '1,80p' OmniDocBench/omnidocbench/dataset/end2end_dataset.py 2>/dev/null || find OmniDocBench -name 'end2end_dataset.py' | head
