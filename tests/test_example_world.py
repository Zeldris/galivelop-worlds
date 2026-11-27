"""PCK-6: el mundo de ejemplo carga solo, y el núcleo no nombra términos de Tarkor (invariante 9)."""

import re
import unittest
from pathlib import Path

from gworld.canon import canon_index
from gworld.pack import canon_digest, load_pack

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "valle-brumas"

# Lista única de términos de Tarkor (docs/ddd.md, invariante 9). No se escanea este archivo.
TARKOR_TERMS = (
    "Tarkor", "Helek Sirik", "Berig", "Vaelira", "Goirntes", "Nabieus", "Faerus", "Maktor", "Goirno",
    "Cristal Helado", "Clan Serhu", "la Concordia", "Gorhorn", "Kegi", "Hashma", "el Estallido",
    "el Detonante", "la Isla Cambiante",
)


def forbidden_hits(*roots: Path) -> list[tuple[str, str]]:
    pats = [(t, re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.IGNORECASE)) for t in TARKOR_TERMS]
    hits = []
    for root in roots:
        for f in sorted(root.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            hits += [(str(f.relative_to(ROOT)), t) for t, p in pats if p.search(text)]
    return hits


class ExampleWorldTest(unittest.TestCase):
    def test_carga_y_huella(self):
        pack = load_pack(EXAMPLE)
        self.assertEqual(pack.ref.id, "valle-brumas")
        self.assertEqual(pack.ref.sha256, canon_digest(EXAMPLE / "canon"))

    def test_indice_con_ids_validos(self):
        index = canon_index(load_pack(EXAMPLE))
        self.assertGreaterEqual(len(index["facts"]), 5)
        for fact in index["facts"]:
            self.assertRegex(fact["id"], r"^fact:[0-9a-f]{32}$")


class Invariant9Test(unittest.TestCase):
    def test_nucleo_y_ejemplo_sin_terminos_de_tarkor(self):
        hits = forbidden_hits(ROOT / "gworld", EXAMPLE)
        self.assertEqual(hits, [], "términos de Tarkor (archivo, término): " + "; ".join(f"{f}: {t}" for f, t in hits))

    def test_el_escaneo_detecta_y_respeta_limites_de_palabra(self):
        tmp = ROOT / "gworld" / "_tmp_inv9.json"
        try:
            tmp.write_text('{"x": "Helek Sirik y Kegiganov"}', encoding="utf-8")
            hits = [h for h in forbidden_hits(ROOT / "gworld") if "_tmp_inv9" in h[0]]
        finally:
            tmp.unlink()
        self.assertEqual(hits, [("gworld/_tmp_inv9.json", "Helek Sirik")])


if __name__ == "__main__":
    unittest.main()
