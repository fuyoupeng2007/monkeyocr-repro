#!/bin/bash
# FINAL FIX for the 09:43 blocker.
#
# Evidence (minimal repro on this env): with transformers 4.50.0,
#   Qwen2ForCausalLM.generate(..., return_dict=False/True)
# raises "The following model_kwargs are not used by the model: ['return_dict']",
# and when it does get through, it lands in model_kwargs and the generation loop
# calls the model as self(**model_inputs, return_dict=True) -> the LM's forward
# receives return_dict twice ("got multiple values for keyword argument").
#
# StructEqTable's wrapper passes return_dict down to language_model.generate()
# because its caller (struct_eqtable.internvl) calls generate(..., return_dict=True).
# Fix: never forward it. Do it on the real source snapshot as well as the live
# cache, since transformers re-copies remote code from the snapshot each import.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
SNAP=/root/.cache/modelscope/models/opendatalab--PDF-Extract-Kit-1.0/snapshots/master/models/TabRec/StructEqTable/modeling_internvl_chat.py
CACHE=/root/.cache/huggingface/modules/transformers_modules/StructEqTable/modeling_internvl_chat.py
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/final_fix_returndict.log
exec > >(tee -a "$LOG") 2>&1
echo "### final return_dict fix started $(date -Is)"

patch_file() {
  local F="$1"
  [ -f "$F" ] || { echo "  (skip, absent: $F)"; return; }
  $PY - "$F" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
before = src
# 1) generate(): do not pass return_dict into the LM's generate at all
src = src.replace(
    "            output_hidden_states=output_hidden_states,\n            return_dict=return_dict,\n            use_cache=True,\n",
    "            output_hidden_states=output_hidden_states,\n"
    "            # PATCHED-MINERU2: transformers>=4.50 rejects return_dict as a generate()\n"
    "            # kwarg and leaks it into model_kwargs, where the sampling loop then passes\n"
    "            # it to the model a second time. Never forward it.\n"
    "            return_dict=None,\n"
    "            use_cache=True,\n",
)
# 2) forward(): swallow the return_dict the generation loop injects
src = re.sub(
    r"(\n)(\s*)return_dict = return_dict if return_dict is not None else self\.config\.use_return_dict",
    lambda m: (m.group(1) + m.group(2)
               + "# PATCHED-MINERU2: tolerate the return_dict injected by transformers' generation loop\n"
               + m.group(2) + "return_dict = None"),
    src, count=1,
)
p.write_text(src, encoding="utf-8")
print(f"  patched={src != before}  return_dict=None count={src.count('return_dict=None')}")
PY
  $PY -m py_compile "$F" && echo "  compile OK: $F"
}

echo "--- source snapshot"; patch_file "$SNAP"
echo "--- live cache";      patch_file "$CACHE"
echo "--- verify marked lines"
grep -n "PATCHED-MINERU2" "$SNAP" | head
cp "$SNAP" "$PROJ/outputs/modeling_internvl_chat.final.py"
cp "$CACHE" "$PROJ/outputs/modeling_internvl_chat.runtime_final.py"

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
