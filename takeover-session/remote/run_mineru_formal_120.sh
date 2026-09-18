#!/bin/bash
# MinerU 0.9.3 formal 120-page run through the isolated env, then OmniDocBench eval.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
LOG=$PROJ/outputs/mineru_formal_120.log
exec > >(tee -a "$LOG") 2>&1
echo "### MinerU formal 120 started $(date -Is)"

SUBSET=$PROJ/data/omnidocbench_v1_0/subsets
OUT=$PROJ/outputs/mineru_formal_120
mkdir -p "$OUT"

$PY $PROJ/scripts/run_batch_mineru_iso.py \
  --manifest "$SUBSET/manifest_120.jsonl" \
  --pdf-root "$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs" \
  --output-root "$OUT" \
  --magic-pdf "$ENV/bin/magic-pdf" \
  --config "$PROJ/configs/mineru093/magic-pdf.json" \
  --timeout 900
echo "### batch exit=$?"

# rebuild predictions straight from the raw output (idempotent, catches partial runs)
$PY $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest "$SUBSET/manifest_120.jsonl" \
  --raw-root "$OUT/raw" \
  --pred-dir "$OUT/predictions"
echo "### adapter exit=$?"

echo "=== run_log summary ==="
$PY - <<PY
import json, collections
rows=[json.loads(l) for l in open("$OUT/run_log.jsonl",encoding="utf-8") if l.strip()]
c=collections.Counter(r["status"] for r in rows)
secs=[r["seconds"] for r in rows if r.get("seconds")]
print("pages:",len(rows),dict(c))
if secs: print(f"per-page s: min={min(secs):.1f} median={sorted(secs)[len(secs)//2]:.1f} max={max(secs):.1f} total={sum(secs)/60:.1f} min")
PY
echo "### MinerU formal 120 done $(date -Is)"
