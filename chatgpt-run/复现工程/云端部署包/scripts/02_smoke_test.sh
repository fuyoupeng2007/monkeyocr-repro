#!/usr/bin/env bash
set -Eeuo pipefail

export CONDA_ENVS_PATH=/root/autodl-tmp/conda_envs
export PATH=/root/miniconda3/bin:${PATH}
export HF_HOME=/root/autodl-tmp/.cache/huggingface
export MODELSCOPE_CACHE=/root/autodl-tmp/.cache/modelscope
export TMPDIR=/root/autodl-tmp/tmp

if [[ $# -ne 1 ]]; then
  echo "用法：bash scripts/02_smoke_test.sh <图片或PDF路径>" >&2
  exit 2
fi

REPRO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPRO_ROOT}/MonkeyOCR"
INPUT_PATH="$(realpath "$1")"
OUTPUT_DIR="${REPRO_ROOT}/outputs/smoke_test"

eval "$(conda shell.bash hook)"
conda activate monkeyocr
mkdir -p "${OUTPUT_DIR}"

python "${REPRO_ROOT}/scripts/verify_env.py" --repo "${REPO_DIR}"
cd "${REPO_DIR}"

START_TS=$(date +%s)
python parse.py "${INPUT_PATH}" -o "${OUTPUT_DIR}" -c model_configs.yaml
END_TS=$(date +%s)

echo "冒烟测试完成，耗时$((END_TS - START_TS))秒。"
echo "输出目录：${OUTPUT_DIR}"
find "${OUTPUT_DIR}" -maxdepth 2 -type f -printf '%p\n' | sort
