#!/usr/bin/env python3
"""Download the model assets used by the official MinerU 0.9.3 script.

This variant writes a project-local config instead of modifying the account-wide
``~/magic-pdf.json``.  The selected package and upstream script are pinned in
the experiment manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from modelscope import snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    patterns = [
        "models/Layout/LayoutLMv3/*",
        "models/Layout/YOLO/*",
        "models/MFD/YOLO/*",
        "models/MFR/unimernet_small/*",
        "models/TabRec/TableMaster/*",
        "models/TabRec/StructEqTable/*",
    ]
    extract_root = Path(snapshot_download("opendatalab/PDF-Extract-Kit-1.0", allow_patterns=patterns))
    layoutreader_root = Path(snapshot_download("ppaanngggg/layoutreader"))
    config = {
        "config_version": "1.0.0",
        "models-dir": str(extract_root / "models"),
        "layoutreader-model-dir": str(layoutreader_root),
        "device-mode": "cuda",
        "layout-config": {"model": "doclayout_yolo"},
        "table-config": {"model": "struct_eqtable", "enable": True, "max_time": 400},
        "provenance": {
            "mineru_package": "magic-pdf==0.9.3",
            "mineru_git_tag": "magic_pdf-0.9.3-released",
            "model_download_script_source": "MinerU_0.9.3/scripts/download_models.py",
            "modelscope_model": "opendatalab/PDF-Extract-Kit-1.0",
            "layoutreader_modelscope_model": "ppaanngggg/layoutreader",
        },
    }
    args.config.parent.mkdir(parents=True, exist_ok=True)
    args.config.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
