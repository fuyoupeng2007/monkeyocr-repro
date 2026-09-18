#!/bin/bash
# Rebuild MinerU 0.9.3 runtime as a REAL self-contained conda env (Python 3.10).
#
# Why not venv: `python -m venv` (even with --copies) does NOT copy the standard
# library -- the child env keeps resolving stdlib from the parent interpreter's
# prefix, and the original env additionally had
# include-system-site-packages = true. MinerU 0.9.3 therefore ran on MonkeyOCR's
# transformers/torch/click and StructEqTable crashed with
# "got multiple values for keyword argument 'return_dict'".
#
# conda create gives its own stdlib + libpython + bin, so the two experiments
# share nothing. python-3.10.21 is already in /root/miniconda3/pkgs (offline).
set -x
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PATH=/root/miniconda3/bin:$PATH
BASE=/root/autodl-tmp/conda_envs
OLD=$BASE/mineru093_runtime_broken
NEW=$BASE/mineru093_env
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v3.log
exec > >(tee -a "$LOG") 2>&1
echo "### rebuild v3 (conda) started $(date -Is)"

# 0) clear out the half-built venv attempt
[ -d "$NEW" ] && rm -rf "$NEW"
[ -d "$OLD" ] && du -sh "$OLD"

# 1) real env
/root/miniconda3/bin/conda create -y -p "$NEW" python=3.10 pip || exit 1
"$NEW/bin/python" -V || exit 1

# 2) prove the env is self-contained BEFORE installing anything
"$NEW/bin/python" - <<'PY'
import sys, os
print("prefix      =", sys.prefix)
print("base_prefix =", sys.base_prefix)
for p in sys.path: print("   path:", p)
print("stdlib os.py =", os.__file__)
bad = [p for p in sys.path if "monkeyocr" in p]
print("MONKEYOCR PATHS =", bad)
assert not bad, "ISOLATION FAILED"
try:
    import requests  # must NOT exist yet
    print("UNEXPECTED: requests importable -> env leaks")
    raise SystemExit(1)
except ImportError:
    print("clean: no third-party packages yet")
print("ISOLATION OK, python", sys.version.split()[0], "stdlib", sys.base_prefix)
PY
[ $? -ne 0 ] && { echo "### isolation check failed"; exit 1; }

PIP="$NEW/bin/python -m pip"
$PIP install -q --upgrade pip setuptools wheel
echo "### pip: $($NEW/bin/python -m pip -V)"

# 3) torch stack (cu124), then full MinerU 0.9.3 stack, inside the isolated env
$PIP install --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.5.1 torchvision==0.20.1 || echo "### TORCH INSTALL FAILED"

$PIP install "magic-pdf[full]==0.9.3" || echo "### MAGIC-PDF INSTALL FAILED"

$PIP install timm==1.0.29 unimernet==0.2.1 ultralytics rapidocr-paddle rapid-table==3.0.2 \
  || echo "### EXTRAS INSTALL FAILED"

# 4) verify: nothing may resolve outside the env
"$NEW/bin/python" - <<'PY'
import sys, importlib
print("prefix =", sys.prefix)
bad = []
for name in ("torch","torchvision","transformers","click","magic_pdf","timm",
             "ultralytics","struct_eqtable","rapid_table","paddleocr","unimernet","detectron2"):
    try:
        m = importlib.import_module(name)
        f = getattr(m, "__file__", "?") or "?"
        print(f"{name:14s} {getattr(m,'__version__','?'):10s} {f}")
        if "monkeyocr" in f: bad.append(name)
    except Exception as e:
        print(f"{name:14s} IMPORT FAILED: {e!r}")
        bad.append(f"{name}: {e!r}")
print("PROBLEMS =", bad)
PY
echo "### rebuild v3 finished $(date -Is)"
