#!/bin/bash
# Root cause of the "patch has no effect" loop: transformers copies the
# trust_remote_code module out of the model snapshot into
# ~/.cache/huggingface/modules/transformers_modules/<name>/ on EVERY import (the
# cache dir is created at run time, so editing it is futile). The real source is
#   ~/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/TabRec/StructEqTable/
# Patch there, then let the cache be rebuilt.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
SRC=/root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/TabRec/StructEqTable/modeling_internvl_chat.py
MODCACHE=/root/.cache/huggingface/modules/transformers_modules
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/patch_seq_src.log
exec > >(tee -a "$LOG") 2>&1
echo "### structeqtable SOURCE patch started $(date -Is)"

[ -f "$PROJ/outputs/modeling_internvl_chat.src.orig" ] || cp "$SRC" "$PROJ/outputs/modeling_internvl_chat.src.orig"

$PY - "$SRC" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines()
out, n_pop, n_fwd = [], 0, 0
for i, line in enumerate(lines):
    if line.strip() == "outputs = self.language_model.generate(":
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}# PATCHED-MINERU: return_dict also arrives via **generate_kwargs;")
        out.append(f"{indent}# transformers' generate would forward it twice to the LM.")
        out.append(f'{indent}generate_kwargs.pop("return_dict", None)')
        n_pop += 1
    if re.match(r"\s*return_dict = return_dict if return_dict is not None else self\.config\.use_return_dict\s*$", line):
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}# PATCHED-MINERU: transformers>=4.50 injects return_dict into")
        out.append(f"{indent}# model_inputs, which the inner LM call must not receive twice.")
        out.append(f"{indent}return_dict = None")
        n_fwd += 1
    out.append(line)
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"SOURCE patched: pop={n_pop} forward_swallow={n_fwd}")
PY

$PY -m py_compile "$SRC" && echo "COMPILE_OK"
grep -n "PATCHED-MINERU" "$SRC"
cp "$SRC" "$PROJ/outputs/modeling_internvl_chat.src.patched"

echo "--- clearing the HF remote-code cache so it is re-copied from source"
rm -rf "$MODCACHE"/*

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
  head -c 700 "$MD"; echo
fi
echo "### done $(date -Is)"
