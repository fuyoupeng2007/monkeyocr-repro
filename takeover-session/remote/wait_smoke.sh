#!/bin/bash
for i in $(seq 1 15); do
  if ! pgrep -f 'verify_and_smoke.sh' > /dev/null; then break; fi
  sleep 20
done
echo "=== running? ==="; pgrep -af 'verify_and_smoke|magic-pdf' | grep -v pgrep | head -3
echo "=== log ==="
sed -n '/=== IMPORT CHECK ===/,$p' /root/autodl-tmp/monkeyocr-repro/outputs/env_verify_smoke.log | head -70
