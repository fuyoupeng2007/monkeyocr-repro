#!/bin/bash
L=/root/autodl-tmp/monkeyocr-repro/outputs/env_finish_v3b.log
echo "=== FAILED markers with context ==="
grep -n "### .*FAILED" "$L"
echo
echo "=== ERROR lines ==="
grep -n "^ERROR:\|Cannot install\|conflicting dependencies\|ResolutionImpossible\|No matching distribution" "$L" | head -30
echo
echo "=== section around first FAILED ==="
N=$(grep -n "### requirements FAILED\|### full extra FAILED\|### paddlepaddle FAILED" "$L" | head -1 | cut -d: -f1)
if [ -n "$N" ]; then sed -n "$((N-45)),$((N+3))p" "$L"; fi
