#!/bin/bash
cd /root/autodl-tmp/monkeyocr-repro || exit 1
echo "=== MinerU_0.9.3/requirements.txt ==="
cat MinerU_0.9.3/requirements.txt
echo
echo "=== MinerU_0.9.3/setup.py extras ==="
grep -n -A40 'extras_require\|install_requires' MinerU_0.9.3/setup.py | head -70
