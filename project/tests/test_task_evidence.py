import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location('validator',ROOT/'scripts/validate_package.py')
VAL=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VAL)

class EvidenceGateTests(unittest.TestCase):
 def test_no_proof_done_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'testbundle';shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.cache','.git'))
   file=dest/'tasks/backlog.json';d=json.loads(file.read_text(encoding="utf-8"));x=next(y for y in d['tasks'] if y['status']=='pending');x['id']='T000';x['dependencies']=[];x['status']='done';x['pass_state']='PASS';x['evidence_path']=None;file.write_text(json.dumps(d),encoding="utf-8")
   issues=VAL.validate(dest)
   self.assertTrue(any(i.startswith('MISSING_STATUS_PROOF T000') for i in issues),issues)
 def test_skip_requires_waiver(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'testbundle';shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.cache','.git'))
   file=dest/'tasks/backlog.json';d=json.loads(file.read_text(encoding="utf-8"));x=next(y for y in d['tasks'] if y['status']=='pending');x['id']='T000';x['dependencies']=[];x.update(status='skipped',evidence_path='README.md',finished_at='2026-11-04T14:00:00+09:00');file.write_text(json.dumps(d),encoding="utf-8")
   issues=VAL.validate(dest)
   self.assertTrue(any(i.startswith('SKIPPED_WITHOUT_WAIVER T000') for i in issues),issues)
