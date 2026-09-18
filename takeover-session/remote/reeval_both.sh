#!/bin/bash
# Re-evaluate BOTH baselines under model-specific result prefixes so their result
# files can never collide again.
#
# The official scorer names its output after the basename of
# dataset.prediction.data_path, so each model gets its own prediction directory
# (copied, not symlinked) plus its own config.
set -u
PROJ=/root/autodl-tmp/monkeyocr-repro
PY_O=/root/autodl-tmp/conda_envs/omnidocbench/bin/python
LOG=$PROJ/outputs/reeval_both.log
exec > >(tee -a "$LOG") 2>&1
echo "### re-evaluation started $(date -Is)"

for M in monkeyocr mineru; do
  SRC=$PROJ/outputs/${M}_formal_120/predictions
  DST=$PROJ/outputs/eval_inputs/${M}_formal_120
  rm -rf "$DST"; mkdir -p "$DST"
  if [ -d "$SRC" ]; then
    cp -a "$SRC"/. "$DST"/ 2>/dev/null
    echo "$M: copied $(ls "$DST" | wc -l) predictions (non-empty $(find "$DST" -name '*.md' -size +0 | wc -l))"
  else
    echo "$M: no predictions at $SRC"
  fi
done

cat > $PROJ/configs/eval_monkeyocr_120.yaml <<YAML
end2end_eval:
  metrics:
    text_block:
      metric: [Edit_dist]
    display_formula:
      metric: [Edit_dist, CDM]
    table:
      metric: [TEDS, Edit_dist]
    reading_order:
      metric: [Edit_dist]
  dataset:
    dataset_name: end2end_dataset
    ground_truth:
      data_path: $PROJ/data/omnidocbench_v1_0/subsets/formal_120.json
    prediction:
      data_path: $PROJ/outputs/eval_inputs/monkeyocr_formal_120
    match_method: quick_match
YAML

cat > $PROJ/configs/eval_mineru_120.yaml <<YAML
end2end_eval:
  metrics:
    text_block:
      metric: [Edit_dist]
    display_formula:
      metric: [Edit_dist, CDM]
    table:
      metric: [TEDS, Edit_dist]
    reading_order:
      metric: [Edit_dist]
  dataset:
    dataset_name: end2end_dataset
    ground_truth:
      data_path: $PROJ/data/omnidocbench_v1_0/subsets/formal_120.json
    prediction:
      data_path: $PROJ/outputs/eval_inputs/mineru_formal_120
    match_method: quick_match
YAML

cd $PROJ/OmniDocBench || exit 1
for M in monkeyocr mineru; do
  echo "### evaluating $M $(date -Is)"
  $PY_O pdf_validation.py --config $PROJ/configs/eval_${M}_120.yaml
  echo "### $M exit=$?"
done

echo "=== result files ==="
ls -la --time-style=+%H:%M:%S result/ | grep -E "monkeyocr_formal_120|mineru_formal_120" | head -25

echo "### rebuilding comparison $(date -Is)"
$PY_O $PROJ/scripts/build_comparison.py 2>&1 | head -20
echo "### rebuilding deliverables $(date -Is)"
$PY_O $PROJ/scripts/build_deliverables.py 2>&1 | tail -8
echo "### re-evaluation finished $(date -Is)"
