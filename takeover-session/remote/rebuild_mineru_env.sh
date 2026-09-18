#!/bin/bash
# Rebuild the MinerU 0.9.3 runtime as a genuinely ISOLATED environment.
#
# Why: /root/autodl-tmp/conda_envs/mineru093_runtime was created with
#   python -m venv  (from the monkeyocr interpreter) and its pyvenv.cfg has
#   include-system-site-packages = true, while it also has NO stdlib of its own
#   (no os.py, no libpython). Net effect: MinerU's magic_pdf==0.9.3 ran on top of
#   MonkeyOCR's transformers/torch/click -> StructEqTable crashed with
#   "got multiple values for keyword argument 'return_dict'".
#
# Fix: venv --copies (own interpreter binary + own stdlib) with
#   include-system-site-packages = false  ->  two experiments share nothing.
set -x
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export PIP_DISABLE_PIP_VERSION_CHECK=1
PY=/root/miniconda3/bin/python
BASE=/root/autodl-tmp/conda_envs
OLD=$BASE/mineru093_runtime
NEW=$BASE/mineru093_env
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_$(date +%H%M).log
exec > >(tee -a "$LOG") 2>&1
echo "### rebuild started $(date -Is)"

# 0) preserve evidence of the old state
if [ -d "$OLD" ]; then
  ls -1 "$OLD/lib/python3.10/site-packages" > /root/autodl-tmp/monkeyocr-repro/outputs/broken_venv_packages.txt 2>/dev/null
  cp "$OLD/pyvenv.cfg" /root/autodl-tmp/monkeyocr-repro/outputs/broken_venv_pyvenv.cfg 2>/dev/null
  mv "$OLD" "${OLD}_broken"
fi

# 1) fresh isolated venv from the SAME 3.10.21 interpreter used by monkeyocr
$PY -m venv --copies "$NEW" || exit 1
sed -i 's/^include-system-site-packages = .*/include-system-site-packages = false/' "$NEW/pyvenv.cfg"
echo "--- new pyvenv.cfg"; cat "$NEW/pyvenv.cfg"

# 2) prove isolation BEFORE installing anything
"$NEW/bin/python" - <<'PY'
import sys, os
print("prefix      =", sys.prefix)
print("base_prefix =", sys.base_prefix)
print("sys.path:")
for p in sys.path: print("   ", p)
assert "monkeyocr" not in sys.path[0], "stdlib still outside the env"
bad = [p for p in sys.path if "monkeyocr" in p]
print("MONKEYOCR PATHS IN sys.path =", bad)
assert not bad, "ISOLATION FAILED"
import os as _os
print("stdlib os.py =", _os.__file__)
print("ISOLATION OK")
PY
[ $? -ne 0 ] && { echo "### isolation check failed"; exit 1; }

PIP="$NEW/bin/python -m pip"
$PIP install -q --upgrade pip setuptools wheel
echo "### pip ready: $($NEW/bin/python -m pip -V)"

# 3) torch stack first, from the official cu124 index (no cross-env reuse)
$PIP install --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.5.1 torchvision==0.20.1 || echo "### TORCH INSTALL FAILED"

# 4) MinerU 0.9.3 full stack, resolved inside the isolated env
$PIP install "magic-pdf[full]==0.9.3" || echo "### MAGIC-PDF INSTALL FAILED"

# 5) extras the 0.9.3 CLI needs at runtime
$PIP install timm==1.0.29 unimernet==0.2.1 ultralytics rapidocr-paddle rapid-table==3.0.2 || echo "### EXTRAS INSTALL FAILED"

# 6) verification
"$NEW/bin/python" - <<'PY'
import sys
for name in ("torch","transformers","click","magic_pdf","timm","ultralytics","struct_eqtable","rapid_table","paddleocr"):
    try:
        m = __import__(name)
        print(f"{name:14s} {getattr(m,'__version__','?'):10s} {getattr(m,'__file__','?')}")
    except Exception as e:
        print(f"{name:14s} IMPORT FAILED: {e!r}")
PY
echo "### rebuild finished $(date -Is)"
