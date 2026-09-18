#!/bin/bash
# get detectron2 into the isolated env:
#   a) try the copy from the old (ABI-compatible: same py3.10, same torch 2.5.1+cu124)
#   b) verify by real import
#   c) if that fails, fetch the source from GitHub mirrors reachable in CN and build
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
OLD=/root/autodl-tmp/conda_envs/mineru093_runtime_broken/lib/python3.10/site-packages
NEW=$ENV/lib/python3.10/site-packages
LOG=/root/autodl-tmp/monkeyocr-repro/outputs/env_detectron2_b.log
exec > >(tee -a "$LOG") 2>&1
echo "### detectron2 plan B started $(date -Is)"

echo "--- old detectron2 metadata"
grep -E "^Name|^Version|^Requires" $OLD/detectron2-0.6.dist-info/METADATA 2>/dev/null | head -5
echo "--- compiled extension present?"
ls -la $OLD/detectron2/_C*.so 2>/dev/null
echo "--- what torch does it link against"
ldd $OLD/detectron2/_C*.so 2>/dev/null | grep -i torch | head -3

if [ ! -d "$NEW/detectron2" ]; then
  cp -a $OLD/detectron2 $NEW/ && echo "copied detectron2 module tree"
  cp -a $OLD/detectron2-0.6.dist-info $NEW/ 2>/dev/null && echo "copied dist-info"
  # detectron2 also needs its generated version file + egg-link style pieces
  ls $OLD | grep -i detectron2
fi

echo "=== import test ==="
$PY - <<'PY'
import traceback
try:
    import detectron2
    print("detectron2 OK", detectron2.__version__ if hasattr(detectron2,'__version__') else '?', detectron2.__file__)
    from detectron2.data import MetadataCatalog
    from detectron2.modeling import Backbone, BACKBONE_REGISTRY, FPN
    from detectron2.config import get_cfg
    print("detectron2 deep imports OK")
except Exception:
    traceback.print_exc()
PY

if ! $PY -c "import detectron2" 2>/dev/null; then
  echo "### copy path failed -> try CN github mirrors and build"
  cd /tmp || exit 1
  for M in https://gitee.com/mirrors/detectron2.git https://gitclone.com/github.com/facebookresearch/detectron2.git https://ghproxy.net/https://github.com/facebookresearch/detectron2.git; do
    echo "--- trying $M"
    rm -rf /tmp/detectron2_src
    if timeout 180 git clone --depth 1 "$M" /tmp/detectron2_src 2>&1 | tail -3; then
      if [ -d /tmp/detectron2_src/detectron2 ]; then
        MAX_JOBS=32 $PY -m pip install --no-build-isolation --no-deps /tmp/detectron2_src 2>&1 | tail -8
        break
      fi
    fi
  done
fi

echo "=== final import check ==="
$PY - <<'PY'
for name in ("detectron2","unimernet","paddleocr","doclayout_yolo","magic_pdf","torch"):
    try:
        m = __import__(name)
        print(f"OK   {name:14s} {str(getattr(m,'__version__','?')):10s}")
    except Exception as e:
        print(f"FAIL {name:14s} {type(e).__name__}: {e}")
PY
echo "### detectron2 plan B done $(date -Is)"
