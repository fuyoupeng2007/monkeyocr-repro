#!/bin/bash
# FIX for the original 09:43 failure:
#   TypeError: Qwen2ForCausalLM(...) got multiple values for keyword argument 'return_dict'
# StructEqTable's remote-code InternVLChatModel.generate passes return_dict BOTH as a
# named parameter to self.language_model.generate AND (via **generate_kwargs) into
# transformers' generate/_sample path, which then passes it again to the model.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
PROJ=/root/autodl-tmp/monkeyocr-repro
F=/root/.cache/huggingface/modules/transformers_modules/StructEqTable/modeling_internvl_chat.py
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_structeqtable.log
exec > >(tee -a "$LOG") 2>&1
echo "### structeqtable patch started $(date -Is)"

cp "$F" "$PROJ/outputs/modeling_internvl_chat.py.orig" 2>/dev/null || true

$PY - "$F" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
marker = "# PATCHED (MinerU repro)"
if marker in src:
    print("already patched"); raise SystemExit
old = """        outputs = self.language_model.generate(
            inputs_embeds=input_embeds,
            attention_mask=attention_mask,
            generation_config=generation_config,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            use_cache=True,
            **generate_kwargs,
        )"""
new = """        # PATCHED (MinerU repro): return_dict arrives both explicitly and through
        # **generate_kwargs; transformers' generate/_sample then forwards it twice to
        # the language model -> "got multiple values for keyword argument 'return_dict'".
        generate_kwargs.pop("return_dict", None)
        outputs = self.language_model.generate(
            inputs_embeds=input_embeds,
            attention_mask=attention_mask,
            generation_config=generation_config,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            use_cache=True,
            **generate_kwargs,
        )"""
assert old in src, "anchor not found"
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("patched", p)
PY
cp "$F" "$PROJ/outputs/modeling_internvl_chat.py.patched"

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
else
  echo "=== last 25 lines of the run (error context) ==="
  tail -25 "$LOG"
fi
echo "### done $(date -Is)"
