#!/bin/bash
# Speed up the 120-page MinerU run: only ~5GB VRAM is used per process, so run 4
# workers concurrently. The runner is resume-safe (skip-if-prediction-exists), so
# workers simply race over the same manifest without duplicating finished pages.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/mineru_parallel.log
exec > >(tee -a "$LOG") 2>&1
echo "### parallel runner (4 workers) started $(date -Is)"

SUBSET=$PROJ/data/omnidocbench_v1_0/subsets
OUT=$PROJ/outputs/mineru_formal_120
mkdir -p "$OUT"

for W in 1 2 3 4; do
  setsid nohup $PY $PROJ/scripts/run_batch_mineru_iso.py \
    --manifest "$SUBSET/manifest_120.jsonl" \
    --pdf-root "$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs" \
    --output-root "$OUT" \
    --magic-pdf "$ENV/bin/magic-pdf" \
    --config "$PROJ/configs/mineru093/magic-pdf.json" \
    --timeout 900 > "$OUT/worker_$W.log" 2>&1 < /dev/null &
  echo "worker $W pid=$!"
  sleep 8
done

# wait for all workers
while pgrep -f run_batch_mineru_iso.py > /dev/null; do
  DONE=$(ls "$OUT/predictions" 2>/dev/null | wc -l)
  LOAD=$(uptime | sed 's/.*average//')
  echo "[$(date +%H:%M:%S)] predictions=$DONE/120 load=$LOAD"
  sleep 120
done
echo "### all workers finished $(date -Is)"
echo "predictions: $(ls "$OUT/predictions" | wc -l)/120"
echo "non-empty: $(find "$OUT/predictions" -name '*.md' -size +0 | wc -l)"
