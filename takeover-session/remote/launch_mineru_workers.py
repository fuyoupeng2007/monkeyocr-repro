#!/usr/bin/env python3
"""Launch N MinerU workers with guaranteed correct cwd and absolute config paths.

magic-pdf's CLI does
    if not os.path.exists('./configs/mineru093/magic-pdf.json'): exit(1)
when MINERU_TOOLS_CONFIG_JSON is unset, so every worker MUST run with cwd set to
the project root and an absolute --config / --pdf-root / --output-root.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

PROJ = Path("/root/autodl-tmp/monkeyocr-repro")
ENV_PY = Path("/root/autodl-tmp/conda_envs/mineru093_env/bin/python")
ENV_MAGIC = Path("/root/autodl-tmp/conda_envs/mineru093_env/bin/magic-pdf")
MANIFEST = PROJ / "data/omnidocbench_v1_0/subsets/manifest_120.jsonl"
PDF_ROOT = PROJ / "data/omnidocbench_v1_0/mineru_input_pdfs"
OUTPUT_ROOT = PROJ / "outputs/mineru_formal_120"
CONFIG = PROJ / "configs/mineru093/magic-pdf.json"
RUNNER = PROJ / "scripts/run_batch_sharded.py"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=3600,
                    help="per-page magic-pdf timeout; dense table/formula pages on a "
                         "shared host can exceed 15 min, so 3600 avoids discarding work")
    args = ap.parse_args()

    env = os.environ.copy()
    env.update({
        "NO_ALBUMENTATIONS_UPDATE": "1",
        "MODELSCOPE_CACHE": "/root/.cache/modelscope",
        "HF_HOME": "/root/.cache/huggingface",
        "MINERU_TOOLS_CONFIG_JSON": str(CONFIG),
    })
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    procs = []
    for s in range(args.shards):
        log = open(OUTPUT_ROOT / f"shard_{s}.log", "a", encoding="utf-8")
        p = subprocess.Popen(
            [str(ENV_PY), str(RUNNER),
             "--manifest", str(MANIFEST),
             "--pdf-root", str(PDF_ROOT),
             "--output-root", str(OUTPUT_ROOT),
             "--magic-pdf", str(ENV_MAGIC),
             "--config", str(CONFIG),
             "--shard", str(s), "--shards", str(args.shards),
             "--timeout", str(args.timeout)],
            cwd=str(PROJ), env=env, stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
        procs.append((s, p, log))
        print(f"shard {s} pid={p.pid} cwd={PROJ}", flush=True)
        time.sleep(6)

    while any(p.poll() is None for _, p, _ in procs):
        n = len(list((OUTPUT_ROOT / "predictions").glob("*.md")))
        nz = len([f for f in (OUTPUT_ROOT / "predictions").glob("*.md") if f.stat().st_size > 0])
        print(f"[{time.strftime('%H:%M:%S')}] predictions={n}/120 non-empty={nz}", flush=True)
        time.sleep(180)

    for s, p, log in procs:
        log.close()
        print(f"shard {s} exit={p.returncode}", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
