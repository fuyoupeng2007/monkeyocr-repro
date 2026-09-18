#!/bin/bash
cd /root/autodl-tmp/monkeyocr-repro || exit 1
echo "=== OmniDocBench entrypoints ==="
ls OmniDocBench/
sed -n '1,40p' OmniDocBench/README.md | grep -n -i "python\|run\|eval" | head -20
echo
echo "=== how eval was invoked before (bash history) ==="
grep -n "OmniDocBench\|end2end" /root/.bash_history | tail -12
echo
echo "=== config merge/end2end yaml ==="
ls OmniDocBench/configs/ 2>/dev/null
cat OmniDocBench/configs/end2end.yaml 2>/dev/null | head -30
echo
echo "=== omnidocbench env python ==="
/root/autodl-tmp/conda_envs/omnidocbench/bin/python -c "import sys;print(sys.version)" 2>&1 | head -3
