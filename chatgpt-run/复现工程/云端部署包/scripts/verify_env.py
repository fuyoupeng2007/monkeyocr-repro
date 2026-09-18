from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


def folder_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()

    import torch

    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count(),
        "gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        "repo": str(repo),
        "model_config_exists": (repo / "model_configs.yaml").is_file(),
        "weights_exists": (repo / "model_weight").is_dir(),
        "weights_bytes": folder_size(repo / "model_weight") if (repo / "model_weight").is_dir() else 0,
    }
    try:
        report["nvidia_smi"] = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True,
        ).strip()
    except Exception as exc:  # noqa: BLE001
        report["nvidia_smi_error"] = repr(exc)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    failures = []
    if not report["cuda_available"]:
        failures.append("PyTorch无法使用CUDA")
    if not report["model_config_exists"]:
        failures.append("缺少model_configs.yaml")
    if not report["weights_exists"] or report["weights_bytes"] < 1_000_000_000:
        failures.append("模型权重缺失或下载不完整")
    if failures:
        print("环境检查失败：" + "；".join(failures), file=sys.stderr)
        return 1
    print("环境检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

