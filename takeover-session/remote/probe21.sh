#!/bin/bash
ENV=/root/autodl-tmp/conda_envs/mineru093_env
echo "=== doc_analyze_by_custom_model.py: detectron2 usage ==="
grep -n "detectron2\|import" $ENV/lib/python3.10/site-packages/magic_pdf/model/doc_analyze_by_custom_model.py | head -30
echo
echo "=== context around the model_manager region (lines 120-175) ==="
sed -n '120,175p' $ENV/lib/python3.10/site-packages/magic_pdf/model/doc_analyze_by_custom_model.py
echo
echo "=== is detectron2 import guarded anywhere? ==="
grep -rn "import detectron2\|from detectron2" $ENV/lib/python3.10/site-packages/magic_pdf/ | head -10
echo
echo "=== broken venv detectron2 provenance ==="
ls -la /root/autodl-tmp/conda_envs/mineru093_runtime_broken/lib/python3.10/site-packages/ | grep -i detectron
cat /root/autodl-tmp/conda_envs/mineru093_runtime_broken/lib/python3.10/site-packages/detectron2-0.6.dist-info/METADATA 2>/dev/null | head -8
echo
echo "=== ninja / compiler availability for building detectron2 ==="
which ninja gcc g++ nvcc 2>&1
gcc --version 2>/dev/null | head -1
nproc
