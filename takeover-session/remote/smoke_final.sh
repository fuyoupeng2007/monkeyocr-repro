#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/smoke_final.log
exec > >(tee -a "$LOG") 2>&1
echo "### final smoke started $(date -Is)"

$PY -m pip install --no-deps tabulate numkong 2>&1 | tail -2

echo "=== IMPORT CHECK ==="
$PY - <<'PY'
import importlib
mods = ["torch","torchvision","transformers","magic_pdf","timm","ultralytics",
        "struct_eqtable","rapid_table","paddleocr","paddle","unimernet",
        "doclayout_yolo","detectron2","cv2","sklearn","numpy","pandas"]
bad=[]
for name in mods:
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:15s} {str(getattr(m,'__version__','?')):12s}")
    except Exception as e:
        print(f"FAIL {name:15s} {type(e).__name__}: {e}")
        bad.append(name)
print("STILL FAILING =", bad)
PY

echo
echo "=== SMOKE: magic-pdf on one OmniDocBench page ==="
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
echo "pdf=$PDF  (same page that failed at 09:41 and 09:43)"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### magic-pdf rc=$? (0 = success)"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
echo
echo "=== markdown head (first 900 chars) ==="
MD=$(find "$OUT" -name '*.md' | head -1)
echo "md=$MD"
if [ -n "$MD" ]; then head -c 900 "$MD"; echo; echo "--- chars: $(wc -c < "$MD")"; fi
echo "=== tables / formulas found ==="
if [ -n "$MD" ]; then
  echo "table tags: $(grep -c '<table' "$MD" || true)"
  echo "display formulas: $(grep -c '\$\$' "$MD" || true)"
fi
echo "### final smoke done $(date -Is)"
