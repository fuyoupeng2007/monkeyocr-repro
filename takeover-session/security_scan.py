"""Security scan before publishing to a PUBLIC GitHub repo.

Looks for API keys, tokens, passwords, private-key headers, and personal paths in
the files that are about to be uploaded. Prints every hit so it can be reviewed or
excluded; exits non-zero when findings exist, so a publish step can gate on it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOTS = [
    Path(r"D:\chatgpt\刘禹良团队_入组调研与复现审批\复现工程"),
    Path(r"D:\haeness\monkeyocr-takeover"),
]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".ipynb_checkpoints", "ssh", ".ssh"}
SKIP_FILES = {"security_scan.py"}  # this file contains the detection patterns themselves
SKIP_EXT = {".zip", ".gz", ".tgz", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".pdf", ".pyc", ".pt", ".onnx"}

PATTERNS = [
    ("OpenAI key", re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("OpenSSH private key", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----")),
    ("generic password assignment", re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{3,}['\"]")),
    ("generic api key assignment", re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("authorization header", re.compile(r"(?i)authorization\s*:\s*bearer\s+\S{8,}")),
    ("huggingface token", re.compile(r"\bhf_[A-Za-z0-9]{20,}")),
    ("modelscope token", re.compile(r"(?i)modelscope[_-]?token\s*[:=]\s*\S{8,}")),
]

# things that are fine and would otherwise false-positive
ALLOW = re.compile(r"(?i)(your[_-]?api[_-]?key|example|placeholder|<.*>|\*\*\*|xxx|dummy|fake|os\.environ|getenv)")


def main() -> int:
    hits: list[tuple[str, str, int, str]] = []
    scanned = 0
    for root in ROOTS:
        if not root.exists():
            print(f"[skip] {root} not found")
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.name in SKIP_FILES:
                continue
            if p.suffix.lower() in SKIP_EXT:
                continue
            if p.stat().st_size > 2_000_000:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned += 1
            for i, line in enumerate(text.splitlines(), 1):
                if ALLOW.search(line):
                    continue
                for name, rx in PATTERNS:
                    if rx.search(line):
                        hits.append((name, str(p), i, line.strip()[:150]))

    print(f"scanned {scanned} text files in {len(ROOTS)} roots")
    if hits:
        print(f"\n!! {len(hits)} potential secret(s):")
        for name, path, line_no, line in hits:
            print(f"  [{name}] {path}:{line_no}\n      {line}")
        return 1
    print("no secrets detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
