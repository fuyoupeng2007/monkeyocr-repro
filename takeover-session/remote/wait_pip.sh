#!/bin/bash
# wait for any running pip to finish (max ~9 min), then report env state
for i in $(seq 1 18); do
  if ! pgrep -f 'pip install' > /dev/null; then break; fi
  sleep 30
done
echo "=== pip still running? ==="
pgrep -af 'pip install' | grep -v pgrep | head -2
echo "=== rebuild log tail 15 ==="
tail -15 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
echo "=== env size ==="
du -sh /root/autodl-tmp/conda_envs/mineru093_env
