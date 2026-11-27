"""MAP-5 paso 1: paridad de ``gworld.maps`` con ``map-generator/`` de WMF sobre Helek.

El cruzado (``helek.gworld.json`` contra ``helek.json``) corre sin el clon de WMF. Los tests que leen el ``.map``
se saltan si no esta. Cada caso cita la linea de ``map-generator/tests/test_importar.py`` de la que sale.
"""
import importlib.util
import json
import random
import tempfile
import unittest
from pathlib import Path

from gworld._delaunay import triangulate
from gworld.maps import FmgImporter, ImportReview, MapError, _records
from gworld.schema import validate
from gworld.schemas import load_schema
from gworld.topology import check_map

FIX = Path(__file__).parent / "fixtures" / "helek"
MAP = Path("/home/user/World-Maker-Fantasy/docs/map/Helek_World.map")
MINI = Path(__file__).parent / "fixtures" / "mini.map"
STATES_RECORD = 14
# Diferencia conocida: Nabieus se movio a mano en WMF (helek.json) tras importar; el .map la guarda en otra celda.
MOVED = {614: {"cell": 3227, "point": [581.38, 317.03]}}  # gworld; WMF: celda 3237, (650.0, 318.0)

_spec = importlib.util.spec_from_file_location("helek_regen", FIX / "regen.py")
regen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(regen)


def _layer(cell, layer):
    ids = [z.split(":", 1)[1] for z in cell["zones"] if z.startswith(layer + ":")]
    return int(ids[0]) if ids else 0  # en WMF 0 = ninguna


def _import_altered(change):
    """Importa una copia del .map con ``change(registros)`` aplicado."""
    recs = _records(MAP.read_text(encoding="utf-8"))
    change(recs)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.map"
        p.write_text("\r\n".join(recs), encoding="utf-8", newline="")
        return FmgImporter().import_map(p)


class FixtureCross(unittest.TestCase):
    """Sin WMF: cada celda y cada lugar de ``helek.gworld.json`` casan con ``helek.json``."""

    @classmethod
    def setUpClass(cls):
        cls.w = json.loads((FIX / "helek.json").read_text(encoding="utf-8"))
        cls.g = json.loads((FIX / "helek.gworld.json").read_text(encoding="utf-8"))

    def test_celda_a_celda(self):
        w, g = self.w["celdas"], self.g["cells"]
        self.assertEqual(len(g), len(w))
        for wc, gc in zip(w, g):
            self.assertEqual(gc["id"], wc["i"])
            self.assertEqual(gc["height"], wc["h"], wc["i"])
            self.assertEqual(gc["biome"], str(wc["bioma"]), wc["i"])
            self.assertEqual(_layer(gc, "region"), wc["region"], wc["i"])
            self.assertEqual(_layer(gc, "province"), wc["provincia"], wc["i"])
            self.assertEqual(_layer(gc, "landmass"), wc["continente"], wc["i"])
            self.assertEqual(gc["neighbours"], wc["c"], wc["i"])
            self.assertEqual(gc["vertices"], wc["v"], wc["i"])

    def test_vertices(self):
        self.assertEqual(self.g["geometry"]["vertices"], self.w["vertices"])

    def test_lugares(self):
        w = {p["i"]: p for p in self.w["lugares"]}
        g = {p["id"]: p for p in self.g["places"]}
        self.assertEqual(set(g), set(w))
        for i, wp in w.items():
            gp = g[i]
            if i in MOVED:
                self.assertEqual({"cell": gp["cell"], "point": gp["point"]}, MOVED[i])
                self.assertEqual((wp["celda"], wp["x"], wp["y"]), (3237, 650.0, 318.0))
                wp = {**wp, "celda": gp["cell"], "x": gp["point"][0], "y": gp["point"][1]}
            self.assertEqual((gp["name"], gp["cell"], gp["point"], gp["type"]),
                             (wp["nombre"], wp["celda"], [wp["x"], wp["y"]], wp["tipo"]))
            self.assertEqual(gp.get("capitalOf"), f"region:{wp['region']}" if wp["capital"] else None)

    def test_zonas_con_nombre(self):
        names = {z["id"]: z["name"] for z in self.g["zones"]}
        for r in self.w["regiones"]:
            self.assertEqual(names[f"region:{r['i']}"], r["nombre"])
        for p in self.w["provincias"]:
            self.assertEqual(names[f"province:{p['i']}"], p["nombre"])

    def test_valida_y_pasa_check_map(self):
        self.assertEqual(validate(self.g, load_schema("gworld.map/0")), [])
        check_map(self.g)

    def test_cifras_de_helek(self):
        # WMF test_importar.py:42
        g = self.g
        self.assertEqual(len(g["cells"]), 5120)
        self.assertEqual(sum(z["layer"] == "landmass" for z in g["zones"]), 2)
        self.assertEqual([z["name"] for z in g["zones"] if z["layer"] == "region"],
                         ["Cristal Helado", "Llanuras del Viento Rojo", "Ciénaga Troncal", "El Margen Silencioso",
                          "La Meseta del Orden"])
        self.assertEqual(len(g["places"]), 5)
        provinces = [z for z in g["zones"] if z["layer"] == "province"]
        self.assertTrue(provinces)
        self.assertTrue(all(z["parent"] == "region:18" for z in provinces))
        # El agua (h < 20) es siempre bioma 0
        self.assertTrue(all((c["height"] < 20) == (c["biome"] == "0") for c in g["cells"]))


class Parity(unittest.TestCase):
    def test_version_distinta_falla_con_su_motivo(self):
        # WMF test_importar.py:66
        text = MINI.read_text(encoding="utf-8").replace("1.137.6", "1.140.0", 1)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.map"
            p.write_text(text, encoding="utf-8")
            with self.assertRaises(MapError) as cm:
                FmgImporter().import_map(p)
        self.assertEqual(cm.exception.code, "unsupported_version")
        self.assertIn("1.140.0", str(cm.exception))
        self.assertIn("solo se conoce la 1.137.6", str(cm.exception))

    def test_delaunay_vacio(self):
        # WMF test_importar.py:96: ningun punto dentro del circulo de un triangulo
        rnd = random.Random(7)
        pts = [(rnd.uniform(0, 100), rnd.uniform(0, 100)) for _ in range(150)]
        tri, half = triangulate(pts)
        hull = sum(1 for h in half if h == -1)
        self.assertEqual(len(tri) // 3, 2 * len(pts) - 2 - hull)
        for t in range(len(tri) // 3):
            a, b, c = (pts[tri[3 * t + k]] for k in range(3))
            giro = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            for k, p in enumerate(pts):
                if k in tri[3 * t:3 * t + 3]:
                    continue
                ax, ay, bx, by, cx, cy = a[0] - p[0], a[1] - p[1], b[0] - p[0], b[1] - p[1], c[0] - p[0], c[1] - p[1]
                det = ((ax * ax + ay * ay) * (bx * cy - cx * by) - (bx * bx + by * by) * (ax * cy - cx * ay)
                       + (cx * cx + cy * cy) * (ax * by - bx * ay))
                self.assertLessEqual(det * giro, 1e-6, f"punto {k} dentro del circulo del triangulo {t}")


@unittest.skipUnless(MAP.exists(), "sin el mapa real de WMF")
class FromRealMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc, cls.review = FmgImporter().import_with_review(MAP)

    def test_igual_al_fixture(self):
        # WMF test_importar.py:60: salida estable, dos imports iguales e iguales al fixture
        again = FmgImporter().import_map(MAP)
        self.assertEqual(again, self.doc)
        self.assertEqual(regen.dump(again), regen.dump(self.doc))
        self.assertEqual(regen.dump(self.doc), (FIX / "helek.gworld.json").read_text(encoding="utf-8"))

    def test_area_de_region_cambiada_da_mismatch_con_su_numero(self):
        # WMF test_importar.py:80 (+1 al area guardada: FMG guardo 19808 y las celdas suman 19807)
        def change(recs):
            states = json.loads(recs[STATES_RECORD])
            self.assertEqual(states[18]["i"], 18)
            states[18]["area"] += 1
            recs[STATES_RECORD] = json.dumps(states)
        with self.assertRaises(MapError) as cm:
            _import_altered(change)
        self.assertEqual(cm.exception.code, "mismatch")
        self.assertIn("region 18: FMG guardo 19808 km2 y las celdas suman 19807", cm.exception.detail)

    def test_informe_revisar(self):
        # WMF test_importar.py:54: 40 marcadores automaticos y 610 burgs borrados, fuera del mapa
        r = self.review
        self.assertIsInstance(r, ImportReview)
        self.assertEqual(len(r.markers), 40)
        self.assertEqual(r.deleted_burgs, 610)
        self.assertFalse({p["name"] for p in self.doc["places"]} & {m.name for m in r.markers})

    def test_import_map_da_solo_el_documento(self):
        self.assertIsInstance(FmgImporter().import_map(MAP), dict)


if __name__ == "__main__":
    unittest.main()
