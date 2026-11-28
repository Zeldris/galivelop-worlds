import copy
import unittest

from gworld.schema import check_schema, validate
from gworld.schemas import load_schema

H = "sha256:" + "b" * 64
V = [[0, 0], [1, 0], [1, 1], [0, 1], [2, 0], [2, 1]]
MAP = {
    "kind": "gworld.map/0",
    "origin": {"file": {"name": "maps/ejemplo.map", "format": "fmg", "formatVersion": "1.137.6"}, "sha256": H},
    "geometry": {"width": 2, "height": 1, "unitKm": 1, "vertices": V},
    "cells": [
        {"id": 0, "center": [0.5, 0.5], "vertices": [0, 1, 2, 3], "neighbours": [1], "height": 30,
         "zones": ["region:1"]},
        {"id": 1, "center": [1.5, 0.5], "vertices": [1, 4, 5, 2], "neighbours": [0], "height": 25},
    ],
    "zones": [{"id": "region:1", "layer": "region", "name": "Una", "color": "#112233"}],
    "routes": [{"id": 0, "group": "roads", "points": [[0.5, 0.5], [1.5, 0.5]], "cells": [0, 1]}],
    "rivers": [],
}


def codes(doc):
    return [(e.path, e.code) for e in validate(doc, load_schema("gworld.map/0"))]


def mut(fn):
    d = copy.deepcopy(MAP)
    fn(d)
    return d


class MapSchemaTest(unittest.TestCase):
    def test_check_schema(self):
        check_schema(load_schema("gworld.map/0"))

    def test_valid(self):
        self.assertEqual(codes(MAP), [])

    def test_sin_origen(self):
        self.assertEqual(codes(mut(lambda d: d.pop("origin"))), [("", "required")])

    def test_sin_huella(self):
        self.assertEqual(codes(mut(lambda d: d["origin"].pop("sha256"))), [("/origin", "required")])

    def test_sin_archivo(self):
        self.assertEqual(codes(mut(lambda d: d["origin"].pop("file"))), [("/origin", "required")])

    def test_huella_mal(self):
        d = mut(lambda d: d["origin"].update(sha256="abc"))
        self.assertEqual(codes(d), [("/origin/sha256", "pattern")])

    def test_vecina_no_entera(self):
        d = mut(lambda d: d["cells"][0].update(neighbours=["1"]))
        self.assertEqual(codes(d), [("/cells/0/neighbours/0", "type")])

    def test_vecina_negativa(self):
        d = mut(lambda d: d["cells"][1].update(neighbours=[-1]))
        self.assertEqual(codes(d), [("/cells/1/neighbours/0", "minimum")])

    def test_zona_id_mal(self):
        d = mut(lambda d: d["cells"][0].update(zones=["Region 1"]))
        self.assertEqual(codes(d), [("/cells/0/zones/0", "pattern")])

    def test_punto_mal(self):
        d = mut(lambda d: d["geometry"]["vertices"].append([1]))
        self.assertEqual(codes(d), [("/geometry/vertices/6", "minItems")])


if __name__ == "__main__":
    unittest.main()
