#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
export PIP_DISABLE_PIP_VERSION_CHECK=1
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop2.log
exec > >(tee -a "$LOG") 2>&1
echo "### deps round 2 started $(date -Is)"

$PY -m pip install --no-deps "pytz" "pyparsing" "protobuf" "python-dateutil" \
  "rapidfuzz" "Pillow" "requests" "PyYAML" "tqdm" "six" "packaging" "chardet" \
  "cython" "pycryptodome" "imghdr" "shapely" "scikit-image" "onnxruntime" || true

echo "=== DEEP IMPORT CHECK (real imports) ==="
$PY - <<'PY'
import importlib
mods = ["torch","torchvision","transformers","magic_pdf","timm","ultralytics",
        "struct_eqtable","rapid_table","paddleocr","paddle","unimernet",
        "doclayout_yolo","cv2","sklearn","numpy","omegaconf","decorator","psutil",
        "torchmetrics","pycocotools","fitz","pandas"]
bad = []
for name in mods:
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:16s} {str(getattr(m,'__version__','?')):12s}")
    except Exception as e:
        print(f"FAIL {name:16s} {type(e).__name__}: {e}")
        bad.append(name)
print("STILL FAILING =", bad)
PY

echo "=== magic_pdf CLI import test ==="
$PY -c "from magic_pdf.tools.cli import cli; print('cli import OK')" 2>&1 | tail -5
echo "### deps round 2 done $(date -Is)"
