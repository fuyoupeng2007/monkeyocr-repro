#!/bin/bash
for i in $(seq 1 15); do
  if ! pgrep -f 'fix_leaf_and_smoke.sh' > /dev/null; then break; fi
  sleep 20
done
echo "=== running? ==="; pgrep -af 'fix_leaf_and_smoke|magic-pdf' | grep -v pgrep | head -3
echo "=== leaf log: pip tail ==="
sed -n '1,25p' /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_leaf.log
echo "=== IMPORT CHECK + SMOKE ==="
sed -n '/=== IMPORT CHECK ===/,$p' /root/autodl-tmp/monkeyocr-repro/outputs/env_deps_leaf.log | head -80
