#!/usr/bin/env python3
"""Synthetic local edit regression: no mutation outside target+explicit allowed_reflow IDs.
Does not verify rendered visual equivalence, source geometry or PDF quality.
"""
import argparse, json
from pathlib import Path

def diff_scene(before,after,target_ids,allowed_reflow_ids=()):
 issues=[]
 if (before.get('project_id'), before.get('page_id'), before.get('size_mm')) != (after.get('project_id'),after.get('page_id'),after.get('size_mm')):
  issues.append({'code':'DOCUMENT_IDENTITY_CHANGED'})
 b={x['id']:x for x in before.get('elements',[])}
 a={x['id']:x for x in after.get('elements',[])}
 expected=set(target_ids)|set(allowed_reflow_ids)
 for ident in set(b)|set(a):
  if b.get(ident)!=a.get(ident) and ident not in expected:
   issues.append({'code':'UNEXPECTED_EDIT','element':ident})
 for ident in target_ids:
  if b.get(ident)==a.get(ident):issues.append({'code':'TARGET_UNCHANGED','element':ident})
  if b.get(ident,{}).get('locked'):issues.append({'code':'LOCKED_TARGET_EDITED','element':ident})
 return issues

def main():
 p=argparse.ArgumentParser();p.add_argument('before');p.add_argument('after');p.add_argument('--target',action='append',required=True);p.add_argument('--reflow',action='append',default=[])
 args=p.parse_args();before=json.load(open(args.before,encoding="utf-8"));after=json.load(open(args.after,encoding="utf-8"))
 issues=diff_scene(before,after,args.target,args.reflow)
 print(json.dumps({'issue_count':len(issues),'issues':issues},ensure_ascii=False,indent=2))
 return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
