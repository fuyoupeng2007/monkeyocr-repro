#!/bin/bash
# Place MinerU 0.9.3's full stack by hand, every version pinned to a combination
# that actually exists on PyPI / the official paddle index. No resolver freedom.
#
# Lessons from the previous attempts:
#  * constraints.txt says transformers==4.50.0 and tokenizers==0.21.0 -- letting
#    pip resolve `transformers` (no pin) pulled 5.17.0, which MinerU 0.9.3 (4.x
#    era code) will not run on.
#  * doclayout_yolo==0.0.2 (setup.py) was never published; only 0.0.2b1/0.0.3/0.0.4.
#    Use 0.0.2b1 to stay closest to the pinned API.
#  * paddlepaddle==3.0.0b1 is absent from the aliyun PyPI mirror -> official index.
#  * --no-deps everywhere: the venv is already isolated, so no transitive package
#    may silently upgrade torch/transformers.
set -x
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PIP="$ENV/bin/python -m pip"
PIPX="$PIP install --no-deps --disable-pip-version-check"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_final_pins.log
exec > >(tee -a "$LOG") 2>&1
echo "### pinned placement started $(date -Is)"

$PIPX --upgrade pip setuptools wheel

# --- MinerU core -------------------------------------------------------------
$PIPX "magic-pdf==0.9.3"

# --- requirements.txt, pinned (torch stays 2.5.1+cu124) ----------------------
$PIPX "boto3>=1.28.43" "Brotli" "click>=8.1.7" "fast-langdetect==0.2.0" \
      "loguru>=0.6.0" "numpy==1.26.4" "pdfminer.six==20231228" \
      "pydantic==2.7.4" "PyMuPDF==1.24.14" "scikit-learn==1.5.2" \
      "transformers==4.50.0" "tokenizers==0.21.0" "huggingface_hub==0.30.0" \
      "safetensors==0.5.3" "accelerate==1.6.0" "regex" "requests" "tqdm" "six" \
      "python-dateutil" "PyYAML" "loguru" "chardet" || echo "### requirements FAILED"

# --- setup.py [full] extra ---------------------------------------------------
$PIPX "unimernet==0.2.1" "doclayout_yolo==0.0.2b1" "paddleocr==2.7.3" \
      "struct-eqtable==0.3.2" "einops" "rapidocr-paddle" "rapid_table" \
      "ultralytics" "matplotlib" "opencv-python-headless" "pyclipper" "shapely" \
      || echo "### full extra FAILED"

# paddlepaddle: official index (mirror lacks the 3.0.0b1 pin)
$PIPX --index-url https://www.paddlepaddle.org.cn/packages/stable/cpu/ "paddlepaddle==3.0.0b1" \
  || $PIPX --index-url https://www.paddlepaddle.org.cn/packages/stable/cu126/ "paddlepaddle==3.0.0b1" \
  || $PIPX "paddlepaddle==3.0.0b2" \
  || echo "### paddlepaddle FAILED"

# --- layout detection backend ------------------------------------------------
# magic-pdf 0.9.3 imports `import doclayout_yolo` at runtime; the pypi build of
# doclayout_yolo ships a `doclayout_yolo` module, so the wheel is the right
# backend here (verified below by reading magic_pdf's own import site).
"$ENV/bin/python" - <<'PY'
import pathlib, re
p = pathlib.Path("/root/autodl-tmp/conda_envs/mineru093_env/lib/python3.10/site-packages/magic_pdf/model/pdf_extract_kit.py")
if p.exists():
    txt = p.read_text(encoding="utf-8", errors="replace")
    print("--- layout imports in pdf_extract_kit.py")
    for line in txt.splitlines():
        if "doclayout" in line.lower() or "detectron2" in line.lower() or "apply_layout" in line:
            print("   ", line.strip()[:160])
PY

# --- final report ------------------------------------------------------------
echo "=== FINAL ENV REPORT ==="
"$ENV/bin/python" - <<'PY'
import importlib
importlib.invalidate_caches()
bad = []
for name in ("torch","torchvision","transformers","tokenizers","click","magic_pdf","timm",
             "ultralytics","struct_eqtable","rapid_table","paddleocr","paddle","unimernet",
             "doclayout_yolo","detectron2","fitz","sklearn","numpy","pydantic","einops",
             "accelerate","cv2","pyclipper","shapely"):
    try:
        m = importlib.import_module(name)
        f = getattr(m, "__file__", "?") or "?"
        print(f"{name:16s} {str(getattr(m,'__version__','?')):12s} {f}")
        if "monkeyocr" in f: bad.append((name, f))
    except Exception as e:
        print(f"{name:16s} IMPORT FAILED: {type(e).__name__}: {e}")
        bad.append((name, str(e)))
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available())
print("PROBLEMS =", bad)
PY
echo "### pinned placement done $(date -Is)"
