"""Topologia de un mapa ``gworld.map/0`` (MAP-3): ``check_map`` y consultas de ``Topology``.

``check_map(doc)`` recibe un documento que ya valida contra el esquema y comprueba lo que el esquema no puede:
referencias que existen, vecinas simetricas y grafo conexo sin celdas huerfanas (invariante 3). Falla con
``MapError``; ``detail`` es siempre un dict con la clave ``id`` (la celda, zona, ruta o rio afectado) y, si hace
falta, otras claves. El primer fallo se decide por un orden fijo y por id ascendente, nunca por orden de dict o set.

Distancias (como WMF, ``medir.distancia`` y ``consultar.camino``): recta entre centros por ``unitKm``; el camino
es Dijkstra sobre vecinas con coste la distancia entre centros. Diferencia con WMF: aqui ``passable=None`` deja
pasar por todas las celdas; WMF por defecto solo pasa por tierra (altura >= nivel del mar).
"""

import heapq
import math
from collections import deque
from typing import Callable

from gworld.maps import MapError


def _fail(code: str, message: str, id, **extra) -> MapError:
    return MapError(code, message, {"id": id, **extra})


def check_map(doc: dict) -> None:
    cells = doc["cells"]
    vcount = len(doc["geometry"]["vertices"])
    by_id: dict[int, dict] = {}
    prev = None
    for c in cells:
        i = c["id"]
        if i in by_id:
            raise _fail("duplicate_cell", f"id de celda repetido: {i}", i)
        if prev is not None and i < prev:
            raise _fail("cells_unordered", f"la celda {i} va despues de la {prev}", i)
        by_id[i] = c
        prev = i

    zones: dict[str, dict] = {}
    for z in doc["zones"]:
        if z["id"] in zones:
            raise _fail("duplicate_zone", f"id de zona repetido: {z['id']}", z["id"])
        zones[z["id"]] = z
        if z["layer"] != z["id"].split(":", 1)[0]:
            raise _fail("layer_mismatch", f"la zona {z['id']} dice capa {z['layer']}", z["id"], layer=z["layer"])
    for zid in sorted(zones):
        z = zones[zid]
        if "parent" in z and z["parent"] not in zones:
            raise _fail("unknown_parent", f"la zona {zid} tiene padre inexistente {z['parent']}", zid,
                        parent=z["parent"])
        if "centerCell" in z and z["centerCell"] not in by_id:
            raise _fail("unknown_center_cell", f"la zona {zid} tiene centerCell inexistente {z['centerCell']}", zid,
                        cell=z["centerCell"])

    for i, c in by_id.items():
        for v in c["vertices"]:
            if v >= vcount:
                raise _fail("vertex_out_of_range", f"la celda {i} cita el vertice {v} de {vcount}", i, vertex=v)
        for n in c["neighbours"]:
            if n == i:
                raise _fail("self_neighbour", f"la celda {i} es vecina de si misma", i)
            if n not in by_id:
                raise _fail("unknown_neighbour", f"la celda {i} cita la vecina inexistente {n}", i, neighbour=n)
        layers: dict[str, str] = {}
        for zid in c.get("zones", []):
            if zid not in zones:
                raise _fail("unknown_zone", f"la celda {i} cita la zona inexistente {zid}", i, zone=zid)
            layer = zones[zid]["layer"]
            if layer in layers:
                raise _fail("duplicate_layer", f"la celda {i} tiene dos zonas de la capa {layer}", i, layer=layer,
                            zones=sorted({layers[layer], zid}))
            layers[layer] = zid
    for i, c in by_id.items():
        for n in sorted(c["neighbours"]):
            if i not in by_id[n]["neighbours"]:
                raise _fail("asymmetric_neighbour", f"la celda {i} cita a {n} pero {n} no cita a {i}", i, neighbour=n)

    for r in sorted(doc["routes"], key=lambda r: r["id"]):
        for n in r.get("cells", []):
            if n not in by_id:
                raise _fail("unknown_route_cell", f"la ruta {r['id']} cita la celda inexistente {n}", r["id"], cell=n)
    for r in sorted(doc["rivers"], key=lambda r: r["id"]):
        for n in r["cells"]:
            if n not in by_id:
                raise _fail("unknown_river_cell", f"el rio {r['id']} cita la celda inexistente {n}", r["id"], cell=n)

    for i, c in by_id.items():
        if not c["neighbours"]:
            raise _fail("orphan_cell", f"la celda {i} no tiene vecinas", i)
    start = cells[0]["id"]
    seen = {start}
    queue = deque([start])
    while queue:
        for n in by_id[queue.popleft()]["neighbours"]:
            if n not in seen:
                seen.add(n)
                queue.append(n)
    if len(seen) != len(by_id):
        lowest = min(i for i in by_id if i not in seen)
        raise _fail("disconnected", f"el grafo no es conexo: la celda {lowest} no se alcanza desde la {start}",
                    lowest, start=start)


class Topology:
    """Consultas sobre un mapa ya comprobado (``check_map`` en el constructor)."""

    def __init__(self, doc: dict):
        check_map(doc)
        self.doc = doc
        self._km = doc["geometry"]["unitKm"]
        self._cells = {c["id"]: c for c in doc["cells"]}
        self._zones = {z["id"]: z for z in doc["zones"]}
        self._members: dict[str, list[int]] = {zid: [] for zid in self._zones}
        for c in doc["cells"]:
            for zid in c.get("zones", []):
                self._members[zid].append(c["id"])

    def _cell(self, cell: int) -> dict:
        if cell not in self._cells:
            raise _fail("unknown_cell", f"no existe la celda {cell}", cell)
        return self._cells[cell]

    def neighbours(self, cell: int) -> list[int]:
        return sorted(self._cell(cell)["neighbours"])

    def zones_of(self, cell: int) -> list[str]:
        return sorted(self._cell(cell).get("zones", []))

    def zone_of(self, cell: int, layer: str) -> str | None:
        return next((z for z in self.zones_of(cell) if self._zones[z]["layer"] == layer), None)

    def cells_in(self, zone: str) -> list[int]:
        if zone not in self._zones:
            raise _fail("unknown_zone", f"no existe la zona {zone}", zone)
        return list(self._members[zone])

    def zones(self, layer: str | None = None) -> list[str]:
        return sorted(z for z, v in self._zones.items() if layer is None or v["layer"] == layer)

    def routes(self, group: str | None = None) -> list[dict]:
        return sorted((r for r in self.doc["routes"] if group is None or r["group"] == group), key=lambda r: r["id"])

    def rivers(self) -> list[dict]:
        return sorted(self.doc["rivers"], key=lambda r: r["id"])

    def distance_km(self, a: int, b: int) -> float:
        return math.dist(self._cell(a)["center"], self._cell(b)["center"]) * self._km

    def hops(self, a: int, b: int) -> int:
        self._cell(a), self._cell(b)
        dist = {a: 0}
        queue = deque([a])
        while queue:
            c = queue.popleft()
            if c == b:
                return dist[c]
            for n in self._cells[c]["neighbours"]:
                if n not in dist:
                    dist[n] = dist[c] + 1
                    queue.append(n)
        raise AssertionError("grafo conexo: siempre hay camino")  # pragma: no cover

    def path(self, a: int, b: int, passable: Callable[[dict], bool] | None = None) -> tuple[list[int], float] | None:
        """Camino mas corto de ``a`` a ``b`` por vecinas: ``(celdas, km)``, o ``None`` si no hay.

        ``passable(celda)`` filtra las celdas por las que se puede pasar, extremos incluidos (``None``: todas).
        Empates de longitud: gana el camino cuya celda previa tiene el id menor (cola ordenada por ``(km, id)``).
        """
        self._cell(a), self._cell(b)
        ok = (lambda i: True) if passable is None else (lambda i: bool(passable(self._cells[i])))
        if not ok(a) or not ok(b):
            return None
        best, prev, heap, done = {a: 0.0}, {}, [(0.0, a)], set()
        while heap:
            d, c = heapq.heappop(heap)
            if c in done:
                continue
            done.add(c)
            if c == b:
                break
            for n in sorted(self._cells[c]["neighbours"]):
                if n in done or not ok(n):
                    continue
                nd = d + self.distance_km(c, n)
                if nd < best.get(n, math.inf) or (nd == best[n] and n in prev and c < prev[n]):
                    best[n], prev[n] = nd, c
                    heapq.heappush(heap, (nd, n))
        if b not in best:
            return None
        route = [b]
        while route[-1] != a:
            route.append(prev[route[-1]])
        return route[::-1], best[b]
