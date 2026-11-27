"""PCK-7: paquete de prueba sobre docs/rpgtarkor/ de WMF, solo lectura (D11, invariante 4).

Se salta si no hay WMF: se localiza con GW_WMF_DIR o en ../World-Maker-Fantasy junto al repo.
Si GW_TARKOR_INDEX_OUT apunta a un archivo, se escribe ahí el índice para inspeccionarlo.
"""

import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from gworld.canon import canon_index
from gworld.pack import canon_digest, load_pack
from tests.wmf import wmf_dir

ROOT = Path(__file__).resolve().parent.parent


def wmf_canon() -> Path | None:
    base = wmf_dir()
    src = base / "docs" / "rpgtarkor" if base else None
    return src if src and src.is_dir() else None


def set_mode(root: Path, writable: bool) -> None:
    for p in [root, *root.rglob("*")]:
        if p.is_symlink():
            continue
        mode = p.stat().st_mode
        bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
        p.chmod(mode | stat.S_IWUSR if writable else mode & ~bits)


class TarkorPackTest(unittest.TestCase):
    def test_paquete_de_prueba_solo_lectura(self):
        src = wmf_canon()
        if src is None:
            self.skipTest("no hay WMF: define GW_WMF_DIR (o deja ../World-Maker-Fantasy junto al repo)")
        digest_before = canon_digest(src)
        mtime_before = src.stat().st_mtime_ns
        md_files = sorted(p.relative_to(src).as_posix() for p in src.rglob("*.md"))
        self.assertEqual(len(md_files), 34)

        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "pack"
            canon = pack_dir / "canon"
            shutil.copytree(src, canon)
            manifest = {
                "kind": "gworld.pack/0",
                "id": "tarkor-prueba",
                "version": "0.0.1",
                "licence": {"spdx": "CC-BY-NC-SA-4.0"},
                "canon": {"path": "canon", "sha256": canon_digest(canon)},
                "rules": [],
            }
            (pack_dir / "pack.json").write_text(json.dumps(manifest), encoding="utf-8")
            set_mode(canon, writable=False)
            try:
                index = canon_index(load_pack(pack_dir))
                again = canon_index(load_pack(pack_dir))
            finally:
                set_mode(canon, writable=True)

        self.assertEqual(index, again)
        ids = [f["id"] for f in index["facts"]]
        self.assertEqual(len(set(ids)), len(ids))
        files = {f["file"] for f in index["facts"]}
        self.assertEqual(sorted(files), md_files)
        out = os.environ.get("GW_TARKOR_INDEX_OUT")
        if out:
            Path(out).write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nhechos del índice de prueba: {len(ids)}")

        self.assertEqual(canon_digest(src), digest_before)
        self.assertEqual(src.stat().st_mtime_ns, mtime_before)


if __name__ == "__main__":
    unittest.main()
