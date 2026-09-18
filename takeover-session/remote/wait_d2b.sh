#!/bin/bash
for i in $(seq 1 20); do
  if ! pgrep -f 'install_detectron2_b.sh' > /dev/null; then break; fi
  sleep 20
done
echo "=== running? ==="; pgrep -af 'install_detectron2_b|git clone|pip install' | grep -v pgrep | head -3
echo "=== log ==="
cat /root/autodl-tmp/monkeyocr-repro/outputs/env_detectron2_b.log
