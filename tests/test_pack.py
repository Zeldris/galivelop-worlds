import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from gworld.pack import PackError, WorldPack, canon_digest, load_pack


def make(root, canon_files=None, canon_file=None, licence=None, canon_path=None, sha=None, raw=None, drop=()):
    root = Path(root)
    if canon_file is not None:
        (root / "canon.md").write_bytes(canon_file)
        target = root / "canon.md"
        cp = "canon.md"
    else:
        for name, data in (canon_files or {"a.md": b"uno", "sub/b.md": b"dos"}).items():
            f = root / "canon" / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        target = root / "canon"
        cp = "canon"
    m = {"kind": "gworld.pack/0", "id": "mundo", "version": "1", "licence": {"spdx": "MIT"} if licence is None else licence,
         "canon": {"path": canon_path or cp, "sha256": sha or canon_digest(target)}, "rules": ["r1"]}
    for k in drop:
        m.pop(k)
    (root / "pack.json").write_text(raw if raw is not None else json.dumps(m), encoding="utf-8")


def code_of(tc, root):
    with tc.assertRaises(PackError) as cm:
        load_pack(root)
    return cm.exception


class PackTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.d = Path(self._t.name)

    def test_valid_file_canon(self):
        make(self.d, canon_file=b"hola", licence={"text": "t", "conditions": "c"})
        p = load_pack(self.d)
        self.assertIsInstance(p, WorldPack)
        self.assertEqual(p.ref.id, "mundo")
        self.assertEqual(p.ref.sha256, canon_digest(self.d / "canon.md"))
        self.assertEqual((p.licence.spdx, p.licence.text, p.licence.conditions), (None, "t", "c"))
        self.assertEqual(p.canon_path, self.d / "canon.md")
        self.assertEqual(p.rules, ("r1",))

    def test_valid_dir_canon(self):
        make(self.d)
        p = load_pack(str(self.d))
        self.assertEqual(p.root, self.d)
        self.assertEqual(p.canon_path, self.d / "canon")
        self.assertEqual(p.licence.spdx, "MIT")
        self.assertEqual(p.manifest["version"], "1")

    def test_no_licence(self):
        make(self.d, drop=("licence",))
        e = code_of(self, self.d)
        self.assertEqual(e.code, "schema")
        self.assertIn("licence", str(e))

    def test_empty_licence(self):
        make(self.d, licence={})
        self.assertEqual(code_of(self, self.d).code, "schema")

    def test_no_manifest(self):
        self.assertEqual(code_of(self, self.d).code, "no_manifest")
        self.assertEqual(code_of(self, self.d / "nada").code, "no_manifest")

    def test_bad_json(self):
        make(self.d, raw="{no")
        self.assertEqual(code_of(self, self.d).code, "bad_json")

    def test_canon_dotdot(self):
        (self.d / "pk").mkdir()
        (self.d / "fuera").mkdir()
        make(self.d / "pk", canon_path="../fuera", sha="sha256:" + "0" * 64)
        self.assertEqual(code_of(self, self.d / "pk").code, "canon_outside")

    def test_canon_absolute(self):
        make(self.d, canon_path=str(self.d), sha="sha256:" + "0" * 64)
        self.assertEqual(code_of(self, self.d).code, "canon_outside")

    def test_canon_symlink_outside(self):
        (self.d / "pk").mkdir()
        (self.d / "fuera").mkdir()
        os.symlink(self.d / "fuera", self.d / "pk" / "canon")
        make(self.d / "pk", canon_files={}, canon_path="canon", sha="sha256:" + "0" * 64)
        self.assertEqual(code_of(self, self.d / "pk").code, "canon_outside")

    def test_licence_only_conditions(self):
        make(self.d, licence={"conditions": "x"})
        e = code_of(self, self.d)
        self.assertEqual(e.code, "schema")
        self.assertIn("licence", str(e))

    @unittest.skipUnless(hasattr(os, "symlink"), "sin symlinks")
    def test_dir_symlink_in_canon(self):
        make(self.d)
        (self.d / "otro").mkdir()
        try:
            os.symlink(self.d / "otro", self.d / "canon" / "enlace", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("el SO no permite symlinks")
        with self.assertRaises(PackError) as cm:
            canon_digest(self.d / "canon")
        self.assertEqual(cm.exception.code, "canon_outside")

    def test_json_recursion_error_is_bad_json(self):
        # Si json.loads se queda sin pila (depende de la versión de Python), es bad_json.
        make(self.d, raw="{}")
        with mock.patch("gworld.pack.json.loads", side_effect=RecursionError("maximum recursion depth")):
            err = code_of(self, self.d)
        self.assertEqual(err.code, "bad_json")
        self.assertIn("demasiado anidado", str(err))

    def test_deeply_nested_json_is_pack_error(self):
        # Hay versiones de Python cuyo json.loads lo parsea (y falla el esquema) y otras que no:
        # en las dos, el fallo es un PackError, nunca una RecursionError suelta.
        make(self.d, raw='{"rules":' + "[" * 100000 + "]" * 100000 + "}")
        err = code_of(self, self.d)
        self.assertIn(err.code, {"bad_json", "schema"})
        if err.code == "bad_json":
            self.assertIn("demasiado anidado", str(err))
        else:
            self.assertIn("gworld.pack/0", str(err))

    def test_unreadable_subdir_raises(self):
        make(self.d)
        err = OSError(13, "Permission denied", str(self.d / "canon" / "sub"))

        def fake_walk(top, followlinks=False, onerror=None):
            onerror(err)
            return iter(())
        with mock.patch("gworld.pack.os.walk", fake_walk):
            with self.assertRaises(PackError) as cm:
                canon_digest(self.d / "canon")
        self.assertEqual(cm.exception.code, "unreadable")
        self.assertIn("Permission denied", str(cm.exception))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root lee igual")
    def test_unreadable_canon_file(self):
        make(self.d)
        f = self.d / "canon" / "a.md"
        sha = canon_digest(self.d / "canon")
        make(self.d, sha=sha)
        f.chmod(0)
        self.addCleanup(f.chmod, 0o644)
        self.assertEqual(code_of(self, self.d).code, "unreadable")

    def test_canon_path_root_rejected(self):
        for cp in (".", "sub/.."):
            with self.subTest(cp=cp):
                make(self.d, canon_path=cp, sha="sha256:" + "0" * 64)
                err = code_of(self, self.d)
                self.assertEqual(err.code, "canon_outside")
                self.assertIn("raíz del paquete", str(err))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "sin mkfifo")
    def test_fifo_in_canon(self):
        make(self.d)
        os.mkfifo(self.d / "canon" / "fifo")
        with self.assertRaises(PackError) as cm:
            canon_digest(self.d / "canon")
        self.assertEqual(cm.exception.code, "canon_special")
        self.assertIn("especial", str(cm.exception))
        with self.assertRaises(PackError) as cm:
            canon_digest(self.d / "canon" / "fifo")
        self.assertEqual(cm.exception.code, "canon_special")

    @unittest.skipUnless(hasattr(os, "symlink"), "sin symlinks")
    def test_outside_message_says_canon(self):
        make(self.d)
        (self.d / "otro.md").write_bytes(b"x")
        (self.d / "canon" / "l.md").symlink_to(self.d / "otro.md")
        with self.assertRaises(PackError) as cm:
            canon_digest(self.d / "canon")
        self.assertEqual(cm.exception.code, "canon_outside")
        self.assertIn("fuera del canon", str(cm.exception))
        self.assertNotIn("fuera del paquete", str(cm.exception))

    def test_non_utf8_name(self):
        make(self.d)
        try:
            (self.d / "canon" / os.fsdecode(b"\xff.md")).write_bytes(b"x")
        except OSError:
            self.skipTest("el sistema de archivos no admite nombres no UTF-8")
        with self.assertRaises(PackError) as cm:
            canon_digest(self.d / "canon")
        self.assertEqual(cm.exception.code, "canon_name")

    def test_validate_recursion_own_code(self):
        make(self.d)
        with mock.patch("gworld.pack.validate", side_effect=RecursionError):
            err = code_of(self, self.d)
        self.assertEqual(err.code, "too_deep")
        self.assertIn("demasiado anidado", str(err))

    def test_canon_path_nul(self):
        make(self.d, canon_path="canon\0x", sha="sha256:" + "0" * 64)
        self.assertEqual(code_of(self, self.d).code, "canon_outside")

    def test_canon_missing(self):
        make(self.d, canon_path="no-existe", sha="sha256:" + "0" * 64)
        self.assertEqual(code_of(self, self.d).code, "canon_missing")

    def test_canon_hash_mismatch(self):
        make(self.d, sha="sha256:" + "0" * 64)
        e = code_of(self, self.d)
        self.assertEqual(e.code, "canon_hash")
        self.assertIn("0" * 64, str(e))
        self.assertIn(canon_digest(self.d / "canon"), str(e))

    def test_digest_changes_with_byte_and_rename(self):
        make(self.d)
        h0 = canon_digest(self.d / "canon")
        (self.d / "canon" / "a.md").write_bytes(b"unO")
        h1 = canon_digest(self.d / "canon")
        self.assertNotEqual(h0, h1)
        (self.d / "canon" / "a.md").write_bytes(b"uno")
        self.assertEqual(canon_digest(self.d / "canon"), h0)
        (self.d / "canon" / "a.md").rename(self.d / "canon" / "c.md")
        self.assertNotEqual(canon_digest(self.d / "canon"), h0)

    def test_digest_independent_of_creation_order(self):
        files = {"a.md": b"1", "z/b.md": b"2", "m.md": b"3"}
        a, b = self.d / "a", self.d / "b"
        for root, order in ((a, list(files)), (b, list(reversed(files)))):
            for n in order:
                f = root / n
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(files[n])
        self.assertEqual(canon_digest(a), canon_digest(b))

    def test_load_writes_nothing(self):
        make(self.d)
        snap = sorted((str(p), p.stat().st_mtime_ns) for p in self.d.rglob("*"))
        load_pack(self.d)
        self.assertEqual(snap, sorted((str(p), p.stat().st_mtime_ns) for p in self.d.rglob("*")))


if __name__ == "__main__":
    unittest.main()
