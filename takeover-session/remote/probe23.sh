#!/bin/bash
ENV=/root/autodl-tmp/conda_envs/mineru093_env
SP=$ENV/lib/python3.10/site-packages
echo "=== all detectron2 references in magic_pdf (file:line) ==="
grep -rn "detectron2" $SP/magic_pdf/ --include=*.py | sed "s|$SP/||" | head -30
echo
echo "=== magic_pdf/model/model_list.py imports ==="
grep -n "^from\|^import\|import " $SP/magic_pdf/model/model_list.py | head -20
echo
echo "=== magic_pdf/model/pdf_extract_kit.py imports (top 40) ==="
sed -n '1,60p' $SP/magic_pdf/model/pdf_extract_kit.py
echo
echo "=== is detectron2 imported at module scope anywhere reachable from CustomPEKModel? ==="
grep -rn "detectron2" $SP/magic_pdf/model/*.py
echo
echo "=== how the 09:43 run got past this: find guarded import ==="
grep -rn -B3 -A3 "import detectron2" $SP/magic_pdf/model/sub_modules/layout/*/*.py | head -40
