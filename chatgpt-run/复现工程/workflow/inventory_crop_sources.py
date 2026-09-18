#!/usr/bin/env python3
"""Inventory frozen GT and MonkeyOCR detector regions for crop-ablation design."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--ground-truth', type=Path, required=True)
p.add_argument('--pages-root', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a=p.parse_args()
gt=json.loads(a.ground_truth.read_text(encoding='utf-8'))
if isinstance(gt, dict):
    records=gt.get('data', gt.get('samples', gt.get('pages', [])))
else: records=gt
out={'gt_count':len(records), 'gt_top_keys': sorted(records[0].keys()) if records else [],
     'gt_type_counts':Counter(), 'model_type_counts':Counter(), 'examples':[]}
for r in records:
    for d in r.get('layout_dets', []): out['gt_type_counts'][d.get('category_type',d.get('type','<none>'))]+=1
for fp in sorted(a.pages_root.glob('*/*_middle.json')):
    x=json.loads(fp.read_text(encoding='utf-8'))
    blocks=x.get('pdf_info',[{}])[0].get('preproc_blocks',[])
    for b in blocks: out['model_type_counts'][b.get('type','<none>')]+=1
    if len(out['examples'])<3: out['examples'].append({'file':str(fp),'blocks':blocks[:3]})
out['gt_type_counts']=dict(out['gt_type_counts']);out['model_type_counts']=dict(out['model_type_counts'])
a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
