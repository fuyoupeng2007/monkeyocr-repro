#!/usr/bin/env python3
"""Fixed-condition crop-margin ablation using released MonkeyOCR single-task prompts.

Candidates are detector regions that overlap a compatible frozen GT region but
do not fully cover it.  The same selected regions are recognized at 0%, 2%, and
5% symmetric box expansion.  Region scores are normalized character edit
distance against the paired GT string; they are diagnostic, not OmniDocBench
end-to-end scores.
"""
from __future__ import annotations
import argparse, json, os, re, time, traceback
from collections import defaultdict
from pathlib import Path
from PIL import Image
import torch
from magic_pdf.model.custom_model import MonkeyOCR

TASK={"text":"Please output the text content from the image.","formula":"Please write out the expression of the formula in the image using LaTeX format.","table":"Please output the table in the image in LaTeX format."}
MAP={"text":("text_block","text"),"title":("title","text"),"table":("table","table"),"interline_equation":("equation_isolated","formula")}

def xy(poly):
    a=poly[0::2]; b=poly[1::2]; return [min(a),min(b),max(a),max(b)]
def area(b): return max(0,b[2]-b[0])*max(0,b[3]-b[1])
def iou(a,b):
    z=[max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])]
    return area(z)/(area(a)+area(b)-area(z)+1e-8)
def ed(a,b):
    a=re.sub(r"\s+","",a or ""); b=re.sub(r"\s+","",b or "")
    if not a: return float(bool(b))
    if not b: return 1.0
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1): cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]/max(len(a),len(b))
def gt_text(d): return d.get("text") or d.get("latex") or d.get("html") or ""

def select(gt_path, pages, n):
    records=json.loads(gt_path.read_text(encoding="utf-8")); byname={r["page_info"]["image_path"]:r for r in records}
    candidates=defaultdict(list)
    for fp in sorted(pages.glob("*/*_middle.json")):
        stem=fp.name[:-12]
        record=byname.get(stem+".jpg")
        if not record: continue
        blocks=json.loads(fp.read_text(encoding="utf-8")).get("pdf_info",[{}])[0].get("preproc_blocks",[])
        for bi,b in enumerate(blocks):
            typ=b.get("type"); spec=MAP.get(typ)
            if not spec or not b.get("bbox"): continue
            target,task=spec; mb=[float(x) for x in b["bbox"]]
            best=None
            for gi,g in enumerate(record.get("layout_dets",[])):
                if g.get("ignore") or g.get("category_type")!=target or not g.get("poly"): continue
                gb=xy(g["poly"]); score=iou(mb,gb)
                if best is None or score>best[0]: best=(score,gi,g,gb)
            if not best: continue
            score,gi,g,gb=best; coverage=area([max(mb[0],gb[0]),max(mb[1],gb[1]),min(mb[2],gb[2]),min(mb[3],gb[3])])/(area(gb)+1e-8)
            if score>=0.30 and coverage<0.985 and gt_text(g):
                category="text" if task=="text" else task
                candidates[category].append({"page":stem,"image_path":record["page_info"]["image_path"],"model_type":typ,"task":task,"model_block_index":bi,"gt_index":gi,"detector_bbox":mb,"gt_bbox":gb,"iou":round(score,5),"gt_coverage":round(coverage,5),"gt":gt_text(g)})
    quotas={"text":20,"table":15,"formula":15}; chosen=[]; used=set()
    for cat,q in quotas.items():
        rows=sorted(candidates[cat],key=lambda x:(x["gt_coverage"],x["iou"]))
        for r in rows:
            key=(r["page"],r["gt_index"])
            if key not in used: chosen.append(r); used.add(key)
            if sum(x["task"]==("text" if cat=="text" else cat) for x in chosen)>=q: break
    if len(chosen)<n:
        for rows in candidates.values():
            for r in sorted(rows,key=lambda x:(x["gt_coverage"],x["iou"])):
                if (r["page"],r["gt_index"]) not in used: chosen.append(r);used.add((r["page"],r["gt_index"]))
                if len(chosen)>=n: break
            if len(chosen)>=n: break
    return chosen[:n]

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ground-truth',type=Path,required=True);p.add_argument('--pages',type=Path,required=True);p.add_argument('--images',type=Path,required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--n',type=int,default=50);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True); cases=select(a.ground_truth,a.pages,a.n)
    (a.out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Selected {len(cases)} cases',flush=True)
    model=MonkeyOCR(str(a.config)); results=[]
    for ci,c in enumerate(cases,1):
        im=Image.open(a.images/c['image_path']).convert('RGB'); W,H=im.size
        for margin in (0,.02,.05):
            x1,y1,x2,y2=c['detector_bbox']; w=x2-x1;h=y2-y1
            box=(max(0,int(x1-w*margin)),max(0,int(y1-h*margin)),min(W,int(x2+w*margin)),min(H,int(y2+h*margin)))
            crop=im.crop(box); tag=f"{ci:02d}_{margin:.2f}"; crop.save(a.out/'crops'/f'{tag}.png') if (a.out/'crops').exists() else None
            (a.out/'crops').mkdir(exist_ok=True); crop.save(a.out/'crops'/f'{tag}.png')
            try:
                torch.cuda.reset_peak_memory_stats(); t=time.perf_counter(); answer=model.chat_model.batch_inference([crop],[TASK[c['task']]])[0]; secs=time.perf_counter()-t
                status='ok'; err=None
            except Exception as e:
                answer='';secs=None;status='error';err=repr(e)
            row={**c,'case_id':ci,'margin':margin,'crop_bbox':box,'prediction':answer,'region_edit_distance':ed(c['gt'],answer),'seconds':secs,'status':status,'error':err}
            results.append(row); (a.out/'responses').mkdir(exist_ok=True);(a.out/'responses'/f'{tag}.txt').write_text(answer,encoding='utf-8')
            print(f'{ci}/{len(cases)} margin={margin:.2f} {status}',flush=True)
    (a.out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={}
    for task in ('text','table','formula'):
        rows=[r for r in results if r['task']==task and r['status']=='ok']; summary[task]={}
        for m in (0,.02,.05):
            vals=[r['region_edit_distance'] for r in rows if r['margin']==m]; summary[task][str(m)]={'n':len(vals),'mean_edit_distance':sum(vals)/len(vals) if vals else None}
    (a.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
