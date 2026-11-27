import os
import re
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from gworld.canon import canon_index, normalize, read_facts
from gworld.pack import PackError, load_pack
from tests.test_pack import make

DOC = b"""intro

# Reino
Texto del reino.

## Ciudad
Una ciudad.

## Ciudad
Otra ciudad.

## Ciudad
Una ciudad.
"""


class CanonTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.d = Path(self._t.name)
        self.canon = self.d / "canon"
        self.canon.mkdir()
        (self.canon / "a.md").write_bytes(DOC)
        (self.canon / "sub").mkdir()
        (self.canon / "sub" / "b.md").write_bytes(b"# B\nhola\n")

    def ids(self, path=None):
        return {(f.file, f.headings, f.text): f.id for f in read_facts(path or self.canon)}

    def test_sections(self):
        facts = read_facts(self.canon)
        self.assertEqual([(f.file, f.headings) for f in facts], [
            ("a.md", ()), ("a.md", ("Reino",)), ("a.md", ("Reino", "Ciudad")),
            ("a.md", ("Reino", "Ciudad")), ("a.md", ("Reino", "Ciudad")), ("sub/b.md", ("B",))])
        self.assertEqual(facts[1].text, "Texto del reino.")

    def test_stable_ids_invariant5(self):
        self.assertEqual(self.ids(), self.ids())

    def test_edit_changes_only_that_section(self):
        before = self.ids()
        cp = self.d / "copy"
        shutil.copytree(self.canon, cp)
        p = cp / "a.md"
        p.write_bytes(p.read_bytes().replace(b"Texto del reino.", b"Texto cambiado."))
        after = self.ids(cp)
        changed = {k for k in after if after[k] != before.get(k)}
        self.assertEqual(len(changed), 1)
        (k,) = changed
        self.assertEqual(k[1], ("Reino",))
        unchanged = {k: v for k, v in after.items() if k not in changed}
        self.assertTrue(all(before[k] == v for k, v in unchanged.items()))

    def test_duplicate_headings_distinct_ids(self):
        ids = [f.id for f in read_facts(self.canon) if f.headings == ("Reino", "Ciudad")]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)  # incluso con el mismo texto (1.ª y 3.ª)

    def test_headings_in_code_ignored(self):
        (self.canon / "c.md").write_bytes(b"# T\n```\n# no\n```\n~~~\n## tampoco\n~~~\nfin\n")
        facts = [f for f in read_facts(self.canon) if f.file == "c.md"]
        self.assertEqual([f.headings for f in facts], [("T",)])
        self.assertIn("# no", facts[0].text)
        self.assertIn("fin", facts[0].text)

    def test_normalize(self):
        self.assertEqual(normalize("a \t b  \r\n\r\n\r\n\r\n c \r"), "a b\n\nc")
        (self.canon / "w.md").write_bytes(b"# X\r\nuno   dos\r\n")
        (self.d / "o").mkdir()
        (self.d / "o" / "w.md").write_bytes(b"# X\nuno dos")
        self.assertEqual({f.id for f in read_facts(self.canon / "w.md")},
                         {f.id for f in read_facts(self.d / "o" / "w.md")})

    def test_read_only_invariant4(self):
        before = self.ids()
        for p in [*self.canon.rglob("*"), self.canon]:
            p.chmod(p.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        try:
            self.assertEqual(self.ids(), before)
        finally:
            for p in [self.canon, *self.canon.rglob("*")]:
                p.chmod(p.stat().st_mode | stat.S_IWUSR)

    def test_no_write_modes_in_module(self):
        src = Path(__file__).resolve().parent.parent / "gworld" / "canon.py"
        code = "\n".join(l for l in src.read_text(encoding="utf-8").splitlines())
        # quita el docstring del módulo para no coincidir con su prosa
        code = code.split('"""', 2)[2]
        self.assertIsNone(re.search(r"open\([^)]*['\"][^'\"]*[wax+][^'\"]*['\"]", code))
        self.assertNotIn("write_text", code)
        self.assertNotIn("write_bytes", code)

    def test_index_valid(self):
        make(self.d, canon_files={"a.md": DOC, "sub/b.md": b"# B\nhola\n"})
        idx = canon_index(load_pack(self.d))
        self.assertEqual(idx["kind"], "gworld.canon/0")
        self.assertEqual(len(idx["facts"]), 6)
        self.assertRegex(idx["facts"][0]["id"], r"^fact:[0-9a-f]{32}$")

    def test_bad_encoding_reason(self):
        (self.canon / "x.md").write_bytes(b"\xff\xfe")
        with self.assertRaises(PackError) as cm:
            read_facts(self.canon)
        self.assertEqual(cm.exception.code, "bad_encoding")


if __name__ == "__main__":
    unittest.main()
