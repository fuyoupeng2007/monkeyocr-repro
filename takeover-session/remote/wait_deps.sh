#!/bin/bash
for i in $(seq 1 17); do
  if ! pgrep -f 'fix_deps.sh' > /dev/null; then break; fi
  sleep 30
done
echo "=== running? ==="; pgrep -af 'fix_deps|pip install' | grep -v pgrep | head -3
echo "=== import check result ==="
sed -n '/=== IMPORT CHECK ===/,$p' /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop.log | head -25
echo "=== rounds ==="
grep -n '^--- round' /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop.log
