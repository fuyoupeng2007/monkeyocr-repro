#!/bin/bash
# Minimal repro: does Qwen2ForCausalLM.generate(return_dict=False) crash on this
# transformers build? That isolates whether generate injects return_dict into
# model_kwargs (and thus duplicates it at self(**model_inputs, return_dict=True)).
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
LOG=$PROJ/outputs/repro_returndict.log
exec > >(tee -a "$LOG") 2>&1
echo "### repro started $(date -Is)"
$PY - <<'PY' 2>&1 | tail -30
import torch, transformers
from transformers import Qwen2Config, Qwen2ForCausalLM
print("transformers", transformers.__version__, "torch", torch.__version__)
cfg = Qwen2Config(vocab_size=128, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                  num_attention_heads=2, num_key_value_heads=2, max_position_embeddings=64)
m = Qwen2ForCausalLM(cfg).cuda().eval()
ids = torch.tensor([[1, 2, 3, 4]], device="cuda")
for kw in ({}, {"return_dict": False}, {"return_dict": True}):
    try:
        out = m.generate(ids, max_new_tokens=3, do_sample=False, **kw)
        print(f"generate(**{kw}) OK -> {out.shape}")
    except Exception as e:
        print(f"generate(**{kw}) FAILED: {type(e).__name__}: {str(e)[:160]}")
# and the direct model call the generation loop performs
try:
    out = m(input_ids=ids, return_dict=True)
    print("m(input_ids, return_dict=True) OK")
except Exception as e:
    print("m(input_ids, return_dict=True) FAILED:", type(e).__name__, str(e)[:160])
PY
echo "### repro done $(date -Is)"
