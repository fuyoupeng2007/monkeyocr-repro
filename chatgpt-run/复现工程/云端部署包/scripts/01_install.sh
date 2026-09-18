#!/usr/bin/env bash
set -Eeuo pipefail

REPRO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPRO_ROOT}/MonkeyOCR"
ENV_NAME="monkeyocr"
EXPECTED_COMMIT="b5e94d3aed972e2e07e7d5c654a0dc588419f4b9"

echo "[1/8] 检查NVIDIA GPU"
nvidia-smi

echo "[2/8] 初始化conda"
if ! command -v conda >/dev/null 2>&1; then
  echo "未找到conda。请在AutoDL选择带Miniconda/Anaconda的PyTorch镜像。" >&2
  exit 2
fi
eval "$(conda shell.bash hook)"

if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "复用现有环境：${ENV_NAME}"
else
  conda create -y -n "${ENV_NAME}" python=3.10
fi
conda activate "${ENV_NAME}"

echo "[3/8] 检查固定代码版本"
if [[ ! -d "${REPO_DIR}" ]]; then
  echo "未找到${REPO_DIR}，请完整上传部署包。" >&2
  exit 3
fi
if [[ -f "${REPO_DIR}/REPRO_COMMIT.txt" ]]; then
  grep -qx "${EXPECTED_COMMIT}" "${REPO_DIR}/REPRO_COMMIT.txt"
fi

echo "[4/8] 安装PyTorch CUDA 12.4"
python -m pip install --upgrade pip setuptools wheel

# AutoDL基础镜像已经带有与目标版本完全一致的CUDA 12.4运行库。
# 复用这些只读库可避免在50GB数据盘中重复保存约3.2GB文件。
TARGET_SITE="$(python -c 'import site; print(site.getsitepackages()[0])')"
BASE_SITE="/root/miniconda3/lib/python3.12/site-packages"
if [[ -d "${BASE_SITE}/nvidia" ]]; then
  ln -sfn "${BASE_SITE}/nvidia" "${TARGET_SITE}/nvidia"
  for metadata in "${BASE_SITE}"/nvidia_*.dist-info; do
    [[ -e "${metadata}" ]] || continue
    ln -sfn "${metadata}" "${TARGET_SITE}/$(basename "${metadata}")"
  done
else
  echo "基础镜像缺少匹配的CUDA运行库，停止以避免静默使用错误版本。" >&2
  exit 4
fi

# Triton包含Python ABI扩展，不能复用基础镜像的Python 3.12文件。
if [[ -L "${TARGET_SITE}/triton" ]]; then
  unlink "${TARGET_SITE}/triton"
fi
if [[ -L "${TARGET_SITE}/triton-3.1.0.dist-info" ]]; then
  unlink "${TARGET_SITE}/triton-3.1.0.dist-info"
fi
python -m pip install --no-deps \
  '/root/autodl-tmp/wheels/triton-3.1.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'

python -m pip install \
  --no-deps \
  '/root/autodl-tmp/wheels/torch-2.5.1+cu124-cp310-cp310-linux_x86_64.whl' \
  'https://mirrors.aliyun.com/pytorch-wheels/cu124/torchvision-0.20.1%2Bcu124-cp310-cp310-linux_x86_64.whl' \
  'https://mirrors.aliyun.com/pytorch-wheels/cu124/torchaudio-2.5.1%2Bcu124-cp310-cp310-linux_x86_64.whl'
python -m pip install filelock 'typing-extensions>=4.8.0' networkx jinja2 fsspec 'sympy==1.13.1' numpy pillow

python -c 'import torch; assert torch.cuda.is_available(); x=torch.ones(64,64,device="cuda"); y=x@x; torch.cuda.synchronize(); print("PyTorch CUDA验证通过:", torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), float(y[0,0]))'

echo "[5/8] 安装MonkeyOCR官方依赖"
# LMDeploy及Ray体积较大，先从已校验的本地wheel安装，避免慢速网络中断后反复下载。
python -m pip install '/root/autodl-tmp/wheels/ray-2.58.0-cp310-cp310-manylinux2014_x86_64.whl'
python -m pip install '/root/autodl-tmp/wheels/lmdeploy-0.8.0-cp310-cp310-manylinux2014_x86_64.whl'
# OpenCV 4.12+在Python 3.9+要求NumPy 2，而MonkeyOCR固定NumPy<2。
# 预装4.11可阻止pip依次下载多个不兼容候选版本进行回溯。
python -m pip install --no-deps \
  '/root/autodl-tmp/wheels/opencv_python-4.11.0.86-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl' \
  '/root/autodl-tmp/wheels/opencv_python_headless-4.11.0.86-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'
python -m pip install -e "${REPO_DIR}"
# parse.py直接导入pdf2image，但上游pyproject未声明它。
python -m pip install huggingface_hub modelscope pdf2image dill

echo "[6/8] 下载原版MonkeyOCR权重（默认ModelScope）"
cd "${REPO_DIR}"
python tools/download_model.py -t modelscope

echo "[7/8] 应用官方3090/4090 LMDeploy补丁"
python tools/lmdeploy_patcher.py patch

echo "[8/8] 验证环境"
python "${REPRO_ROOT}/scripts/verify_env.py" --repo "${REPO_DIR}"

echo "安装完成。请运行：bash scripts/02_smoke_test.sh <图片或不超过5页的PDF>"
