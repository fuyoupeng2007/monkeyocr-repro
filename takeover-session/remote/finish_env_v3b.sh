#!/bin/bash
# Finish the isolated MinerU 0.9.3 environment.
#
# Pins follow MinerU 0.9.3's OWN setup.py [full] extra (the authoritative list):
#   unimernet==0.2.1 (needs timm>=0.9.16,<0.10 -> so timm 0.9.x, NOT 1.0.x),
#   doclayout_yolo==0.0.2, paddleocr==2.7.3, paddlepaddle==3.0.0b1,
#   struct-eqtable==0.3.2, einops, accelerate, rapidocr-paddle, rapid_table,
#   ultralytics, PyYAML, matplotlib.
# Deliberately NOT reproduced from the old broken env: timm==1.0.29 (violates
# unimernet's bound) and the torch<=2.3.1 pin (we keep 2.5.1+cu124 so both
# experiments share one torch).
set -x
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PIP="$ENV/bin/python -m pip"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_finish_v3b.log
exec > >(tee -a "$LOG") 2>&1
echo "### finish v3b started $(date -Is)"

# 1) MinerU core without dependency resolution (requirements.txt deps placed by hand)
$PIP install --no-deps "magic-pdf[full]==0.9.3" || echo "### magic-pdf core FAILED"

# 2) requirements.txt, verbatim (torch already at 2.5.1+cu124)
$PIP install \
  "boto3>=1.28.43" "Brotli>=1.1.0" "click>=8.1.7" "fast-langdetect==0.2.0" \
  "loguru>=0.6.0" "numpy>=1.21.6,<2.0.0" "pdfminer.six==20231228" \
  "pydantic>=2.7.2,<2.8.0" "PyMuPDF>=1.24.9" "scikit-learn>=1.0.2" "transformers" \
  || echo "### requirements FAILED"

# 3) setup.py [full] extra, minus torch/paddle-detectron2 extras handled below
$PIP install \
  "unimernet==0.2.1" \
  "matplotlib" \
  "ultralytics" \
  "paddleocr==2.7.3" \
  "struct-eqtable==0.3.2" \
  "einops" \
  "accelerate" \
  "doclayout_yolo==0.0.2" \
  "rapidocr-paddle" \
  "rapid_table" \
  "PyYAML" \
  || echo "### full extra FAILED"

# 4) paddle on Linux: 3.0.0b1 is what the project pins
$PIP install "paddlepaddle==3.0.0b1" || echo "### paddlepaddle FAILED (OCR via paddle may be unavailable)"

# 5) resolve timm to whatever unimernet allows, then report
$PIP install "timm>=0.9.16,<0.10" || echo "### timm FAILED"
DT=$($PIP index versions detectron2 2>/dev/null | head -3)
echo "--- detectron2 availability: $DT"
$PIP install detectron2 || echo "### detectron2 unavailable from index (layout uses doclayout_yolo instead)"

echo "=== FINAL ENV REPORT ==="
"$ENV/bin/python" - <<'PY'
import sys, importlib
print("prefix =", sys.prefix, "| python", sys.version.split()[0])
bad = []
for name in ("torch","torchvision","transformers","click","magic_pdf","timm","ultralytics",
             "struct_eqtable","rapid_table","paddleocr","unimernet","doclayout_yolo",
             "detectron2","fitz","sklearn","numpy","pydantic","einops","accelerate"):
    try:
        m = importlib.import_module(name)
        f = getattr(m, "__file__", "?") or "?"
        print(f"{name:15s} {str(getattr(m,'__version__','?')):12s} {f}")
        if "monkeyocr" in f: bad.append((name, f))
    except Exception as e:
        print(f"{name:15s} IMPORT FAILED: {e!r}")
print("OUT-OF-ENV =", bad)
import torch; print("torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
PY
echo "### finish v3b done $(date -Is)"
