#!/bin/bash
# Wait for the MinerU workers, then run the whole tail of the pipeline:
# adapter -> official evaluation -> comparison table -> Chinese deliverables.
# Idempotent and safe to run repeatedly.
set -u
PROJ=/root/autodl-tmp/monkeyocr-repro
OUT=$PROJ/outputs/mineru_formal_120
PY_M=${PROJ}/../conda_envs/mineru093_env/bin/python
PY_M=/root/autodl-tmp/conda_envs/mineru093_env/bin/python
PY_O=/root/autodl-tmp/conda_envs/omnidocbench/bin/python
LOG=$PROJ/outputs/pipeline_tail.log
exec > >(tee -a "$LOG") 2>&1
echo "### pipeline tail watcher started $(date -Is)"

for i in $(seq 1 240); do          # up to ~10 h
  if ! pgrep -f 'run_batch_sharded\.py' > /dev/null; then break; fi
  N=$(find "$OUT/predictions" -name '*.md' -size +0 2>/dev/null | wc -l)
  echo "[$(date +%H:%M:%S)] non-empty predictions=$N/120"
  sleep 150
done
echo "### workers finished $(date -Is)"
echo "predictions: $(ls "$OUT/predictions" 2>/dev/null | wc -l)/120 ; non-empty: $(find "$OUT/predictions" -name '*.md' -size +0 2>/dev/null | wc -l)"

echo "### adapter pass $(date -Is)"
$PY_M $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest $PROJ/data/omnidocbench_v1_0/subsets/manifest_120.jsonl \
  --raw-root "$OUT/raw" --pred-dir "$OUT/predictions" 2>&1 | tail -20
echo "### after adapter: non-empty=$(find "$OUT/predictions" -name '*.md' -size +0 | wc -l)/120"

echo "### official evaluation (both baselines, isolated result prefixes) $(date -Is)"
bash $PROJ/scripts/reeval_both.sh
echo "### pipeline tail finished $(date -Is)"
