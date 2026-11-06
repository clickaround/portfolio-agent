#!/usr/bin/env python3
"""Allowlisted public GitHub source-only cloning at pinned SHA. Dry-run unless --apply.
Does NOT install dependencies or execute cloned scripts. Requires git + internet for --apply.
"""
from __future__ import annotations
import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
import argparse, json, subprocess, shutil, re, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parent.parent
LOCK=ROOT/'research/repos.lock.json'
TARGET=ROOT/'.cache/vendor'
def run(cmd, cwd=None):
 start=time.monotonic()
 p=subprocess.run(cmd, cwd=cwd,text=True,capture_output=True,timeout=900)
 return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout[-3000:],stderr=p.stderr[-3000:],seconds=round(time.monotonic()-start,2))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--group',default=None);ap.add_argument('--id',default=None);ap.add_argument('--apply',action='store_true');ap.add_argument('--force',action='store_true',help='refuse to override existing by default; force allows re-validate existing clone but never deletes it')
 a=ap.parse_args(); d=json.loads(LOCK.read_text(encoding="utf-8"))['repositories']; selected=[r for r in d if (a.id and r['id']==a.id) or (not a.id and (not a.group or r['group']==a.group))]
 if not selected:ap.error('No matching allowlisted pinned repositories; inspect research/repos.lock.json')
 summary=[]
 for r in selected:
  id,sha,github=r['id'],r['sha'],r['github']
  if not re.fullmatch(r'[a-z0-9-]+',id) or not re.fullmatch(r'[0-9a-f]{40}',sha) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',github):raise SystemExit('Invalid pinned repository')
  path=TARGET/id; url='https://github.com/'+github+'.git'
  if not a.apply:
   summary.append(dict(id=id,url=url,sha=sha,path=str(path.relative_to(ROOT)),action='WOULD_CLONE_PINNED',executed=False));continue
  if not shutil.which('git'):raise SystemExit('git command not found; no clone attempted')
  if path.exists():
   if not (path/'.git').is_dir():raise SystemExit('Refusing non-git existing target '+str(path))
   p=run(['git','-C',str(path),'rev-parse','HEAD']);cur=p['stdout'].strip()
   if p['exit_code']==0 and cur==sha:summary.append(dict(id=id,action='ALREADY_PINNED',sha=sha,executed=False));continue
   raise SystemExit(f'Refusing to overwrite existing repo {path}: found {cur}, expected {sha}. Move it manually after inspection.')
  TARGET.mkdir(parents=True,exist_ok=True)
  cl=run(['git','-c','protocol.file.allow=never','clone','--filter=blob:none','--no-checkout','--no-tags',url,str(path)])
  if cl['exit_code']!=0:summary.append(dict(id=id,action='CLONE_FAILED',result=cl));continue
  co=run(['git','-C',str(path),'checkout','--detach',sha]); verify=run(['git','-C',str(path),'rev-parse','HEAD']) if co['exit_code']==0 else None
  ok=co['exit_code']==0 and verify and verify['stdout'].strip()==sha
  summary.append(dict(id=id,action='CHECKOUT_PINNED' if ok else 'CHECKOUT_FAILED',sha=sha,clone=cl,checkout=co,verification=verify))
 target=ROOT/'.cache/clone-logs';target.mkdir(parents=True,exist_ok=True)
 log=target/('clone_'+('apply' if a.apply else 'preview')+'.json');log.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps(dict(applied=a.apply,selected=len(selected),summary=[{'id':x['id'],'action':x['action'],'sha':x.get('sha')} for x in summary],log=str(log)),indent=2))
 return 1 if any(x['action'].endswith('FAILED') for x in summary) else 0
if __name__=='__main__':sys.exit(main())
