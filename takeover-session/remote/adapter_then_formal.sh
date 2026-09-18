#!/bin/bash
# Adapter check on the smoke output, then launch the formal 120-page MinerU run.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/adapter_check_then_formal.log
exec > >(tee -a "$LOG") 2>&1
echo "### adapter check $(date -Is)"

# 1) adapter on the smoke page
printf '%s\n' '{"image_path":"jiaocaineedrop_jiaocai_needrop_en_2211.jpg"}' > /tmp/one_page_manifest.jsonl
$PY $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest /tmp/one_page_manifest.jsonl \
  --raw-root "$PROJ/outputs/mineru_smoke_iso" \
  --pred-dir "$PROJ/outputs/mineru_smoke_iso/pred_check" 2>&1 | tail -12
echo "--- adapted prediction head:"
head -c 400 "$PROJ/outputs/mineru_smoke_iso/pred_check/jiaocaineedrop_jiaocai_needrop_en_2211.md" 2>/dev/null
echo

# 2) formal 120-page run (same manifest/subset as the MonkeyOCR formal run)
echo "### formal 120-page MinerU run starting $(date -Is)"
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
echo "### batch rc=$?"

echo "### rebuilding predictions from raw output $(date -Is)"
$PY $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest "$SUBSET/manifest_120.jsonl" \
  --raw-root "$OUT/raw" \
  --pred-dir "$OUT/predictions" 2>&1 | tail -15

echo "=== run_log summary ==="
$PY - <<PY
import json, collections
rows=[json.loads(l) for l in open("$OUT/run_log.jsonl",encoding="utf-8") if l.strip()]
c=collections.Counter(r["status"] for r in rows)
secs=[r["seconds"] for r in rows if r.get("seconds")]
print("pages:",len(rows),dict(c))
if secs:
    s=sorted(secs); print(f"per-page s: min={s[0]:.1f} median={s[len(s)//2]:.1f} max={s[-1]:.1f} total={sum(secs)/60:.1f} min")
errs=[r for r in rows if r["status"]=="error"]
for e in errs[:5]: print("ERR:", e["stem"], e.get("error"))
PY
echo "### formal 120 done $(date -Is)"
