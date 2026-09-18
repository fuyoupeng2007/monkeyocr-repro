#!/bin/bash
# The last mile: transformers' generation loop calls the LM as
#   self(**model_inputs, return_dict=True)
# and model_inputs already carries return_dict (it was put into model_kwargs by
# the caller's generate_kwargs), so the LM's forward receives it twice.
# Patching the model class is the one place that cannot be shadowed by the
# remote-code cache, so do it at runtime via the env's sitecustomize.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/runtime_guard.log
exec > >(tee -a "$LOG") 2>&1
echo "### runtime guard started $(date -Is)"

cat > "$ENV/lib/python3.10/site-packages/sitecustomize.py" <<'PY'
"""PATCHED-MINERU runtime guards (applied automatically by Python at startup).

1. Qwen2ForCausalLM.forward: transformers' generation loop calls the model as
   self(**model_inputs, return_dict=True) while the caller already injected
   return_dict into model_kwargs -> "got multiple values for keyword argument
   'return_dict'". Drop the duplicate before the signature binds it.
"""
import os

if os.environ.get("MINERU_GUARD", "1") == "1":
    try:
        from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM
        _orig_forward = Qwen2ForCausalLM.forward

        def _guarded_forward(self, *args, **kwargs):
            kwargs.pop("return_dict", None)
            return _orig_forward(self, *args, **kwargs)

        Qwen2ForCausalLM.forward = _guarded_forward
        Qwen2ForCausalLM._mineru_return_dict_guard = True
    except Exception:  # transformers not imported yet / layout changed
        pass
PY
echo "--- sitecustomize written"
$PY -c "from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM as Q; print('guard active:', getattr(Q,'_mineru_return_dict_guard',False))"

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
  head -c 800 "$MD"; echo
fi
echo "### done $(date -Is)"
