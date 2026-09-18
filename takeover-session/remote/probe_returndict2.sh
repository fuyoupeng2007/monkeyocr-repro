#!/bin/bash
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/probe_returndict2.log
exec > >(tee -a "$LOG") 2>&1
echo "### probe2 started $(date -Is)"

$PY - <<'PY' 2>&1 | tail -45
import inspect, numpy as np, PIL.Image as Image
from transformers import AutoModel
import struct_eqtable.internvl.internvl as I

_orig_from_pretrained = AutoModel.from_pretrained

def hooked(*a, **kw):
    m = _orig_from_pretrained(*a, **kw)
    print(">>> remote class:", type(m).__mro__[:4])
    inner = getattr(m, "language_model", None)
    if inner is not None:
        print(">>> inner LM class:", type(inner).__mro__[:4])
        print(">>> inner LM forward sig:", str(inspect.signature(type(inner).forward))[:220])
        _f = type(inner).forward
        def logged(self2, *args, **kwargs):
            print(">>> INNER forward kwargs:", sorted(kwargs.keys()), "| return_dict=", kwargs.get("return_dict", "<absent>"))
            return _f(self2, *args, **kwargs)
        type(inner).forward = logged
        print(">>> hook installed on", type(inner).__name__)
    else:
        print(">>> no language_model attr")
    return m

I.AutoModel.from_pretrained = hooked

from struct_eqtable import build_model
model = build_model(
    model_ckpt="/root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/TabRec/StructEqTable",
    max_new_tokens=64, max_time=60, lmdeploy=False, flash_attn=False, batch_size=1,
).cuda()
print("built:", type(model))
try:
    out = model([Image.fromarray(np.full((64, 64, 3), 255, dtype="uint8"))], output_format="html")
    print("OUTPUT:", str(out)[:200])
except Exception as e:
    print("STILL FAILS:", type(e).__name__, str(e)[:300])
PY
echo "### probe2 done $(date -Is)"
