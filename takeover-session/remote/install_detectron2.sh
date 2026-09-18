#!/bin/bash
# Install detectron2 (needed because magic_pdf imports its layoutlmv3 submodules at
# import time, even when layout_model == doclayout_yolo) plus last leaf deps.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
export PIP_DISABLE_PIP_VERSION_CHECK=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=/root/autodl-tmp/monkeyocr-repro/configs/mineru093/magic-pdf.json
PROJ=/root/autodl-tmp/monkeyocr-repro
LOG=$PROJ/outputs/env_detectron2.log
exec > >(tee -a "$LOG") 2>&1
echo "### detectron2 install started $(date -Is)"

$PY -m pip install --no-deps stringzilla 2>&1 | tail -2
$PY -m pip install ninja 2>&1 | tail -2

echo "=== attempt 1: build from source (official repo) ==="
MAX_JOBS=32 $PY -m pip install --no-build-isolation --no-deps \
  "git+https://github.com/facebookresearch/detectron2.git" 2>&1 | tail -25
RC=$?
echo "### attempt 1 rc=$RC"

if ! $PY -c "import detectron2" 2>/dev/null; then
  echo "=== attempt 2: prebuilt wheel (torch 2.5 cu124 cpu-abi wheel mirrors) ==="
  $PY -m pip install --no-deps --find-links https://dl.fbaipublicfiles.com/detectron2/wheels/cu124/torch2.5/index.html detectron2 2>&1 | tail -5 \
  || $PY -m pip install --no-deps --index-url https://mirrors.aliyun.com/pytorch-wheels/cu124 detectron2 2>&1 | tail -5
fi

echo "=== import verification ==="
$PY - <<'PY'
import importlib
for name in ("detectron2","unimernet","paddleocr","doclayout_yolo","magic_pdf"):
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:15s} {str(getattr(m,'__version__','?')):12s} {getattr(m,'__file__','?')}")
    except Exception as e:
        print(f"FAIL {name:15s} {type(e).__name__}: {e}")
PY
echo "### detectron2 install done $(date -Is)"
