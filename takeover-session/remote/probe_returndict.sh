#!/bin/bash
# Diagnostic: hook the language model inside StructEqTable and print exactly what
# its forward receives, so we can see where the duplicate return_dict comes from.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/probe_returndict.log
exec > >(tee -a "$LOG") 2>&1
echo "### probe started $(date -Is)"

$PY - <<'PY' 2>&1 | tail -40
import torch, types
from struct_eqtable import build_model
import struct_eqtable.internvl.internvl as I

orig_init = I.InternVLChatModel.__init__ if hasattr(I, "InternVLChatModel") else None
print("InternVLChatModel present:", orig_init is not None)

# hook: after the model is built, instrument the LM's forward
_orig = I.InternVLChatModel.__init__
def patched_init(self, *a, **kw):
    _orig(self, *a, **kw)
    lm = getattr(self, "language_model", None)
    print(">>> LM class:", type(lm).__mro__[:3])
    print(">>> LM generate signature:", str(__import__('inspect').signature(lm.generate))[:200])
    fwd = type(lm).forward
    def logged_forward(self2, *args, **kwargs):
        print(">>> LM.forward keys:", sorted(kwargs.keys()))
        if "return_dict" in kwargs:
            print(">>> return_dict value:", kwargs.get("return_dict"))
        return fwd(self2, *args, **kwargs)
    type(lm).forward = logged_forward
    print(">>> hook installed on", type(lm).__name__)

I.InternVLChatModel.__init__ = patched_init

model = build_model(
    model_ckpt="/root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/TabRec/StructEqTable",
    max_new_tokens=64, max_time=60, lmdeploy=False, flash_attn=False, batch_size=1,
).cuda()
print("model built:", type(model))
import PIL.Image as Image
import numpy as np
img = Image.fromarray(np.full((64, 64, 3), 255, dtype="uint8"))
out = model([img], output_format="html")
print("OUTPUT:", str(out)[:200])
PY
echo "### probe done $(date -Is)"
