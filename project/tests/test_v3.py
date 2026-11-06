import importlib.util,json,subprocess,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('fmt',R/'scripts/format_check.py')
fmt=importlib.util.module_from_spec(spec);spec.loader.exec_module(fmt)
class TestV3(unittest.TestCase):
 def test_formats(self):
  d=json.loads((R.parent/'agents/portfolioAgent/examples/SYNTHETIC_output-spec.json').read_text(encoding="utf-8"));self.assertEqual([],fmt.validate(d));self.assertEqual(['bad width_mm'],fmt.validate({**d,'width_mm':float('nan')}))
 def test_custom_formats(self):
  d=json.loads((R.parent/'agents/portfolioAgent/examples/SYNTHETIC_output-spec.json').read_text(encoding="utf-8"));self.assertEqual([],fmt.validate({**d,'width_mm':127,'height_mm':355.5,'page_count':12}));self.assertIn('margins+safe consume page',fmt.validate({**d,'width_mm':20,'height_mm':20}))
 def test_clone_dry_run(self):
  p=subprocess.run([sys.executable,str(R/'scripts/clone_repos.py'),'--id','designcraft'],capture_output=True,text=True);self.assertEqual(0,p.returncode,p.stderr);self.assertIn('WOULD_CLONE_PINNED',p.stdout)
 def test_repos_pinned(self):
  d=json.loads((R/'research/repos.lock.json').read_text(encoding="utf-8"));self.assertGreaterEqual(len(d['repositories']),24);self.assertEqual(len({x['id'] for x in d['repositories']}),len(d['repositories']))
 def test_roles(self):
  x=json.loads((R/'agent-roles/contracts/task-result.schema.json').read_text(encoding="utf-8"));self.assertIn('evidence_paths',x['properties'])
 def test_task_dag_not_duplicated(self):
  d=json.loads((R/'tasks/backlog.json').read_text(encoding="utf-8")); self.assertGreaterEqual(len(d['tasks']),80);self.assertEqual(len({x['id'] for x in d['tasks']}),len(d['tasks']))
if __name__=='__main__':unittest.main()
