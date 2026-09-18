#!/usr/bin/env python3
"""Create an evidence-first 15-case MonkeyOCR failure atlas."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path

REASONS={
 'text':'文字识别或文本合并错误：按官方文本编辑距离从高到低抽取。',
 'formula':'公式识别错误：按官方展示公式编辑距离从高到低抽取。',
 'table':'表格结构或表格内容错误：按较低 TEDS 或较高编辑距离抽取。',
 'reading_order':'阅读顺序错误：按官方阅读顺序编辑距离从高到低抽取。',
 'empty':'漏检或上游异常：检测后没有有效区域，推理接口收到空提示列表。'}

def score(x):
 m=x.get('metric',{})
 if 'Edit_dist' in m: return float(m['Edit_dist'])
 if 'TEDS' in m: return 1-float(m['TEDS'])
 return float(x.get('edit',0))
def main():
 p=argparse.ArgumentParser();p.add_argument('--logs',type=Path,required=True);p.add_argument('--eval',type=Path,required=True);p.add_argument('--images',type=Path,required=True);p.add_argument('--predictions',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 logs=[json.loads(x) for x in a.logs.read_text(encoding='utf-8').splitlines() if x.strip()]; cases=[]; used=set()
 for r in logs:
  if r.get('status')=='error':
   cases.append({'source':'run_log','kind':'empty','img_id':r['image_path'],'reason':REASONS['empty'],'evidence':r}); used.add(r['image_path'])
 files={'text':'predictions_quick_match_text_block_result.json','formula':'predictions_quick_match_display_formula_result.json','table':'predictions_quick_match_table_result.json','reading_order':'predictions_quick_match_reading_order_result.json'}
 quotas={'text':2,'formula':2,'table':2,'reading_order':1}
 for kind,fn in files.items():
  rows=json.loads((a.eval/fn).read_text(encoding='utf-8'))
  n=0
  for r in sorted(rows,key=score,reverse=True):
   img=r.get('img_id') or r.get('image_name')
   if not img or img in used: continue
   cases.append({'source':fn,'kind':kind,'img_id':img,'reason':REASONS[kind],'evidence':r,'severity':score(r)});used.add(img);n+=1
   if n>=quotas[kind]:break
 for i,c in enumerate(cases,1):
  d=a.out/f'{i:02d}_{c["kind"]}_{Path(c["img_id"]).stem}';d.mkdir(parents=True,exist_ok=True)
  src=a.images/c['img_id']
  if src.exists():shutil.copy2(src,d/src.name)
  pred=a.predictions/f'{Path(c["img_id"]).stem}.md'
  if pred.exists():shutil.copy2(pred,d/'page_prediction.md')
  (d/'case.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
  e=c['evidence']; gt=e.get('gt',''); pd=e.get('pred','')
  (d/'case.md').write_text(f'# 案例 {i:02d}\n\n类别：{c["kind"]}\n\n原因判断：{c["reason"]}\n\n## 真值摘录\n\n```text\n{gt}\n```\n\n## 模型输出摘录\n\n```text\n{pd}\n```\n',encoding='utf-8')
 (a.out/'index.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Created {len(cases)} cases')
if __name__=='__main__':main()
