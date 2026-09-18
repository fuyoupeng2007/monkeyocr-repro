#!/usr/bin/env python3
"""Freeze and download a deterministic OmniDocBench v1.0 evaluation subset."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path


REVISION = "f5f559bddf50e36f7f9899d842d0006f13ce8afc"
BASE_URL = "https://hf-mirror.com/datasets/opendatalab/OmniDocBench/resolve"


def page_features(page: dict) -> dict:
    attrs = page["page_info"]["page_attribute"]
    cats = collections.Counter(x["category_type"] for x in page["layout_dets"])
    return {
        "image_path": page["page_info"]["image_path"],
        "source": attrs.get("data_source", "unknown"),
        "language": attrs.get("language", "unknown"),
        "layout": attrs.get("layout", "unknown"),
        "table_count": cats["table"],
        "formula_count": cats["equation_isolated"],
        "inline_formula_count": cats["equation_inline"],
        "element_count": sum(cats.values()),
        "fuzzy_scan": bool(attrs.get("fuzzy_scan", False)),
        "watermark": bool(attrs.get("watermark", False)),
    }


def select_formal(pages: list[dict], count: int, seed: int) -> list[int]:
    """Greedy coverage selection over document type, language, layout, and content."""
    rng = random.Random(seed)
    features = [page_features(p) for p in pages]
    sources = sorted({f["source"] for f in features})
    languages = sorted({f["language"] for f in features})
    layouts = sorted({f["layout"] for f in features})

    source_target = {k: count / len(sources) for k in sources}
    lang_weights = {"en": 0.40, "simplified_chinese": 0.40, "en_ch_mixed": 0.20}
    lang_target = {k: count * lang_weights.get(k, 1 / len(languages)) for k in languages}
    layout_target = {k: max(5.0, count / len(layouts)) for k in layouts}
    feature_target = {"table": count * 0.35, "formula": count * 0.35, "complex": count * 0.45}

    selected: list[int] = []
    remaining = list(range(len(pages)))
    rng.shuffle(remaining)
    counts = collections.Counter()

    while remaining and len(selected) < count:
        best_i = None
        best_score = float("-inf")
        for i in remaining:
            f = features[i]
            score = 0.0
            score += 5.0 * max(0.0, source_target[f["source"]] - counts[("source", f["source"])]) / source_target[f["source"]]
            score += 4.0 * max(0.0, lang_target[f["language"]] - counts[("language", f["language"])]) / max(1.0, lang_target[f["language"]])
            score += 2.0 * max(0.0, layout_target[f["layout"]] - counts[("layout", f["layout"])]) / layout_target[f["layout"]]
            if f["table_count"]:
                score += 2.5 * max(0.0, feature_target["table"] - counts["table"]) / feature_target["table"]
            if f["formula_count"]:
                score += 2.5 * max(0.0, feature_target["formula"] - counts["formula"]) / feature_target["formula"]
            if f["layout"] != "single_column":
                score += 1.5 * max(0.0, feature_target["complex"] - counts["complex"]) / feature_target["complex"]
            score += min(f["element_count"], 80) / 500.0
            score += rng.random() * 1e-6
            if score > best_score:
                best_i, best_score = i, score

        assert best_i is not None
        selected.append(best_i)
        f = features[best_i]
        counts[("source", f["source"])] += 1
        counts[("language", f["language"])] += 1
        counts[("layout", f["layout"])] += 1
        counts["table"] += int(bool(f["table_count"]))
        counts["formula"] += int(bool(f["formula_count"]))
        counts["complex"] += int(f["layout"] != "single_column")
        remaining.remove(best_i)
    return selected


def select_pilot(pages: list[dict], formal_indices: list[int], count: int, seed: int) -> list[int]:
    """Choose a challenge-rich, diverse pilot entirely inside the formal subset."""
    rng = random.Random(seed + 1)
    features = [page_features(p) for p in pages]
    selected: list[int] = []
    remaining = formal_indices.copy()
    rng.shuffle(remaining)
    counts = collections.Counter()
    while remaining and len(selected) < count:
        best_i, best_score = None, float("-inf")
        for i in remaining:
            f = features[i]
            score = 4.0 / (1 + counts[("source", f["source"])])
            score += 3.0 / (1 + counts[("language", f["language"])])
            score += 2.0 / (1 + counts[("layout", f["layout"])])
            score += 2.0 * bool(f["table_count"])
            score += 2.0 * bool(f["formula_count"])
            score += 1.0 * (f["layout"] != "single_column")
            score += min(f["element_count"], 100) / 200.0
            score += rng.random() * 1e-6
            if score > best_score:
                best_i, best_score = i, score
        assert best_i is not None
        selected.append(best_i)
        f = features[best_i]
        counts[("source", f["source"])] += 1
        counts[("language", f["language"])] += 1
        counts[("layout", f["layout"])] += 1
        remaining.remove(best_i)
    return selected


def download(url: str, target: Path, retries: int = 5) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "monkeyocr-repro/1.0"})
            with urllib.request.urlopen(req, timeout=120) as src, partial.open("wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            partial.replace(target)
            return
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(2 ** attempt)


def summarize(items: list[dict]) -> dict:
    f = [page_features(x) for x in items]
    return {
        "pages": len(items),
        "source": dict(collections.Counter(x["source"] for x in f)),
        "language": dict(collections.Counter(x["language"] for x in f)),
        "layout": dict(collections.Counter(x["layout"] for x in f)),
        "pages_with_table": sum(bool(x["table_count"]) for x in f),
        "pages_with_display_formula": sum(bool(x["formula_count"]) for x in f),
        "pages_with_complex_layout": sum(x["layout"] != "single_column" for x in f),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--formal-count", type=int, default=120)
    parser.add_argument("--pilot-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=250605)
    args = parser.parse_args()

    args.root.mkdir(parents=True, exist_ok=True)
    gt_path = args.root / "OmniDocBench.json"
    gt_url = f"{BASE_URL}/{REVISION}/OmniDocBench.json"
    download(gt_url, gt_path)
    pages = json.loads(gt_path.read_text(encoding="utf-8"))
    if len(pages) != 981:
        raise RuntimeError(f"Expected 981 pages for v1.0, got {len(pages)}")

    formal_indices = select_formal(pages, args.formal_count, args.seed)
    pilot_indices = select_pilot(pages, formal_indices, args.pilot_count, args.seed)
    formal = [pages[i] for i in formal_indices]
    pilot = [pages[i] for i in pilot_indices]

    subsets = args.root / "subsets"
    subsets.mkdir(exist_ok=True)
    (subsets / "formal_120.json").write_text(json.dumps(formal, ensure_ascii=False, indent=2), encoding="utf-8")
    (subsets / "pilot_20.json").write_text(json.dumps(pilot, ensure_ascii=False, indent=2), encoding="utf-8")

    pilot_paths = {x["page_info"]["image_path"] for x in pilot}
    manifest_lines = []
    for rank, page in enumerate(formal):
        f = page_features(page)
        f.update({"formal_rank": rank, "pilot": f["image_path"] in pilot_paths})
        # v1.0 JSON stores basenames while the repository stores images beneath images/.
        f["local_image_path"] = "images/" + Path(f["image_path"]).name
        manifest_lines.append(f)
        rel = f["local_image_path"].replace("\\", "/")
        quoted = "/".join(urllib.parse.quote(part) for part in rel.split("/"))
        download(f"{BASE_URL}/{REVISION}/{quoted}", args.root / rel)

    manifest_lines.sort(key=lambda x: (not x["pilot"], x["formal_rank"]))
    (subsets / "manifest_120.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in manifest_lines), encoding="utf-8"
    )
    (subsets / "pilot_page_ids.txt").write_text(
        "\n".join(Path(x["page_info"]["image_path"]).name for x in pilot) + "\n", encoding="utf-8"
    )
    (subsets / "formal_page_ids.txt").write_text(
        "\n".join(Path(x["page_info"]["image_path"]).name for x in formal) + "\n", encoding="utf-8"
    )
    provenance = {
        "dataset_repo": "opendatalab/OmniDocBench",
        "dataset_revision": REVISION,
        "ground_truth_sha256": hashlib.sha256(gt_path.read_bytes()).hexdigest(),
        "seed": args.seed,
        "selection": "deterministic greedy stratification; pilot is a challenge-rich subset of formal",
        "pilot": summarize(pilot),
        "formal": summarize(formal),
    }
    (subsets / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
