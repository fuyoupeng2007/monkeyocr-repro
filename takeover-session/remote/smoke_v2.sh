#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/smoke_v2.log
exec > >(tee -a "$LOG") 2>&1
echo "### smoke v2 started $(date -Is)"

# albumentations 2.x dropped numpy<2 support (KeyError: numpy.uint32);
# unimernet 0.2.1 is a 2024-era release -> pin the 1.4.x line.
$PY -m pip install --no-deps "albumentations==1.4.24" "albucore==0.0.24" pydantic 2>&1 | tail -2

echo "=== unimernet import (the last blocker) ==="
$PY -c "
import importlib
for n in ('unimernet','albumentations'):
    try:
        m=importlib.import_module(n); print('OK  ',n, getattr(m,'__version__','?'))
    except Exception as e: print('FAIL',n,type(e).__name__,e)
"

echo
echo "=== SMOKE: magic-pdf on the page that failed before ==="
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### magic-pdf rc=$?"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
MD=$(find "$OUT" -name '*.md' | head -1)
echo "=== markdown: $MD ==="
if [ -n "$MD" ]; then
  echo "chars=$(wc -c < "$MD")  html_tables=$(grep -c '<table' "$MD" || true)  display_formulas=$(grep -c '\$\$' "$MD" || true)"
  head -c 700 "$MD"; echo
fi
echo "### smoke v2 done $(date -Is)"
