import unittest

from gworld.maps import FmgImporter, MapError
from gworld.schema import validate
from gworld.schemas import load_schema
from gworld.topology import Topology, check_map
from tests.test_maps import FIXTURE

# Mapa a mano, unitKm 2. Centros: 0 (0,0), 1 (3,4), 2 (6,0), 3 (9,4), 4 (12,0).
# Distancias en unidades: 0-1 5, 0-2 6, 1-2 5, 1-3 6, 2-3 5, 3-4 5 (km: el doble).
_NEIGH = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1, 3], 3: [1, 2, 4], 4: [3]}
_CENTER = {0: [0, 0], 1: [3, 4], 2: [6, 0], 3: [9, 4], 4: [12, 0]}
_ZONES = {0: ["landmass:1", "region:1", "province:1"], 1: ["landmass:1", "region:1", "province:1"],
          2: ["landmass:1", "region:1"], 3: ["landmass:1", "region:2"], 4: ["landmass:1", "region:2"]}


def small():
    return {
        "kind": "gworld.map/0",
        "origin": {"file": {"name": "a.map", "format": "x", "formatVersion": "1"}, "sha256": "sha256:" + "0" * 64},
        "geometry": {"width": 20, "height": 10, "unitKm": 2, "yDown": True,
                     "vertices": [[0, 0], [1, 0], [0, 1], [1, 1]]},
        "cells": [{"id": i, "center": list(_CENTER[i]), "vertices": [0, 1, 2], "neighbours": list(_NEIGH[i]),
                   "height": 30 if i != 4 else 10, "zones": list(_ZONES[i])} for i in range(5)],
        "zones": [{"id": "landmass:1", "layer": "landmass", "name": "L"},
                  {"id": "region:1", "layer": "region", "name": "R1", "centerCell": 0},
                  {"id": "region:2", "layer": "region", "name": "R2"},
                  {"id": "province:1", "layer": "province", "name": "P", "parent": "region:1"}],
        "routes": [{"id": 0, "group": "roads", "points": [[0, 0], [9, 4]], "cells": [0, 1, 3]},
                   {"id": 1, "group": "searoutes", "points": [[9, 4], [12, 0]]}],
        "rivers": [{"id": 0, "cells": [4, 3]}],
    }


def mutated(fn):
    d = small()
    fn(d)
    return d


class CheckMapTest(unittest.TestCase):
    def fails(self, doc, code, id, **extra):
        with self.assertRaises(MapError) as cm:
            check_map(doc)
        self.assertEqual(cm.exception.code, code)
        self.assertEqual(cm.exception.detail["id"], id)
        for k, v in extra.items():
            self.assertEqual(cm.exception.detail[k], v)

    def test_mapa_a_mano_valido(self):
        self.assertEqual(validate(small(), load_schema("gworld.map/0")), [])
        check_map(small())

    def test_importar_dos_veces_pasa_y_es_igual(self):
        a, b = FmgImporter().import_map(FIXTURE), FmgImporter().import_map(FIXTURE)
        self.assertEqual(a, b)
        self.assertEqual(a["origin"]["sha256"], b["origin"]["sha256"])
        check_map(a)

    def test_celda_aislada(self):
        def f(d):
            d["cells"].append({"id": 5, "center": [20, 0], "vertices": [0, 1, 2], "neighbours": []})
        self.fails(mutated(f), "orphan_cell", 5)

    def test_celda_aislada_con_vecinas_de_las_demas_no_es_huerfana_sino_desconexa(self):
        def f(d):
            d["cells"].append({"id": 5, "center": [20, 0], "vertices": [0, 1, 2], "neighbours": [6]})
            d["cells"].append({"id": 6, "center": [21, 0], "vertices": [0, 1, 2], "neighbours": [5]})
        self.fails(mutated(f), "disconnected", 5, start=0)

    def test_desconexo_da_el_id_mas_bajo_de_la_otra_componente(self):
        def f(d):
            d["cells"] += [{"id": 6, "center": [0, 9], "vertices": [0, 1, 2], "neighbours": [7, 8]},
                           {"id": 7, "center": [1, 9], "vertices": [0, 1, 2], "neighbours": [6]},
                           {"id": 8, "center": [2, 9], "vertices": [0, 1, 2], "neighbours": [6]}]
        self.fails(mutated(f), "disconnected", 6)

    def test_id_repetido(self):
        self.fails(mutated(lambda d: d["cells"][3].update(id=2)), "duplicate_cell", 2)

    def test_fuera_de_orden(self):
        def f(d):
            d["cells"][1], d["cells"][2] = d["cells"][2], d["cells"][1]
        self.fails(mutated(f), "cells_unordered", 1)

    def test_vecina_inexistente(self):
        self.fails(mutated(lambda d: d["cells"][4]["neighbours"].append(99)), "unknown_neighbour", 4, neighbour=99)

    def test_vecina_de_si_misma(self):
        self.fails(mutated(lambda d: d["cells"][2]["neighbours"].append(2)), "self_neighbour", 2)

    def test_vecindad_asimetrica(self):
        self.fails(mutated(lambda d: d["cells"][4]["neighbours"].append(0)), "asymmetric_neighbour", 4, neighbour=0)

    def test_vertice_fuera_de_rango(self):
        self.fails(mutated(lambda d: d["cells"][3].update(vertices=[0, 1, 4])), "vertex_out_of_range", 3, vertex=4)

    def test_zona_inexistente_en_celda(self):
        self.fails(mutated(lambda d: d["cells"][1]["zones"].append("region:9")), "unknown_zone", 1, zone="region:9")

    def test_parent_inexistente(self):
        self.fails(mutated(lambda d: d["zones"][3].update(parent="region:9")), "unknown_parent", "province:1")

    def test_center_cell_inexistente(self):
        self.fails(mutated(lambda d: d["zones"][1].update(centerCell=77)), "unknown_center_cell", "region:1", cell=77)

    def test_capa_distinta_del_prefijo(self):
        self.fails(mutated(lambda d: d["zones"][2].update(layer="province")), "layer_mismatch", "region:2")

    def test_dos_zonas_de_una_capa(self):
        self.fails(mutated(lambda d: d["cells"][3]["zones"].append("region:1")), "duplicate_layer", 3,
                   layer="region", zones=["region:1", "region:2"])

    def test_zona_repetida(self):
        self.fails(mutated(lambda d: d["zones"].append(dict(d["zones"][2]))), "duplicate_zone", "region:2")

    def test_celda_inexistente_en_ruta(self):
        self.fails(mutated(lambda d: d["routes"][0]["cells"].append(50)), "unknown_route_cell", 0, cell=50)

    def test_celda_inexistente_en_rio(self):
        self.fails(mutated(lambda d: d["rivers"][0]["cells"].append(50)), "unknown_river_cell", 0, cell=50)

    def test_un_fallo_no_depende_del_orden_de_las_zonas(self):
        def f(d):
            d["zones"][3].update(parent="region:9")
            d["zones"][1].update(centerCell=77)
        a, b = mutated(f), mutated(f)
        b["zones"].reverse()
        for d in (a, b):
            self.fails(d, "unknown_parent", "province:1")  # province < region


class TopologyTest(unittest.TestCase):
    def setUp(self):
        self.t = Topology(small())

    def test_comprueba_al_construir(self):
        with self.assertRaises(MapError) as cm:
            Topology(mutated(lambda d: d["cells"][4]["neighbours"].append(0)))
        self.assertEqual(cm.exception.code, "asymmetric_neighbour")

    def test_vecinas(self):
        self.assertEqual(self.t.neighbours(3), [1, 2, 4])
        self.assertEqual(self.t.neighbours(4), [3])

    def test_celda_desconocida(self):
        with self.assertRaises(MapError) as cm:
            self.t.neighbours(9)
        self.assertEqual((cm.exception.code, cm.exception.detail["id"]), ("unknown_cell", 9))

    def test_zonas(self):
        self.assertEqual(self.t.zones_of(0), ["landmass:1", "province:1", "region:1"])
        self.assertEqual(self.t.zone_of(3, "region"), "region:2")
        self.assertIsNone(self.t.zone_of(3, "province"))
        self.assertEqual(self.t.cells_in("region:1"), [0, 1, 2])
        self.assertEqual(self.t.cells_in("province:1"), [0, 1])
        self.assertEqual(self.t.zones(), ["landmass:1", "province:1", "region:1", "region:2"])
        self.assertEqual(self.t.zones("region"), ["region:1", "region:2"])
        with self.assertRaises(MapError) as cm:
            self.t.cells_in("region:9")
        self.assertEqual((cm.exception.code, cm.exception.detail["id"]), ("unknown_zone", "region:9"))

    def test_rutas_y_rios(self):
        self.assertEqual([r["id"] for r in self.t.routes()], [0, 1])
        self.assertEqual([r["id"] for r in self.t.routes("searoutes")], [1])
        self.assertEqual(self.t.routes("nada"), [])
        self.assertEqual(self.t.rivers()[0]["cells"], [4, 3])

    def test_distancia_recta_en_km(self):
        self.assertEqual(self.t.distance_km(0, 1), 10.0)  # 5 unidades * 2 km
        self.assertEqual(self.t.distance_km(0, 4), 24.0)
        self.assertEqual(self.t.distance_km(2, 2), 0.0)

    def test_saltos(self):
        self.assertEqual(self.t.hops(0, 4), 3)
        self.assertEqual(self.t.hops(0, 3), 2)
        self.assertEqual(self.t.hops(4, 4), 0)

    def test_camino_mas_corto(self):
        self.assertEqual(self.t.path(0, 4), ([0, 1, 3, 4], 32.0))  # 10 + 12 + 10
        self.assertEqual(self.t.path(4, 0), ([4, 3, 1, 0], 32.0))
        self.assertEqual(self.t.path(2, 2), ([2], 0.0))

    def test_empate_se_decide_por_id(self):
        # 0-1-3 y 0-2-3 miden 22 km los dos: gana el de la celda previa con id menor (1).
        self.assertEqual(self.t.path(0, 3), ([0, 1, 3], 22.0))

    def test_camino_con_celdas_transitables(self):
        self.assertEqual(self.t.path(0, 3, lambda c: c["id"] != 1), ([0, 2, 3], 22.0))
        self.assertEqual(self.t.path(0, 3, lambda c: c["height"] >= 20), ([0, 1, 3], 22.0))

    def test_sin_camino(self):
        self.assertIsNone(self.t.path(0, 4, lambda c: c["height"] >= 20))  # el destino es agua
        self.assertIsNone(self.t.path(0, 4, lambda c: c["id"] not in (3,)))  # 4 solo se llega por 3
        self.assertIsNone(self.t.path(0, 3, lambda c: c["id"] not in (1, 2)))


if __name__ == "__main__":
    unittest.main()
