"""MAP-5 paso 2: medidas de Helek de ``gworld.geometry`` y ``gworld.maprules`` iguales a las de WMF.

Corre sin el clon de WMF: usa ``tests/fixtures/helek/helek.gworld.json``. Las cifras salen de ejecutar
``map-generator/medir.py`` (``medidas``) de WMF en solo lectura; cada bloque cita la linea de WMF. gworld aplica
``unitKm`` y WMF ``kmPorUnidad``; en Helek los dos valen 1.
"""
import copy
import json
import unittest
from pathlib import Path

from gworld import geometry
from gworld.maprules import check_rules

FIX = Path(__file__).parent / "fixtures" / "helek"
SHA = json.loads((FIX / "helek.gworld.json").read_text(encoding="utf-8"))["origin"]["sha256"]

# WMF map-generator/tests/test_visor.py:66-88 (medidas.json = medir.medidas) y medir.py:97 (_medida): area, ancho x alto
# y caja [x0, y0, x1, y1] de las celdas de tierra de cada zona. Id de WMF -> zona de gworld.
AREAS = {  # zona: (area km2, (ancho, alto), caja)
    "region:17": (18421.5, (207, 121), [501, 18, 708, 139]),
    "region:18": (19907.0, (127, 251), [464, 117, 591, 368]),
    "region:19": (21178.0, (162, 180), [554, 128, 716, 308]),
    "region:20": (8058.5, (217, 104), [492, 290, 709, 394]),
    "region:21": (23499.5, (223, 169), [489, 324, 712, 493]),
    "province:1": (2249.5, (81, 89), [483, 279, 564, 368]),
    "province:2": (3187.0, (79, 71), [512, 213, 591, 284]),
    "province:3": (2214.5, (61, 56), [487, 276, 548, 332]),
    "province:4": (2294.0, (62, 66), [468, 226, 530, 292]),
    "landmass:2": (98193.0, (260, 504), [74, -4, 334, 500]),  # Vaelira
    "landmass:3": (91166.0, (252, 475), [464, 18, 716, 493]),  # Berig
}
# WMF map-generator/canon.json (medidas) y medir.comprobar (medir.py:91): lo que WMF mide para cada regla del canon.
CANON_RULES = [
    ("area", "region:18", 19900, 19907.0),
    ("extent", "region:17", [205, 120], [207, 121]),
    ("extent", "region:19", [160, 178], [162, 180]),
    ("extent", "region:18", [126, 249], [127, 251]),
    ("extent", "region:21", [221, 167], [223, 169]),
    ("extent", "region:20", [215, 103], [217, 104]),
    ("extent", "landmass:3", [250, 470], [252, 475]),
]

DOC = json.loads((FIX / "helek.gworld.json").read_text(encoding="utf-8"))


def land(doc, zone):
    sea = doc["seaLevel"]
    return [c["id"] for c in doc["cells"] if zone in c["zones"] and c["height"] >= sea]


def rules(doc):
    return {"kind": "gworld.maprules/0", "map": doc["origin"]["sha256"], "tolerance": 0.03, "rules": [
        {"id": f"{t}-{z.replace(':', '-')}", "type": t, "text": "t", "source": "canon", "zone": z, "value": v}
        for t, z, v, _ in CANON_RULES]}


class MeasuresTest(unittest.TestCase):
    def test_area_y_envolvente_de_cada_zona(self):
        # WMF test_visor.py:66-76
        self.assertEqual(DOC["geometry"]["unitKm"], 1)
        for zone, (area, ext, _) in AREAS.items():
            cells = land(DOC, zone)
            with self.subTest(zone=zone):
                self.assertGreater(len(cells), 0)
                self.assertAlmostEqual(geometry.area_km2(DOC, cells), area, places=3)
                got = geometry.extent_km(DOC, cells)
                self.assertEqual(len(got), 2)
                for g, e in zip(got, ext):
                    self.assertAlmostEqual(g, e, places=3)

    def test_unit_km_escala_area_y_envolvente(self):
        # Diferencia con WMF (kmPorUnidad = 1): gworld multiplica por unitKm y por unitKm**2 el area.
        doc = copy.deepcopy(DOC)
        doc["geometry"]["unitKm"] = 2
        cells = land(doc, "region:18")
        self.assertAlmostEqual(geometry.area_km2(doc, cells), 19907.0 * 4, places=3)
        for g, e in zip(geometry.extent_km(doc, cells), (127, 251)):
            self.assertAlmostEqual(g, e * 2, places=3)

    def test_el_canon_de_wmf_se_cumple(self):
        # WMF test_medir.py:26 (test_helek_json_respeta_el_canon)
        res = check_rules(DOC, rules(DOC))
        self.assertEqual([r.ok for r in res], [True] * len(CANON_RULES), [r.detail for r in res])
        for r, (typ, _, _, medido) in zip(res, CANON_RULES):
            text = f"{medido:,.0f}".replace(",", ".") if typ == "area" else " × ".join(
                f"{x:,.0f}".replace(",", ".") for x in medido)
            with self.subTest(rule=r.id):
                self.assertTrue(r.detail.startswith(f"medido {text} "), r.detail)

    def test_mover_una_frontera_hace_fallar(self):
        # WMF test_medir.py:32: un tercio de las celdas de las Llanuras pasa a la Cienaga.
        doc = copy.deepcopy(DOC)
        llanuras = sorted((c for c in doc["cells"] if "region:18" in c["zones"]), key=lambda c: c["id"])
        for c in llanuras[: len(llanuras) // 3]:
            c["zones"] = ["region:19" if z == "region:18" else z for z in c["zones"]]
        res = {r.id: r for r in check_rules(doc, rules(doc))}
        bad = {i for i, r in res.items() if not r.ok}
        # Area y envolvente de las Llanuras, y la envolvente de la Cienaga (que absorbe el tercio), se salen.
        self.assertEqual(bad, {"area-region-18", "extent-region-18", "extent-region-19"})
        self.assertIn("medido ", res["area-region-18"].detail)
        self.assertIn("(canon 19.900, ±3%)", res["area-region-18"].detail)
        self.assertNotIn("medido 19.907", res["area-region-18"].detail)
        self.assertIn("(canon 126 × 249, ±3%)", res["extent-region-18"].detail)
        self.assertNotIn("medido 127 × 251", res["extent-region-18"].detail)
        self.assertEqual(sum(1 for r in res.values() if r.ok), len(CANON_RULES) - 3)


class BoxTest(unittest.TestCase):
    def test_la_caja_de_berig_encierra_sus_celdas(self):
        # WMF test_visor.py:80: la caja de Berig (medir.py:97) contiene el centro de cada celda de tierra.
        x0, y0, x1, y1 = AREAS["landmass:3"][2]
        cells = [c for c in DOC["cells"] if "landmass:3" in c["zones"] and c["height"] >= DOC["seaLevel"]]
        self.assertGreater(len(cells), 0)
        for c in cells:
            self.assertTrue(x0 <= c["center"][0] <= x1 and y0 <= c["center"][1] <= y1, c["id"])
        # La caja que sale de los anillos de gworld es la de WMF.
        pts = [q for o, _ in geometry.polygons(DOC, [c["id"] for c in cells]) for q in o]
        got = [min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts)]
        self.assertEqual(got, [float(v) for v in (x0, y0, x1, y1)])


if __name__ == "__main__":
    unittest.main()
