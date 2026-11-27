"""MAP-5 paso 4: paridad de ``gworld.topology.Topology`` con las consultas de lectura de WMF sobre Helek.

Corre sin el clon de WMF. Cada caso cita la linea de ``map-generator/tests/test_consultar.py`` de la que sale. Las
celdas son las que usa el test de WMF: Nabieus (lugar 614) esta en la celda 3227 en el ``.map`` y es la que da el
localizador de WMF para (581.38, 317.03), aunque ``helek.json`` lo ponga en la 3237 (ver ``fixtures/helek/README.md``).
Las cifras salen de ejecutar ``consultar.camino`` y el Dijkstra de ``consultar.py:344-357`` de WMF; los centros de
``helek.gworld.json`` van redondeados, de ahi la tolerancia pequena en km. WMF pasa por tierra con ``h >= 20``
(``editar.TIERRA``); aqui ``passable`` lo dice con ``height``.
"""
import json
import unittest
from pathlib import Path

from gworld.topology import Topology

FIX = Path(__file__).parent / "fixtures" / "helek" / "helek.gworld.json"
TIERRA = 20


def tierra(cell):
    return cell["height"] >= TIERRA


class HelekTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = Topology(json.loads(FIX.read_text(encoding="utf-8")))

    def test_region_y_pertenencia(self):
        # WMF test_consultar.py:92 test_region_y_nombres: la region 18 tiene 435 celdas y 4 provincias.
        t = self.t
        self.assertEqual(len(t.cells_in("region:18")), 435)  # WMF test_consultar.py:94
        provs = [z for z in t.doc["zones"] if z.get("parent") == "region:18"]
        self.assertEqual(sorted(z["id"] for z in provs), ["province:1", "province:2", "province:3", "province:4"])  # :96
        # La Cienaga (WMF :100 'CIENAGA') es la region 19, con 454 celdas; la Meseta (:102) es la 21.
        self.assertEqual(len(t.cells_in("region:19")), 454)
        self.assertEqual(t.zone_of(4140, "region"), "region:21")  # Ordinum, en la Meseta del Orden
        self.assertEqual(t.zone_of(3227, "region"), "region:20")  # Nabieus, en el Margen Silencioso
        self.assertEqual(t.zone_of(727, "region"), None)  # mar: sin region
        for c in t.cells_in("region:18"):
            self.assertEqual(t.zone_of(c, "region"), "region:18")

    def test_camino_recto_ordinum_nabieus(self):
        # WMF test_consultar.py:199: Ordinum (570.94, 397.8) = celda 4140 a Nabieus (581.38, 317.03) = celda 3227.
        t = self.t
        self.assertEqual(t.neighbours(4140), [4063, 4064, 4139, 4141, 4214])
        self.assertEqual(t.neighbours(3227), [3147, 3148, 3226, 3228, 3300, 3301, 3378])
        # WMF :205 da 81.5 km entre los puntos; entre los centros de celda (ligeramente distintos) son 82.84.
        self.assertAlmostEqual(t.distance_km(4140, 3227), 82.84, delta=0.05)
        self.assertEqual(t.hops(4140, 3227), 10)
        ruta, km = t.path(4140, 3227, tierra)
        # WMF Dijkstra (consultar.py:344-357): mismo camino, 86.53 km con sus centros sin redondear.
        self.assertEqual(ruta, [4140, 4064, 3990, 3910, 3835, 3685, 3605, 3526, 3450, 3378, 3227])
        self.assertAlmostEqual(km, 86.55, delta=0.05)
        self.assertEqual(t.path(3227, 4140, tierra)[0], ruta[::-1])

    def test_camino_con_rodeo_si_la_recta_cruza_mar(self):
        # WMF test_consultar.py:216: de (107.9, 267.6) = celda 2610 a (88.4, 390.0) = celda 3937, rodeo de 129.4 km.
        t = self.t
        ruta, km = t.path(2610, 3937, tierra)
        # WMF Dijkstra (consultar.py:344-357): mismas 24 celdas, 131.90 km (aqui 131.97 por el redondeo de centros).
        self.assertEqual(ruta, [2610, 2690, 2772, 2850, 2929, 3012, 3095, 3179, 3253, 3254, 3328, 3329, 3401, 3476,
                                3551, 3631, 3709, 3784, 3785, 3860, 3861, 3934, 3935, 3937])
        self.assertAlmostEqual(km, 131.9, delta=0.1)
        self.assertEqual(t.hops(2610, 3937), 10)  # sin filtro, por vecinas, mucho mas corto: cruza mar
        self.assertAlmostEqual(t.distance_km(2610, 3937), 123.94, delta=0.01)
        self.assertGreater(km, t.distance_km(2610, 3937))  # WMF :222: el rodeo es mas largo que la recta
        self.assertTrue(all(tierra(t._cells[c]) for c in ruta))
        sin_filtro, km_mar = t.path(2610, 3937)
        self.assertLess(km_mar, km)  # sin filtro gana el trayecto por mar
        self.assertFalse(all(tierra(t._cells[c]) for c in sin_filtro))  # WMF :219: la recta pisa mar

    def test_camino_sin_camino_explica_el_motivo(self):
        # WMF test_consultar.py:240: (199.3, 473.5) = celda 4871 y (524.2, 429.2) = celda 4418 no se unen por tierra.
        t = self.t
        self.assertIsNone(t.path(4871, 4418, tierra))
        self.assertEqual(t.hops(4871, 4418), 20)  # por vecinas si estan unidas (solo cruzando mar)
        self.assertIsNotNone(t.path(4871, 4418))
        # WMF :246: el inicio (100, 100) cae en mar (celda 727, h 0): sin camino por tierra desde ahi.
        self.assertEqual(t._cells[727]["height"], 0)
        self.assertIsNone(t.path(727, 4140, tierra))
        self.assertIsNone(t.path(4140, 727, tierra))


if __name__ == "__main__":
    unittest.main()
