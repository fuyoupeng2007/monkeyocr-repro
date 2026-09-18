#!/usr/bin/env python3
"""Make one PDF per benchmark image for legacy MinerU 0.9.3 input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in args.manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    for row in rows:
        src = args.data_root / row.get("local_image_path", row["image_path"])
        dst = args.output / f"{src.stem}.pdf"
        if dst.exists() and dst.stat().st_size > 0:
            continue
        with Image.open(src) as im:
            im.convert("RGB").save(dst, "PDF", resolution=150.0)
    print(f"prepared {len(list(args.output.glob('*.pdf')))} PDFs")


if __name__ == "__main__":
    main()
