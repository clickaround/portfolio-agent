import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_designcraft_web.py"
spec = importlib.util.spec_from_file_location("designcraft_web_installer", SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class DesignCraftInstallerTest(unittest.TestCase):
    def test_zip_traversal_is_rejected_before_any_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "test.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(f"{installer.DIRECTORY}/index.html", "safe")
                z.writestr(f"{installer.DIRECTORY}/../../escape", "unsafe")
            with self.assertRaises(ValueError):
                installer.extract_checked(archive, root / "out")
            self.assertFalse((root / "out").exists())
            self.assertFalse((root / "escape").exists())

    def test_zip_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "test.zip"
            entry = zipfile.ZipInfo(f"{installer.DIRECTORY}/link")
            entry.create_system = 3
            entry.external_attr = (0o120777 << 16)
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(entry, "target")
            with self.assertRaises(ValueError):
                installer.extract_checked(archive, root / "out")
