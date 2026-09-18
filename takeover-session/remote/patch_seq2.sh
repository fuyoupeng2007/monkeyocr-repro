#!/bin/bash
# Robust line-based patch of StructEqTable's remote-code model:
#   1) generate(): drop return_dict from **generate_kwargs  (avoid duplicate kwarg)
#   2) forward():  swallow the return_dict that transformers' generate injects
#      into model_inputs (transformers >=4.50 calls self(**model_inputs, return_dict=True))
# Both are verified after writing, and the file is syntactically compiled.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
F=/root/.cache/huggingface/modules/transformers_modules/StructEqTable/modeling_internvl_chat.py
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/patch_seq2.log
exec > >(tee -a "$LOG") 2>&1
echo "### structeqtable patch v2 started $(date -Is)"

[ -f "$PROJ/outputs/modeling_internvl_chat.py.orig" ] || cp "$F" "$PROJ/outputs/modeling_internvl_chat.py.orig"

$PY - "$F" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").splitlines()

def already(txt): return "PATCHED-MINERU" in txt
out = []
i = 0
n_pop = n_fwd = 0
while i < len(lines):
    line = lines[i]
    # (1) inside generate(): inject pop right before language_model.generate(
    if line.strip() == "outputs = self.language_model.generate(" and not any(already(l) for l in lines[max(0,i-6):i]):
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}# PATCHED-MINERU: return_dict also arrives via **generate_kwargs;")
        out.append(f"{indent}# transformers' generate then forwards it twice to the LM.")
        out.append(f'{indent}generate_kwargs.pop("return_dict", None)')
        n_pop += 1
    # (2) inside forward(): swallow return_dict injected into model_inputs
    if re.match(r"\s*return_dict = return_dict if return_dict is not None else self\.config\.use_return_dict\s*$", line):
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}# PATCHED-MINERU: transformers>=4.50 injects return_dict into")
        out.append(f"{indent}# model_inputs; the inner LM call must not receive it twice.")
        out.append(f"{indent}return_dict = None")
        n_fwd += 1
    out.append(line)
    i += 1

src = "\n".join(out) + "\n"
# (3) belt and braces: strip a doubled return_dict at the inner LM call site
src = src.replace(
    "            output_hidden_states=output_hidden_states,\n            return_dict=return_dict,\n",
    "            output_hidden_states=output_hidden_states,\n            return_dict=return_dict,\n",
)
p.write_text(src, encoding="utf-8")
print(f"injected pop={n_pop} forward_swallow={n_fwd}")
PY

echo "--- verification ---"
grep -n "PATCHED-MINERU" "$F" | head -10
echo "--- compile check ---"
$PY -m py_compile "$F" && echo "COMPILE_OK"
cp "$F" "$PROJ/outputs/modeling_internvl_chat.py.patched_v2"

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
