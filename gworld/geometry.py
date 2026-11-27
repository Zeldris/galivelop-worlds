"""Geometria de zonas de un mapa ``gworld.map/0`` (MAP-4): anillos de contorno, poligonos, area y envolvente.

Port de ``map-generator/geometria.py`` de WMF. Las celdas son poligonos de vertices compartidos
(``cells[i].vertices`` indexa ``geometry.vertices``), todas con el mismo sentido de giro. Todo sale en km:
``km = unidad * unitKm`` y el area se multiplica por ``unitKm**2`` (WMF no lo aplica porque su ``kmPorUnidad`` es 1).

Determinista: las salidas no dependen del orden de ``cells`` ni del hash de sets. Anillos y poligonos son listas de
``(x, y)`` en km, sin repetir el primer punto; un poligono es ``(exterior, huecos)``.
"""

from typing import Iterable

Ring = list[tuple[float, float]]
Polygon = tuple[Ring, list[Ring]]


def _signed_area(ring: Ring) -> float:
    """Formula de Gauss (shoelace), la misma que d3.polygonArea."""
    a = 0.0
    for k in range(len(ring)):
        x0, y0 = ring[k - 1]
        x1, y1 = ring[k]
        a += y0 * x1 - x0 * y1
    return a / 2


def _inside(p, ring: Ring) -> bool:
    x, y = p
    d = False
    for k in range(len(ring)):
        x0, y0 = ring[k - 1]
        x1, y1 = ring[k]
        if (y1 > y) != (y0 > y) and x < (x0 - x1) * (y - y1) / (y0 - y1) + x1:
            d = not d
    return d


def _vertex_rings(doc: dict, cells: Iterable[int]) -> list[list[int]]:
    """Anillos de indices de vertice. Una arista dirigida a->b es de contorno si b->a no es de otra celda del conjunto."""
    by_id = {c["id"]: c["vertices"] for c in doc["cells"]}
    directed = set()
    for i in set(cells):
        vs = by_id[i]
        for k in range(len(vs)):
            directed.add((vs[k], vs[(k + 1) % len(vs)]))
    nxt: dict[int, list[int]] = {}
    for a, b in directed:
        if (b, a) not in directed and a != b:
            nxt.setdefault(a, []).append(b)
    for outs in nxt.values():
        outs.sort()
    result = []
    while nxt:
        start = min(nxt)
        ring = [start]
        cur = start
        while True:
            outs = nxt.get(cur)
            if not outs:
                break
            n = outs.pop()
            if not outs:
                del nxt[cur]
            if n == start:
                break
            ring.append(n)
            cur = n
        if len(ring) >= 3:
            result.append(ring)
    return result


def _km_ring(doc: dict, ring: list[int]) -> Ring:
    geo = doc["geometry"]
    k = geo["unitKm"]
    vs = geo["vertices"]
    return [(vs[v][0] * k, vs[v][1] * k) for v in ring]


def rings(doc: dict, cells: Iterable[int]) -> list[Ring]:
    """Contornos cerrados del conjunto de celdas, en km. Orden: por el menor vertice de cada uno (el de salida)."""
    return [_km_ring(doc, r) for r in _vertex_rings(doc, cells)]


def polygons(doc: dict, cells: Iterable[int]) -> list[Polygon]:
    """``(exterior, huecos)`` en km. Exterior: el giro de la primera celda (menor id); los otros anillos son huecos.

    Cada hueco va al primer exterior (orden por menor punto y longitud) que lo contiene.
    """
    cells = sorted(set(cells))
    if not cells:
        return []
    by_id = {c["id"]: c["vertices"] for c in doc["cells"]}
    first = _km_ring(doc, by_id[cells[0]])
    turn = _signed_area(first) > 0
    outers: list[Ring] = []
    holes: list[Ring] = []
    for ring in rings(doc, cells):
        (outers if (_signed_area(ring) > 0) == turn else holes).append(ring)
    outers.sort(key=lambda r: (min(r), len(r)))
    result: list[tuple[Ring, list[Ring]]] = [(o, []) for o in outers]
    for h in holes:
        for outer, hs in result:
            if _inside(h[0], outer):
                hs.append(h)
                break
    return result


def area_km2(doc: dict, cells: Iterable[int]) -> float:
    """Suma de |exterior| menos |huecos|, en km2 (``unitKm`` ya aplicado a las coordenadas)."""
    return sum(abs(_signed_area(o)) - sum(abs(_signed_area(h)) for h in hs) for o, hs in polygons(doc, cells))


def extent_km(doc: dict, cells: Iterable[int]) -> tuple[float, float]:
    """``(ancho E-O, alto N-S)`` en km del rectangulo que encierra los exteriores; ``(0, 0)`` si no hay celdas."""
    pts = [q for o, _ in polygons(doc, cells) for q in o]
    if not pts:
        return 0, 0
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    return max(xs) - min(xs), max(ys) - min(ys)
