#!/bin/bash
# MinerU 0.9.3 single-page smoke test on the isolated env.
# Verifies: CLI runs, Markdown is produced, and the OmniDocBench adapter converts it.
set -x
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PROJ=/root/autodl-tmp/monkeyocr-repro
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
PDF=$PROJ/data/omnidocbench_v1_0/mineru_input_pdfs/jiaocaineedrop_jiaocai_needrop_en_2211.pdf
OUT=$PROJ/outputs/mineru_smoke_iso
rm -rf "$OUT"; mkdir -p "$OUT"

echo "### which magic-pdf: $ENV/bin/magic-pdf"
"$ENV/bin/python" -c "import sys,magic_pdf,transformers,torch;print('py',sys.version.split()[0]);print('magic_pdf',magic_pdf.__file__);print('transformers',transformers.__file__);print('torch',torch.__version__,torch.cuda.is_available())"

time "$ENV/bin/magic-pdf" -p "$PDF" -o "$OUT" -m ocr
echo "### exit=$?"
echo "=== produced files ==="
find "$OUT" -type f -printf '%10s %p\n' | sort -k2

echo "=== markdown preview ==="
MD=$(find "$OUT" -name '*.md' | head -1)
echo "md=$MD"
[ -n "$MD" ] && head -c 1500 "$MD"

echo "=== content_list preview ==="
CL=$(find "$OUT" -name '*content_list.json' | head -1)
echo "content_list=$CL"
[ -n "$CL" ] && "$ENV/bin/python" -c "
import json,sys
d=json.load(open('$CL',encoding='utf-8'))
print('blocks:',len(d))
from collections import Counter
print(Counter(b.get('type') for b in d))
print(json.dumps(d[:3],ensure_ascii=False,indent=1)[:1500])
"
echo "### smoke done"
