import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gworld._delaunay import _angle
from gworld.maps import FmgImporter, MapError, MapImporter, _voronoi
from gworld.schema import validate
from gworld.schemas import load_schema
from gworld.topology import check_map
from tests.wmf import wmf_dir

FIXTURE = Path(__file__).parent / "fixtures" / "mini.map"
_WMF = wmf_dir()
REAL = _WMF / "docs" / "map" / "Helek_World.map" if _WMF else None


def import_text(text):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.map"
        p.write_text(text, encoding="utf-8")
        return FmgImporter().import_map(p)


def fixture_lines():
    return FIXTURE.read_text(encoding="utf-8").split("\n")


def code_of(text, fragment=None):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.map"
        p.write_text(text, encoding="utf-8")
        with unittest.TestCase().assertRaises(MapError) as cm:
            FmgImporter().import_map(p)
        if fragment is not None:
            unittest.TestCase().assertIn(fragment, str(cm.exception))
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
        again = FmgImporter().import_map(FIXTURE)
        self.assertEqual(again, self.doc)
        self.assertEqual(again["origin"]["sha256"], self.doc["origin"]["sha256"])

    def test_pasa_check_map(self):
        check_map(self.doc)

    def test_import_map_llama_a_check_map(self):
        err = MapError("orphan_cell", "x", {"id": 3})
        with mock.patch("gworld.topology.check_map", side_effect=err):
            with self.assertRaises(MapError) as cm:
                FmgImporter().import_map(FIXTURE)
        self.assertEqual((cm.exception.code, cm.exception.detail), ("orphan_cell", {"id": 3}))

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
        self.assertEqual(code_of("hola\nmundo\n", "el registro 5 no es el SVG"), "malformed")
        lines = fixture_lines()
        lines[0] = "no es una version"
        self.assertEqual(code_of("\n".join(lines), "no empieza por una version de FMG"), "malformed")

    def test_truncado(self):
        lines = fixture_lines()
        self.assertEqual(code_of("\n".join(lines[:20]), "tiene 20 registros"), "malformed")  # faltan registros
        self.assertEqual(code_of("\n".join(lines[:5] + ["<svg>"] + lines[6:]), "no se cierra"), "malformed")  # SVG sin cerrar

    def test_registro_json_roto(self):
        lines = fixture_lines()
        lines[6] = lines[6][:100]
        self.assertEqual(code_of("\n".join(lines), "no es JSON valido"), "malformed")

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
        self.assertIn("no es texto UTF-8", str(cm.exception))


    def test_provincia_de_estado_inexistente_sin_parent(self):
        for state in (0, 9):
            lines = fixture_lines()
            lines[30] = lines[30].replace('"state":1', f'"state":{state}')
            prov = [z for z in import_text("\n".join(lines))["zones"] if z["id"] == "province:1"][0]
            self.assertNotIn("parent", prov)

    def test_ruta_invalida_se_salta(self):
        good = '{"i":0,"group":"roads","feature":1,"points":[[110.2,100,0],[210.5,105.25,1]]}'
        bad = ['{"i":1,"group":"Bad Group","points":[[1,2],[3,4]]}', '{"i":1,"group":"roads","points":[[1,2]]}',
               '{"i":1,"group":"roads","points":[[1,2],["a",4]]}']
        for b in bad:
            lines = fixture_lines()
            lines[37] = f"[{good},{b}]"
            self.assertEqual([r["id"] for r in import_text("\n".join(lines))["routes"]], [0], b)

    def test_burgo_sin_nombre_se_salta(self):
        lines = fixture_lines()
        lines[15] = lines[15].replace('"name":"Villa Uno",', "")
        self.assertEqual(import_text("\n".join(lines))["places"], [])

    def test_error_aritmetico_es_malformed(self):
        with mock.patch("gworld.maps.triangulate", side_effect=ZeroDivisionError("division by zero")):
            with self.assertRaises(MapError) as cm:
                FmgImporter().import_map(FIXTURE)
        self.assertEqual(cm.exception.code, "malformed")
        self.assertIn("ZeroDivisionError", str(cm.exception))


class RevisarTolerante(unittest.TestCase):
    """El informe «revisar» no puede tumbar import_map: lo ilegible se salta y se cuenta."""

    @staticmethod
    def altered(markers, notes):
        lines = fixture_lines()
        lines[35] = markers if isinstance(markers, str) else json.dumps(markers)
        lines[4] = notes if isinstance(notes, str) else json.dumps(notes)
        return "\n".join(lines)

    @staticmethod
    def both(text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.map"
            p.write_text(text, encoding="utf-8")
            return FmgImporter().import_map(p), FmgImporter().import_with_review(p)

    def test_marcador_sin_type(self):
        text = self.altered([{"i": 1, "x": 1, "y": 2, "cell": 0}, {"i": 2, "type": "ruins", "x": 1, "y": 2, "cell": 0}], [])
        doc, (doc2, review) = self.both(text)
        self.assertEqual(doc, doc2)
        self.assertEqual([m.id for m in review.markers], [2])
        self.assertEqual(review.skipped, 1)

    def test_nota_con_name_numerico(self):
        text = self.altered([{"i": 2, "type": "ruins", "x": 1, "y": 2, "cell": 0}],
                            [{"id": "marker2", "name": 7, "legend": "ok"}])
        doc, (_, review) = self.both(text)
        self.assertIsNone(review.markers[0].name)
        self.assertEqual(review.markers[0].legend, "ok")

    def test_notas_que_no_son_json(self):
        text = self.altered([{"i": 2, "type": "ruins", "x": 1, "y": 2, "cell": 0}], "{no es json")
        doc, (doc2, review) = self.both(text)
        self.assertEqual(doc, doc2)
        self.assertEqual(len(review.markers), 1)
        self.assertIsNone(review.markers[0].name)
        self.assertEqual(review.skipped, 1)


class GeometriaTest(unittest.TestCase):
    def test_circuncentro_como_fmg(self):
        # Circuncentro exacto (7, 3.5): 1372/196 da 7, pero FMG hace Math.floor(1/D * X) y (1/196)*1372 < 7.
        _, _, _, verts = _voronoi([[0, 0], [0, 7], [14, 0]], [])
        self.assertEqual(verts, {0: [6, 3]})

    def test_angulo_en_el_circuncentro(self):
        # Delaunator daria NaN; aqui 0, sin ZeroDivisionError.
        self.assertEqual(_angle(0, 0), 0.0)
        self.assertEqual(_angle(0.0, -0.0), 0.0)

@unittest.skipUnless(REAL is not None and REAL.exists(), "no hay WMF: define GW_WMF_DIR (o deja ../World-Maker-Fantasy junto al repo)")
class RealMapSmoke(unittest.TestCase):
    def test_humo(self):
        d = FmgImporter().import_map(REAL)
        self.assertEqual(validate(d, load_schema("gworld.map/0")), [])
        self.assertEqual(len(d["cells"]), 5120)
        check_map(d)


if __name__ == "__main__":
    unittest.main()
