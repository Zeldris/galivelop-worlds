"""Importadores de mapas (MAP-2): ``MapImporter`` y ``FmgImporter`` (Azgaar's Fantasy Map Generator 1.137.6).

``FmgImporter().import_map(path)`` lee el archivo ``.map`` (solo lectura) y devuelve un documento ``gworld.map/0``
que valida contra su esquema. El mismo archivo da el mismo documento. Fallos como ``MapError`` con ``code`` estable:
``unreadable`` (error de E/S), ``malformed`` (no es un .map de FMG, truncado o con registros ilegibles),
``unsupported_version`` (no es la 1.137.6), ``mismatch`` (las celdas reconstruidas no cuadran con lo que guardo FMG),
``schema`` (el documento producido no valida: fallo del importador).
``import_with_review`` devuelve ademas un ``ImportReview`` (marcadores automaticos y burgs borrados).

El ``.map`` no guarda la forma de las celdas del mapa politico: solo la rejilla y sus alturas; FMG las rehace al
cargar y los arrays por celda siguen ese orden. Aqui se rehacen igual (``reGraph`` de FMG) y se comprueba, con el
area de cada region y las celdas de cada masa de tierra, que el orden coincide.
"""

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from gworld._delaunay import triangulate
from gworld.schema import validate
from gworld.schemas import load_schema

FMG_VERSION = "1.137.6"
IMPORTER_ID = "fmg/0"
SEA_LEVEL = 20
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

# Posicion de cada registro del .map (FMG 1.137.6): 46 registros separados por saltos de linea.
_PARAMS, _NOTES, _BIOMES, _GRID, _GRID_H, _GRID_F, _GRID_T, _FEATURES, _STATES, _BURGS = 0, 4, 3, 6, 7, 9, 10, 12, 14, 15
_C_BIOME, _C_RIVER, _C_STATE, _C_PROVINCE = 16, 22, 25, 27
_PROVINCES, _RIVERS, _MARKERS, _ROUTES = 30, 32, 35, 37
_MIN_RECORDS = 45


class MapError(Exception):
    def __init__(self, code: str, message: str, detail: Any = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = detail if detail is not None else message


@dataclass(frozen=True)
class Marker:
    """Marcador automatico de FMG (nombre en ingles): no entra en el mapa, queda en el informe."""
    id: int
    type: str
    x: float
    y: float
    cell: int
    name: str | None
    legend: str | None


@dataclass(frozen=True)
class ImportReview:
    """Lo que FMG genero solo y el importador no lleva al mapa, para que una persona lo revise (como ``revisar`` de WMF)."""
    markers: tuple[Marker, ...]
    deleted_burgs: int


class MapImporter(Protocol):
    """Contrato de un importador: de un archivo a un documento ``gworld.map/0``."""

    def import_map(self, path: str | Path) -> dict: ...


# --- lectura del archivo ---

def _records(text: str) -> list[str]:
    if "\r\n" in text:
        return text.split("\r\n")
    lines = text.split("\n")  # sin CRLF, el SVG del registro 5 ocupa varias lineas
    if len(lines) < 6 or not lines[5].startswith("<svg"):
        raise MapError("malformed", "el registro 5 no es el SVG: no parece un .map de FMG")
    end = next((i for i in range(5, len(lines)) if lines[i].rstrip().endswith("</svg>")), None)
    if end is None:
        raise MapError("malformed", "el SVG del registro 5 no se cierra: archivo truncado")
    return lines[:5] + ["\n".join(lines[5:end + 1])] + lines[end + 1:]


def _ints(rec: str) -> list[int]:
    return [int(v) for v in rec.split(",")] if rec else []


def _json(rec: str, name: str, default=None):
    if not rec:
        return default
    try:
        return json.loads(rec)
    except ValueError as e:
        raise MapError("malformed", f"el registro {name} no es JSON valido: {e}") from e


# --- reconstruccion de celdas (reGraph de FMG) ---

def _next(e: int) -> int:
    return e - 2 if e % 3 == 2 else e + 1


def _voronoi(points, boundary):
    allp = list(points) + list(boundary)
    n = len(points)
    tri, half = triangulate(allp)
    cell_v: list = [None] * n
    cell_c: list = [None] * n
    edge = [0] * n
    verts: dict[int, list] = {}
    for e in range(len(tri)):
        p = tri[_next(e)]
        if p < n and cell_c[p] is None:
            edges, cur = [], e
            while True:
                edges.append(cur)
                cur = half[_next(cur)]
                if cur in (-1, e) or len(edges) >= 20:
                    break
            cell_v[p] = [a // 3 for a in edges]
            cell_c[p] = [tri[a] for a in edges if tri[a] < n]
            edge[p] = 1 if len(edges) > len(cell_c[p]) else 0
        t = e // 3
        if t not in verts:
            (ax, ay), (bx, by), (cx, cy) = (allp[tri[3 * t + k]] for k in range(3))
            d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
            if d == 0:
                raise MapError("malformed", "rejilla degenerada: triangulo sin area")
            a2, b2, c2 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
            # Como getCircumcenter de FMG: 1/D por el numerador, no numerador / D (redondean distinto).
            verts[t] = [math.floor((1 / d) * (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by))),
                        math.floor((1 / d) * (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)))]
    return cell_v, cell_c, edge, verts


def _round(v: float, digits: int = 0) -> float:
    m = 10**digits
    return math.floor(v * m + 0.5) / m  # Math.round de JS: .5 hacia +infinito


def _polygon_area(pts) -> float:
    return sum(pts[i - 1][1] * pts[i][0] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))) / 2


def _regraph(grid, heights, types, grid_features):
    pts, spacing2 = grid["points"], grid["spacing"] ** 2
    if not (len(pts) == len(heights) == len(types) == len(grid_features)):
        raise MapError("malformed", "los arrays de la rejilla no tienen la longitud de sus puntos")
    _, gc, gedge, _ = _voronoi(pts, grid["boundary"])
    newp, newh = [], []
    for i, (x, y) in enumerate(pts):
        h, t = heights[i], types[i]
        if h < SEA_LEVEL and t not in (-1, -2):
            continue
        if t == -2 and (i % 4 == 0 or grid["features"][grid_features[i]]["type"] == "lake"):
            continue
        newp.append([x, y])
        newh.append(h)
        if t in (1, -1) and not gedge[i]:
            for j in gc[i]:
                if i > j or types[j] != t or _d2(x, y, pts[j]) < spacing2:
                    continue
                newp.append([_round((x + pts[j][0]) / 2, 1), _round((y + pts[j][1]) / 2, 1)])
                newh.append(h)
    cv, cc, _, verts = _voronoi(newp, grid["boundary"])
    vlist = [verts[t] for t in range(len(verts))]
    areas = [int(min(abs(_polygon_area([verts[v] for v in vs])), 65535)) for vs in cv]
    return newp, newh, cv, cc, vlist, areas


def _d2(x, y, q):
    return (y - q[1]) ** 2 + (x - q[0]) ** 2


def _landmasses(cc, heights, features):
    n = len(heights)
    out = [0] * n
    for f in features:
        if not isinstance(f, dict) or not f.get("land"):
            continue
        stack = [f["firstCell"]]
        out[f["firstCell"]] = f["i"]
        while stack:
            for j in cc[stack.pop()]:
                if not out[j] and heights[j] >= SEA_LEVEL:
                    out[j] = f["i"]
                    stack.append(j)
    return out


# --- el importador ---

def _color(v) -> dict:
    return {"color": v} if isinstance(v, str) and _COLOR.match(v) else {}


def _text(s):
    """Texto de FMG sin surrogates sueltos (algun nombre automatico trae medio emoji)."""
    return None if s is None else s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def _live(items) -> list[dict]:
    return [x for x in items if isinstance(x, dict) and not x.get("removed")]


class FmgImporter:
    """Azgaar's Fantasy Map Generator, version 1.137.6."""

    id = IMPORTER_ID
    format = "fmg"
    version = FMG_VERSION

    def import_map(self, path: str | Path) -> dict:
        return self.import_with_review(path)[0]

    def import_with_review(self, path: str | Path) -> tuple[dict, ImportReview]:
        p = Path(path)
        try:
            raw = p.read_bytes()
        except OSError as e:
            raise MapError("unreadable", f"no se puede leer {p}: {e}") from e
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise MapError("malformed", f"{p.name} no es texto UTF-8: no parece un .map de FMG") from e
        try:
            doc, review = self._build(_records(text), p.name, "sha256:" + hashlib.sha256(raw).hexdigest())
        except (KeyError, IndexError, TypeError, ValueError, AttributeError, ArithmeticError) as e:
            raise MapError("malformed", f"{p.name}: registros incoherentes ({type(e).__name__}: {e})") from e
        errors = validate(doc, load_schema("gworld.map/0"))
        if errors:
            e = errors[0]
            raise MapError("schema", f"el mapa importado no valida: {e.path} {e.code}", [(x.path, x.code) for x in errors])
        from gworld.topology import check_map  # aqui y no arriba: topology importa MapError de este modulo
        check_map(doc)
        return doc, review

    def _build(self, rec: list[str], name: str, digest: str) -> tuple[dict, ImportReview]:
        params = rec[_PARAMS].split("|")
        if params[0] != FMG_VERSION:
            if not re.match(r"^\d+\.\d+\.\d+$", params[0]):
                raise MapError("malformed", f"{name}: la primera linea no empieza por una version de FMG")
            raise MapError("unsupported_version", f"{name} es de FMG {params[0]} y solo se conoce la {FMG_VERSION}",
                           params[0])
        if len(rec) < _MIN_RECORDS:
            raise MapError("malformed", f"{name} tiene {len(rec)} registros y FMG {FMG_VERSION} guarda 46: truncado")
        width, height = int(params[4]), int(params[5])
        grid = _json(rec[_GRID], "grid")
        pts, heights, cv, cc, vertices, areas = _regraph(grid, _ints(rec[_GRID_H]), _ints(rec[_GRID_T]),
                                                         _ints(rec[_GRID_F]))
        n = len(pts)
        per_cell = {k: _ints(rec[i]) for k, i in (("biome", _C_BIOME), ("state", _C_STATE),
                                                  ("province", _C_PROVINCE))}
        for k, v in per_cell.items():
            if len(v) != n:
                raise MapError("mismatch", f"{k}: el archivo guarda {len(v)} celdas y se reconstruyen {n}")

        states = [s for s in _live(_json(rec[_STATES], "states", [])) if s.get("i")]
        by_state: dict[int, int] = {}
        for i in range(n):
            if heights[i] >= SEA_LEVEL:
                by_state[per_cell["state"][i]] = by_state.get(per_cell["state"][i], 0) + areas[i]
        for s in states:
            if by_state.get(s["i"], 0) != s["area"]:
                raise MapError("mismatch", f"region {s['i']}: FMG guardo {s['area']} km2 y las celdas suman "
                                           f"{by_state.get(s['i'], 0)}")
        features = _json(rec[_FEATURES], "features", [])
        land = _landmasses(cc, heights, features)
        for f in features:
            if isinstance(f, dict) and f.get("land") and land.count(f["i"]) != f["cells"]:
                raise MapError("mismatch", f"masa de tierra {f['i']}: FMG guardo {f['cells']} celdas y salen "
                                           f"{land.count(f['i'])}")

        zones, cells = [], []
        masses = [f for f in features if isinstance(f, dict) and f.get("land")]
        for f in masses:
            zones.append({"id": f"landmass:{f['i']}", "layer": "landmass", "name": f"Landmass {f['i']}"})
        for s in states:
            z = {"id": f"region:{s['i']}", "layer": "region", "name": s["name"], **_color(s.get("color"))}
            if isinstance(s.get("center"), int) and 0 <= s["center"] < n:
                z["centerCell"] = s["center"]
            zones.append(z)
        for pv in _live(_json(rec[_PROVINCES], "provinces", [])):
            z = {"id": f"province:{pv['i']}", "layer": "province", "name": pv["name"], **_color(pv.get("color"))}
            if pv.get("state"):
                z["parent"] = f"region:{pv['state']}"
            if isinstance(pv.get("center"), int) and 0 <= pv["center"] < n:
                z["centerCell"] = pv["center"]
            zones.append(z)
        known = {z["id"] for z in zones}

        for i in range(n):
            ids = [f"landmass:{land[i]}" if land[i] else None,
                   f"region:{per_cell['state'][i]}" if per_cell["state"][i] else None,
                   f"province:{per_cell['province'][i]}" if per_cell["province"][i] else None]
            cell = {"id": i, "center": [_round(pts[i][0], 1), _round(pts[i][1], 1)], "vertices": cv[i],
                    "neighbours": cc[i], "height": heights[i], "area": areas[i], "biome": str(per_cell["biome"][i])}
            cell["zones"] = [z for z in ids if z in known]
            cells.append(cell)

        colors, _, names = (s.split(",") for s in rec[_BIOMES].split("|"))
        biomes = {str(i): {"name": nm, **_color(colors[i])} for i, nm in enumerate(names)}

        places = []
        for b in _live(_json(rec[_BURGS], "burgs", [])):
            if not b.get("i"):
                continue
            pl = {"id": b["i"], "name": b["name"], "cell": b["cell"], "point": [_round(b["x"], 2), _round(b["y"], 2)]}
            if b.get("type"):
                pl["type"] = b["type"]
            if b.get("capital") and f"region:{b.get('state')}" in known:
                pl["capitalOf"] = f"region:{b['state']}"
            places.append(pl)

        routes = []
        for r in _json(rec[_ROUTES], "routes", []):
            rt = {"id": r["i"], "group": r["group"], "points": [[_round(q[0], 2), _round(q[1], 2)] for q in r["points"]]}
            if f"landmass:{r.get('feature')}" in known:
                rt["zone"] = f"landmass:{r['feature']}"
            routes.append(rt)

        rivers = []
        for r in _json(rec[_RIVERS], "rivers", []):
            rc = [c for c in r.get("cells") or [] if isinstance(c, int) and 0 <= c < n]
            if rc:
                rv = {"id": r["i"], "cells": rc}
                if r.get("name"):
                    rv["name"] = r["name"]
                rivers.append(rv)

        notes = {x.get("id"): x for x in _json(rec[_NOTES], "notes", []) if isinstance(x, dict)}
        markers = tuple(
            Marker(m["i"], m["type"], _round(m["x"], 2), _round(m["y"], 2), m["cell"],
                   _text(notes.get(f"marker{m['i']}", {}).get("name")),
                   _text(notes.get(f"marker{m['i']}", {}).get("legend")))
            for m in _json(rec[_MARKERS], "markers", []) if isinstance(m, dict))
        deleted = sum(1 for b in _json(rec[_BURGS], "burgs", []) if isinstance(b, dict) and b.get("removed"))

        origin = {"file": {"name": name, "format": self.format, "formatVersion": FMG_VERSION}, "sha256": digest,
                  "importer": f"{self.id}", "seed": params[3], "created": params[2]}
        doc = {"kind": "gworld.map/0", "origin": origin,
                "geometry": {"width": width, "height": height, "unitKm": 1, "yDown": True, "vertices": vertices},
                "seaLevel": SEA_LEVEL, "biomes": biomes, "cells": cells, "zones": zones, "places": places,
                "routes": routes, "rivers": rivers}
        return doc, ImportReview(markers, deleted)
