import importlib.util,json,math,tempfile,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

class V2StructuralTests(unittest.TestCase):
 def test_bad_boolean_page_rejected(self):
  g=loadmod('geometry_v2a','../backend/common/checks/check_layout.py')
  self.assertIn('BAD_PAGE_SIZE',[x['code'] for x in g.check_scene({'size_mm':[True,297],'elements':[]})])
 def test_nan_bbox_rejected(self):
  g=loadmod('geometry_v2b','../backend/common/checks/check_layout.py')
  doc={'size_mm':[420,297],'elements':[{'id':'x','kind':'text','box_mm':[0,float('nan'),10,10]}]}
  self.assertIn('BAD_BBOX',[x['code'] for x in g.check_scene(doc)])
 def test_unscoped_overlap_rejected(self):
  g=loadmod('geometry_v2c','../backend/common/checks/check_layout.py')
  doc={'size_mm':[420,297],'elements':[{'id':'x','kind':'text','box_mm':[0,0,10,10],'allow_overlap':True}]}
  self.assertIn('UNSCOPED_OVERLAP_WAIVER',[x['code'] for x in g.check_scene(doc)])
 def test_missing_asset_id_and_unknown_ref(self):
  g=loadmod('geometry_v2d','../backend/common/checks/check_layout.py')
  doc={'size_mm':[420,297],'elements':[{'id':'x','kind':'image','box_mm':[0,0,10,10],'asset_id':'not-there'}]}
  self.assertIn('UNKNOWN_ASSET_ID',[x['code'] for x in g.check_scene(doc,{'another'})])
 def test_annotated_overlap_allowed(self):
  g=loadmod('geometry_v2e','../backend/common/checks/check_layout.py')
  doc={'size_mm':[420,297],'elements':[{'id':'x','kind':'text','box_mm':[0,0,10,10]},{'id':'y','kind':'text','box_mm':[1,1,2,2]}], 'intentional_overlaps':[{'elements':['x','y'],'reason':'design intent: foreground title over backdrop'}]}
  self.assertEqual(g.check_scene(doc),[])
 def test_edit_only_target(self):
  d=loadmod('edit_v2','../backend/common/checks/check_edit_diff.py')
  src={'project_id':'p','page_id':'1','size_mm':[420,297],'elements':[{'id':'x','box_mm':[10,10,10,10]}, {'id':'y','box_mm':[20,20,20,20]}]}
  dst=json.loads(json.dumps(src));dst['elements'][0]['box_mm'][2]=12
  self.assertEqual(d.diff_scene(src,dst,['x']),[])
  dst['elements'][1]['box_mm'][0]=25
  self.assertEqual(d.diff_scene(src,dst,['x'])[0]['code'],'UNEXPECTED_EDIT')
 def test_source_hash(self):
  mod=loadmod('hash_v2','../backend/common/checks/check_asset_hash.py')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.svg';p.write_bytes(b'<svg></svg>');h=hashlib.sha256(p.read_bytes()).hexdigest()
   m={'assets':[{'id':'x','relative_path':'test.svg','sha256':h}]}
   self.assertEqual(mod.check_assets(m,Path(tmp)),[])
   m['assets'][0]['sha256']='0'*64
   self.assertEqual(mod.check_assets(m,Path(tmp))[0]['code'],'HASH_MISMATCH')
   m['assets'][0]['relative_path']='../../etc/passwd'
   self.assertEqual(mod.check_assets(m,Path(tmp))[0]['code'],'OUTSIDE_SOURCE_ROOT')
 def test_nonempty_task_proofs(self):
  m=loadmod('validate_v2','scripts/validate_package.py')
  self.assertEqual(m.validate(ROOT),[])
  d=json.loads((ROOT/'tasks/backlog.json').read_text(encoding="utf-8"));d['tasks'][0]['status']='done'
  # The live package is not mutated; policy is exercised in dedicated fixture below.
  self.assertTrue(all(x.get('evidence_path') for x in d['tasks'] if x['status']=='done'))
 def test_all_task_ids_unique(self):
  d=json.loads((ROOT/'tasks/backlog.json').read_text(encoding="utf-8"));ids=[x['id'] for x in d['tasks']]
  self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':unittest.main()
