"""Conversor de las reglas de mapa de Tarkor (MAP-4, paso 4): ``lore.json`` y ``canon.json`` de WMF -> ``gworld.maprules/0``.

Lee en solo lectura (nunca escribe en WMF) las reglas de ``map-generator/lore.json`` y las medidas de
``map-generator/canon.json`` y las traduce a los tipos de ``gworld.maprules`` resolviendo los nombres a ids de un
``gworld.map/0`` importado de ``Helek_World.map``: una zona por ``name`` (capa region, salvo ``provincia`` y
``continente``) y un lugar por ``name``. Un nombre que no resuelve es un ``MapError`` (``unknown_name``) que lo cita.

Los continentes de WMF (Berig, Vaelira) son las masas de tierra del mapa, que FMG no nombra: como en
``importar.py`` de WMF, Berig es la masa que tiene la region «Cristal Helado» y Vaelira la otra (debe haber dos).

Uso: ``python3 -m tools.tarkor_maprules --wmf ../World-Maker-Fantasy --out reglas.json``.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from gworld.maprules import bind
from gworld.maps import FmgImporter, MapError
from gworld.schema import validate
from gworld.schemas import load_schema

MAP_FILE = Path("docs/map/Helek_World.map")
LORE_FILE = Path("map-generator/lore.json")
CANON_FILE = Path("map-generator/canon.json")
BERIG_REGION = "Cristal Helado"  # la region que dice cual es la masa de Berig (importar.py de WMF)

DIRS = {"norte": "north", "sur": "south", "este": "east", "oeste": "west"}
AXES = {"norte-sur": "north-south", "sur-norte": "south-north", "oeste-este": "west-east", "este-oeste": "east-west"}
LINES = {"norte-sur": "north-south", "este-oeste": "east-west"}


def _slug(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:64].strip("-")


def _pick(table: dict, key: str, what: str, rid: str):
    if key not in table:
        raise MapError("unknown_name", f"{what} {key!r} no se resuelve (regla {rid})", {"id": rid, "name": key})
    v = table[key]
    if isinstance(v, list):  # varios con el mismo nombre
        if len(v) > 1:
            raise MapError("ambiguous_name", f"{what} {key!r} es ambiguo: {', '.join(map(str, v))} (regla {rid})",
                           {"id": rid, "name": key, "candidates": v})
        return v[0]
    return v


class _Names:
    """Nombres de WMF -> ids del mapa."""

    def __init__(self, doc: dict):
        self.layers: dict[str, dict[str, list[str]]] = {"region": {}, "province": {}}
        for z in doc["zones"]:
            if z["layer"] in self.layers:
                self.layers[z["layer"]].setdefault(z["name"], []).append(z["id"])
        self.places: dict[str, list[int]] = {}
        for p in doc["places"]:
            self.places.setdefault(p["name"], []).append(p["id"])
        berig_region = next(iter(self.layers["region"].get(BERIG_REGION, [])), None)
        count: Counter = Counter()
        for c in doc["cells"]:
            if berig_region in c.get("zones", []):
                count.update(z for z in c["zones"] if z.startswith("landmass:"))
        masses = [z["id"] for z in doc["zones"] if z["layer"] == "landmass"]
        self.continents: dict[str, str] = {}
        if count and len(masses) == 2:
            berig = count.most_common(1)[0][0]
            self.continents = {"Berig": berig, "Vaelira": next(m for m in masses if m != berig)}

    def zone(self, ref: Any, rid: str) -> str:
        """Nombre (region) o ``{"continente": n}`` / ``{"provincia": n}``."""
        if isinstance(ref, str):
            return _pick(self.layers["region"], ref, "region", rid)
        (kind, name), = ref.items()
        if kind == "continente":
            return _pick(self.continents, name, "continente", rid)
        return _pick(self.layers["province"], name, "provincia", rid)

    def place(self, name: str, rid: str) -> int:
        return _pick(self.places, name, "lugar", rid)


def _rule(lore: dict, n: _Names) -> dict:
    rid, t = lore["id"], lore["tipo"]

    def z(ref: Any) -> str:
        return n.zone(ref, rid)

    if t == "orden":
        out = {"type": "order", "axis": _pick(AXES, lore["eje"], "eje", rid),
               "groups": [[z(x) for x in g] for g in lore["grupos"]]}
    elif t == "oeste-de":
        out = {"type": "side-of", "a": z(lore["a"]), "b": z(lore["b"]), "side": "west"}
    elif t == "frontera":
        out = {"type": "border", "a": z(lore["a"]), "b": z(lore["b"]),
               "orientation": _pick(LINES, lore["orientacion"], "orientacion", rid)}
    elif t == "costa-a-costa":
        out = {"type": "coast-to-coast", "zone": z(lore["region"]), "axis": "west-east"}
    elif t == "solo-linda":
        out = {"type": "only-borders", "zone": z(lore["region"]), "with": [z(x) for x in lore["con"]]}
    elif t == "lindan":
        out = {"type": "borders", "a": z(lore["a"]), "b": z(lore["b"])}
    elif t == "cierra-por":
        out = {"type": "closes-by", "zone": z(lore["region"]), "edge": _pick(DIRS, lore["borde"], "borde", rid),
               "by": z(lore["por"]), "min": lore["minimo"]}
    elif t == "adelgaza":
        out = {"type": "narrows", "zone": z(lore["region"]), "toward": _pick(DIRS, lore["hacia"], "direccion", rid),
               "between": [z(x) for x in lore["entre"]], "and": [z(x) for x in lore["y"]], "max": lore["maximo"]}
    elif t == "corredor":
        out = {"type": "corridor", "from": z({"provincia": lore["desde"]["provincia"]}), "to": z(lore["hasta"]),
               "along": z(lore["bordea"]), "side": _pick(DIRS, lore["lado"], "lado", rid)}
    elif t == "dentro-de":
        out = {"type": "inside", "landmass": z({"continente": lore["continente"]}),
               "zones": [z(x) for x in lore["regiones"]]}
    elif t == "sin-tierra-fuera":
        out = {"type": "no-land-outside", "landmasses": [z({"continente": c}) for c in lore["continentes"]],
               "name": lore["nombre"]}
    elif t == "borde-norte":
        out = {"type": "edge", "landmass": z({"continente": lore["continente"]}), "side": "north"}
    else:
        raise MapError("unknown_type", f"tipo de regla {t!r} desconocido (regla {rid})", {"id": rid, "type": t})
    return {"id": rid, "text": lore["texto"], "source": lore["fuente"], **out}


def _measure(m: dict, n: _Names) -> dict:
    kind = m["que"]
    if kind == "distancia":
        a, b = m["lugares"]
        label = m.get("lore") or f"{a} -> {b}"
        rid = ("distance-" + _slug(label))[:64].strip("-")
        out = {"type": "distance", "places": [n.place(a, rid), n.place(b, rid)]}
        text = f"Distancia {label}: {a} y {b}"
    else:
        name = m.get("continente") or m["region"]
        typ = {"area": "area", "envolvente": "extent", "forma": "shape"}[kind]
        rid = f"{typ}-{_slug(name)}"[:64].strip("-")
        out = {"type": typ, "zone": n.zone({"continente": name} if "continente" in m else name, rid)}
        text = f"{ {'area': 'Área', 'extent': 'Envolvente', 'shape': 'Forma'}[typ] } de {name}"
    if "valor" in m:
        out["value"] = m["valor"]
    if "rango" in m:
        out["range"] = m["rango"]
    if m.get("nota"):
        text += f". {m['nota']}"
    return {"id": rid, "text": text, "source": m["fuente"], **out}


def convert(lore: dict, canon: dict, doc: dict) -> dict:
    """``gworld.maprules/0`` de las reglas de ``lore`` y las medidas de ``canon`` sobre el mapa ``doc``."""
    n = _Names(doc)
    rules = [_rule(r, n) for r in lore["reglas"]]
    undecided = [_rule(r, n) for r in lore.get("sinDecidir", [])]
    used = {r["id"] for r in rules + undecided}
    measures = [_measure(m, n) for m in canon["medidas"]]
    free = [_measure(m, n) for m in canon.get("sinDecidir", [])]
    for r in measures + free:  # los ids generados que chocan reciben -2, -3...
        base, k = r["id"], 1
        while r["id"] in used:
            k += 1
            r["id"] = f"{base[:64 - len(str(k)) - 1].strip('-')}-{k}"
        used.add(r["id"])
    rules += measures
    undecided += free
    out = {"kind": "gworld.maprules/0", "map": doc["origin"]["sha256"], "tolerance": canon["tolerancia"],
           "rules": rules}
    if undecided:
        out["undecided"] = undecided
    errors = validate(out, load_schema("gworld.maprules/0"))
    if errors:
        e = errors[0]
        raise MapError("schema", f"la salida no cumple gworld.maprules/0: {e.path or '/'} {e.code} {e.params}",
                       [(x.path, x.code) for x in errors])
    bind(out, doc)
    return out


def convert_dir(wmf: "str | Path") -> dict:
    """Importa ``Helek_World.map`` de la carpeta de WMF y convierte sus reglas (solo lectura)."""
    base = Path(wmf)
    lore = json.loads((base / LORE_FILE).read_text(encoding="utf-8"))
    canon = json.loads((base / CANON_FILE).read_text(encoding="utf-8"))
    return convert(lore, canon, FmgImporter().import_map(base / MAP_FILE))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wmf", required=True, help="carpeta de World-Maker-Fantasy (solo lectura)")
    ap.add_argument("--out", required=True, help="gworld.maprules/0 que se escribe")
    args = ap.parse_args(argv)
    if Path(args.out).resolve().is_relative_to(Path(args.wmf).resolve()):
        print(f"error: --out {args.out} cae dentro de --wmf {args.wmf} (WMF es solo lectura)", file=sys.stderr)
        return 1
    try:
        rules = convert_dir(args.wmf)
    except (MapError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
