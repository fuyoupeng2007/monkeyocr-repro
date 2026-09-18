#!/usr/bin/env python3
"""Run the frozen MinerU 0.9.3 CLI over a manifest and flatten Markdown outputs.

Every manifest entry receives a prediction file.  Failed parses receive an empty
file so the official evaluator counts them as misses rather than silently
dropping them.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import traceback
from pathlib import Path


def append_jsonl(path: Path, item: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--pdf-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--magic-pdf", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    args = p.parse_args()

    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    pred_dir = args.output_root / "predictions"
    raw_dir = args.output_root / "raw"
    pred_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    log = args.output_root / "run_log.jsonl"
    env = os.environ.copy()
    env["MINERU_TOOLS_CONFIG_JSON"] = str(args.config)

    for index, row in enumerate(rows, 1):
        image_name = Path(row["image_path"]).name
        stem = Path(image_name).stem
        pdf = args.pdf_root / f"{stem}.pdf"
        pred = pred_dir / f"{stem}.md"
        event = {"image_path": row["image_path"], "stem": stem,
                 "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        if pred.exists():
            print(f"[{index}/{len(rows)}] SKIP {stem}", flush=True)
            continue
        page_out = raw_dir / stem
        page_out.mkdir(parents=True, exist_ok=True)
        try:
            if not pdf.exists():
                raise FileNotFoundError(pdf)
            print(f"[{index}/{len(rows)}] RUN  {pdf.name}", flush=True)
            started = time.perf_counter()
            cp = subprocess.run([str(args.magic_pdf), "-p", str(pdf), "-o", str(page_out), "-m", "ocr"],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=600)
            seconds = time.perf_counter() - started
            (page_out / "cli.log").write_text(cp.stdout, encoding="utf-8", errors="replace")
            if cp.returncode != 0:
                raise RuntimeError(f"magic-pdf exit {cp.returncode}")
            candidates = sorted(page_out.rglob("*.md"), key=lambda x: (x.name != f"{stem}.md", len(x.parts)))
            if not candidates:
                raise FileNotFoundError("MinerU produced no Markdown file")
            shutil.copy2(candidates[0], pred)
            event.update({"status": "ok", "seconds": round(seconds, 4), "markdown": str(candidates[0])})
            print(f"[{index}/{len(rows)}] OK   {seconds:.2f}s", flush=True)
        except Exception as exc:
            pred.write_text("", encoding="utf-8")
            event.update({"status": "error", "error": repr(exc), "traceback": traceback.format_exc()})
            print(f"[{index}/{len(rows)}] FAIL {exc!r}", flush=True)
        append_jsonl(log, event)


if __name__ == "__main__":
    main()
