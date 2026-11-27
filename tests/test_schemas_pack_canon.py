import copy
import unittest

from gworld.schema import check_schema, validate
from gworld.schemas import load_schema

H = "sha256:" + "a" * 64
PACK = {
    "kind": "gworld.pack/0", "id": "mundo-ejemplo", "version": "0.1.0",
    "licence": {"spdx": "MIT"}, "canon": {"path": "canon/", "sha256": H}, "rules": [],
}
CANON = {
    "kind": "gworld.canon/0", "pack": {"id": "mundo-ejemplo", "version": "0.1.0", "sha256": H},
    "facts": [{"id": "fact:" + "0" * 16, "file": "canon/a.md", "headings": ["A", "B"],
               "text": "texto", "sha256": H}],
}


def codes(doc, kind):
    return [(e.path, e.code) for e in validate(doc, load_schema(kind))]


def mut(base, fn):
    d = copy.deepcopy(base)
    fn(d)
    return d


class SchemasTest(unittest.TestCase):
    def test_check_schema(self):
        for k in ("gworld.pack/0", "gworld.canon/0"):
            check_schema(load_schema(k))

    def test_unknown_kind(self):
        with self.assertRaisesRegex(ValueError, "esquema desconocido"):
            load_schema("gworld.nada/0")

    def test_valid(self):
        self.assertEqual(codes(PACK, "gworld.pack/0"), [])
        self.assertEqual(codes(CANON, "gworld.canon/0"), [])
        self.assertEqual(codes(mut(PACK, lambda d: d.update(licence={"text": "t", "conditions": "c"})),
                               "gworld.pack/0"), [])

    def test_pack_sin_licencia(self):
        d = mut(PACK, lambda d: d.pop("licence"))
        self.assertEqual(codes(d, "gworld.pack/0"), [("", "required")])

    def test_licencia_vacia(self):
        d = mut(PACK, lambda d: d.update(licence={}))
        self.assertEqual(codes(d, "gworld.pack/0"), [("/licence", "minProperties")])

    def test_sin_huella_canon(self):
        d = mut(PACK, lambda d: d["canon"].pop("sha256"))
        self.assertEqual(codes(d, "gworld.pack/0"), [("/canon", "required")])

    def test_huella_mal(self):
        d = mut(PACK, lambda d: d["canon"].update(sha256="sha256:xyz"))
        self.assertEqual(codes(d, "gworld.pack/0"), [("/canon/sha256", "pattern")])

    def test_kind_equivocado(self):
        d = mut(PACK, lambda d: d.update(kind="gworld.canon/0"))
        self.assertEqual(codes(d, "gworld.pack/0"), [("/kind", "const")])

    def test_propiedad_extra(self):
        d = mut(PACK, lambda d: d.update(extra=1))
        self.assertEqual(codes(d, "gworld.pack/0"), [("", "additionalProperties")])

    def test_fact_sin_id(self):
        d = mut(CANON, lambda d: d["facts"][0].pop("id"))
        self.assertEqual(codes(d, "gworld.canon/0"), [("/facts/0", "required")])

    def test_fact_huella_mal(self):
        d = mut(CANON, lambda d: d["facts"][0].update(sha256="abc"))
        self.assertEqual(codes(d, "gworld.canon/0"), [("/facts/0/sha256", "pattern")])


if __name__ == "__main__":
    unittest.main()
