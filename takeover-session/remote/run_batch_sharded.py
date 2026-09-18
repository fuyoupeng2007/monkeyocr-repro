#!/usr/bin/env python3
"""Run MinerU 0.9.3 over the manifest, sharded by --shard/--shards, resumably.

Sharding is by manifest index modulo, so workers never touch the same page.
  <output_root>/predictions/<stem>.md  OmniDocBench-readable Markdown (empty on failure)
  <output_root>/raw/<stem>/...         raw magic-pdf output
  <output_root>/run_log_<shard>.jsonl  per-page status / timing
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mineru_to_omnidocbench_md import find_page_dir, markdown_for_page  # noqa: E402


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
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    all_rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = [(i, r) for i, r in enumerate(all_rows) if i % args.shards == args.shard]

    pred_dir = args.output_root / "predictions"
    raw_dir = args.output_root / "raw"
    pred_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    log = args.output_root / f"run_log_shard{args.shard}.jsonl"
    lock_dir = args.output_root / ".page_locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    claim = lock_dir / ".claim"
    claim.write_text(f"shard {args.shard}", encoding="utf-8")

    env = os.environ.copy()
    env["MINERU_TOOLS_CONFIG_JSON"] = str(args.config)

    for n, (index, row) in enumerate(rows, 1):
        stem = Path(Path(row["image_path"]).name).stem
        pdf = args.pdf_root / f"{stem}.pdf"
        pred = pred_dir / f"{stem}.md"
        event = {"image_path": row["image_path"], "stem": stem, "shard": args.shard,
                 "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        if pred.exists() and pred.stat().st_size > 0:
            print(f"[s{args.shard} {n}/{len(rows)}] SKIP {stem}", flush=True)
            continue
        # Claim the page atomically so concurrent workers never parse the same page
        # twice (which also corrupts their shared raw output directory).
        lock = lock_dir / f"{stem}.lock"
        try:
            os.link(claim, lock)
        except FileExistsError:
            print(f"[s{args.shard} {n}/{len(rows)}] BUSY {stem}", flush=True)
            continue
        except OSError:
            pass  # locking unavailable -> proceed (single-worker mode)
        page_out = raw_dir / stem
        page_out.mkdir(parents=True, exist_ok=True)
        try:
            if not pdf.exists():
                raise FileNotFoundError(pdf)
            print(f"[s{args.shard} {n}/{len(rows)}] RUN  {stem}", flush=True)
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
            event.update({"status": "ok", "seconds": round(seconds, 3), "chars": len(text), "source": kind})
            print(f"[s{args.shard} {n}/{len(rows)}] OK   {seconds:.2f}s chars={len(text)}", flush=True)
        except Exception as exc:
            pred.write_text("", encoding="utf-8")
            event.update({"status": "error", "error": repr(exc), "traceback": traceback.format_exc()})
            print(f"[s{args.shard} {n}/{len(rows)}] FAIL {exc!r}", flush=True)
        finally:
            try:
                lock.unlink(missing_ok=True)
            except Exception:
                pass
        append_jsonl(log, event)
    print(f"shard {args.shard} finished: {len(rows)} assigned")


if __name__ == "__main__":
    main()
