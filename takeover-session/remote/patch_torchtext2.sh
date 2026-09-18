#!/bin/bash
# torchtext vs torch 2.5: libtorchtext.so fails to load with
#   undefined symbol _ZN5torch3jit17parseSchemaOrNameERKSs
# (removed from torch >= 2.4). No torchtext release matches torch 2.5 because
# torchtext was discontinued after 0.18.0 (torch 2.3).
#
# unimernet only needs `torchtext.data.metrics`, which is pure Python; the C++
# extension is never used by the inference path. So instead of downgrading all of
# torch (and losing cu124), make the extension load best-effort.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_torchtext2.log
exec > >(tee -a "$LOG") 2>&1
echo "### torchtext ext patch started $(date -Is)"

# 1) restore unimernet's tasks/__init__.py (the earlier soft-import broke setup_task)
if [ -f "$PROJ/outputs/unimernet_tasks_init.py.orig" ]; then
  cp "$PROJ/outputs/unimernet_tasks_init.py.orig" "$SP/unimernet/tasks/__init__.py"
  echo "restored unimernet/tasks/__init__.py"
fi
grep -n "unimernet_train" "$SP/unimernet/tasks/__init__.py"

# 2) make torchtext's C++ extension optional, keep the pure-python modules
$PY -m pip install --no-deps "torchtext==0.18.0" 2>&1 | tail -2
F=$SP/torchtext/_extension.py
cp "$F" "$PROJ/outputs/torchtext_extension.py.orig"

$PY - "$F" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
marker = "# PATCHED (MinerU repro)"
if marker in src:
    print("already patched")
    raise SystemExit
needle = "def _load_lib(lib: str) -> bool:"
idx = src.find(needle)
assert idx != -1, "anchor not found"
# insert an early-return guard right after the def line + docstring line
lines = src[idx:].splitlines(keepends=True)
# find end of the def line
ins = idx + len(lines[0])
guard = (
    "\n    # " + marker[2:] + ": torchtext has no build for torch 2.5; the C++ ops are\n"
    "    # unused by unimernet's inference path, so treat the extension as absent.\n"
    "    import warnings as _w\n"
    "    _w.warn('torchtext C++ extension skipped (no torch 2.5 compatible build)')\n"
    "    return False\n"
)
src = src[:ins] + guard + src[ins:]
p.write_text(src, encoding="utf-8")
print("patched", p)
PY
cp "$F" "$PROJ/outputs/torchtext_extension.py.patched"

# 3) verify chain + the module unimernet actually needs
$PY - <<'PY' 2>&1 | tail -12
import warnings; warnings.simplefilter("ignore")
from torchtext.data import metrics
print("torchtext.data.metrics OK")
from unimernet.common.registry import registry
import unimernet.tasks as T
print("task class:", registry.get_task_class("unimernet_train"))
from magic_pdf.model.sub_modules.model_init import AtomModelSingleton
print("magic_pdf model_init chain OK")
PY

echo
echo "=== SMOKE: full model load + 1 page ==="
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### magic-pdf rc=$?"
echo "=== produced ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
MD=$(find "$OUT" -name '*.md' | head -1)
echo "=== md: $MD ==="
if [ -n "$MD" ]; then
  echo "chars=$(wc -c < "$MD")  html_tables=$(grep -c '<table' "$MD" || true)"
  head -c 700 "$MD"; echo
fi
echo "### done $(date -Is)"
