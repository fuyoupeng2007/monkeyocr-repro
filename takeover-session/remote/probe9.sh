#!/bin/bash
echo "=== rebuild procs ==="
pgrep -af 'rebuild_mineru_env_v3|pip install' | grep -v pgrep | head -5
echo "=== rebuild log tail ==="
tail -12 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
echo "=== env size ==="
du -sh /root/autodl-tmp/conda_envs/mineru093_env 2>/dev/null
echo "=== disk ==="
df -h /root/autodl-tmp | tail -1
echo "=== tmp leftovers (should be cleaned) ==="
ls -la /tmp/tmp* /tmp/pip-unpack-* 2>/dev/null | head -8
