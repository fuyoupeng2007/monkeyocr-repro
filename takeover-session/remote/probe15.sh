#!/bin/bash
echo "=== procs ==="
pgrep -af 'pip install' | grep -v pgrep | head -3
echo "=== log size / tail 3 ==="
ls -la /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
tail -3 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
echo "=== inflight downloads (size twice, 15s apart) ==="
find /tmp -maxdepth 2 -type f -size +5M -printf '%s %p\n' 2>/dev/null | sort -rn | head -3
sleep 15
echo "--- after 15s ---"
find /tmp -maxdepth 2 -type f -size +5M -printf '%s %p\n' 2>/dev/null | sort -rn | head -3
echo "=== env site-packages count ==="
ls /root/autodl-tmp/conda_envs/mineru093_env/lib/python3.10/site-packages | wc -l
