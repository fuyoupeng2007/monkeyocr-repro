#!/bin/bash
# transformers>=4.48 auto-enables SDPA; unimernet's CustomMBartDecoder does not
# implement it, so model construction raises. Pin the attention implementation to
# "eager" at the two construction sites in MinerU's unimernet wrapper.
set -u
ENV=/root/autodl-tmp/conda_envs/mineru093_env
PY=$ENV/bin/python
SP=$ENV/lib/python3.10/site-packages
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
export MODELSCOPE_CACHE=/root/.cache/modelscope
export HF_HOME=/root/.cache/huggingface
export MINERU_TOOLS_CONFIG_JSON=$PROJ/configs/mineru093/magic-pdf.json
LOG=$PROJ/outputs/env_patch_attn.log
exec > >(tee -a "$LOG") 2>&1
echo "### attn patch started $(date -Is)"

F=$SP/magic_pdf/model/sub_modules/mfr/unimernet/Unimernet.py
echo "=== relevant lines ==="
grep -n "from_pretrained\|config\|attn" "$F" | head -25
cp "$F" "$PROJ/outputs/magicpdf_unimernet.py.orig"

$PY - "$F" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1])
src = p.read_text(encoding="utf-8")
if "PATCHED (MinerU repro): force eager attention" in src:
    print("already patched"); raise SystemExit
# insert a forced-eager marker for every direct model construction
n = 0
def force(m):
    global n
    n += 1
    return f"{m.group(0)}\n        # PATCHED (MinerU repro): force eager attention (custom MBart decoder has no SDPA)\n        try:\n            _m.config._attn_implementation = 'eager'\n        except Exception:\n            pass"
src2 = re.sub(r"=\s*UniMERNet\.from_pretrained\([^\n]*\)", force, src)
src2 = re.sub(r"=\s*CustomMBartForCausalLM\.from_pretrained\([^\n]*\)", force, src2)
if n == 0:
    print("no from_pretrained site matched; showing file for manual patch")
    print("\n".join(f"{i+1}: {l}" for i, l in enumerate(src.splitlines()) if "from_pretrained" in l))
    raise SystemExit(1)
p.write_text(src2, encoding="utf-8")
print(f"patched {n} construction site(s)")
PY
cp "$F" "$PROJ/outputs/magicpdf_unimernet.py.patched"

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
