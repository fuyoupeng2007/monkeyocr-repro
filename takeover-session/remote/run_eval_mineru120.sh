#!/bin/bash
# Official OmniDocBench end2end evaluation of the MinerU 120-page predictions,
# byte-for-byte the same config/metrics/match_method as the MonkeyOCR formal run.
set -u
PROJ=/root/autodl-tmp/monkeyocr-repro
export NO_ALBUMENTATIONS_UPDATE=1
LOG=$PROJ/outputs/eval_mineru_120.log
exec > >(tee -a "$LOG") 2>&1
echo "### MinerU 120 evaluation started $(date -Is)"

PRED=$PROJ/outputs/mineru_formal_120/predictions
echo "predictions: $(ls "$PRED" | wc -l) files, non-empty: $(find "$PRED" -name '*.md' -size +0 | wc -l)"

cd $PROJ/OmniDocBench || exit 1
/root/autodl-tmp/conda_envs/omnidocbench/bin/python pdf_validation.py --config $PROJ/configs/eval_mineru_120.yaml
echo "### eval rc=$?"

echo "=== new result files ==="
ls -la result/ | grep -i "mineru_formal_120" || echo "(none matched)"
echo "=== headline metrics ==="
F=result/mineru_formal_120_quick_match_metric_result.json
if [ -f "$F" ]; then
  /root/autodl-tmp/conda_envs/omnidocbench/bin/python - "$F" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
def g(path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur: return default
        cur = cur[k]
    return cur
print("text_block   Edit_dist ALL_page_avg :", g(["text_block","all","Edit_dist","ALL_page_avg"]))
print("display_formula Edit_dist ALL      :", g(["display_formula","all","Edit_dist","ALL_page_avg"]))
print("table        TEDS all              :", g(["table","all","TEDS","all"]))
print("table        TEDS_structure_only   :", g(["table","all","TEDS_structure_only","all"]))
print("table        Edit_dist ALL_page_avg:", g(["table","all","Edit_dist","ALL_page_avg"]))
print("reading_order Edit_dist ALL        :", g(["reading_order","all","Edit_dist","ALL_page_avg"]))
PY
else
  echo "metric file not found: $F"
fi
echo "### MinerU 120 evaluation done $(date -Is)"
