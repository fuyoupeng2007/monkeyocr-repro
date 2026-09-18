#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_torchtext4.log
exec > >(tee -a "$LOG") 2>&1
echo "### torchtext final patch started $(date -Is)"

$PY - "$SP/torchtext/_extension.py" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")

# 1) de-duplicate: drop any previously inserted patch block in _init_extension
src = re.sub(r"\n    # PATCHED \(MinerU repro\).*?globals\(\)\['_torchtext'\] = None\n", "\n", src, flags=re.DOTALL)

# 2) make the load call itself tolerant (OSError comes from ctypes inside _load_lib)
old = '    _load_lib("libtorchtext")'
new = (
    '    # PATCHED (MinerU repro): libtorchtext.so is compiled against torch<=2.3 and\n'
    '    # cannot load on torch 2.5 (undefined symbol _ZN5torch3jit17parseSchemaOrNameERKSs).\n'
    '    # unimernet inference only uses the pure-python torchtext.data.metrics, so a\n'
    '    # missing C++ extension is tolerated instead of fatal.\n'
    '    try:\n'
    '        _load_lib("libtorchtext")\n'
    '    except OSError as _e:  # pragma: no cover\n'
    '        import warnings as _w\n'
    '        _w.warn(f"torchtext C++ extension skipped (torch 2.5 ABI): {_e!r}")\n'
    '        return\n'
)
assert old in src, "anchor missing"
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("patched")
PY
echo "--- patched region:"; sed -n '53,80p' "$SP/torchtext/_extension.py"
cp "$SP/torchtext/_extension.py" "$PROJ/outputs/torchtext_extension.py.patched_v4"

echo
echo "=== verify ==="
$PY - <<'PY' 2>&1 | tail -10
import warnings; warnings.simplefilter("ignore")
import torchtext
from torchtext.data import metrics
print("torchtext OK, metrics fn:", [n for n in dir(metrics) if not n.startswith('_')][:5])
from unimernet.common.registry import registry
print("unimernet_train registered:", registry.get_task_class("unimernet_train") is not None)
from magic_pdf.model.sub_modules.model_init import AtomModelSingleton
print("magic_pdf chain OK")
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
