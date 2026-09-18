#!/bin/bash
# Self-healing dependency loop: repeatedly exercise the REAL import chain that
# magic-pdf walks at model-init time, install whatever module is missing, repeat.
# Ends by running the actual single-page smoke test.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export PIP_DISABLE_PIP_VERSION_CHECK=1
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_selfheal.log
exec > >(tee -a "$LOG") 2>&1
echo "### self-heal started $(date -Is)"

# name -> pip requirement, where they differ
pipname() {
  case "$1" in
    cv2) echo opencv-python-headless ;;
    sklearn) echo scikit-learn ;;
    fitz) echo PyMuPDF ;;
    PIL) echo Pillow ;;
    yaml) echo PyYAML ;;
    bs4) echo beautifulsoup4 ;;
    *) echo "$1" ;;
  esac
}

for round in $(seq 1 25); do
  OUT=$($PY - <<'PY' 2>&1
import traceback, re, sys
try:
    from magic_pdf.model.sub_modules.model_init import AtomModelSingleton
    from magic_pdf.model.pdf_extract_kit import CustomPEKModel
    import magic_pdf.model.sub_modules.mfr.unimernet.Unimernet as U
    print("CHAIN_OK")
except Exception as e:
    msg = str(e)
    m = re.search(r"No module named '([A-Za-z0-9_\.]+)'", msg)
    if m:
        print("MISSING " + m.group(1).split(".")[0])
    else:
        traceback.print_exc()
        print("OTHER " + type(e).__name__ + ": " + msg)
PY
)
  echo "--- round $round: $OUT"
  case "$OUT" in
    *CHAIN_OK*) echo "IMPORT CHAIN CLEAN"; break ;;
    *MISSING*) MOD=$(echo "$OUT" | sed -n 's/^MISSING //p' | head -1); PKG=$(pipname "$MOD")
               echo "    installing $PKG"; $PY -m pip install --no-deps "$PKG" 2>&1 | tail -2 ;;
    *) echo "    non-missing error, stopping loop"; break ;;
  esac
done

echo
echo "=== SMOKE: magic-pdf on one OmniDocBench page ==="
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"
time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
RC=$?
echo "### magic-pdf rc=$RC"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2
MD=$(find "$OUT" -name '*.md' | head -1)
echo "=== markdown: $MD ==="
if [ -n "$MD" ]; then
  echo "chars=$(wc -c < "$MD")  html_tables=$(grep -c '<table' "$MD" || true)"
  head -c 600 "$MD"; echo
fi
echo "### self-heal + smoke done $(date -Is)"
