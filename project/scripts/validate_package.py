#!/usr/bin/env python3
"""Offline v2 package integrity + task DAG + evidence-state validation. Not a real plugin/backend test."""
from __future__ import annotations
import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
import json, math, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent   # project/ (governance docs, tasks, research)
HUB=ROOT.parent/'agents'/'portfolio-plugin'   # plugin root: .claude-plugin, skills, scripts
AGENTS=ROOT.parent/'agents'
REQUIRED=['README_START_HERE.md','README.md','AGENTS.md','CLAUDE.md','GOALS.md','PLANS.md',
 'memory/NOW.md','memory/HANDOFF.md','research/SOURCES.md','research/repos.lock.json',
 'tasks/backlog.json','docs/PROBLEM_DECOMPOSITION.md',
 'docs/V2_AUDIT_REPORT.md','docs/TASK_RUNBOOK.md']
HUB_REQUIRED=['plugin.json','.claude-plugin/plugin.json','.agents/plugins/marketplace.json','AGENTS.md']
AGENT_REQUIRED=['portfolioAgent/AGENTS.md','sourcePrepAgent/AGENTS.md','reviewAgent/AGENTS.md','reviewAgent/benchmarks/SPEC.md']
SCHEMA='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'

def read_json(path):
 def reject_const(t):raise ValueError('Nonstandard JSON constant: '+t)
 return json.loads(path.read_text(encoding='utf-8'),parse_constant=reject_const)

def _walk(root, suffix):
 import os
 for d, dirs, files in os.walk(root):
  dirs[:] = [x for x in dirs if x not in ('.cache', '.git', 'node_modules', 'preview', '__pycache__')]
  for f in files:
   if f.endswith(suffix): yield Path(d) / f

def validate(root=ROOT):
 errors=[]
 for path in REQUIRED:
  if not (root/path).is_file():errors.append('MISSING_FILE '+path)
 for path in HUB_REQUIRED:
  if not (HUB/path).is_file():errors.append('MISSING_FILE agents/portfolio-plugin/'+path)
 for path in AGENT_REQUIRED:
  if not (AGENTS/path).is_file():errors.append('MISSING_FILE agents/'+path)
 for f in _walk(root,'.json'):
  try:read_json(f)
  except Exception as e:errors.append('INVALID_JSON '+str(f.relative_to(root))+' '+str(e))
 try:
  m=read_json(HUB/'plugin.json');c=read_json(HUB/'.claude-plugin/plugin.json')
  if m.get('$schema')!=SCHEMA:errors.append('BAD_PORTABLE_SCHEMA')
  if m.get('name')!='portfolio-agent' or c.get('name')!=m.get('name'):errors.append('PLUGIN_NAME_MISMATCH')
  if m.get('version')!=c.get('version') or m.get('version')!='0.4.0':errors.append('PLUGIN_VERSION_MISMATCH')
  market=read_json(HUB/'.agents/plugins/marketplace.json')
  if market['plugins'][0]['source']['path']!='./':errors.append('MARKETPLACE_ROOT_PATH_BAD')
  if not market['plugins'][0].get('policy'):errors.append('MARKETPLACE_POLICY_MISSING')
 except Exception as e:errors.append('PLUGIN_FAILED '+str(e))
 skill_paths=list((HUB/'skills').glob('*/SKILL.md'))
 if not skill_paths:errors.append('NO_SKILLS')
 for f in skill_paths:
  v=f.read_text(encoding='utf-8')
  if not v.startswith('---\n') or v.count('\n---\n')<1:errors.append('SKILL_FRONTMATTER '+str(f))
  if not re.search(r'^name: [a-z0-9-]+$',v,re.M):errors.append('SKILL_NAME '+str(f))
  if not re.search(r'^description: .{20,}$',v,re.M):errors.append('SKILL_DESCRIPTION '+str(f))
 try:
  data=read_json(root/'tasks/backlog.json');tasks=data['tasks']
  ids=[t['id'] for t in tasks]
  if len(ids)!=len(set(ids)):errors.append('DUPLICATE_TASK')
  idx={t['id']:t for t in tasks}
  for t in tasks:
   i=t['id'];st=t['status'];card=root/f'tasks/cards/{i}.md'
   if not card.is_file():errors.append('MISSING_TASK_CARD '+i)
   if st not in ('pending','in_progress','done','blocked','skipped'):errors.append('BAD_STATUS '+i)
   if not t.get('verification') or not t.get('negative_test') or not t.get('outputs'):errors.append('WEAK_TASK '+i)
   if not list((root/'plans').glob(t['phase']+'-*.md')):errors.append('MISSING_PHASE_PLAN '+i)
   for dep in t['dependencies']+t.get('optional_dependencies',[]):
    if dep not in idx:errors.append('UNKNOWN_DEP '+i+'=>'+dep)
   if st in ('done','blocked','skipped'):
    if not t.get('evidence_path') or not (root/t['evidence_path']).is_file():errors.append('MISSING_STATUS_PROOF '+i)
    if not t.get('finished_at'):errors.append('MISSING_FINISHED_AT '+i)
   if st=='done' and t.get('pass_state')!='PASS':errors.append('DONE_WITHOUT_PASS '+i)
   if st=='skipped' and not t.get('waiver'):errors.append('SKIPPED_WITHOUT_WAIVER '+i)
   if st=='blocked' and not t.get('blocked_reason'):errors.append('BLOCKED_WITHOUT_REASON '+i)
  visiting=set();seen=set()
  def visit(i):
   if i in visiting:errors.append('CYCLE '+i);return
   if i in seen:return
   visiting.add(i)
   for dep in idx[i]['dependencies']:
    if dep in idx:visit(dep)
   visiting.remove(i);seen.add(i)
  for i in idx:visit(i)
 except Exception as e:errors.append('DAG_FAILED '+str(e))
 try:
  repos=read_json(root/'research/repos.lock.json')['repositories']
  if len(repos)<15:errors.append('NOT_ENOUGH_AUDITED_REPOS')
  for r in repos:
   if not re.fullmatch(r'[a-f0-9]{40}',r.get('sha','')):errors.append('BAD_SHA '+r.get('id','?'))
   if r.get('runtime_status') not in ('NOT_RUN','PASS','FAIL','BLOCKED'):errors.append('BAD_RUNTIME_STATUS '+r['id'])
   if r.get('runtime_status')!='NOT_RUN' and not r.get('runtime_evidence_path'):errors.append('UNPROVEN_RUNTIME '+r['id'])
 except Exception as e:errors.append('REPO_LOCK_ERROR '+str(e))
 bad=[str(p.relative_to(root)) for p in _walk(root,'') if '.cache' not in p.relative_to(root).parts and (p.suffix in ('.pyc','.pyo') or '__pycache__' in p.parts)]
 if bad:errors.append('COMPILED_FILES_IN_ZIP '+str(bad[:4]))
 return errors

if __name__=='__main__':
 errs=validate()
 print(f'PACKAGE_CHECK: {"PASS" if not errs else "FAIL"}; errors={len(errs)}')
 for e in errs:print(' - '+e)
 print('Scope: static manifests, local schemas as JSON files, DAG/proofs/skills. NOT external plugin install, schema semantics, professional portfolio quality, or backend execution.')
 sys.exit(1 if errs else 0)
