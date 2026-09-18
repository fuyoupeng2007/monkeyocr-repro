#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[r for r in json.loads(a.results.read_text(encoding='utf-8')) if r['status']=='ok']
by=defaultdict(dict)
for r in rows: by[r['case_id']][r['margin']]=r
summary={}
for task in ('text','table','formula','all'):
 groups=[v for v in by.values() if task=='all' or v.get(0,{}).get('task')==task]
 data=[]
 for v in groups:
  if not all(m in v for m in (0,.02,.05)):continue
  data.append({'case_id':v[0]['case_id'],'original':v[0]['region_edit_distance'],'expand_2pct':v[.02]['region_edit_distance'],'expand_5pct':v[.05]['region_edit_distance']})
 means={k:(sum(x[k] for x in data)/len(data) if data else None) for k in ('original','expand_2pct','expand_5pct')}
 changes={}
 for label,key in [('expand_2pct','expand_2pct'),('expand_5pct','expand_5pct')]:
  delta=[x['original']-x[key] for x in data]
  changes[label]={'improved':sum(x>.01 for x in delta),'unchanged':sum(abs(x)<=.01 for x in delta),'degraded':sum(x<-.01 for x in delta),'mean_delta':sum(delta)/len(delta) if delta else None}
 summary[task]={'n':len(data),'mean_edit_distance':means,'vs_original':changes}
a.out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
