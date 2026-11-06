#!/usr/bin/env python3
"""Verify immutable source bytes against manifest SHA-256. Refuses path traversal/symlinks outside project root."""
import argparse,hashlib,json
from pathlib import Path

def check_assets(manifest,source_root):
 root=source_root.resolve();issues=[]
 for a in manifest.get('assets',[]):
  rel=a.get('relative_path','')
  p=(root/rel).resolve()
  try:p.relative_to(root)
  except ValueError:issues.append({'code':'OUTSIDE_SOURCE_ROOT','id':a.get('id')});continue
  if not p.is_file():issues.append({'code':'SOURCE_MISSING','id':a.get('id')});continue
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  if h!=a.get('sha256'):issues.append({'code':'HASH_MISMATCH','id':a.get('id')})
 return issues

def main():
 p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('source_root',type=Path)
 a=p.parse_args();m=json.loads(a.manifest.read_text(encoding="utf-8"))
 issues=check_assets(m,a.source_root)
 print(json.dumps({'issue_count':len(issues),'issues':issues},ensure_ascii=False,indent=2))
 return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
