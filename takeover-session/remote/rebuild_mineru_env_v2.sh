#!/bin/bash
# Rebuild MinerU 0.9.3 runtime as a genuinely ISOLATED Py3.10 environment.
#
# Root cause being fixed (found during takeover):
#   conda_envs/mineru093_runtime was created with `python -m venv` from the
#   monkeyocr interpreter, had NO stdlib of its own (no os.py, no libpython) and
#   pyvenv.cfg said include-system-site-packages = true. So magic_pdf==0.9.3 ran
#   on MonkeyOCR's transformers/torch/click -> StructEqTable died with
#   "got multiple values for keyword argument 'return_dict'".
#
# Fix: venv --copies from the Py3.10.21 interpreter with
#      include-system-site-packages = false  =>  zero bleed-through.
set -x
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export PIP_DISABLE_PIP_VERSION_CHECK=1
BASE=/root/autodl-tmp/conda_envs
PY=$BASE/monkeyocr/bin/python          # must be 3.10.x
NEW=$BASE/mineru093_env
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_rebuild_v2.log
exec > >(tee -a "$LOG") 2>&1
echo "### rebuild v2 started $(date -Is)"

# 0) abort if a wrong-version env is sitting there
if [ -d "$NEW" ]; then
  if ! "$NEW/bin/python" -c 'import sys; sys.exit(0 if sys.version_info[:2]==(3,10) else 1)'; then
    echo "### removing wrong-version env $NEW"
    rm -rf "$NEW"
  fi
fi

echo "--- interpreter versions"
"$PY" -V
"$NEW/bin/python" -V 2>/dev/null || echo "(new env not created yet)"

# 1) create the isolated env with a COPIED interpreter (own stdlib, own binary)
if [ ! -x "$NEW/bin/python" ]; then
  "$PY" -m venv --copies "$NEW" || exit 1
fi
sed -i 's/^include-system-site-packages = .*/include-system-site-packages = false/' "$NEW/pyvenv.cfg"
echo "--- pyvenv.cfg"; cat "$NEW/pyvenv.cfg"
"$NEW/bin/python" -V || exit 1

# 2) prove isolation BEFORE installing anything
"$NEW/bin/python" - <<'PY'
import sys, os
print("prefix      =", sys.prefix)
print("base_prefix =", sys.base_prefix)
for p in sys.path: print("   path:", p)
print("stdlib os.py =", os.__file__)
bad = [p for p in sys.path if "monkeyocr" in p]
print("MONKEYOCR PATHS =", bad)
assert not bad, "ISOLATION FAILED"
import sysconfig; print("py ver =", sys.version)
print("ISOLATION OK")
PY
[ $? -ne 0 ] && { echo "### isolation check failed"; exit 1; }

PIP="$NEW/bin/python -m pip"
$PIP install -q --upgrade pip setuptools wheel
echo "### pip ready: $($NEW/bin/python -m pip -V)"

# 3) torch stack (cu124), then the MinerU stack, all resolved inside the env
$PIP install --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.5.1 torchvision==0.20.1 || echo "### TORCH INSTALL FAILED"

$PIP install "magic-pdf[full]==0.9.3" || echo "### MAGIC-PDF INSTALL FAILED"

$PIP install timm==1.0.29 unimernet==0.2.1 ultralytics rapidocr-paddle rapid-table==3.0.2 \
  || echo "### EXTRAS INSTALL FAILED"

# 4) verification: no import may resolve outside the env
"$NEW/bin/python" - <<'PY'
import sys, importlib
print("prefix =", sys.prefix)
bad = []
for name in ("torch","torchvision","transformers","click","magic_pdf","timm",
             "ultralytics","struct_eqtable","rapid_table","paddleocr","unimernet"):
    try:
        m = importlib.import_module(name)
        f = getattr(m, "__file__", "?") or "?"
        print(f"{name:14s} {getattr(m,'__version__','?'):10s} {f}")
        if "monkeyocr" in f: bad.append((name, f))
    except Exception as e:
        print(f"{name:14s} IMPORT FAILED: {e!r}")
        bad.append((name, f"import error {e!r}"))
print("OUT-OF-ENV OR BROKEN IMPORTS =", bad)
PY
echo "### rebuild v2 finished $(date -Is)"
