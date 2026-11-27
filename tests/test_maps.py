import hashlib
import tempfile
import unittest
from pathlib import Path

from gworld.maps import FmgImporter, MapError, MapImporter
from gworld.schema import validate
from gworld.schemas import load_schema

FIXTURE = Path(__file__).parent / "fixtures" / "mini.map"
REAL = Path("/home/user/World-Maker-Fantasy/docs/map/Helek_World.map")


def import_text(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.map"
        p.write_text(text, encoding="utf-8")
        return FmgImporter().import_map(p)


def fixture_lines():
    return FIXTURE.read_text(encoding="utf-8").split("\n")


def code_of(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.map"
        p.write_text(text, encoding="utf-8")
        with unittest.TestCase().assertRaises(MapError) as cm:
            FmgImporter().import_map(p)
        return cm.exception.code


class FmgImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = FmgImporter().import_map(FIXTURE)

    def test_cumple_la_interfaz(self):
        imp: MapImporter = FmgImporter()
        self.assertEqual(imp.import_map(FIXTURE)["kind"], "gworld.map/0")

    def test_valida_contra_el_esquema(self):
        self.assertEqual(validate(self.doc, load_schema("gworld.map/0")), [])

    def test_contenido(self):
        d = self.doc
        self.assertEqual(len(d["cells"]), 20)
        self.assertEqual([c["id"] for c in d["cells"]], list(range(20)))
        self.assertEqual([z["id"] for z in d["zones"]], ["landmass:1", "region:1", "province:1"])
        self.assertEqual(d["zones"][2]["parent"], "region:1")
        self.assertEqual(d["cells"][0]["zones"], ["landmass:1", "region:1", "province:1"])
        self.assertEqual(d["cells"][19]["zones"], ["landmass:1"])
        self.assertEqual([p["name"] for p in d["places"]], ["Villa Uno"])  # la borrada no entra
        self.assertEqual(d["places"][0]["capitalOf"], "region:1")
        self.assertEqual(d["rivers"][0]["cells"], [0, 1, 6])  # sin el -1
        self.assertEqual(d["routes"][0]["zone"], "landmass:1")

    def test_vecinas_simetricas(self):
        n = {c["id"]: set(c["neighbours"]) for c in self.doc["cells"]}
        for a, ns in n.items():
            for b in ns:
                self.assertIn(a, n[b])

    def test_origen_y_huella(self):
        o = self.doc["origin"]
        self.assertEqual(o["sha256"], "sha256:" + hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(o["file"], {"name": "mini.map", "format": "fmg", "formatVersion": "1.137.6"})
        self.assertEqual(o["seed"], "42")

    def test_huella_cambia_con_el_archivo(self):
        lines = fixture_lines()
        lines[0] = lines[0].replace("|42|", "|43|")
        self.assertNotEqual(import_text("\n".join(lines))["origin"]["sha256"], self.doc["origin"]["sha256"])

    def test_determinista(self):
        self.assertEqual(FmgImporter().import_map(FIXTURE), self.doc)

    def test_crlf_equivale(self):
        text = FIXTURE.read_text(encoding="utf-8").replace("\n", "\r\n")
        d = import_text(text)
        self.assertEqual(d["cells"], self.doc["cells"])

    def test_version_distinta(self):
        lines = fixture_lines()
        lines[0] = lines[0].replace("1.137.6", "1.99.0", 1)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.map"
            p.write_text("\n".join(lines))
            with self.assertRaises(MapError) as cm:
                FmgImporter().import_map(p)
        self.assertEqual(cm.exception.code, "unsupported_version")
        self.assertEqual(cm.exception.detail, "1.99.0")

    def test_no_es_un_map(self):
        self.assertEqual(code_of("hola\nmundo\n"), "malformed")
        lines = fixture_lines()
        lines[0] = "no es una version"
        self.assertEqual(code_of("\n".join(lines)), "malformed")

    def test_truncado(self):
        lines = fixture_lines()
        self.assertEqual(code_of("\n".join(lines[:20])), "malformed")  # faltan registros
        self.assertEqual(code_of("\n".join(lines[:5] + ["<svg>"] + lines[6:])), "malformed")  # SVG sin cerrar

    def test_registro_json_roto(self):
        lines = fixture_lines()
        lines[6] = lines[6][:100]
        self.assertEqual(code_of("\n".join(lines)), "malformed")

    def test_array_de_otra_longitud(self):
        lines = fixture_lines()
        lines[25] = "0,0,0"
        self.assertEqual(code_of("\n".join(lines)), "mismatch")

    def test_area_que_no_cuadra(self):
        lines = fixture_lines()
        lines[14] = lines[14].replace('"area":', '"area":1')
        self.assertEqual(code_of("\n".join(lines)), "mismatch")

    def test_no_existe(self):
        with self.assertRaises(MapError) as cm:
            FmgImporter().import_map(FIXTURE.with_name("no-existe.map"))
        self.assertEqual(cm.exception.code, "unreadable")

    def test_no_utf8(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.map"
            p.write_bytes(b"\xff\xfe\x00")
            with self.assertRaises(MapError) as cm:
                FmgImporter().import_map(p)
        self.assertEqual(cm.exception.code, "malformed")


@unittest.skipUnless(REAL.exists(), "sin el mapa real de WMF")
class RealMapSmoke(unittest.TestCase):
    def test_humo(self):
        d = FmgImporter().import_map(REAL)
        self.assertEqual(validate(d, load_schema("gworld.map/0")), [])
        self.assertEqual(len(d["cells"]), 5120)


if __name__ == "__main__":
    unittest.main()
