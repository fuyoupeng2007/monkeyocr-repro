#!/bin/bash
echo "=== rebuild procs ==="
pgrep -af 'rebuild_mineru_env_v3|pip install' | grep -v pgrep | head -3
echo "=== rebuild log tail 25 ==="
tail -25 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
echo "=== env size / disk ==="
du -sh /root/autodl-tmp/conda_envs/mineru093_env 2>/dev/null
df -h /root/autodl-tmp | tail -1
