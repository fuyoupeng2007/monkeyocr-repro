#!/bin/bash
# Real end-to-end smoke: load every model, run 1 page, emit Markdown.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/smoke_v3.log
exec > >(tee -a "$LOG") 2>&1
echo "### smoke v3 started $(date -Is)"

PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
echo "page: $(basename "$PDF")"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### magic-pdf rc=$?"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
MD=$(find "$OUT" -name '*.md' | head -1)
echo "=== markdown: $MD ==="
if [ -n "$MD" ]; then
  echo "chars=$(wc -c < "$MD")  html_tables=$(grep -c '<table' "$MD" || true)"
  head -c 800 "$MD"; echo
else
  echo "NO MARKDOWN PRODUCED"
fi
echo "=== adapter on this page ==="
$PY $PROJ/scripts/mineru_to_omnidocbench_md.py \
  --manifest <(echo '{"image_path":"jiaocaineedrop_jiaocai_needrop_en_2211.jpg"}') \
  --raw-root "$OUT" --pred-dir "$OUT/pred_check" 2>&1 | tail -12
echo "### smoke v3 done $(date -Is)"
