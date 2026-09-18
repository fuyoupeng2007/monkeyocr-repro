#!/usr/bin/env python3
"""Run MinerU 0.9.3 over the OmniDocBench subset manifest, resumably.

Layout mirrors the MonkeyOCR formal run so the two are scored identically:
  <output_root>/raw/<stem>/...        raw magic-pdf output
  <output_root>/predictions/<stem>.md OmniDocBench-readable Markdown
  <output_root>/run_log.jsonl         per page status / timing
Failed pages get an empty prediction file (counted as a miss by the scorer).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import traceback
from pathlib import Path

from mineru_to_omnidocbench_md import blocks_to_markdown, find_page_dir, markdown_for_page


def append_jsonl(path: Path, item: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--pdf-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--magic-pdf", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    if args.limit:
        rows = rows[: args.limit]

    pred_dir = args.output_root / "predictions"
    raw_dir = args.output_root / "raw"
    pred_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    log = args.output_root / "run_log.jsonl"

    env = os.environ.copy()
    env["MINERU_TOOLS_CONFIG_JSON"] = str(args.config)

    for index, row in enumerate(rows, 1):
        stem = Path(Path(row["image_path"]).name).stem
        pdf = args.pdf_root / f"{stem}.pdf"
        pred = pred_dir / f"{stem}.md"
        event = {"image_path": row["image_path"], "stem": stem,
                 "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        if pred.exists() and pred.stat().st_size > 0:
            print(f"[{index}/{len(rows)}] SKIP {stem}", flush=True)
            continue
        page_out = raw_dir / stem
        page_out.mkdir(parents=True, exist_ok=True)
        try:
            if not pdf.exists():
                raise FileNotFoundError(pdf)
            print(f"[{index}/{len(rows)}] RUN  {stem}", flush=True)
            started = time.perf_counter()
            cp = subprocess.run([str(args.magic_pdf), "-p", str(pdf), "-o", str(page_out), "-m", "ocr"],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=args.timeout)
            seconds = time.perf_counter() - started
            (page_out / "cli.log").write_text(cp.stdout or "", encoding="utf-8", errors="replace")
            if cp.returncode != 0:
                raise RuntimeError(f"magic-pdf exit {cp.returncode}")
            text, kind = markdown_for_page(find_page_dir(page_out, stem), stem)
            if not text.strip():
                raise RuntimeError("empty markdown from MinerU")
            pred.write_text(text, encoding="utf-8")
            event.update({"status": "ok", "seconds": round(seconds, 3),
                          "chars": len(text), "source": kind})
            print(f"[{index}/{len(rows)}] OK   {seconds:.2f}s chars={len(text)} ({kind})", flush=True)
        except Exception as exc:
            pred.write_text("", encoding="utf-8")
            event.update({"status": "error", "error": repr(exc), "traceback": traceback.format_exc()})
            print(f"[{index}/{len(rows)}] FAIL {exc!r}", flush=True)
        append_jsonl(log, event)

    done = sum(1 for line in log.read_text(encoding="utf-8").splitlines() if line.strip())
    print(f"run_log entries: {done}")


if __name__ == "__main__":
    main()
