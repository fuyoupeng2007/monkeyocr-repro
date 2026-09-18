#!/bin/bash
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=/root/autodl-tmp/monkeyocr-repro/configs/mineru093/magic-pdf.json
echo "=== full traceback for detectron2 ==="
$PY - <<'PY' 2>&1 | tail -40
import traceback
try:
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
    from magic_pdf.pipe.OCRPipe import OCRPipe
    print("module import fine; now constructing model")
    import json, pathlib
    pdf = pathlib.Path("/root/autodl-tmp/monkeyocr-repro/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf")
    p = OCRPipe(pdf.read_bytes(), [], [], "ocr")
    p.pipe_classify()
    p.pipe_analyze()
    print("ANALYZE OK")
except Exception:
    traceback.print_exc()
PY
echo
echo "=== layoutlmv3 package __init__ ==="
cat $SP/magic_pdf/model/sub_modules/layout/layoutlmv3/__init__.py 2>/dev/null | head -20
echo "=== layoutreader references ==="
grep -rn "layoutreader\|LayoutReader" $SP/magic_pdf/model/sub_modules/model_init.py | head -10
echo "=== who imports the layoutlmv3 package ==="
grep -rn "layoutlmv3" $SP/magic_pdf/ --include=*.py | grep -v "sub_modules/layout/layoutlmv3/" | head -10
