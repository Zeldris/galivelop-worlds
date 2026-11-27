"""Reglas de mapa (MAP-4): artefacto ``gworld.maprules/0``, ``load_map_rules``, ``bind`` y ``check_facts``.

``load_map_rules(path)`` lee y valida el archivo (``MapError``: ``unreadable``, ``malformed``, ``schema``,
``duplicate_rule``). ``bind(rules, doc)`` comprueba las reglas contra un ``gworld.map/0`` sin medir nada:
``map_mismatch`` (la huella de las reglas no es la de origen del mapa), ``bad_params`` (faltan o sobran
parametros, o su forma no es la de la tabla), ``bad_direction``, ``unknown_ref`` (zona o lugar que no existe) y
``wrong_layer`` (zona de otra capa que la que pide el parametro). El ``detail`` es un dict con el ``id`` de la
regla y lo afectado. ``check_facts(rules, index)`` da los ids de ``facts`` que no estan en el canon.

``PARAMS`` es la tabla de parametros de cada tipo (nombre -> ``Param``), que ``bind`` usa y el motor
(``check_rules``, paso 3) reutiliza para leer los parametros ya validados.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Container

from gworld.maps import MapError
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
    "narrows": {"zone": _zone(), "toward": Param("dir", CARDINAL), "between": _zone(), "and": _zone(),
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
    seen: set[str] = set()
    for r in _all(rules):
        if r["id"] in seen:
            raise _fail("duplicate_rule", f"id de regla repetido {r['id']!r}", r["id"])
        seen.add(r["id"])
    return rules


def _all(rules: dict) -> list[dict]:
    return list(rules["rules"]) + list(rules.get("undecided", []))


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
