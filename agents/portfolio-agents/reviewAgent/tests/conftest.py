import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "backend" / "common" / "src"))
import pascal_bootstrap  # noqa: E402
pascal_bootstrap.setup()
