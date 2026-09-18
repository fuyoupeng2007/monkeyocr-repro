#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_verify_smoke.log
exec > >(tee -a "$LOG") 2>&1
echo "### verify+smoke started $(date -Is)"

$PY -m pip install --no-deps scikit-image onnxruntime 2>&1 | tail -2

echo "=== IMPORT CHECK ==="
$PY - <<'PY'
import importlib
mods = ["torch","torchvision","transformers","magic_pdf","timm","ultralytics",
        "struct_eqtable","rapid_table","paddleocr","paddle","unimernet",
        "doclayout_yolo","cv2","sklearn","numpy","pandas","torchmetrics","pycocotools"]
bad=[]
for name in mods:
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:16s} {str(getattr(m,'__version__','?')):12s}")
    except Exception as e:
        print(f"FAIL {name:16s} {type(e).__name__}: {e}")
        bad.append(name)
print("STILL FAILING =", bad)
PY

echo
echo "=== SMOKE: single page through magic-pdf ==="
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
echo "pdf=$PDF"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### magic-pdf exit=$?"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
echo "=== markdown head ==="
MD=$(find "$OUT" -name '*.md' | head -1)
echo "md=$MD"
[ -n "$MD" ] && head -c 1200 "$MD"
echo
echo "### verify+smoke done $(date -Is)"
