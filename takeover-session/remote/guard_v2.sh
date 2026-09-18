#!/bin/bash
# Definitive guard: strip return_dict at the LM's generate() entry, before
# transformers can put it into model_kwargs and then pass it twice to the model.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/guard_v2.log
exec > >(tee -a "$LOG") 2>&1
echo "### guard v2 started $(date -Is)"

cat > "$ENV/lib/python3.10/site-packages/sitecustomize.py" <<'PY'
"""PATCHED-MINERU runtime guard.

transformers 4.50's GenerationMixin turns any unrecognised generate kwarg into a
model kwarg; a `return_dict` that reaches generate() therefore ends up in
model_kwargs, and the sampling loop then calls the model as
    self(**model_inputs, return_dict=True)
so the model's forward receives return_dict twice:

    TypeError: Qwen2ForCausalLM(...) got multiple values for keyword argument 'return_dict'

This is exactly the crash that blocked the MinerU 0.9.3 smoke test at 09:43.
Strip it at both entry points.
"""
import os

if os.environ.get("MINERU_GUARD", "1") == "1":
    try:
        from transformers.generation.utils import GenerationMixin
        from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM

        if not getattr(GenerationMixin, "_mineru_rd_guard", False):
            _orig_generate = GenerationMixin.generate

            def _guarded_generate(self, *args, **kwargs):
                kwargs.pop("return_dict", None)
                return _orig_generate(self, *args, **kwargs)

            _guarded_generate._mineru_rd_guard = True
            GenerationMixin.generate = _guarded_generate
            GenerationMixin._mineru_rd_guard = True

        if not getattr(Qwen2ForCausalLM, "_mineru_rd_guard", False):
            _orig_forward = Qwen2ForCausalLM.forward

            def _guarded_forward(self, *args, **kwargs):
                kwargs.pop("return_dict", None)
                return _orig_forward(self, *args, **kwargs)

            Qwen2ForCausalLM.forward = _guarded_forward
            Qwen2ForCausalLM._mineru_rd_guard = True
    except Exception as _e:  # pragma: no cover
        import sys
        print(f"[mineru-guard] not applied: {_e!r}", file=sys.stderr)
PY

echo "--- guard self-test (must print OK, i.e. no duplicate-kwarg error) ---"
$PY - <<'PY' 2>&1 | tail -12
import torch
from transformers import Qwen2Config, Qwen2ForCausalLM
from transformers.generation.utils import GenerationMixin
print("GenerationMixin guarded:", getattr(GenerationMixin, "_mineru_rd_guard", False))
print("Qwen2ForCausalLM guarded:", getattr(Qwen2ForCausalLM, "_mineru_rd_guard", False))
cfg = Qwen2Config(vocab_size=128, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                  num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=64)
m = Qwen2ForCausalLM(cfg).cuda().eval()
ids = torch.tensor([[1, 2, 3, 4]], device="cuda")
out = m.generate(ids, max_new_tokens=3, do_sample=False, return_dict=True)
print("OK: generate(return_dict=True) survived ->", tuple(out.shape))
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
  head -c 900 "$MD"; echo
fi
echo "### done $(date -Is)"
