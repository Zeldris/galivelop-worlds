"""MAP-4 paso 4: conversor de las reglas de Tarkor (``tools/tarkor_maprules.py``).

Unitarios con lore, canon y mapa minimos a mano; humo con ``Helek_World.map`` y las reglas de WMF, que se salta si no
hay WMF (``GW_WMF_DIR`` o ``../World-Maker-Fantasy`` junto al repo).
"""

import json
import tempfile
import contextlib
import io
import unittest
from pathlib import Path
from unittest import mock

from gworld.maprules import bind, check_rules, load_map_rules
from gworld.maps import FmgImporter, MapError
from tools.tarkor_maprules import convert, convert_dir, main
from tests.wmf import wmf_dir as locate_wmf

SHA = "sha256:" + "ab" * 32
FAKE = {
    "origin": {"sha256": SHA},
    "zones": [
        {"id": "landmass:2", "layer": "landmass", "name": "Landmass 2"},
        {"id": "landmass:3", "layer": "landmass", "name": "Landmass 3"},
        {"id": "region:1", "layer": "region", "name": "Cristal Helado"},
        {"id": "region:2", "layer": "region", "name": "Llanuras"},
        {"id": "region:3", "layer": "region", "name": "Margen"},
        {"id": "province:1", "layer": "province", "name": "Cruce"},
    ],
    "places": [{"id": 7, "name": "Alfa"}, {"id": 8, "name": "Beta"}],
    # Berig es la masa de Cristal Helado (landmass:3); Vaelira, la otra.
    "cells": [{"id": 0, "zones": ["landmass:3", "region:1"]}, {"id": 1, "zones": ["landmass:3", "region:2"]},
              {"id": 2, "zones": ["landmass:2"]}],
}
SRC = "fuente"


def lore(*rules, undecided=()):
    return {"reglas": [{"texto": "t", "fuente": SRC, **r} for r in rules],
            "sinDecidir": [{"texto": "t", "fuente": SRC, **r} for r in undecided]}


def canon(medidas=(), undecided=()):
    return {"tolerancia": 0.05, "medidas": [{"fuente": SRC, **m} for m in medidas],
            "sinDecidir": [{"fuente": SRC, **m} for m in undecided]}


def one(rule: dict) -> dict:
    out = convert(lore(rule), canon(), FAKE)
    bind(out, FAKE)
    (r,) = out["rules"]
    return r


class ConvertTest(unittest.TestCase):
    def check(self, rule: dict, **want):
        r = one({"id": "r", **rule})
        self.assertEqual({k: r[k] for k in want}, want)
        self.assertEqual((r["id"], r["text"], r["source"]), ("r", "t", SRC))
        self.assertNotIn("facts", r)

    def test_cabecera(self):
        out = convert(lore(), canon(), FAKE)
        self.assertEqual(out, {"kind": "gworld.maprules/0", "map": SHA, "tolerance": 0.05, "rules": []})

    def test_orden(self):
        self.check({"tipo": "orden", "eje": "norte-sur", "grupos": [["Cristal Helado"], ["Llanuras", "Margen"]]},
                   type="order", axis="north-south", groups=[["region:1"], ["region:2", "region:3"]])

    def test_oeste_de_regiones_y_continentes(self):
        self.check({"tipo": "oeste-de", "a": "Llanuras", "b": "Margen"}, type="side-of", a="region:2", b="region:3",
                   side="west")
        self.check({"tipo": "oeste-de", "a": {"continente": "Vaelira"}, "b": {"continente": "Berig"}},
                   a="landmass:2", b="landmass:3")

    def test_frontera(self):
        self.check({"tipo": "frontera", "a": "Llanuras", "b": "Margen", "orientacion": "norte-sur"}, type="border",
                   orientation="north-south")

    def test_costa_a_costa(self):
        self.check({"tipo": "costa-a-costa", "region": "Cristal Helado"}, type="coast-to-coast", zone="region:1",
                   axis="west-east")

    def test_solo_linda_y_lindan(self):
        self.check({"tipo": "solo-linda", "region": "Margen", "con": ["Llanuras"]}, type="only-borders",
                   zone="region:3", **{"with": ["region:2"]})
        self.check({"tipo": "lindan", "a": "Margen", "b": "Llanuras"}, type="borders", a="region:3", b="region:2")

    def test_cierra_por(self):
        self.check({"tipo": "cierra-por", "region": "Llanuras", "borde": "sur", "por": "Margen", "minimo": 0.9},
                   type="closes-by", zone="region:2", edge="south", by="region:3", min=0.9)

    def test_adelgaza(self):
        self.check({"tipo": "adelgaza", "region": "Margen", "hacia": "oeste", "entre": ["Llanuras", "Cristal Helado"],
                    "y": ["Llanuras"], "maximo": 0.85},
                   type="narrows", zone="region:3", toward="west", between=["region:2", "region:1"],
                   max=0.85, **{"and": ["region:2"]})

    def test_corredor(self):
        self.check({"tipo": "corredor", "desde": {"provincia": "Cruce"}, "hasta": "Llanuras", "bordea": "Margen",
                    "lado": "oeste"}, type="corridor", **{"from": "province:1"}, to="region:2", along="region:3",
                   side="west")

    def test_dentro_de_y_sin_tierra_fuera(self):
        self.check({"tipo": "dentro-de", "continente": "Berig", "regiones": ["Llanuras"]}, type="inside",
                   landmass="landmass:3", zones=["region:2"])
        self.check({"tipo": "sin-tierra-fuera", "continentes": ["Vaelira", "Berig"], "nombre": "Isla"},
                   type="no-land-outside", landmasses=["landmass:2", "landmass:3"], name="Isla")

    def test_medidas(self):
        out = convert(lore(), canon([
            {"que": "area", "region": "Llanuras", "valor": 100},
            {"que": "envolvente", "continente": "Berig", "valor": [10, 20]},
            {"que": "distancia", "lugares": ["Alfa", "Beta"], "lore": "A → B", "rango": [1, 2]}]), FAKE)
        bind(out, FAKE)
        a, e, d = out["rules"]
        self.assertEqual((a["id"], a["type"], a["zone"], a["value"]), ("area-llanuras", "area", "region:2", 100))
        self.assertEqual((e["id"], e["type"], e["zone"], e["value"]), ("extent-berig", "extent", "landmass:3", [10, 20]))
        self.assertEqual((d["id"], d["type"], d["places"], d["range"]), ("distance-a-b", "distance", [7, 8], [1, 2]))

    def test_sin_decidir(self):
        out = convert(lore(undecided=[{"id": "muro", "tipo": "borde-norte", "continente": "Berig", "nota": "n"}]),
                      canon(undecided=[{"que": "area", "continente": "Berig", "rango": [5, 6], "nota": "x"},
                                       {"que": "forma", "continente": "Vaelira"}]), FAKE)
        bind(out, FAKE)
        edge, area, shape = out["undecided"]
        self.assertEqual((edge["type"], edge["landmass"], edge["side"]), ("edge", "landmass:3", "north"))
        self.assertEqual((area["id"], area["type"], area["range"]), ("area-berig", "area", [5, 6]))
        self.assertEqual((shape["id"], shape["type"], shape["zone"]), ("shape-vaelira", "shape", "landmass:2"))
        self.assertEqual(out["rules"], [])

    def test_nombre_que_no_resuelve(self):
        cases = [
            (lore({"id": "r", "tipo": "lindan", "a": "Margen", "b": "Mordor"}), canon(), "Mordor"),
            (lore({"id": "r", "tipo": "dentro-de", "continente": "Atlantis", "regiones": ["Margen"]}), canon(),
             "Atlantis"),
            (lore({"id": "r", "tipo": "corredor", "desde": {"provincia": "Nada"}, "hasta": "Margen",
                   "bordea": "Margen", "lado": "oeste"}), canon(), "Nada"),
            (lore(), canon([{"que": "distancia", "lugares": ["Alfa", "Omega"]}]), "Omega"),
            (lore(), canon([{"que": "area", "region": "Fantasma", "valor": 1}]), "Fantasma"),
        ]
        for lo, ca, name in cases:
            with self.subTest(name=name), self.assertRaises(MapError) as cm:
                convert(lo, ca, FAKE)
            self.assertEqual(cm.exception.code, "unknown_name")
            self.assertIn(repr(name), str(cm.exception))

    def test_ids_generados_recortados_a_64(self):
        long = "Region " + "muy larga " * 10
        doc = {**FAKE, "zones": FAKE["zones"] + [{"id": "region:9", "layer": "region", "name": long}]}
        out = convert(lore(), canon([{"que": "area", "region": long, "valor": 1},
                                     {"que": "envolvente", "region": long, "valor": [1, 2]},
                                     {"que": "distancia", "lugares": ["Alfa", "Beta"], "lore": long, "valor": 1}]),
                      doc)
        for r in out["rules"]:
            self.assertLessEqual(len(r["id"]), 64)
            self.assertFalse(r["id"].endswith("-"))

    def test_ids_que_chocan_llevan_sufijo(self):
        out = convert(lore(), canon([{"que": "area", "region": "Llanuras", "valor": 1},
                                     {"que": "area", "region": "Llanuras", "valor": 2}],
                                    undecided=[{"que": "area", "region": "Llanuras", "rango": [1, 2]}]), FAKE)
        self.assertEqual([r["id"] for r in out["rules"]], ["area-llanuras", "area-llanuras-2"])
        self.assertEqual([r["id"] for r in out["undecided"]], ["area-llanuras-3"])

    def test_nombre_ambiguo(self):
        doc = {**FAKE, "zones": FAKE["zones"] + [{"id": "region:8", "layer": "region", "name": "Llanuras"}],
               "places": FAKE["places"] + [{"id": 9, "name": "Alfa"}]}
        for lo, ca, name in [(lore({"id": "r", "tipo": "lindan", "a": "Margen", "b": "Llanuras"}), canon(),
                              "Llanuras"),
                             (lore(), canon([{"que": "distancia", "lugares": ["Alfa", "Beta"]}]), "Alfa")]:
            with self.subTest(name=name), self.assertRaises(MapError) as cm:
                convert(lo, ca, doc)
            self.assertEqual(cm.exception.code, "ambiguous_name")
            self.assertIn(repr(name), str(cm.exception))
        # Un nombre repetido que ninguna regla cita no estorba.
        convert(lore({"id": "r", "tipo": "lindan", "a": "Margen", "b": "Cristal Helado"}), canon(), doc)

    def test_salida_invalida_no_se_escribe(self):
        bad = canon([{"que": "envolvente", "region": "Llanuras", "rango": [1, 2]}])
        with self.assertRaises(MapError) as cm:
            convert(lore(), bad, FAKE)
        self.assertEqual(cm.exception.code, "bad_params")
        self.assertIn("extent no admite range", str(cm.exception))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r.json"
            err = io.StringIO()
            with mock.patch("tools.tarkor_maprules.convert_dir", lambda wmf: convert(lore(), bad, FAKE)), \
                    contextlib.redirect_stderr(err):
                self.assertEqual(main(["--wmf", "wmf", "--out", str(out)]), 1)
            self.assertFalse(out.exists())
            self.assertIn("extent no admite range", err.getvalue())

    def test_out_dentro_de_wmf(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sub" / ".." / "reglas.json"
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main(["--wmf", tmp, "--out", str(out)]), 1)
            self.assertIn("cae dentro de --wmf", err.getvalue())
            self.assertFalse(out.exists())

    def test_tipo_desconocido(self):
        with self.assertRaises(MapError) as cm:
            convert(lore({"id": "r", "tipo": "raro"}), canon(), FAKE)
        self.assertEqual(cm.exception.code, "unknown_type")
        self.assertIn("raro", str(cm.exception))

    def test_continente_sin_dos_masas(self):
        doc = {**FAKE, "zones": [z for z in FAKE["zones"] if z["id"] != "landmass:2"]}
        with self.assertRaises(MapError) as cm:
            convert(lore({"id": "r", "tipo": "oeste-de", "a": {"continente": "Vaelira"}, "b": "Margen"}), canon(), doc)
        self.assertIn("'Vaelira'", str(cm.exception))


def wmf_dir() -> Path | None:
    base = locate_wmf()
    if base is None:
        return None
    needed = (base / "docs" / "map" / "Helek_World.map", base / "map-generator" / "lore.json",
              base / "map-generator" / "canon.json")
    return base if all(p.is_file() for p in needed) else None


# Reglas que el humo espera en False, con su detalle exacto: ninguna por ahora (las 22 salen bien).
KNOWN_FALSE: dict[str, str] = {}


class SmokeTest(unittest.TestCase):
    def test_helek(self):
        base = wmf_dir()
        if base is None:
            self.skipTest("no hay WMF: define GW_WMF_DIR (o deja ../World-Maker-Fantasy junto al repo)")
        doc = FmgImporter().import_map(base / "docs" / "map" / "Helek_World.map")
        rules = convert_dir(base)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "reglas.json"
            self.assertEqual(main(["--wmf", str(base), "--out", str(out)]), 0)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), rules)
            loaded = load_map_rules(out)
        bind(loaded, doc)
        self.assertEqual((len(loaded["rules"]), len(loaded["undecided"])), (22, 3))
        res = check_rules(doc, loaded)
        decided, free = res[:22], res[22:]
        self.assertEqual(sum(1 for r in decided if r.type in ("area", "extent", "distance")), 9)
        self.assertEqual(sum(1 for r in decided if r.type not in ("area", "extent", "distance")), 13)
        self.assertEqual({r.id for r in decided if r.ok is False}, set(KNOWN_FALSE))
        for r in decided:
            if r.id in KNOWN_FALSE:
                self.assertEqual(r.detail, KNOWN_FALSE[r.id])
        self.assertEqual(sum(1 for r in decided if r.ok is True), 22 - len(KNOWN_FALSE))
        self.assertEqual([r.ok for r in free], [None, None, None])


if __name__ == "__main__":
    unittest.main()
