"""Reglas de mapa (MAP-4): artefacto ``gworld.maprules/0``, ``load_map_rules``, ``bind`` y ``check_facts``.

``load_map_rules(path)`` lee y valida el archivo (``MapError``: ``unreadable``, ``malformed``, ``schema``,
``duplicate_rule``). ``bind(rules, doc)`` comprueba las reglas contra un ``gworld.map/0`` sin medir nada:
``map_mismatch`` (la huella de las reglas no es la de origen del mapa), ``bad_params`` (faltan o sobran
parametros, o su forma no es la de la tabla), ``bad_direction``, ``unknown_ref`` (zona o lugar que no existe) y
``wrong_layer`` (zona de otra capa que la que pide el parametro). El ``detail`` es un dict con el ``id`` de la
regla y lo afectado. ``check_facts(rules, index)`` da los ids de ``facts`` que no estan en el canon.

``PARAMS`` es la tabla de parametros de cada tipo (nombre -> ``Param``), que ``bind`` usa y el motor
(``check_rules``) reutiliza para leer los parametros ya validados.

``check_rules(doc, rules)`` mide cada regla (primero ``rules``, luego ``undecided``) y da un ``RuleResult`` por
regla; los detalles siguen los de ``comprobar.py`` y ``medir.py`` de WMF. Tierra: ``height >= seaLevel`` (20 si el
mapa no lo dice; una celda sin ``height`` es agua). Punto de una celda: ``center * unitKm``. Norte, sur, este y oeste
segun ``geometry.yDown`` (por defecto true: la y crece hacia el sur). Una celda sin zona en la capa de una zona es la
«region 0» de WMF: no cuenta como vecina de otra region. Las coordenadas de los detalles son las del mapa, en km.
"""

import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Container, NamedTuple

from gworld import geometry
from gworld.maps import SEA_LEVEL, MapError
from gworld.schema import validate
from gworld.schemas import load_schema

CARDINAL = frozenset({"north", "south", "east", "west"})
AXES = frozenset({"north-south", "south-north", "west-east", "east-west"})
LINES = frozenset({"north-south", "east-west"})  # orientacion de una frontera
CROSSINGS = frozenset({"west-east", "north-south"})  # eje de una costa a costa
LAND_OR_REGION = frozenset({"region", "landmass"})


@dataclass(frozen=True)
class Param:
    """Un parametro de un tipo de regla.

    ``kind``: ``zone`` (id de zona; ``arg`` = capas admitidas o None si cualquiera), ``zones`` (lista no vacia de
    zonas), ``groups`` (lista de al menos 2 listas no vacias de zonas), ``place`` (id entero de lugar), ``places``
    (lista de exactamente 2 lugares), ``dir`` (cadena de ``arg``), ``number`` (>= 0), ``text`` (cadena no vacia).
    """

    kind: str
    arg: frozenset | None = None
    required: bool = True


def _zone(*layers: str, required: bool = True) -> Param:
    return Param("zone", frozenset(layers) or None, required)


PARAMS: dict[str, dict[str, Param]] = {
    "order": {"axis": Param("dir", AXES), "groups": Param("groups")},
    "side-of": {"a": _zone(), "b": _zone(), "side": Param("dir", CARDINAL)},
    "border": {"a": _zone(), "b": _zone(), "orientation": Param("dir", LINES)},
    "coast-to-coast": {"zone": _zone(), "axis": Param("dir", CROSSINGS)},
    "only-borders": {"zone": _zone(), "with": Param("zones")},
    "borders": {"a": _zone(), "b": _zone()},
    "closes-by": {"zone": _zone(), "edge": Param("dir", CARDINAL), "by": _zone(), "min": Param("number"),
                  "strip": Param("number", required=False)},
    "narrows": {"zone": _zone(), "toward": Param("dir", CARDINAL), "between": Param("zones"), "and": Param("zones"),
                "max": Param("number")},
    "corridor": {"from": _zone("province"), "to": _zone(), "along": _zone(), "side": Param("dir", CARDINAL)},
    "inside": {"landmass": _zone("landmass"), "zones": Param("zones")},
    "no-land-outside": {"landmasses": Param("zones", frozenset({"landmass"})), "name": Param("text")},
    "area": {"zone": _zone()},
    "extent": {"zone": _zone()},
    "distance": {"places": Param("places")},
    "edge": {"landmass": _zone("landmass"), "side": Param("dir", CARDINAL)},
    "shape": {"zone": _zone(required=False)},
}
RULE_TYPES = ("order", "side-of", "border", "coast-to-coast", "only-borders", "borders", "closes-by", "narrows",
              "corridor", "inside", "no-land-outside", "area", "extent", "distance")
UNDECIDED_TYPES = ("edge", "area", "extent", "distance", "shape")
# Medidas de canon.json: exactamente uno de `value` y `range` (en `undecided`, como mucho uno).
# `value` es un numero (area, distance) o un par [ancho, alto] (extent); `range` es un par [lo, hi].
MEASURES = frozenset({"area", "extent", "distance"})
# Parametros que se comparan en la capa de otro (el motor mira la zona del vecino en la capa de `a`).
SAME_LAYER = {"closes-by": (("zone", "by"),), "borders": (("a", "b"),), "only-borders": (("zone", "with"),)}
COMMON = frozenset({"id", "type", "text", "source", "facts"})


def _fail(code: str, message: str, rule_id: str, **extra: Any) -> MapError:
    return MapError(code, f"{message} (regla {rule_id})", {"id": rule_id, **extra})


def load_map_rules(path: "str | Path") -> dict:
    """Lee y valida un ``gworld.maprules/0``; ``MapError`` si no se puede leer, no es JSON o no valida."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise MapError("unreadable", f"no se puede leer {p}: {e}") from e
    try:
        rules = json.loads(text)
    except (ValueError, RecursionError) as e:
        raise MapError("malformed", f"{p.name} no es JSON valido: {e}") from e
    try:
        errors = validate(rules, load_schema("gworld.maprules/0"))
    except RecursionError as e:
        raise MapError("malformed", f"{p.name} demasiado anidado") from e
    if errors:
        e = errors[0]
        raise MapError("schema", f"{p.name} no cumple gworld.maprules/0: {e.path or '/'} {e.code} {e.params}",
                       [(x.path, x.code) for x in errors])
    tol = rules.get("tolerance")
    if tol is not None and not _is_num(tol):
        raise MapError("schema", f"{p.name} no cumple gworld.maprules/0: /tolerance no es un numero finito",
                       [("/tolerance", "finite")])
    seen: set[str] = set()
    for r in _all(rules):
        if r["id"] in seen:
            raise _fail("duplicate_rule", f"id de regla repetido {r['id']!r}", r["id"])
        seen.add(r["id"])
    return rules


def _all(rules: dict) -> list[dict]:
    return list(rules["rules"]) + list(rules.get("undecided", []))


def _is_num(v: Any) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return isinstance(v, int) or math.isfinite(v)


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def bind(rules: dict, doc: dict) -> None:
    """Comprueba ``rules`` contra el mapa ``doc``; ``MapError`` con el primer fallo (reglas, luego sin decidir)."""
    if rules["map"] != doc["origin"]["sha256"]:
        raise MapError("map_mismatch", f"las reglas son del mapa {rules['map']} y este es {doc['origin']['sha256']}",
                       {"expected": rules["map"], "actual": doc["origin"]["sha256"]})
    layers = {z["id"]: z["layer"] for z in doc.get("zones", [])}
    places = {p["id"] for p in doc.get("places", [])}
    for section, allowed in (("rules", RULE_TYPES), ("undecided", UNDECIDED_TYPES)):
        for r in rules.get(section, []):
            _bind_rule(r, allowed, layers, places)


def _bind_rule(r: dict, allowed: tuple[str, ...], layers: dict[str, str], places: set) -> None:
    rid, typ = r["id"], r["type"]
    if typ not in allowed:
        raise _fail("bad_params", f"tipo {typ!r} no admitido aqui", rid, type=typ)
    table = PARAMS[typ]
    known = COMMON | set(table) | ({"value", "range"} if typ in MEASURES else set())
    extra = sorted(set(r) - known)
    if extra:
        raise _fail("bad_params", f"sobran parametros {extra}", rid, type=typ, extra=extra)
    missing = sorted(n for n, p in table.items() if p.required and n not in r)
    if missing:
        raise _fail("bad_params", f"faltan parametros {missing}", rid, type=typ, missing=missing)
    if typ in MEASURES:
        _bind_measure(r, typ, rid, decided=allowed is RULE_TYPES)
    for name, p in table.items():
        if name in r:
            _bind_param(rid, name, p, r[name], layers, places)
    if typ == "closes-by":
        if not r.get("strip", 10) > 0:
            raise _fail("bad_params", "strip debe ser > 0", rid, param="strip", value=r["strip"])
        if r["min"] > 1:
            raise _fail("bad_params", "min debe estar entre 0 y 1", rid, param="min", value=r["min"])
    for a, b in SAME_LAYER.get(typ, ()):
        if a in r and b in r:
            want = layers[r[a]]
            for z in (r[b] if isinstance(r[b], list) else [r[b]]):
                if layers[z] != want:
                    raise _fail("wrong_layer", f"{b}: {z!r} es de la capa {layers[z]!r} y {a} de {want!r}", rid,
                                param=b, ref=z, layer=layers[z], expected=[want])


def _bind_measure(r: dict, typ: str, rid: str, decided: bool) -> None:
    has = [k for k in ("value", "range") if k in r]
    if (decided and len(has) != 1) or len(has) > 1:
        raise _fail("bad_params", "exige exactamente uno de value y range" if decided else
                    "admite como mucho uno de value y range", rid, type=typ, has=has)
    if "value" in r:
        v = r["value"]
        pair = typ == "extent"
        ok = (isinstance(v, list) and len(v) == 2 and all(_is_num(x) and x >= 0 for x in v)) if pair else \
            _is_num(v) and v >= 0
        if not ok:
            raise _fail("bad_params", "value debe ser un par [ancho, alto]" if pair else "value debe ser un numero >= 0",
                        rid, param="value", value=v)
    if "range" in r:
        v = r["range"]
        if typ == "extent":
            raise _fail("bad_params", "extent no admite range (solo value [ancho, alto])", rid, param="range", value=v)
        if not (isinstance(v, list) and len(v) == 2 and all(_is_num(x) and x >= 0 for x in v) and v[0] <= v[1]):
            raise _fail("bad_params", "range debe ser un par [lo, hi] con lo <= hi", rid, param="range", value=v)


def _bind_param(rid: str, name: str, p: Param, v: Any, layers: dict[str, str], places: set) -> None:
    def bad(what: str) -> MapError:
        return _fail("bad_params", f"{name} debe ser {what}", rid, param=name, value=v)

    def zone(z: Any, layers_ok: frozenset | None) -> None:
        if not isinstance(z, str):
            raise bad("un id de zona")
        if z not in layers:
            raise _fail("unknown_ref", f"{name}: la zona {z!r} no existe", rid, param=name, ref=z)
        if layers_ok and layers[z] not in layers_ok:
            raise _fail("wrong_layer", f"{name}: {z!r} es de la capa {layers[z]!r}, no de {sorted(layers_ok)}", rid,
                        param=name, ref=z, layer=layers[z], expected=sorted(layers_ok))

    def place(x: Any) -> None:
        if not _is_int(x):
            raise bad("un id de lugar (entero)")
        if x not in places:
            raise _fail("unknown_ref", f"{name}: el lugar {x!r} no existe", rid, param=name, ref=x)

    if p.kind == "zone":
        zone(v, p.arg)
    elif p.kind == "zones":
        if not isinstance(v, list) or not v:
            raise bad("una lista no vacia de zonas")
        for z in v:
            zone(z, p.arg)
    elif p.kind == "groups":
        if not isinstance(v, list) or len(v) < 2 or any(not isinstance(g, list) or not g for g in v):
            raise bad("una lista de al menos 2 grupos no vacios de zonas")
        for g in v:
            for z in g:
                zone(z, p.arg)
    elif p.kind == "place":
        place(v)
    elif p.kind == "places":
        if not isinstance(v, list) or len(v) != 2:
            raise bad("una lista de 2 lugares")
        for x in v:
            place(x)
    elif p.kind == "dir":
        if not isinstance(v, str):
            raise bad("una cadena")
        if v not in p.arg:
            raise _fail("bad_direction", f"{name}: {v!r} no es una direccion valida", rid, param=name, value=v,
                        allowed=sorted(p.arg))
    elif p.kind == "number":
        if not _is_num(v) or v < 0:
            raise bad("un numero >= 0")
    elif p.kind == "text":
        if not isinstance(v, str) or not v:
            raise bad("una cadena no vacia")


def check_facts(rules: dict, index: Container[str]) -> list[str]:
    """Ids de ``facts`` de las reglas que no estan en ``index`` (los ids del canon), sin repetir y en orden."""
    out: list[str] = []
    for r in _all(rules):
        for f in r.get("facts", []):
            if f not in index and f not in out:
                out.append(f)
    return out


class RuleResult(NamedTuple):
    """Resultado de una regla: ``ok`` es None en las de ``undecided`` (se mide sin juzgar)."""

    id: str
    type: str
    ok: bool | None
    detail: str


_ES = {"north": "norte", "south": "sur", "east": "este", "west": "oeste"}
_LETTER = {"north": "N", "south": "S", "east": "E", "west": "O"}
_OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}
_DEFAULT_TOLERANCE = 0.03


def _num(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


class _Map:
    """Vista del mapa para medir: celdas de tierra, puntos en km, zonas y direcciones."""

    def __init__(self, doc: dict):
        self.doc = doc
        geo = doc["geometry"]
        self.km = geo["unitKm"]
        self.y_down = geo.get("yDown", True)
        sea = doc.get("seaLevel", SEA_LEVEL)
        self.cells = {c["id"]: c for c in doc["cells"]}
        self.land = {i for i, c in self.cells.items() if "height" in c and c["height"] >= sea}
        self.layer = {z["id"]: z["layer"] for z in doc.get("zones", [])}
        self.members: dict[str, list[int]] = {z: [] for z in self.layer}
        self.zone_in: dict[int, dict[str, str]] = {}
        for i, c in self.cells.items():
            self.zone_in[i] = {self.layer[z]: z for z in c.get("zones", []) if z in self.layer}
            for z in c.get("zones", []):
                if z in self.members:
                    self.members[z].append(i)
        self.places = {p["id"]: p for p in doc.get("places", [])}

    def pt(self, i: int) -> tuple[float, float]:
        c = self.cells[i]["center"]
        return c[0] * self.km, c[1] * self.km

    def land_of(self, zone: str) -> list[int]:
        return [i for i in self.members[zone] if i in self.land]

    def centroid(self, cells: list[int]) -> tuple[float, float]:
        pts = [self.pt(i) for i in cells]
        return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)

    def sign(self, d: str) -> tuple[int, int]:
        """(indice de coordenada, signo): ``signo * p[indice]`` crece hacia la direccion ``d``."""
        if d == "east":
            return 0, 1
        if d == "west":
            return 0, -1
        return 1, (1 if self.y_down else -1) * (1 if d == "south" else -1)

    def toward(self, d: str, p: tuple[float, float]) -> float:
        k, s = self.sign(d)
        return s * p[k]

    def has_sea(self, i: int) -> bool:
        return any(n not in self.land for n in self.cells[i]["neighbours"])

    def region_of(self, i: int, layer: str) -> str | None:
        return self.zone_in[i].get(layer)


def check_rules(doc: dict, rules: dict) -> tuple[RuleResult, ...]:
    """Mide ``rules`` sobre el mapa ``doc`` (antes, ``bind``: ``MapError`` si no casan); ``rules`` y luego ``undecided``."""
    bind(rules, doc)
    m = _Map(doc)
    tol = rules.get("tolerance", _DEFAULT_TOLERANCE)
    out = []
    for section, table in (("rules", _DECIDED), ("undecided", _UNDECIDED)):
        for r in rules.get(section, []):
            ok, detail = table[r["type"]](m, r, tol)
            out.append(RuleResult(r["id"], r["type"], ok, detail))
    return tuple(out)


def _no_land(zone: str) -> tuple[bool, str]:
    return False, f"{zone} sin celdas de tierra"


def _order(m: _Map, r: dict, tol: float):
    last = r["axis"].split("-")[1]
    k, s = m.sign(last)  # s > 0: la coordenada en bruto crece en el sentido del eje
    ys = []
    for g in r["groups"]:
        cs = []
        for z in g:
            land = m.land_of(z)
            if not land:
                return _no_land(z)
            cs.append(m.centroid(land)[k])
        ys.append(sum(cs) / len(cs))
    ok = all(s * a < s * b for a, b in zip(ys, ys[1:]))
    return ok, f"{'x' if k == 0 else 'y'} de los centros: " + (" < " if s > 0 else " > ").join(f"{y:.0f}" for y in ys)


def _side_of(m: _Map, r: dict, tol: float):
    cs = []
    for z in (r["a"], r["b"]):
        land = m.land_of(z)
        if not land:
            return _no_land(z)
        cs.append(m.centroid(land))
    k = m.sign(r["side"])[0]
    ok = m.toward(r["side"], cs[0]) > m.toward(r["side"], cs[1])
    return ok, f"{'x' if k == 0 else 'y'} del centro: {cs[0][k]:.0f} y {cs[1][k]:.0f}"


def _border(m: _Map, r: dict, tol: float):
    b = set(m.land_of(r["b"]))
    pts = set()
    for i in m.land_of(r["a"]):
        ns = [j for j in m.cells[i]["neighbours"] if j in b]
        if ns:
            pts.add(i)
            pts.update(ns)
    if not pts:
        return False, "las zonas no lindan"
    xs = [m.pt(i)[0] for i in pts]
    ys = [m.pt(i)[1] for i in pts]
    ex, ey = max(xs) - min(xs), max(ys) - min(ys)
    ok = ey > ex if r["orientation"] == "north-south" else ex > ey
    return ok, f"extensión N-S {ey:.0f} km, E-O {ex:.0f} km"


def _coast_to_coast(m: _Map, r: dict, tol: float):
    k = 0 if r["axis"] == "west-east" else 1
    cells = m.land_of(r["zone"])
    if not cells:
        return _no_land(r["zone"])
    vs = [m.pt(i)[k] for i in cells]
    v0, v1 = min(vs), max(vs)
    centre = m.centroid(cells)[k]
    coast = [m.pt(i)[k] for i in cells if m.has_sea(i)]
    if not coast:
        return False, "sin celdas costeras"
    lo, hi = min(coast), max(coast)
    margin = 0.15 * (v1 - v0)
    ok = lo < centre < hi and lo <= v0 + margin and hi >= v1 - margin
    c = "x" if k == 0 else "y"
    return ok, f"costa de {c} {lo:.0f} a {hi:.0f} (zona {v0:.0f}-{v1:.0f}, centro {centre:.0f})"


def _neighbour_zones(m: _Map, zone: str):
    """Pares (celda de tierra de ``zone``, vecina de tierra, su zona en la capa de ``zone`` o None)."""
    layer = m.layer[zone]
    for i in m.land_of(zone):
        for j in m.cells[i]["neighbours"]:
            if j in m.land:
                yield i, j, m.region_of(j, layer)


def _only_borders(m: _Map, r: dict, tol: float):
    others = {z for _, _, z in _neighbour_zones(m, r["zone"]) if z not in (None, r["zone"])}
    extra = sorted(others - set(r["with"]))
    return not extra, ("linda solo con lo permitido" if not extra else "sobran: " + ", ".join(extra))


def _borders(m: _Map, r: dict, tol: float):
    n = sum(1 for _, _, z in _neighbour_zones(m, r["a"]) if z == r["b"])
    return n > 0, f"{n} pares de celdas vecinas"


def _closes_by(m: _Map, r: dict, tol: float):
    edge, strip = r["edge"], r.get("strip", 10)
    along = 1 - m.sign(edge)[0]  # coordenada a lo largo del borde
    layer = m.layer[r["zone"]]
    extreme: dict[int, int] = {}
    for i in m.land_of(r["zone"]):
        key = int(m.pt(i)[along] // strip)
        if key not in extreme or m.toward(edge, m.pt(i)) > m.toward(edge, m.pt(extreme[key])):
            extreme[key] = i
    pairs = []
    for i in extreme.values():
        p = m.pt(i)
        for j in m.cells[i]["neighbours"]:
            z = m.region_of(j, layer)
            if j in m.land and z not in (None, r["zone"]):
                q = m.pt(j)
                # La vecina esta mas hacia el borde que al lado: la frontera en diagonal no cuenta como borde.
                if m.toward(edge, q) - m.toward(edge, p) > abs(q[along] - p[along]):
                    pairs.append(z)
    if not pairs:
        return False, f"sin frontera {_ES[edge]}"
    frac = sum(1 for z in pairs if z == r["by"]) / len(pairs)
    return frac >= r["min"], f"{frac:.0%} de {len(pairs)} pares (mínimo {r['min']:.0%})"


def _narrows(m: _Map, r: dict, tol: float):
    zone = m.land_of(r["zone"])
    if not zone:
        return _no_land(r["zone"])
    sides = []
    for zs in (r["between"], r["and"]):  # cada lado es la union de sus zonas, como `entre` e `y` de WMF
        pts = [m.pt(i) for z in zs for i in m.land_of(z)]
        if not pts:
            return False, "un lado sin celdas"
        sides.append(pts)
    d = r["toward"]
    t = {i: -m.toward(d, m.pt(i)) for i in zone}  # crece desde el extremo `toward`
    t0 = min(t.values())
    width = (max(t.values()) - t0) / 4
    quarters: list[list[float]] = [[], [], [], []]
    for i in zone:
        q = min(3, int((t[i] - t0) / width)) if width else 0
        p = m.pt(i)
        quarters[q].append(sum(min(math.dist(p, s) for s in side) for side in sides))
    if not all(quarters):
        return False, "un cuarto sin celdas"
    means = [sum(q) / len(q) for q in quarters]
    central = quarters[1] + quarters[2]
    centre = sum(central) / len(central)
    if not centre:
        return False, f"los cuartos centrales no tienen grosor (0 km): no se puede medir {_ES[d]}/centro"
    return means[0] <= r["max"] * centre, (
        f"grosor por cuartos {_LETTER[d]}→{_LETTER[_OPPOSITE[d]]}: " + ", ".join(f"{x:.0f}" for x in means)
        + f" km; {_ES[d]}/centro = {means[0] / centre:.2f} (máximo {r['max']})")


def _corridor(m: _Map, r: dict, tol: float):
    start = m.land_of(r["from"])
    if not start:
        return False, "la provincia no tiene tierra"
    to, along, side = r["to"], r["along"], r["side"]
    layer = m.layer[to]
    # Paridad con WMF (Q-33, a): si la celda de partida no tiene zona en la capa, home es None y la «region 0» es pisable.
    home = m.region_of(min(start), layer)
    alongc = m.land_of(along)
    if not alongc:
        return _no_land(along)
    ref = m.toward(side, m.centroid(alongc))
    along_set, to_set = set(m.members[along]), set(m.members[to])

    def walkable(i: int) -> bool:
        if i not in m.land:
            return False
        if i in to_set or m.region_of(i, layer) == home:
            return True
        return i in along_set and m.has_sea(i) and m.toward(side, m.pt(i)) > ref

    dist = {i: 0.0 for i in start if walkable(i)}
    heap = [(0.0, i) for i in sorted(dist)]
    heapq.heapify(heap)
    while heap:
        d, i = heapq.heappop(heap)
        if d > dist.get(i, math.inf):
            continue
        if i in to_set:
            return True, f"camino de {d:.0f} km"
        for j in m.cells[i]["neighbours"]:
            if walkable(j):
                nd = d + math.dist(m.pt(i), m.pt(j))
                if nd < dist.get(j, math.inf):
                    dist[j] = nd
                    heapq.heappush(heap, (nd, j))
    return False, "sin camino por tierra"


def _inside(m: _Map, r: dict, tol: float):
    inner = set(m.members[r["landmass"]])
    out = [i for z in r["zones"] for i in m.land_of(z) if i not in inner]
    return not out, f"{len(out)} celdas de tierra fuera de {r['landmass']}"


def _no_land_outside(m: _Map, r: dict, tol: float):
    allowed = {i for z in r["landmasses"] for i in m.members[z]}
    out = [i for i in m.land if i not in allowed]
    places = [p for p in m.places.values() if r["name"] in p["name"]]
    return not out and not places, f"{len(out)} celdas de tierra fuera, {len(places)} lugares «{r['name']}»"


def _measure(m: _Map, r: dict):
    """(medida, texto, unidad) de area, extent o distance."""
    if r["type"] == "distance":
        a, b = (m.places[p]["point"] for p in r["places"])
        v = math.dist(a, b) * m.km
        return v, _num(v), "km"
    cells = m.land_of(r["zone"])
    if r["type"] == "area":
        v = geometry.area_km2(m.doc, cells)
        return v, _num(v), "km²"
    v = list(geometry.extent_km(m.doc, cells))
    return v, " × ".join(_num(x) for x in v), "km"


def _expected(r: dict) -> str:
    if "range" in r:
        return "–".join(_num(x) for x in r["range"])
    v = r["value"]
    return " × ".join(_num(x) for x in v) if isinstance(v, list) else _num(v)


def _within(v, r: dict, tol: float) -> bool:
    if "range" in r:
        lo, hi = r["range"]
        return lo * (1 - tol) <= v <= hi * (1 + tol)
    e = r["value"]
    if isinstance(e, list):
        return all(abs(a - b) <= b * tol for a, b in zip(v, e))
    return abs(v - e) <= e * tol


def _barren(m: _Map, r: dict) -> bool:
    """True si la regla mide el area o la envolvente de una zona sin tierra."""
    return r["type"] in ("area", "extent") and not m.land_of(r["zone"])


def _measured(m: _Map, r: dict, tol: float):
    if _barren(m, r):
        return _no_land(r["zone"])
    v, text, unit = _measure(m, r)
    return _within(v, r, tol), f"medido {text} {unit} (canon {_expected(r)}, ±{tol:.0%})"


def _measured_free(m: _Map, r: dict, tol: float):
    if _barren(m, r):
        return None, _no_land(r["zone"])[1]
    _, text, unit = _measure(m, r)
    canon = f", canon {_expected(r)}" if ("value" in r or "range" in r) else ""
    return None, f"medido {text} {unit}{canon}; sin decidir"


def _edge(m: _Map, r: dict, tol: float):
    cells = m.land_of(r["landmass"])
    if not cells:
        return None, f"{r['landmass']} sin celdas de tierra"
    d = r["side"]
    k, s = m.sign(d)
    vals = [m.pt(i)[k] for i in cells]
    v, word = (max(vals), "máxima") if s > 0 else (min(vals), "mínima")
    return None, f"{'x' if k == 0 else 'y'} {word} de la tierra de {r['landmass']}: {v:.0f} km ({_ES[d]})"


def _shape(m: _Map, r: dict, tol: float):
    return None, "sin medida"


_Check = Callable[[_Map, dict, float], "tuple[bool | None, str]"]
_DECIDED: dict[str, _Check] = {
    "order": _order, "side-of": _side_of, "border": _border, "coast-to-coast": _coast_to_coast,
    "only-borders": _only_borders, "borders": _borders, "closes-by": _closes_by, "narrows": _narrows,
    "corridor": _corridor, "inside": _inside, "no-land-outside": _no_land_outside,
    "area": _measured, "extent": _measured, "distance": _measured,
}
_UNDECIDED: dict[str, _Check] = {"edge": _edge, "area": _measured_free, "extent": _measured_free,
                                 "distance": _measured_free, "shape": _shape}
