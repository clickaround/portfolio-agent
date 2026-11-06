import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('package_validator',ROOT/'scripts/validate_package.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class PackageTests(unittest.TestCase):
    def test_core_package_json_and_dag(self):
        self.assertEqual(mod.validate(ROOT),[])

if __name__=='__main__':unittest.main()
