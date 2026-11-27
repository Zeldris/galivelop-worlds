import json
import tempfile
import unittest
from pathlib import Path

from gworld.maprules import PARAMS, RULE_TYPES, UNDECIDED_TYPES, bind, check_facts, load_map_rules
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
    rule("n", "narrows", zone="region:1", toward="east", between="region:1", max=3, **{"and": "region:2"}),
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


if __name__ == "__main__":
    unittest.main()
