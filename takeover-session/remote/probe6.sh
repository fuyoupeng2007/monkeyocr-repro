#!/bin/bash
echo "===== rebuild progress ====="
tail -5 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_0946.log 2>/dev/null
echo "--- pip procs:"; pgrep -af 'pip install' | head -3
echo "--- new env site-packages count:"; ls /root/autodl-tmp/conda_envs/mineru093_env/lib/python3.10/site-packages 2>/dev/null | wc -l
echo "--- du new env:"; du -sh /root/autodl-tmp/conda_envs/mineru093_env 2>/dev/null
echo
echo "===== ALL report-ish artifacts in project ====="
find /root/autodl-tmp/monkeyocr-repro -maxdepth 2 -type f \( -name '*.md' -o -name '*.json' -o -name '*.yaml' -o -name '*.txt' \) -printf '%TY-%Tm-%Td %TH:%TM %8s %p\n' | sort -r | head -50
echo
echo "===== outputs/ subdirs (2 levels) ====="
find /root/autodl-tmp/monkeyocr-repro/outputs -maxdepth 2 -type d -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -r | head -40
echo
echo "===== OmniDocBench/result ====="
ls -la /root/autodl-tmp/monkeyocr-repro/OmniDocBench/result/ 2>/dev/null | head -30
echo
echo "===== data dir ====="
find /root/autodl-tmp/monkeyocr-repro/data -maxdepth 3 -type d | head -20
echo "--- manifests:"; ls -la /root/autodl-tmp/monkeyocr-repro/data/omnidocbench_v1_0/ 2>/dev/null | head -20
