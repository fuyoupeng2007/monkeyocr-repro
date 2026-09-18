#!/bin/bash
# wait for finish_env_v3b.sh to complete, then show the final report
for i in $(seq 1 17); do
  if ! pgrep -f 'finish_env_v3b.sh' > /dev/null; then break; fi
  sleep 30
done
echo "=== running? ==="
pgrep -af 'finish_env_v3b|pip install' | grep -v pgrep | head -3
echo "=== log tail 60 ==="
tail -60 /root/autodl-tmp/monkeyocr-repro/outputs/env_finish_v3b.log
echo "=== env size ==="
du -sh /root/autodl-tmp/conda_envs/mineru093_env
