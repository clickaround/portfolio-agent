#!/usr/bin/env python3
"""Dependency-aware read-only task listing, with --ready/--all/--phase filtering. Stdlib only."""
import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def ready_tasks(data):
    tasks=data['tasks']
    done={t['id'] for t in tasks if t['status']=='done' and t.get('pass_state')=='PASS' and t.get('evidence_path') and (ROOT/t['evidence_path']).is_file()}
    return [t for t in tasks if t['status']=='pending' and set(t['dependencies']).issubset(done)]

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group()
    g.add_argument('--ready', action='store_true', help='List tasks with satisfied mandatory dependencies (default)')
    g.add_argument('--all', action='store_true', help='List all tasks')
    p.add_argument('--phase',type=str,help='Filter by phase P00..P08')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    data=json.loads((ROOT/'tasks/backlog.json').read_text(encoding='utf-8'))
    rows=data['tasks'] if args.all else ready_tasks(data)
    if args.phase:rows=[t for t in rows if t['phase']==args.phase]
    if args.json:print(json.dumps(rows,ensure_ascii=False,indent=2))
    else:
        for t in rows:print(f"{t['id']} [{t['phase']}] {t['title']} ({t['status']}) evidence={t.get('evidence_path') or '—'}")
        print(f'COUNT={len(rows)}')
if __name__=='__main__':main()
