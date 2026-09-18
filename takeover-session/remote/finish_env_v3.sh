#!/bin/bash
# Finish the isolated MinerU 0.9.3 env WITHOUT letting pip drag torch down to 2.3.1.
#
# magic-pdf[full]==0.9.3 declares torch<=2.3.1,>=2.2.2.  MonkeyOCR runs on
# torch 2.5.1+cu124 and the container driver is CUDA 13 capable, so we keep
# 2.5.1+cu124 for both experiments (same torch = one less confound) and install
# MinerU's other pinned requirements explicitly instead of via the [full] extra.
set -x
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PIP="$ENV/bin/python -m pip"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_finish_v3.log
exec > >(tee -a "$LOG") 2>&1
echo "### finish started $(date -Is)"

$PIP list 2>/dev/null | grep -Ei '^(torch|torchvision|numpy|opencv|magic-pdf|transformers|detectron2|paddle|timm|ultralytics) '

# 1) magic-pdf itself: no dependency resolution, we place deps by hand
$PIP install --no-deps "magic-pdf[full]==0.9.3" || echo "### magic-pdf core FAILED"

# 2) magic-pdf's declared runtime requirements (numpy kept <2 as it pins)
$PIP install \
  "numpy>=1.21.6,<2.0.0" \
  "boto3>=1.28.43" \
  "loguru>=0.6.0" \
  "PyMuPDF>=1.24.9" \
  "pdfminer.six==20231228" \
  "pypdf>=4.0.0" \
  "python-docx>=0.8.11" \
  "doclayout-yolo==0.0.4" \
  "fast-langdetect==0.2.0" \
  "pydantic>=2.7.2,<2.8.0" \
  "scikit-learn>=1.0.2" \
  "shapely>=2.0.4" \
  "torchvision" \
  || echo "### core req FAILED"

# 3) full-extra model backends (the actual layout / formula / OCR / table models)
$PIP install \
  "timm==1.0.29" \
  "ultralytics" \
  "unimernet==0.2.1" \
  "rapidocr-paddle" \
  "rapid-table==3.0.2" \
  "paddleocr" \
  || echo "### extras FAILED"

# 4) verification inside the isolated env
"$ENV/bin/python" - <<'PY'
import sys, importlib
print("prefix =", sys.prefix)
print("py     =", sys.version.split()[0])
bad = []
for name in ("torch","torchvision","transformers","click","magic_pdf","timm","ultralytics",
             "struct_eqtable","rapid_table","paddleocr","unimernet","doclayout_yolo",
             "detectron2","fitz","sklearn","numpy","pydantic"):
    try:
        m = importlib.import_module(name)
        f = getattr(m, "__file__", "?") or "?"
        print(f"{name:15s} {str(getattr(m,'__version__','?')):12s} {f}")
        if "monkeyocr" in f: bad.append((name, f))
    except Exception as e:
        print(f"{name:15s} IMPORT FAILED: {e!r}")
print("OUT-OF-ENV =", bad)
import torch; print("cuda available:", torch.cuda.is_available(), torch.version.cuda)
PY
echo "### finish done $(date -Is)"
