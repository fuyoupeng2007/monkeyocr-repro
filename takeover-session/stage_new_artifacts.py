#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage the newly produced artifacts into the publish folder.

Adds (relative to D:\\haeness\\monkeyocr-takeover):
  deliverables/*.docx, deliverables/*.md      new documents
  deliverables/compare/*                       comparison data
  build_*.py, check_*.py, extract_*.py, *.ps1  the scripts behind them

Excludes, deliberately:
  ~$*.docx                 Word lock files
  *.bak, *.tgz             local backups / archives
  paper_text.txt           extracted full text of the paper (copyright) -- script included instead
  scholarship_text.txt     the owner's personal scholarship data
  fix_quotes*.py, inspect_line.py   one-off patches already applied
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SRC = Path(r'D:\haeness\monkeyocr-takeover')
PUB = Path(r'D:\haeness\_gh_publish\takeover-session')

EXCLUDE_NAMES = {
    'paper_text.txt', 'scholarship_text.txt', 'deliverables.tgz',
    'comparison.json.bak', 'diff_publish.py', 'fix_quotes.py', 'fix_quotes2.py',
    'fix_quotes3.py', 'fix_quotes4.py', 'fix_quotes5.py', 'inspect_line.py',
}
sys.stdout.reconfigure(encoding='utf-8')

copied: list[str] = []
for src in sorted(SRC.rglob('*')):
    if not src.is_file():
        continue
    rel = src.relative_to(SRC)
    parts = rel.parts
    if any(p in {'sync', '__pycache__', '_slides', '.git'} for p in parts):
        continue
    if src.name in EXCLUDE_NAMES or src.name.startswith('~$') or src.suffix == '.bak':
        continue
    # only ship the new batches
    if not (parts[0] == 'deliverables'
            or src.suffix in {'.py', '.ps1'}):
        continue
    if src.suffix == '.py' and not src.name.startswith(('build_', 'check_', 'extract_', 'verify_', 'stage_', 'security_')):
        continue

    dst = PUB / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append(str(rel))

print(f'copied {len(copied)} files:')
for c in copied:
    print('  ', c)
