#!/usr/bin/env bash
set -Eeuo pipefail

export CONDA_ENVS_PATH=/root/autodl-tmp/conda_envs
export PATH=/root/miniconda3/bin:${PATH}
export PIP_CACHE_DIR=/root/autodl-tmp/.cache/pip
export HF_HOME=/root/autodl-tmp/.cache/huggingface
export MODELSCOPE_CACHE=/root/autodl-tmp/.cache/modelscope
export TMPDIR=/root/autodl-tmp/tmp

mkdir -p \
  "${CONDA_ENVS_PATH}" \
  "${PIP_CACHE_DIR}" \
  "${HF_HOME}" \
  "${MODELSCOPE_CACHE}" \
  "${TMPDIR}"

cd /root/autodl-tmp/monkeyocr-repro
bash scripts/01_install.sh
