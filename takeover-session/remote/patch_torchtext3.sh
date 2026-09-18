#!/bin/bash
# torchtext/torch 2.5 ABI: make the C++ extension import optional rather than
# fatal. unimernet only needs torchtext.data.metrics (pure Python); the compiled
# _torchtext/_extension ops are never called by the inference path.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_torchtext3.log
exec > >(tee -a "$LOG") 2>&1
echo "### torchtext optional-ext patch started $(date -Is)"

F=$SP/torchtext/_extension.py
cp "$F" "$PROJ/outputs/torchtext_extension.py.patched_v2_orig" 2>/dev/null || true

$PY - "$F" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")

# undo the previous _load_lib early-return if present
src = re.sub(
    r"\n    # PATCHED \(MinerU repro\).*?return False\n",
    "\n",
    src, flags=re.DOTALL)

# make the compiled-extension import optional
old = "    from torchtext import _torchtext  # noqa"
new = (
    "    # PATCHED (MinerU repro): libtorchtext.so is built against torch<=2.3 and\n"
    "    # fails to load on torch 2.5 (undefined symbol parseSchemaOrName). The\n"
    "    # compiled ops are not used by unimernet's inference path, which only needs\n"
    "    # the pure-python torchtext.data.metrics.\n"
    "    try:\n"
    "        from torchtext import _torchtext  # noqa\n"
    "    except Exception as _e:  # pragma: no cover\n"
    "        import warnings as _w\n"
    "        _w.warn(f'torchtext C++ extension unavailable, python API only: {_e!r}')\n"
    "        globals()['_torchtext'] = None"
)
if old not in src:
    print("anchor `from torchtext import _torchtext` not found; dumping tail")
    print("\n".join(src.splitlines()[-12:]))
    raise SystemExit(1)
src = src.replace(old, new)

# also make _load_lib non-fatal (it raises OSError today)
src = src.replace(
    "    path = Path(__file__).parent / \"lib\" / f\"lib{lib}.so\"",
    "    path = Path(__file__).parent / \"lib\" / f\"lib{lib}.so\"\n"
    "    if not path.exists():\n        return False"
)
p.write_text(src, encoding="utf-8")
print("patched", p)
PY
cp "$F" "$PROJ/outputs/torchtext_extension.py.patched_v3"

echo "=== verify what unimernet needs ==="
$PY - <<'PY' 2>&1 | tail -12
import warnings; warnings.simplefilter("ignore")
import torchtext
from torchtext.data import metrics
print("torchtext import OK; metrics:", [n for n in dir(metrics) if not n.startswith('_')][:6])
from unimernet.common.registry import registry
print("unimernet_train registered:", registry.get_task_class("unimernet_train"))
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
