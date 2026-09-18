#!/bin/bash
cd /root/autodl-tmp/monkeyocr-repro || exit 1
echo "=== one MonkeyOCR prediction ==="
f=$(ls outputs/monkeyocr_formal_120/predictions/*.md | head -1)
echo "file: $f"
head -c 900 "$f"
echo
echo
echo "=== pages dir sample ==="
d=$(ls -d outputs/monkeyocr_formal_120/pages/* | head -1)
echo "dir: $d"; ls -la "$d" | head -12
echo
echo "=== run_log first 3 ==="
head -3 outputs/monkeyocr_formal_120/run_log.jsonl
echo
echo "=== provenance.json ==="
cat data/omnidocbench_v1_0/subsets/provenance.json
echo
echo "=== manifest_120 first 2 ==="
head -2 data/omnidocbench_v1_0/subsets/manifest_120.jsonl
echo
echo "=== rebuild progress ==="
tail -3 outputs/env_rebuild_v3.log
echo "=== GPU / py procs ==="
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
