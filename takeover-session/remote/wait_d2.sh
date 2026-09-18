#!/bin/bash
for i in $(seq 1 28); do
  if ! pgrep -f 'install_detectron2.sh' > /dev/null; then break; fi
  sleep 20
done
echo "=== running? ==="; pgrep -af 'install_detectron2|pip install|ninja' | grep -v pgrep | head -3
echo "=== tail 30 ==="
tail -30 /root/autodl-tmp/monkeyocr-repro/outputs/env_detectron2.log
