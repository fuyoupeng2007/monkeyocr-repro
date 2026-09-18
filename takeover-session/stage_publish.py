"""Stage exactly what will be published to the public GitHub repo.

Rules (from the owner's choices):
  * include: the reproduction project folder + this session's takeover work
  * exclude: ALL key material (private AND public), __pycache__, temp renders
  * include: the large binaries (deploy zips, cloud package, paper PDFs)

Also verifies GitHub's hard limits (no file >100 MB) before we try to push, and
prints a manifest so the upload can be reviewed before it happens.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

STAGE = Path(r"D:\haeness\_gh_publish")
CHATGPT_PROJ = Path(r"D:\chatgpt\刘禹良团队_入组调研与复现审批\复现工程")
TAKEOVER = Path(r"D:\haeness\monkeyocr-takeover")

EXCLUDE_NAMES = {
    "ssh", ".ssh",                       # key material (both private and public)
    "__pycache__", ".ipynb_checkpoints", ".pytest_cache",
    "_slides",                            # temp PNG renders of the deck
}
EXCLUDE_SUFFIX = {".pyc", ".pyo"}
EXCLUDE_FILES = {
    # local bookkeeping that should not be published
    "deliverables.tgz", "results.tar.gz", "omni_result.tgz", "omni_result.tar",
    "comparison.json.bak",
}

MAX_FILE = 100 * 1024 * 1024  # GitHub hard limit


def copy_tree(src: Path, dst: Path) -> tuple[int, int]:
    n = size = 0
    for p in src.rglob("*"):
        if any(part in EXCLUDE_NAMES for part in p.relative_to(src).parts):
            continue
        if p.name in EXCLUDE_FILES or p.suffix.lower() in EXCLUDE_SUFFIX:
            continue
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            n += 1
            size += p.stat().st_size
    return n, size


def main() -> int:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    pairs = [
        (CHATGPT_PROJ, STAGE / "chatgpt-run" / "复现工程"),
        (TAKEOVER, STAGE / "takeover-session"),
    ]
    total_n = total_s = 0
    for src, dst in pairs:
        if not src.exists():
            print(f"[skip] missing: {src}")
            continue
        n, s = copy_tree(src, dst)
        total_n += n
        total_s += s
        print(f"staged {n:4d} files  {s / 1024 / 1024:7.2f} MB  <- {src}")

    # hard-limit check
    big = [(p.stat().st_size, p) for p in STAGE.rglob("*") if p.is_file() and p.stat().st_size > MAX_FILE]
    print(f"\nTOTAL: {total_n} files, {total_s / 1024 / 1024:.2f} MB -> {STAGE}")
    if big:
        print("!! files exceed GitHub's 100 MB hard limit:")
        for sz, p in big:
            print(f"   {sz / 1024 / 1024:.1f} MB  {p}")
        return 1
    print("no file exceeds GitHub's 100 MB limit")

    # confirm no key material slipped in
    leaks = [p for p in STAGE.rglob("*") if p.is_file() and
             (p.name.startswith("id_") or p.name.endswith((".pem", ".key")) or
              "monkeyocr_autodl" in p.name)]
    if leaks:
        print("!! key material present in staging:")
        for p in leaks:
            print("   ", p)
        return 1
    print("no key material in staging")

    # top-level manifest
    print("\ntop level:")
    for p in sorted(STAGE.iterdir()):
        kind = "dir " if p.is_dir() else "file"
        print(f"  {kind} {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
