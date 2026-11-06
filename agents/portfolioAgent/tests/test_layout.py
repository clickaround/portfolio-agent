import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.find_spec('portfolio_agent.core.checks.layout')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class LayoutSmokeTests(unittest.TestCase):
    def test_valid_synthetic_scene(self):
        doc=json.loads((ROOT/'examples/SYNTHETIC_scene.json').read_text(encoding='utf-8'))
        self.assertEqual(mod.check_scene(doc),[])
    def test_deliberately_invalid_scene(self):
        doc=json.loads((ROOT/'examples/SYNTHETIC_scene_invalid.json').read_text(encoding='utf-8'))
        codes={x['code'] for x in mod.check_scene(doc)}
        self.assertIn('PAGE_OVERFLOW',codes)
        self.assertIn('BBOX_OVERLAP',codes)
    def test_crop_requires_review(self):
        doc=json.loads((ROOT/'examples/SYNTHETIC_scene.json').read_text(encoding='utf-8'))
        doc['elements'][0]['allow_crop']=True
        self.assertTrue(any(x['code']=='UNREVIEWED_PDF_CROP' for x in mod.check_scene(doc)))

if __name__=='__main__':unittest.main()
