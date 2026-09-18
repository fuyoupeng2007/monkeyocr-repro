#!/bin/bash
# Authoritative fix for the SDPA error: set the attention implementation on the
# config *before* transformers' PreTrainedModel.__init__ runs its autoset check.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_attn2.log
exec > >(tee -a "$LOG") 2>&1
echo "### attn patch v2 started $(date -Is)"

F=$SP/unimernet/models/unimernet/encoder_decoder.py
cp "$F" "$PROJ/outputs/unimernet_encoder_decoder.py.orig"

$PY - "$F" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
marker = "# PATCHED (MinerU repro): eager attention"
if marker in src:
    print("already patched"); raise SystemExit
# for every `def __init__(self, config...):` followed by super().__init__(config)
# inside this file, force eager attention first.
pattern = re.compile(r"(    def __init__\(self, config[^\n]*\):\n)((?:        [^\n]*\n)*?)(        super\(\)\.__init__\(config\))")
n = 0
def repl(m):
    global n
    n += 1
    return (m.group(1) + m.group(2)
            + "        # " + marker[2:] + " (transformers>=4.48 autoset otherwise picks SDPA,\n"
            + "        # which unimernet's custom MBart/vision modules do not implement)\n"
            + "        config._attn_implementation = 'eager'\n"
            + m.group(3))
src = pattern.sub(repl, src)
p.write_text(src, encoding="utf-8")
print(f"patched {n} __init__ site(s)")
PY
cp "$F" "$PROJ/outputs/unimernet_encoder_decoder.py.patched"
echo "--- patched sites:"; grep -n "eager attention" -A2 "$F" | head -20

# the earlier Unimernet.py patch: check whether it actually landed
echo "--- Unimernet.py patch state:"; grep -n "PATCHED" "$SP/magic_pdf/model/sub_modules/mfr/unimernet/Unimernet.py" | head -5 || echo "(none)"

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
