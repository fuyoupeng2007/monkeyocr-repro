#!/bin/bash
# wait for the conda rebuild to finish, then report
for i in $(seq 1 40); do
  if ! pgrep -f 'rebuild_mineru_env_v3.sh' > /dev/null; then break; fi
  sleep 30
done
echo "=== rebuild procs after wait ==="
pgrep -af 'rebuild_mineru_env_v3|pip install' | grep -v pgrep | head -3
echo "=== tail 40 ==="
tail -40 /root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
echo "=== env size ==="
du -sh /root/autodl-tmp/conda_envs/mineru093_env 2>/dev/null
