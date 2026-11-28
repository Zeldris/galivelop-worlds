"""MAP-5 paso 3: las reglas del lore de Helek sobre ``helek.gworld.json`` (paridad con ``map-generator/tests/test_comprobar.py``).

Corre sin el clon de WMF: las reglas son ``helek.maprules.json`` (lo que da ``tools/tarkor_maprules.py`` sobre
``lore.json`` y ``canon.json`` de WMF; procedencia en ``tests/fixtures/helek/README.md``). Cada caso cita la linea de
``test_comprobar.py`` de la que sale. Las zonas se citan por id: ``region:17`` Cristal Helado, ``region:18`` Llanuras del
Viento Rojo, ``region:19`` Ciénaga Troncal, ``region:20`` El Margen Silencioso, ``region:21`` La Meseta del Orden.
"""
import copy
import json
import re
import unittest
from pathlib import Path

from gworld.maprules import check_rules
from tests.test_maprules import grid, rule, rules

FIX = Path(__file__).parent / "fixtures" / "helek"
LLANURAS, CIENAGA, MARGEN, MESETA = "region:18", "region:19", "region:20", "region:21"
SEA = 20


def _zone_of(cell, layer):
    return next((z for z in cell.get("zones", []) if z.startswith(layer + ":")), None)


def _set_zone(cell, layer, new):
    cell["zones"] = [new if z.startswith(layer + ":") else z for z in cell["zones"]]


class HelekRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((FIX / "helek.gworld.json").read_text(encoding="utf-8"))
        cls.rules = json.loads((FIX / "helek.maprules.json").read_text(encoding="utf-8"))
        # Las reglas del lore (las 13 de comprobar.py); las medidas del canon son de medir.py (paso 2).
        cls.lore_ids = {x["id"] for x in cls.rules["rules"] if x["type"] not in ("area", "extent", "distance")}
        cls.base = {r.id: r for r in check_rules(cls.doc, cls.rules)}

    def result(self, doc):
        return {r.id: r for r in check_rules(doc, self.rules)}

    def new_failures(self, doc):
        """Reglas que fallan en ``doc`` y no fallaban en el mapa real, con su resultado."""
        return {i: r for i, r in self.result(doc).items() if i in self.lore_ids and r.ok is False and self.base[i].ok}

    def land_cells(self, doc, zone):
        return [c for c in doc["cells"] if c["height"] >= SEA and zone in c["zones"]]

    def test_todas_las_reglas_decididas_dan_ok(self):  # WMF test_comprobar.py:27
        decided = [r for r in self.base.values() if r.id in {x["id"] for x in self.rules["rules"]}]
        self.assertEqual(len(decided), 22)
        self.assertEqual({r.id: r.ok for r in decided if r.ok is not True}, {})

    def test_meseta_que_linda_con_llanuras_rompe_meseta_solo_margen(self):  # WMF test_comprobar.py:44
        doc = copy.deepcopy(self.doc)
        cells = {c["id"]: c for c in doc["cells"]}
        cand = [c for c in doc["cells"] if c["height"] >= SEA and LLANURAS in c["zones"]
                and any(MARGEN in cells[j]["zones"] for j in c["neighbours"])]
        chosen = cand[:10]
        ids = {c["id"] for c in chosen}
        self.assertEqual(len(chosen), 10)
        for c in chosen:
            self.assertTrue(any(LLANURAS in cells[j]["zones"] and j not in ids for j in c["neighbours"]))
            _set_zone(c, "region", MESETA)
        new = self.new_failures(doc)
        self.assertEqual(set(new), {"meseta-solo-margen"})
        self.assertIn(LLANURAS, new["meseta-solo-margen"].detail)

    def test_intercambiar_llanuras_y_cienaga_rompe_llanuras_al_oeste(self):  # WMF test_comprobar.py:62
        doc = copy.deepcopy(self.doc)
        swap = {LLANURAS: CIENAGA, CIENAGA: LLANURAS}
        for c in doc["cells"]:
            if _zone_of(c, "region") in swap:
                _set_zone(c, "region", swap[_zone_of(c, "region")])
        new = self.new_failures(doc)
        # WMF da las mismas dos (comprobado en la misma mutacion): su test solo exige la primera.
        self.assertEqual(set(new), {"llanuras-al-oeste", "margen-toda-la-cienaga"})
        xa, xb = (float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", new["llanuras-al-oeste"].detail)[:2])
        self.assertGreater(xa, xb)

    def test_margen_sin_costa_occidental_rompe_corredor_costero(self):  # WMF test_comprobar.py:70
        doc = copy.deepcopy(self.doc)
        cells = {c["id"]: c for c in doc["cells"]}
        own = self.land_cells(doc, MARGEN)
        x_centre = sum(c["center"][0] for c in own) / len(own)

        def has_sea(c):
            return any(cells[j]["height"] < SEA for j in c["neighbours"])

        layers = 0
        while True:  # al hundir las costeras, las de detras pasan a serlo: hasta que no queda costa occidental
            coastal = [c for c in own if c["height"] >= SEA and c["center"][0] < x_centre and has_sea(c)]
            if not coastal:
                break
            for c in coastal:
                c["height"] = 10
            layers += 1
        self.assertGreater(layers, 0)
        new = self.new_failures(doc)
        # Sin costa el Margen se achica y deja de lindar: WMF falla las mismas tres (su test solo exige la primera).
        self.assertEqual(set(new), {"corredor-costero", "margen-se-adelgaza", "margen-sur-de-llanuras"})
        self.assertEqual(new["corredor-costero"].detail, "sin camino por tierra")

    def test_margen_que_no_cierra_la_cienaga_rompe_margen_toda_la_cienaga(self):  # WMF test_comprobar.py:89
        doc = copy.deepcopy(self.doc)
        cells = {c["id"]: c for c in doc["cells"]}
        for c in doc["cells"]:
            if MARGEN in c["zones"] and c["center"][0] > 630 and any(CIENAGA in cells[j]["zones"] for j in c["neighbours"]):
                _set_zone(c, "region", MESETA)
        new = self.new_failures(doc)
        # La Meseta pasa a lindar con la Cienaga: WMF falla tambien meseta-solo-margen (su test solo exige la primera).
        self.assertEqual(set(new), {"margen-toda-la-cienaga", "meseta-solo-margen"})
        self.assertRegex(new["margen-toda-la-cienaga"].detail, r"\d+ ?%")

    def test_lugar_isla_cambiante_rompe_sin_isla_cambiante(self):  # WMF test_comprobar.py:102
        doc = copy.deepcopy(self.doc)
        doc["places"].append({"id": 9999, "name": "Isla Cambiante", "cell": 0, "point": [100, 100]})
        new = self.new_failures(doc)
        self.assertEqual(set(new), {"sin-isla-cambiante"})
        self.assertIn("1 lugares", new["sin-isla-cambiante"].detail)

    def test_adelgaza_con_centro_sin_grosor_falla_sin_excepcion(self):  # WMF test_comprobar.py:111
        r = next(x for x in self.rules["rules"] if x["type"] == "narrows")
        doc = copy.deepcopy(self.doc)
        points = [list(c["center"]) for c in self.land_cells(doc, r["zone"])]
        # Cada celda de los dos lados se pone sobre un punto de la zona: la distancia minima es 0 en todas.
        for z in r["between"] + r["and"]:
            for k, c in enumerate(self.land_cells(doc, z)):
                c["center"] = list(points[k % len(points)])
        res = self.result(doc)[r["id"]]
        self.assertFalse(res.ok)
        self.assertIn("no tienen grosor", res.detail)


class CorridorRegionZero(unittest.TestCase):
    def test_celdas_sin_region_son_pisables(self):  # WMF test_comprobar.py:70 (_corredor: reg_prov = region de la celda de partida; 0 = ninguna)
        # Q-33 (a): paridad con WMF. La provincia parte de una celda sin region (region 0 en WMF) y las celdas
        # sin region tambien se pisan, como en WMF; si no, A no llegaria a C.
        d = grid([".AxC.", "....b"], {"A": ["landmass:1", "province:1"], "x": ["landmass:1"],
                                       "C": ["landmass:1", "region:3"], "b": ["landmass:1", "region:2"]})
        r = rule("c", "corridor", to="region:3", along="region:2", side="west", **{"from": "province:1"})
        (res,) = check_rules(d, rules(r))
        self.assertEqual((res.ok, res.detail), (True, "camino de 20 km"))


if __name__ == "__main__":
    unittest.main()
