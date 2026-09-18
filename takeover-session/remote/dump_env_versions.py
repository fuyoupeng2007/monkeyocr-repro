#!/usr/bin/env python3
"""Dump the exact runtime versions of both experiment environments to JSON.

Recorded so the report can state precisely what was run, instead of "we installed
the official requirements". Output: outputs/env_versions.json
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJ = Path("/root/autodl-tmp/monkeyocr-repro")
BASE = Path("/root/autodl-tmp/conda_envs")
PKGS = ["magic-pdf", "magic_pdf", "torch", "torchvision", "transformers", "tokenizers",
        "huggingface_hub", "timm", "ultralytics", "unimernet", "doclayout_yolo",
        "struct-eqtable", "rapid-table", "rapidocr-paddle", "paddleocr", "paddlepaddle",
        "albumentations", "albucore", "numpy", "PyMuPDF", "scikit-learn", "pydantic",
        "opencv-python-headless", "detectron2", "Levenshtein", "func-timeout", "beautifulsoup4"]


def versions(env: str) -> dict:
    py = BASE / env / "bin/python"
    if not py.exists():
        return {}
    code = (
        "import json,importlib.metadata as m\n"
        f"names={PKGS!r}\n"
        "out={}\n"
        "for n in names:\n"
        "    try: out[n]=m.version(n)\n"
        "    except Exception: pass\n"
        "import sys; out['_python']=sys.version.split()[0]\n"
        "print(json.dumps(out))\n"
    )
    try:
        r = subprocess.run([str(py), "-c", code], capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"_error": repr(e)}


def main() -> None:
    data = {
        "container": "autodl-container-9d1044903a-e0797c2f",
        "gpu": subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                               "--format=csv,noheader"], capture_output=True, text=True).stdout.strip(),
        "cuda": subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                               capture_output=True, text=True).stdout.strip(),
        "envs": {},
    }
    for env in ("monkeyocr", "mineru093_env", "omnidocbench"):
        data["envs"][env] = versions(env)
    out = PROJ / "outputs" / "env_versions.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    for env, v in data["envs"].items():
        print(f"\n== {env}")
        for k in sorted(v):
            print(f"   {k:26s} {v[k]}")


if __name__ == "__main__":
    main()
