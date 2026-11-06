#!/usr/bin/env python3
"""Offline rules for portfolio print/digital dimensions. No renderer claims."""
import argparse,json,math,pathlib,sys
P=pathlib.Path(__file__).resolve().parent.parent

def validate(d):
 err=[]
 if d.get('medium') not in ('print','presentation','digital'):err.append('unknown medium')
 for k in ('width_mm','height_mm','margin_mm','bleed_mm','safe_mm'):
  v=d.get(k)
  if type(v) not in (int,float) or not math.isfinite(v) or v < (0.01 if k in ('width_mm','height_mm') else 0):err.append('bad '+k)
 w=d.get('width_mm',0);h=d.get('height_mm',0)
 if isinstance(w,(int,float)) and isinstance(h,(int,float)) and math.isfinite(w) and math.isfinite(h):
  if min(w,h)>0 and max(w,h)>3000:err.append('oversize')
  if min(w,h)>0 and d.get('margin_mm',0)*2+d.get('safe_mm',0)*2>=min(w,h):err.append('margins+safe consume page')
 pc=d.get('page_count')
 if type(pc)!=int or not 1<=pc<=500:err.append('bad page_count')
 return err
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('file');args=a.parse_args()
 d=json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"));errs=validate(d)
 print(json.dumps({'ok':not errs,'errors':errs},ensure_ascii=False));sys.exit(1 if errs else 0)
