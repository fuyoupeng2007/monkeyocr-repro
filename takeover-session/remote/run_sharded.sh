#!/bin/bash
# Two sharded MinerU workers (2 is enough: PaddleOCR stages are CPU-heavy and the
# shared host already runs at load ~15-33).
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/mineru_sharded.log
exec > >(tee -a "$LOG") 2>&1
echo "### sharded run (2 workers) started $(date -Is)"

SUBSET=$PROJ/data/omnidocbench_v1_0/subsets
OUT=$PROJ/outputs/mineru_formal_120
mkdir -p "$OUT"

for S in 0 1; do
  setsid nohup $PY $PROJ/scripts/run_batch_sharded.py \
    --manifest "$SUBSET/manifest_120.jsonl" \
    --pdf-root "$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs" \
    --output-root "$OUT" \
    --magic-pdf "$ENV/bin/magic-pdf" \
    --config "$PROJ/configs/mineru093/magic-pdf.json" \
    --shard $S --shards 2 --timeout 900 > "$OUT/shard_$S.log" 2>&1 < /dev/null &
  echo "shard $S pid=$!"
  sleep 10
done

while pgrep -f run_batch_sharded.py > /dev/null; do
  N=$(find "$OUT/predictions" -name '*.md' -size +0 2>/dev/null | wc -l)
  echo "[$(date +%H:%M:%S)] non-empty predictions=$N/120"
  sleep 300
done
echo "### shards finished $(date -Is)"
echo "predictions: $(ls "$OUT/predictions" | wc -l)/120 ; non-empty: $(find "$OUT/predictions" -name '*.md' -size +0 | wc -l)"
