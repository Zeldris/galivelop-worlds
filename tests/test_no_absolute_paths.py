"""Los tests no fijan rutas absolutas de una máquina: la carpeta de WMF se localiza con ``tests/wmf.py``."""
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEEDLE = "/home" + "/"


class NoAbsolutePathsTest(unittest.TestCase):
    def test_sin_home_en_tests(self):
        found = []
        for p in sorted(HERE.rglob("*.py")):
            if p == Path(__file__).resolve():
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if NEEDLE in line:
                    found.append(f"{p.relative_to(HERE.parent).as_posix()}:{n}")
        self.assertEqual(found, [], "ruta absoluta '/home/' en: " + ", ".join(found))


if __name__ == "__main__":
    unittest.main()
