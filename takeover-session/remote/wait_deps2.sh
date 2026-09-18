#!/bin/bash
for i in $(seq 1 12); do
  if ! pgrep -f 'fix_deps2.sh' > /dev/null; then break; fi
  sleep 20
done
echo "=== running? ==="; pgrep -af 'fix_deps2|pip install' | grep -v pgrep | head -3
echo "=== deep import check ==="
sed -n '/=== DEEP IMPORT CHECK/,$p' /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop2.log | head -30
