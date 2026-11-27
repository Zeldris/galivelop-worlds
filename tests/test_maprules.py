import json
import tempfile
import unittest
from pathlib import Path

from gworld.maprules import (PARAMS, RULE_TYPES, UNDECIDED_TYPES, RuleResult, bind, check_facts, check_rules,
                             load_map_rules)
from gworld.maps import MapError
from gworld.schema import validate
from gworld.schemas import load_schema
from tests.test_topology import small

SHA = "sha256:" + "0" * 64


def doc():
    d = small()
    d["places"] = [{"id": 1, "name": "A", "cell": 0, "point": [0, 0]}, {"id": 2, "name": "B", "cell": 3, "point": [9, 4]}]
    return d


def rule(id, type, **params):
    return {"id": id, "type": type, "text": "t", "source": "s", **params}


def rules(*rs, undecided=()):
    out = {"kind": "gworld.maprules/0", "map": SHA, "rules": list(rs)}
    if undecided:
        out["undecided"] = list(undecided)
    return out


# Una regla valida de cada tipo sobre el mapa a mano.
VALID = [
    rule("o", "order", axis="west-east", groups=[["region:1"], ["region:2"]]),
    rule("s", "side-of", a="region:1", b="region:2", side="west"),
    rule("b", "border", a="region:1", b="region:2", orientation="north-south"),
    rule("c", "coast-to-coast", zone="landmass:1", axis="west-east"),
    rule("ob", "only-borders", zone="region:1", **{"with": ["region:2"]}),
    rule("bs", "borders", a="region:1", b="region:2"),
    rule("cb", "closes-by", zone="region:1", edge="north", by="region:2", min=2, strip=10),
    rule("n", "narrows", zone="region:1", toward="east", between=["region:1"], max=3, **{"and": ["region:2"]}),
    rule("co", "corridor", to="region:2", along="landmass:1", side="north", **{"from": "province:1"}),
    rule("i", "inside", landmass="landmass:1", zones=["region:1", "region:2"]),
    rule("nl", "no-land-outside", landmasses=["landmass:1"], name="Isla"),
    rule("a", "area", zone="region:1", value=10),
    rule("e", "extent", zone="region:1", value=[3, 4]),
    rule("d", "distance", places=[1, 2], range=[5, 7]),
]
UNDECIDED = [
    rule("ue", "edge", landmass="landmass:1", side="south"),
    rule("ua", "area", zone="region:1"),
    rule("ux", "extent", zone="region:1", range=[1, 2]),
    rule("ud", "distance", places=[1, 2], value=5),
    rule("us", "shape"),
]


class BindTest(unittest.TestCase):
    def fails(self, rs, code, id=None, d=None, **extra):
        with self.assertRaises(MapError) as cm:
            bind(rs, d or doc())
        self.assertEqual(cm.exception.code, code)
        if id is not None:
            self.assertEqual(cm.exception.detail["id"], id)
        for k, v in extra.items():
            self.assertEqual(cm.exception.detail[k], v)
        return cm.exception

    def test_valid_all_types(self):
        r = rules(*VALID, undecided=UNDECIDED)
        self.assertEqual(validate(r, load_schema("gworld.maprules/0")), [])
        self.assertEqual({x["type"] for x in VALID}, set(RULE_TYPES))
        self.assertEqual({x["type"] for x in UNDECIDED}, set(UNDECIDED_TYPES))
        self.assertEqual(set(PARAMS), set(RULE_TYPES) | set(UNDECIDED_TYPES))
        bind(r, doc())

    def test_map_mismatch(self):
        r = rules(VALID[0])
        r["map"] = "sha256:" + "1" * 64
        e = self.fails(r, "map_mismatch", expected="sha256:" + "1" * 64, actual=SHA)
        self.assertIn("map_mismatch", str(e))

    def test_unknown_zone(self):
        self.fails(rules(rule("x", "borders", a="region:1", b="region:99")), "unknown_ref", "x", param="b",
                   ref="region:99")

    def test_unknown_zone_in_list_and_groups(self):
        self.fails(rules(rule("x", "inside", landmass="landmass:1", zones=["region:1", "region:9"])), "unknown_ref",
                   "x", ref="region:9")
        self.fails(rules(rule("y", "order", axis="west-east", groups=[["region:1"], ["nada:1"]])), "unknown_ref",
                   "y", ref="nada:1")

    def test_unknown_place(self):
        self.fails(rules(rule("x", "distance", places=[1, 7], value=3)), "unknown_ref", "x", ref=7)

    def test_wrong_layer(self):
        self.fails(rules(rule("x", "corridor", to="region:2", along="landmass:1", side="north",
                              **{"from": "region:1"})), "wrong_layer", "x", param="from", ref="region:1",
                   layer="region", expected=["province"])

    def test_wrong_layer_in_list(self):
        self.fails(rules(rule("x", "no-land-outside", landmasses=["region:1"], name="n")), "wrong_layer", "x",
                   ref="region:1")

    def test_missing_param(self):
        self.fails(rules(rule("x", "borders", a="region:1")), "bad_params", "x", missing=["b"])

    def test_extra_param(self):
        self.fails(rules(rule("x", "borders", a="region:1", b="region:2", side="west")), "bad_params", "x",
                   extra=["side"])

    def test_wrong_param_shape(self):
        self.fails(rules(rule("x", "closes-by", zone="region:1", edge="north", by="region:2", min="mucho")),
                   "bad_params", "x", param="min")
        self.fails(rules(rule("y", "borders", a=5, b="region:2")), "bad_params", "y", param="a")
        self.fails(rules(rule("z", "distance", places=[1], value=3)), "bad_params", "z", param="places")

    def test_value_and_range_exactly_one(self):
        self.fails(rules(rule("x", "area", zone="region:1")), "bad_params", "x", has=[])
        self.fails(rules(rule("y", "area", zone="region:1", value=1, range=[1, 2])), "bad_params", "y",
                   has=["value", "range"])
        self.fails(rules(rule("z", "extent", zone="region:1", value=3)), "bad_params", "z", param="value")
        self.fails(rules(rule("w", "area", zone="region:1", range=[3, 1])), "bad_params", "w", param="range")

    def test_undecided_value_range_optional_but_not_both(self):
        bind(rules(undecided=[rule("u", "area", zone="region:1")]), doc())
        self.fails(rules(undecided=[rule("u", "area", zone="region:1", value=1, range=[1, 2])]), "bad_params", "u")

    def test_undecided_type_in_rules_and_back(self):
        self.fails(rules(rule("x", "shape")), "bad_params", "x", type="shape")
        self.fails(rules(undecided=[rule("x", "borders", a="region:1", b="region:2")]), "bad_params", "x")

    def test_bad_direction(self):
        e = self.fails(rules(rule("x", "side-of", a="region:1", b="region:2", side="up")), "bad_direction", "x",
                       param="side", value="up")
        self.assertEqual(e.detail["allowed"], ["east", "north", "south", "west"])

    def test_direction_sets_differ_by_type(self):
        self.fails(rules(rule("x", "order", axis="north", groups=[["region:1"], ["region:2"]])), "bad_direction", "x")
        self.fails(rules(rule("y", "border", a="region:1", b="region:2", orientation="west-east")), "bad_direction",
                   "y")
        self.fails(rules(rule("z", "coast-to-coast", zone="region:1", axis="east-west")), "bad_direction", "z")
        for axis in ("north-south", "south-north", "west-east", "east-west"):
            bind(rules(rule("o", "order", axis=axis, groups=[["region:1"], ["region:2"]])), doc())


class LoadTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.p = Path(self._t.name) / "r.json"

    def write(self, obj):
        self.p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")

    def fails(self, code):
        with self.assertRaises(MapError) as cm:
            load_map_rules(self.p)
        self.assertEqual(cm.exception.code, code)
        return cm.exception

    def test_valid(self):
        self.write(rules(*VALID, undecided=UNDECIDED))
        self.assertEqual(load_map_rules(self.p)["map"], SHA)

    def test_unreadable_and_malformed(self):
        self.fails("unreadable")
        self.write("{no")
        self.fails("malformed")

    def test_schema_errors(self):
        r = rules(rule("x", "teleport"))
        self.write(r)
        self.assertIn("enum", str(self.fails("schema")))
        self.write(rules(rule("Bad Id", "area", zone="region:1", value=1)))
        self.assertIn("pattern", str(self.fails("schema")))
        self.write({**rules(), "map": "sha256:xx"})
        self.fails("schema")
        self.write(rules(undecided=[rule("u", "borders", a="region:1", b="region:2")]))
        self.fails("schema")
        self.write({"kind": "gworld.maprules/0", "map": SHA})
        self.assertIn("required", str(self.fails("schema")))

    def test_duplicate_rule(self):
        self.write(rules(VALID[1], undecided=[rule("s", "shape")]))
        e = self.fails("duplicate_rule")
        self.assertEqual(e.detail["id"], "s")
        self.write(rules(VALID[1], VALID[1]))
        self.assertEqual(self.fails("duplicate_rule").detail["id"], "s")

    def test_tolerance_default_documented(self):
        self.assertEqual(load_schema("gworld.maprules/0")["properties"]["tolerance"]["default"], 0.03)


class FactsTest(unittest.TestCase):
    def test_check_facts(self):
        r = rules(rule("a", "shape", facts=["f1", "f2"]), undecided=[rule("b", "shape", facts=["f2", "f3"])])
        self.assertEqual(check_facts(r, {"f1"}), ["f2", "f3"])
        self.assertEqual(check_facts(r, {"f1", "f2", "f3"}), [])
        self.assertEqual(check_facts(rules(VALID[0]), set()), [])


def grid(rows, zones, y_down=True, unit=1, places=()):
    """Mapa de celdas cuadradas de 10 unidades: ``rows`` son cadenas (``.`` = mar), ``zones`` da las zonas de cada letra."""
    h, w = len(rows), len(rows[0])
    ids = sorted({z for zs in zones.values() for z in zs})
    cells = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            ns = [(r + dr) * w + c + dc for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                  if 0 <= r + dr < h and 0 <= c + dc < w]
            cell = {"id": r * w + c, "center": [10 * c + 5, 10 * r + 5], "neighbours": ns,
                    "vertices": [r * (w + 1) + c, r * (w + 1) + c + 1, (r + 1) * (w + 1) + c + 1,
                                 (r + 1) * (w + 1) + c], "height": 0 if ch == "." else 30}
            if ch != ".":
                cell["zones"] = list(zones.get(ch, []))
            cells.append(cell)
    return {"kind": "gworld.map/0", "origin": {"file": {"name": "g.map", "format": "x"}, "sha256": SHA},
            "geometry": {"width": 10 * w, "height": 10 * h, "unitKm": unit, "yDown": y_down,
                         "vertices": [[10 * c, 10 * r] for r in range(h + 1) for c in range(w + 1)]},
            "seaLevel": 20, "cells": cells,
            "zones": [{"id": z, "layer": z.split(":")[0], "name": z} for z in ids], "routes": [], "rivers": [],
            "places": [{"id": i, "name": n, "cell": 0, "point": pt} for i, (n, pt) in enumerate(places, 1)]}


Z = {"a": ["landmass:1", "region:1"], "b": ["landmass:1", "region:2"], "c": ["landmass:1", "region:3"]}


class CheckRulesTest(unittest.TestCase):
    def one(self, d, r, ok, detail, tol=None):
        rs = rules(r)
        if tol is not None:
            rs["tolerance"] = tol
        (res,) = check_rules(d, rs)
        self.assertEqual(res, RuleResult(r["id"], r["type"], ok, detail))

    def test_bind_primero_y_orden(self):
        d = grid([".a.", ".b."], Z)
        other = {**rules(rule("x", "borders", a="region:1", b="region:2")), "map": "sha256:" + "1" * 64}
        with self.assertRaises(MapError) as cm:
            check_rules(d, other)
        self.assertEqual(cm.exception.code, "map_mismatch")
        out = check_rules(d, rules(rule("r", "borders", a="region:1", b="region:2"), undecided=[rule("u", "shape")]))
        self.assertEqual([(x.id, x.ok) for x in out], [("r", True), ("u", None)])
        self.assertIsInstance(out, tuple)

    def test_order_cuatro_sentidos_con_y_down(self):
        # a al noroeste de b en coordenadas del mapa (x e y menores).
        for y_down in (True, False):
            d = grid(["a.", ".b"], Z, y_down=y_down)
            groups = [["region:1"], ["region:2"]]
            self.one(d, rule("o", "order", axis="west-east", groups=groups), True, "x de los centros: 5 < 15")
            self.one(d, rule("o", "order", axis="east-west", groups=groups), False, "x de los centros: 5 > 15")
            op = "<" if y_down else ">"
            self.one(d, rule("o", "order", axis="north-south", groups=groups), y_down, f"y de los centros: 5 {op} 15")
            op = ">" if y_down else "<"
            self.one(d, rule("o", "order", axis="south-north", groups=groups), not y_down,
                     f"y de los centros: 5 {op} 15")

    def test_order_media_de_grupo_y_estricto(self):
        # Grupo 1 = region 1 y 2 (y 10 y 20: media 15); grupo 2 = region 3 (y 25).
        d = grid(["a.", "b.", "c."], Z)
        groups = [["region:1", "region:2"], ["region:3"]]
        self.one(d, rule("o", "order", axis="north-south", groups=groups), True, "y de los centros: 10 < 25")
        d2 = grid(["a.", "b."], Z)  # dos grupos con la misma y media: no es estricto
        self.one(d2, rule("o", "order", axis="north-south", groups=[["region:1"], ["region:1"]]), False,
                 "y de los centros: 5 < 5")

    def test_side_of_cuatro_lados_con_y_down(self):
        for y_down in (True, False):
            d = grid(["a.", ".b"], Z, y_down=y_down)
            for side, ok, k in (("west", True, "x"), ("east", False, "x"), ("north", y_down, "y"),
                                ("south", not y_down, "y")):
                self.one(d, rule("s", "side-of", a="region:1", b="region:2", side=side), ok,
                         f"{k} del centro: 5 y 15")

    def test_side_of_masa_de_tierra_y_sin_tierra(self):
        d = grid(["a.", ".b"], {**Z, "b": ["landmass:2", "region:2"]})
        self.one(d, rule("s", "side-of", a="landmass:1", b="landmass:2", side="west"), True, "x del centro: 5 y 15")
        d["cells"][3]["height"] = 0
        self.one(d, rule("s", "side-of", a="landmass:1", b="landmass:2", side="west"), False,
                 "landmass:2 sin celdas de tierra")

    def test_border(self):
        d = grid(["......", ".aabb.", ".aabb.", ".aabb.", ".aabb.", "......"], Z)
        self.one(d, rule("b", "border", a="region:1", b="region:2", orientation="north-south"), True,
                 "extensión N-S 30 km, E-O 10 km")
        self.one(d, rule("b", "border", a="region:1", b="region:2", orientation="east-west"), False,
                 "extensión N-S 30 km, E-O 10 km")
        h = grid(["....", ".aa.", ".bb.", "...."], Z)
        self.one(h, rule("b", "border", a="region:1", b="region:2", orientation="east-west"), False,
                 "extensión N-S 10 km, E-O 10 km")
        h = grid(["......", ".aaaa.", ".bbbb.", "......"], Z)
        self.one(h, rule("b", "border", a="region:1", b="region:2", orientation="east-west"), True,
                 "extensión N-S 10 km, E-O 30 km")
        self.one(grid([".ab.c"], Z), rule("b", "border", a="region:1", b="region:3", orientation="east-west"), False,
                 "las zonas no lindan")

    def test_coast_to_coast(self):
        d = grid(["......", ".aaaa.", "......"], Z)
        self.one(d, rule("c", "coast-to-coast", zone="region:1", axis="west-east"), True,
                 "costa de x 15 a 45 (zona 15-45, centro 30)")
        gap = grid(["YYYY.YYYY", "YZZZZZZZY", "YYYYYYYYY"], {"Y": ["region:2"], "Z": ["region:1"]})
        self.one(gap, rule("c", "coast-to-coast", zone="region:1", axis="west-east"), False,
                 "costa de x 45 a 45 (zona 15-75, centro 45)")
        solid = grid(["YYY", "YZY", "YYY"], {"Y": ["region:2"], "Z": ["region:1"]})
        self.one(solid, rule("c", "coast-to-coast", zone="region:1", axis="north-south"), False,
                 "sin celdas costeras")

    def test_only_borders(self):
        d = grid(["......", ".aabb.", ".aacc.", "......"], Z)
        self.one(d, rule("o", "only-borders", zone="region:1", **{"with": ["region:2", "region:3"]}), True,
                 "linda solo con lo permitido")
        self.one(d, rule("o", "only-borders", zone="region:1", **{"with": ["region:2"]}), False, "sobran: region:3")

    def test_only_borders_celda_sin_zona_es_region_0(self):
        d = grid([".abx."], {**Z, "x": ["landmass:1"]})  # x: tierra sin region
        self.one(d, rule("o", "only-borders", zone="region:2", **{"with": ["region:1"]}), True,
                 "linda solo con lo permitido")
        self.one(d, rule("o", "only-borders", zone="region:2", **{"with": ["region:3"]}), False, "sobran: region:1")

    def test_borders(self):
        d = grid([".aabbcc."], Z)
        self.one(d, rule("b", "borders", a="region:1", b="region:2"), True, "1 pares de celdas vecinas")
        self.one(d, rule("b", "borders", a="region:1", b="region:3"), False, "0 pares de celdas vecinas")

    def test_closes_by(self):
        rows = ["......", ".aaaa.", ".aaaa.", ".bbcc.", "......"]
        d = grid(rows, Z)
        r = dict(zone="region:1", edge="south", by="region:2")
        self.one(d, rule("c", "closes-by", min=0.4, **r), True, "50% de 4 pares (mínimo 40%)")
        self.one(d, rule("c", "closes-by", min=0.6, **r), False, "50% de 4 pares (mínimo 60%)")
        # Franjas de 20 km: las columnas de x 25 y 35 comparten franja y solo cuenta una (la primera).
        self.one(d, rule("c", "closes-by", min=0.7, strip=20, **r), False, "67% de 3 pares (mínimo 70%)")
        # Con la y hacia arriba el sur es la fila de arriba: da al mar, sin frontera.
        up = grid(rows, Z, y_down=False)
        self.one(up, rule("c", "closes-by", min=0.4, **r), False, "sin frontera sur")
        self.one(up, rule("c", "closes-by", min=0.4, **{**r, "edge": "north"}), True, "50% de 4 pares (mínimo 40%)")

    def test_closes_by_este_y_diagonal(self):
        # Borde este de a: la columna de la derecha; solo cuentan las vecinas mas al este que al lado.
        d = grid([".ab.", ".ac."], Z)
        self.one(d, rule("c", "closes-by", zone="region:1", edge="east", by="region:2", min=0.5), True,
                 "50% de 2 pares (mínimo 50%)")
        self.one(d, rule("c", "closes-by", zone="region:1", edge="east", by="region:2", min=0.6), False,
                 "50% de 2 pares (mínimo 60%)")

    def test_narrows(self):
        d = grid(["AAAAAAAA", "ZZZZZZZZ", "BBZZZZZZ", "BBZZZZZZ", "BBBBBBBB"],
                 {"A": ["region:1"], "B": ["region:2"], "Z": ["region:3"]})
        base = dict(zone="region:3", between=["region:1"], **{"and": ["region:2"]})
        (res,) = check_rules(d, rules(rule("n", "narrows", toward="west", max=0.7, **base)))
        self.assertTrue(res.ok)
        self.assertRegex(res.detail, r"^grosor por cuartos O→E: 20, \d+, \d+, \d+ km; oeste/centro = 0\.\d\d "
                                     r"\(máximo 0\.7\)$")
        (res,) = check_rules(d, rules(rule("n", "narrows", toward="east", max=0.5, **base)))
        self.assertFalse(res.ok)
        self.assertRegex(res.detail, r"^grosor por cuartos E→O: .* km; este/centro = \d\.\d\d \(máximo 0\.5\)$")

    def test_narrows_sin_lado_y_sin_cuarto(self):
        d = grid([".ab."], Z)
        self.one(d, rule("n", "narrows", zone="region:1", toward="west", between=["region:2"], max=1,
                         **{"and": ["region:3"]}), False, "un lado sin celdas")
        e = grid(["AZB"], {"A": ["region:1"], "B": ["region:2"], "Z": ["region:3"]})
        self.one(e, rule("n", "narrows", zone="region:3", toward="west", between=["region:1"], max=1,
                         **{"and": ["region:2"]}), False, "un cuarto sin celdas")

    def test_corridor(self):
        d = grid([".....", ".ABB.", "..CC."], {"A": ["landmass:1", "region:1", "province:1"],
                                               "B": ["landmass:1", "region:2"], "C": ["landmass:1", "region:3"]})
        r = dict(to="region:3", along="region:2", **{"from": "province:1"})
        self.one(d, rule("c", "corridor", side="west", **r), True, "camino de 20 km")
        self.one(d, rule("c", "corridor", side="east", **r), False, "sin camino por tierra")

    def test_corridor_lado_norte_y_sur_segun_y_down(self):
        z = {"A": ["province:1", "region:1"], "B": ["region:2"], "C": ["region:3"]}
        rows = ["......", ".ABBC.", "..BB.."]
        r = dict(to="region:3", along="region:2", **{"from": "province:1"})
        for y_down in (True, False):
            d = grid(rows, z, y_down=y_down)
            # La fila de arriba de B (la unica que toca a A y a C) es su norte con y hacia el sur y su sur con y hacia arriba.
            for side, ok in (("north", y_down), ("south", not y_down)):
                self.one(d, rule("c", "corridor", side=side, **r), ok,
                         "camino de 30 km" if ok else "sin camino por tierra")

    def test_corridor_sin_tierra(self):
        d = grid([".A.."], {"A": ["province:1", "region:1"]})
        d["cells"][1]["height"] = 0
        r = rule("c", "corridor", to="region:1", along="region:1", side="west", **{"from": "province:1"})
        self.one(d, r, False, "la provincia no tiene tierra")

    def test_inside(self):
        d = grid([".ab.", ".x.."], {**Z, "x": ["region:3"]})
        self.one(d, rule("i", "inside", landmass="landmass:1", zones=["region:1", "region:2"]), True,
                 "0 celdas de tierra fuera de landmass:1")
        self.one(d, rule("i", "inside", landmass="landmass:1", zones=["region:1", "region:3"]), False,
                 "1 celdas de tierra fuera de landmass:1")

    def test_no_land_outside(self):
        d = grid([".ab."], Z, places=[("Puerto Sur", [5, 5])])
        r = rule("n", "no-land-outside", landmasses=["landmass:1"], name="Isla")
        self.one(d, r, True, "0 celdas de tierra fuera, 0 lugares «Isla»")
        out = grid([".ax."], {**Z, "x": []}, places=[("Isla Verde", [5, 5])])
        self.one(out, r, False, "1 celdas de tierra fuera, 1 lugares «Isla»")
        self.one(d, rule("n", "no-land-outside", landmasses=["landmass:1"], name="Puerto"), False,
                 "0 celdas de tierra fuera, 1 lugares «Puerto»")

    def measure_map(self):
        # Region 1: 2x2 celdas de 10 unidades con unitKm 2: 40 x 40 km, 1600 km2. Lugares a 50 unidades: 100 km.
        return grid(["....", ".aa.", ".aa.", "...."], Z, unit=2, places=[("P", [0, 0]), ("Q", [30, 40])])

    def test_area(self):
        d = self.measure_map()
        self.one(d, rule("a", "area", zone="region:1", value=1560), True, "medido 1.600 km² (canon 1.560, ±3%)")
        self.one(d, rule("a", "area", zone="region:1", value=1000), False, "medido 1.600 km² (canon 1.000, ±3%)")
        self.one(d, rule("a", "area", zone="region:1", range=[1400, 1560]), True,
                 "medido 1.600 km² (canon 1.400–1.560, ±3%)")
        self.one(d, rule("a", "area", zone="region:1", range=[1400, 1500]), False,
                 "medido 1.600 km² (canon 1.400–1.500, ±3%)")

    def test_tolerancia(self):
        d = self.measure_map()
        r = rule("a", "area", zone="region:1", value=1500)
        self.one(d, r, False, "medido 1.600 km² (canon 1.500, ±3%)")
        self.one(d, r, True, "medido 1.600 km² (canon 1.500, ±10%)", tol=0.1)

    def test_area_solo_tierra(self):
        d = self.measure_map()
        d["cells"][5]["height"] = 10  # una celda de la zona pasa a agua: quedan 1200 km2
        self.one(d, rule("a", "area", zone="region:1", value=1200), True, "medido 1.200 km² (canon 1.200, ±3%)")

    def test_extent(self):
        d = self.measure_map()
        self.one(d, rule("e", "extent", zone="region:1", value=[40, 40]), True,
                 "medido 40 × 40 km (canon 40 × 40, ±3%)")
        self.one(d, rule("e", "extent", zone="region:1", value=[40, 20]), False,
                 "medido 40 × 40 km (canon 40 × 20, ±3%)")

    def test_distance(self):
        d = self.measure_map()
        self.one(d, rule("d", "distance", places=[1, 2], range=[90, 110]), True, "medido 100 km (canon 90–110, ±3%)")
        self.one(d, rule("d", "distance", places=[1, 2], value=50), False, "medido 100 km (canon 50, ±3%)")

    def test_undecided(self):
        d = self.measure_map()
        out = check_rules(d, rules(undecided=[
            rule("ue", "edge", landmass="landmass:1", side="north"),
            rule("ua", "area", zone="region:1"),
            rule("ux", "extent", zone="region:1", value=[1, 2]),
            rule("ud", "distance", places=[1, 2], range=[1, 2]),
            rule("us", "shape")]))
        self.assertEqual(out, (
            RuleResult("ue", "edge", None, "y mínima de la tierra de landmass:1: 30 km (norte)"),
            RuleResult("ua", "area", None, "medido 1.600 km²; sin decidir"),
            RuleResult("ux", "extent", None, "medido 40 × 40 km, canon 1 × 2; sin decidir"),
            RuleResult("ud", "distance", None, "medido 100 km, canon 1–2; sin decidir"),
            RuleResult("us", "shape", None, "sin medida")))

    def test_undecided_edge_cuatro_lados(self):
        # Tierra de x 30..50 e y 30..50 km (centros de celdas de 20 km, unitKm 2).
        cases = ((True, "south", "y máxima", 50, "sur"), (False, "south", "y mínima", 30, "sur"),
                 (True, "north", "y mínima", 30, "norte"), (False, "north", "y máxima", 50, "norte"),
                 (True, "east", "x máxima", 50, "este"), (True, "west", "x mínima", 30, "oeste"))
        for y_down, side, word, v, es in cases:
            d = grid(["....", ".aa.", ".aa.", "...."], Z, y_down=y_down, unit=2)
            (res,) = check_rules(d, rules(undecided=[rule("ue", "edge", landmass="landmass:1", side=side)]))
            self.assertEqual(res.detail, f"{word} de la tierra de landmass:1: {v} km ({es})")


if __name__ == "__main__":
    unittest.main()
