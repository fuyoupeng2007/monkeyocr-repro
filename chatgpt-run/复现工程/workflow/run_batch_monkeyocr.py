#!/usr/bin/env python3
"""Run MonkeyOCR once-loaded, resumable inference over a frozen manifest."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
import traceback
from pathlib import Path

import torch

from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
from magic_pdf.data.dataset import ImageDataset
from magic_pdf.model.custom_model import MonkeyOCR
from magic_pdf.model.doc_analyze_by_custom_model_llm import doc_analyze_llm


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def parse_one(model: MonkeyOCR, input_file: Path, page_dir: Path) -> dict:
    stem = input_file.stem
    image_dir = page_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    page_dir.mkdir(parents=True, exist_ok=True)
    image_writer = FileBasedDataWriter(str(image_dir))
    md_writer = FileBasedDataWriter(str(page_dir))
    file_bytes = FileBasedDataReader().read(str(input_file))
    ds = ImageDataset(file_bytes)

    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    infer_result = ds.apply(doc_analyze_llm, MonkeyOCR_model=model)
    pipe_result = infer_result.pipe_ocr_mode(image_writer, MonkeyOCR_model=model)
    seconds = time.perf_counter() - started

    infer_result.draw_model(str(page_dir / f"{stem}_model.pdf"))
    pipe_result.draw_layout(str(page_dir / f"{stem}_layout.pdf"))
    pipe_result.draw_span(str(page_dir / f"{stem}_spans.pdf"))
    pipe_result.dump_md(md_writer, f"{stem}.md", "images")
    pipe_result.dump_content_list(md_writer, f"{stem}_content_list.json", "images")
    pipe_result.dump_middle_json(md_writer, f"{stem}_middle.json")
    return {
        "seconds": round(seconds, 4),
        "peak_vram_mib": round(torch.cuda.max_memory_allocated() / 1024 / 1024, 1),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--pilot-only", action="store_true")
    args = p.parse_args()

    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    if args.pilot_only:
        rows = [x for x in rows if x["pilot"]]
    args.output_root.mkdir(parents=True, exist_ok=True)
    predictions = args.output_root / "predictions"
    pages_dir = args.output_root / "pages"
    predictions.mkdir(exist_ok=True)
    pages_dir.mkdir(exist_ok=True)
    log_path = args.output_root / "run_log.jsonl"

    print(f"Loading MonkeyOCR once for {len(rows)} pages", flush=True)
    load_started = time.perf_counter()
    model = MonkeyOCR(str(args.config))
    print(f"Model loaded in {time.perf_counter() - load_started:.2f}s", flush=True)

    for n, row in enumerate(rows, 1):
        input_file = args.data_root / row.get("local_image_path", row["image_path"])
        stem = input_file.stem
        pred_path = predictions / f"{stem}.md"
        page_dir = pages_dir / stem
        if pred_path.exists() and pred_path.stat().st_size > 0:
            print(f"[{n}/{len(rows)}] SKIP {input_file.name}", flush=True)
            continue
        event = {"image_path": row["image_path"], "stem": stem, "pilot": row["pilot"], "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        try:
            print(f"[{n}/{len(rows)}] RUN  {input_file.name}", flush=True)
            metrics = parse_one(model, input_file, page_dir)
            shutil.copy2(page_dir / f"{stem}.md", pred_path)
            event.update(metrics)
            event["status"] = "ok"
            print(f"[{n}/{len(rows)}] OK   {metrics['seconds']:.2f}s {metrics['peak_vram_mib']:.0f}MiB", flush=True)
        except Exception as exc:
            event.update({"status": "error", "error": repr(exc), "traceback": traceback.format_exc()})
            print(f"[{n}/{len(rows)}] FAIL {exc!r}", flush=True)
        append_jsonl(log_path, event)


if __name__ == "__main__":
    main()
