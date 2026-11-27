import ast
import sys
import unittest
from pathlib import Path

import gworld

ROOT = Path(gworld.__file__).resolve().parent


class PackageTest(unittest.TestCase):
    def test_version_is_str(self):
        self.assertIsInstance(gworld.__version__, str)
        self.assertTrue(gworld.__version__)

    def test_only_stdlib_imports(self):
        allowed = set(sys.stdlib_module_names) | {"gworld"}
        for path in sorted(ROOT.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for name in names:
                    self.assertIn(name, allowed, f"{path.name} importa {name}, fuera de stdlib")


if __name__ == "__main__":
    unittest.main()
