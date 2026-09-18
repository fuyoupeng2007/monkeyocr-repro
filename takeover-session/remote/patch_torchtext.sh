#!/bin/bash
# torchtext has no build compatible with torch 2.5 (undefined symbol
# _ZN5torch3jit17parseSchemaOrNameERKSs for both 0.17.2 and 0.18.0).
# It is only imported by unimernet's *training* task, which inference never
# touches. Patch that single import to be soft, so the inference path imports
# cleanly; the edit is recorded in outputs/ for the report.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
LOG=$PROJ/outputs/env_patch_torchtext.log
exec > >(tee -a "$LOG") 2>&1
echo "### torchtext patch started $(date -Is)"

$PY -m pip uninstall -y torchtext 2>&1 | tail -2

F=$SP/unimernet/tasks/__init__.py
cp "$F" "$PROJ/outputs/unimernet_tasks_init.py.orig"
echo "--- before:"; cat "$F"

$PY - "$F" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
target = "from unimernet.tasks.unimernet_train import UniMERNet_Train"
if target in src and "PATCHED" not in src:
    replacement = (
        "# PATCHED (MinerU repro): UniMERNet_Train imports torchtext.data.metrics, and no\n"
        "# torchtext build exists for torch 2.5 (undefined symbol parseSchemaOrName).\n"
        "# This task class is training-only; the inference path never references it.\n"
        "try:\n"
        "    from unimernet.tasks.unimernet_train import UniMERNet_Train  # noqa: F401\n"
        "except (ImportError, OSError) as _e:  # pragma: no cover\n"
        "    UniMERNet_Train = None\n"
        "    import warnings as _w\n"
        "    _w.warn(f'unimernet train task unavailable (torchtext): {_e!r}')\n"
    )
    src = src.replace(target, replacement)
    p.write_text(src, encoding="utf-8")
    print("patched", p)
else:
    print("already patched or pattern absent")
PY
echo "--- after:"; cat "$F" | head -30
cp "$F" "$PROJ/outputs/unimernet_tasks_init.py.patched"

echo
echo "=== chain test ==="
$PY - <<'PY' 2>&1 | tail -20
import traceback, re
try:
    from magic_pdf.model.sub_modules.model_init import AtomModelSingleton
    from magic_pdf.model.pdf_extract_kit import CustomPEKModel
    import magic_pdf.model.sub_modules.mfr.unimernet.Unimernet as U
    print("CHAIN_OK")
except Exception as e:
    m = re.search(r"No module named '([A-Za-z0-9_\.]+)'", str(e))
    print("MISSING", m.group(1).split(".")[0]) if m else traceback.print_exc()
PY
echo "### torchtext patch done $(date -Is)"
