#!/bin/bash
# Wait for all MinerU workers to finish, then run the official OmniDocBench
# evaluation and rebuild the comparison table. Idempotent: if the eval result
# already exists it is refreshed anyway (cheap compared to the parse run).
set -u
PROJ=/root/autodl-tmp/monkeyocr-repro
OUT=$PROJ/outputs/mineru_formal_120
LOG=$PROJ/outputs/watch_then_eval.log
exec > >(tee -a "$LOG") 2>&1
echo "### watcher started $(date -Is)"

while pgrep -f 'run_batch_(sharded|mineru_iso)\.py' > /dev/null; do
  N=$(find "$OUT/predictions" -name '*.md' -size +0 2>/dev/null | wc -l)
  T=$(ls "$OUT/predictions" 2>/dev/null | wc -l)
  echo "[$(date +%H:%M:%S)] parsed=$T/120 non-empty=$N"
  sleep 240
done
echo "### workers done $(date -Is)"

# rebuild predictions from raw output (fill in anything a crashed worker missed)
/root/autodl-tmp/conda_envs/mineru093_env/bin/python $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest $PROJ/data/omnidocbench_v1_0/subsets/manifest_120.jsonl \
  --raw-root "$OUT/raw" --pred-dir "$OUT/predictions" 2>&1 | tail -20

echo "### running official evaluation $(date -Is)"
bash $PROJ/scripts/run_eval_mineru120.sh
echo "### rebuilding comparison table $(date -Is)"
/root/autodl-tmp/conda_envs/omnidocbench/bin/python $PROJ/scripts/build_comparison.py
echo "### watcher finished $(date -Is)"
