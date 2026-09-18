#!/bin/bash
for i in $(seq 1 17); do
  if ! pgrep -f 'place_pins.sh' > /dev/null; then break; fi
  sleep 30
done
echo "=== running? ==="; pgrep -af 'place_pins|pip install' | grep -v pgrep | head -3
echo "=== FAILED markers ==="; grep -n '###.*FAILED' /root/autodl-tmp/monkeyocr-repro/outputs/env_final_pins.log
echo "=== final report ==="
sed -n '/=== FINAL ENV REPORT ===/,$p' /root/autodl-tmp/monkeyocr-repro/outputs/env_final_pins.log | head -40
echo "=== errors ==="; grep -c "^ERROR: " /root/autodl-tmp/monkeyocr-repro/outputs/env_final_pins.log
