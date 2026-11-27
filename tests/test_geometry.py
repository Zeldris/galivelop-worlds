import unittest

from gworld.geometry import area_km2, extent_km, polygons, rings
from gworld.schema import validate
from gworld.schemas import load_schema
from gworld.topology import check_map


def grid(n, unit_km=1, side=10):
    """Mapa n x n de celdas cuadradas de lado ``side``; ids por filas; todas con el mismo giro."""
    verts = [[x * side, y * side] for y in range(n + 1) for x in range(n + 1)]
    cells = []
    for r in range(n):
        for c in range(n):
            a = r * (n + 1) + c
            neigh = [i for i, ok in ((r * n + c - 1, c > 0), (r * n + c + 1, c < n - 1),
                                     ((r - 1) * n + c, r > 0), ((r + 1) * n + c, r < n - 1)) if ok]
            cells.append({"id": r * n + c, "center": [c * side + side / 2, r * side + side / 2],
                          "vertices": [a, a + 1, a + n + 2, a + n + 1], "neighbours": neigh})
    doc = {"kind": "gworld.map/0",
           "origin": {"file": {"name": "a.map", "format": "x"}, "sha256": "sha256:" + "0" * 64},
           "geometry": {"width": n * side, "height": n * side, "unitKm": unit_km, "yDown": True, "vertices": verts},
           "cells": cells, "zones": [], "routes": [], "rivers": []}
    validate(doc, load_schema("gworld.map/0"))
    check_map(doc)
    return doc


class GeometryTest(unittest.TestCase):
    def test_block_2x2(self):
        doc = grid(3)
        block = [0, 1, 3, 4]
        polys = polygons(doc, block)
        self.assertEqual(len(polys), 1)
        self.assertEqual(polys[0][1], [])
        self.assertEqual(len(rings(doc, block)), 1)
        self.assertEqual(area_km2(doc, block), 400)
        self.assertEqual(extent_km(doc, block), (20, 20))

    def test_diagonal_cells_share_only_a_vertex(self):
        doc = grid(2)
        self.assertEqual(area_km2(doc, [0, 3]), 200)
        self.assertEqual(extent_km(doc, [0, 3]), (20, 20))
        self.assertEqual(len(rings(doc, [0, 3])), 1)  # un solo anillo en ocho, como en WMF

    def test_ring_with_hole(self):
        doc = grid(3)
        ring = [0, 1, 2, 3, 5, 6, 7, 8]
        polys = polygons(doc, ring)
        self.assertEqual(len(polys), 1)
        self.assertEqual(len(polys[0][1]), 1)
        self.assertEqual(len(rings(doc, ring)), 2)
        self.assertEqual(area_km2(doc, ring), 800)
        self.assertEqual(extent_km(doc, ring), (30, 30))

    def test_unit_km_scales(self):
        doc = grid(3, unit_km=2)
        block = [0, 1, 3, 4]
        self.assertEqual(area_km2(doc, block), 1600)
        self.assertEqual(extent_km(doc, block), (40, 40))
        self.assertEqual(area_km2(doc, [0, 1, 2, 3, 5, 6, 7, 8]), 3200)

    def test_empty(self):
        doc = grid(2)
        self.assertEqual(polygons(doc, []), [])
        self.assertEqual(rings(doc, []), [])
        self.assertEqual(area_km2(doc, []), 0)
        self.assertEqual(extent_km(doc, []), (0, 0))

    def test_deterministic_and_order_independent(self):
        doc = grid(3)
        a = polygons(doc, [0, 1, 3, 8])
        self.assertEqual(a, polygons(doc, iter([8, 3, 1, 0, 0])))
        self.assertEqual(len(a), 2)

    def test_shared_edge_is_not_contour(self):
        doc = grid(2)
        self.assertEqual(area_km2(doc, [0, 1]), 200)
        self.assertEqual(len(rings(doc, [0, 1])[0]), 6)
