#!/usr/bin/env python3
"""Offline synthetic axis-aligned page checks ONLY; not vector/print/factual fidelity proof."""
import argparse, json, math, sys
from pathlib import Path

def finite_num(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def check_scene(doc,asset_ids=None):
 issues=[]
 def add(code,els,detail):issues.append(dict(code=code,elements=els,details=detail))
 size=doc.get('size_mm',[])
 if not isinstance(size,list) or len(size)!=2 or not all(finite_num(x) and x>0 for x in size):
  return [{'code':'BAD_PAGE_SIZE','elements':[],'details':'finite positive [width,height] in mm required'}]
 pw,ph=size
 objs=doc.get('elements',[])
 if not isinstance(objs,list):return [{'code':'BAD_ELEMENTS','elements':[],'details':'elements must be list'}]
 ids=set();good=[]
 for ob in objs:
  if not isinstance(ob,dict):add('BAD_ELEMENT',[],str(ob));continue
  eid=ob.get('id')
  if not isinstance(eid,str) or not eid:add('BAD_ID',[],str(eid))
  if eid in ids:add('DUPLICATE_ID',[eid],'duplicate element ID')
  ids.add(eid)
  box=ob.get('box_mm',[])
  if not isinstance(box,list) or len(box)!=4 or not all(finite_num(n) for n in box):
   add('BAD_BBOX',[eid],str(box));continue
  x,y,w,h=box
  if w<=0 or h<=0:add('BAD_BBOX',[eid],'non-positive extent');continue
  if x < -1e-8 or y < -1e-8 or x+w>pw+1e-8 or y+h>ph+1e-8:add('PAGE_OVERFLOW',[eid],str(box))
  kind=ob.get('kind')
  if kind in ('image','pdf-region','svg'):
   aid=ob.get('asset_id')
   if not isinstance(aid,str) or not aid: add('MISSING_ASSET_ID',[eid],'graphic must reference immutable source asset')
   elif asset_ids is not None and aid not in asset_ids:add('UNKNOWN_ASSET_ID',[eid],aid)
  if kind=='pdf-region' and ob.get('allow_crop') is True:
   add('UNREVIEWED_PDF_CROP',[eid],'explicit source-level grant required before this synthetic checker can accept a crop')
  if ob.get('allow_overlap') is True:
   add('UNSCOPED_OVERLAP_WAIVER',[eid],'per-element global waiver forbidden; use intentional_overlaps pairs with reasons')
  if kind=='text' and 'font_size_pt' in ob and finite_num(ob['font_size_pt']) and ob['font_size_pt'] < 6:
   add('CRITICAL_FONT_SIZE',[eid],str(ob['font_size_pt']))
  good.append(ob)
 allowed=set()
 for pair in doc.get('intentional_overlaps',[]):
  if not isinstance(pair,dict) or not isinstance(pair.get('elements'),list) or len(pair['elements'])!=2 or not pair.get('reason'):
   add('BAD_OVERLAP_EXCEPTION',[],str(pair));continue
  if any(i not in ids for i in pair['elements']):add('BAD_OVERLAP_EXCEPTION',pair['elements'],'unknown ID')
  else:allowed.add(frozenset(pair['elements']))
 for idx,a in enumerate(good):
  x,y,ww,hh=a['box_mm']
  for b in good[idx+1:]:
   if frozenset((a['id'],b['id'])) in allowed:continue
   x2,y2,w2,h2=b['box_mm']
   if min(x+ww,x2+w2)-max(x,x2)>1e-8 and min(y+hh,y2+h2)-max(y,y2)>1e-8:
    add('BBOX_OVERLAP',[a['id'],b['id']],'bbox overlap; semantic masks and clipped paths are not modeled')
 return issues

def main():
 p=argparse.ArgumentParser();p.add_argument('file',type=Path);p.add_argument('--asset-manifest',type=Path)
 a=p.parse_args()
 try:
  doc=json.loads(a.file.read_text(encoding='utf-8'),parse_constant=lambda s: (_ for _ in ()).throw(ValueError('non-finite JSON value '+s)))
  asset_ids=None
  if a.asset_manifest:
   m=json.loads(a.asset_manifest.read_text(encoding='utf-8'))
   asset_ids={r['id'] for r in m.get('assets',[])}
  issues=check_scene(doc,asset_ids)
  print(json.dumps({'file':str(a.file),'issue_count':len(issues),'issues':issues,'scope':'synthetic bbox + basic references ONLY'},ensure_ascii=False,indent=2))
  return 1 if issues else 0
 except (ValueError,OSError,KeyError) as e:
  print(json.dumps({'code':'INVALID_INPUT','details':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
