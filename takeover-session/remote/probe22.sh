#!/bin/bash
echo "=== detectron2 install progress ==="
pgrep -af 'install_detectron2|pip install|ninja|setup.py' | grep -v pgrep | head -5
tail -12 /root/autodl-tmp/monkeyocr-repro/outputs/env_detectron2.log
echo
echo "=== GPU ==="
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
