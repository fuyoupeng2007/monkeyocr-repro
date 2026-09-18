#!/bin/bash
# Iteratively install whatever the MinerU runtime still cannot import.
# The venv is isolated, so plain pip installs here cannot touch MonkeyOCR.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
export PIP_DISABLE_PIP_VERSION_CHECK=1
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_deps_loop.log
exec > >(tee -a "$LOG") 2>&1
echo "### deps loop started $(date -Is)"

$PY -m pip install --no-deps \
  "omegaconf==2.3.0" "antlr4-python3-runtime==4.9.3" "decorator" "psutil" \
  "torchmetrics" "pycocotools" "iopath" "portalocker" "fvcore" \
  "tqdm" "requests" "rapidfuzz" "six" "packaging" "wcwidth" "coloredlogs" \
  "humanfriendly" "flatbuffers" "astor" "networkx" "fire" "ftfy" \
  "imgaug" "lmdb" "yacs" "pandas" "tifffile" "imageio" "pyarrow" \
  "beautifulsoup4" "cssutils" "premailer" "encutils" "openpyxl" \
  "markdown" "python-docx" "XlsxWriter" "lxml" "chardet" "pyclipper" || true

for round in 1 2 3 4 5 6; do
  MISSING=$($PY - <<'PY'
import importlib.util as u
mods = ["torch","torchvision","transformers","tokenizers","magic_pdf","timm","ultralytics",
        "struct_eqtable","rapid_table","paddleocr","paddle","unimernet","doclayout_yolo",
        "cv2","sklearn","numpy","pydantic","einops","accelerate","omegaconf","decorator",
        "psutil","torchmetrics","pycocotools"]
print(" ".join([m for m in mods if u.find_spec(m) is None]))
PY
)
  echo "--- round $round missing: [$MISSING]"
  [ -z "$MISSING" ] && break
  for m in $MISSING; do
    case $m in
      cv2) pkg=opencv-python-headless ;;
      sklearn) pkg=scikit-learn ;;
      paddle) pkg=paddlepaddle ;;
      *) pkg=$m ;;
    esac
    echo "    installing $pkg"
    $PY -m pip install --no-deps "$pkg" 2>&1 | tail -2
  done
done

echo "=== IMPORT CHECK ==="
$PY - <<'PY'
import importlib
for name in ("torch","torchvision","transformers","magic_pdf","timm","ultralytics",
             "struct_eqtable","rapid_table","paddleocr","paddle","unimernet",
             "doclayout_yolo","cv2","sklearn","numpy","omegaconf","decorator","psutil"):
    try:
        m = importlib.import_module(name)
        print(f"OK   {name:16s} {str(getattr(m,'__version__','?')):12s} {getattr(m,'__file__','?')}")
    except Exception as e:
        print(f"FAIL {name:16s} {type(e).__name__}: {e}")
PY
echo "### deps loop done $(date -Is)"
