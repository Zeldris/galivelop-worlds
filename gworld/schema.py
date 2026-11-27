"""Comprobación mínima de esquemas en formato gart (subconjunto de JSON Schema).

Se cambiará por la copia vendorizada de gart (decisión D4); la API imita la prevista allí:
``validate``, ``check_schema``, ``ValidationError``, ``SchemaError``, ``KIND_ID_RE`` e ``is_kind_id``.
Falla cerrado: una palabra clave desconocida, un ``$ref`` remoto, ``format`` o un valor mal formado
en el esquema es ``SchemaError``, nunca se ignora.
"""

import re
from dataclasses import dataclass, field
from typing import Any

KIND_ID_RE = r"^[a-z][a-z0-9]*\.[a-z][a-z0-9_.]*/(0|[1-9][0-9]*)$"
_KIND_ID = re.compile(KIND_ID_RE)

_ANNOTATIONS = {"$schema", "$id", "$comment", "title", "description", "default", "examples"}
_KEYWORDS = _ANNOTATIONS | {
    "type", "properties", "required", "additionalProperties", "propertyNames", "minProperties",
    "items", "minItems", "maxItems", "enum", "const", "pattern", "minLength", "maxLength",
    "minimum", "maximum", "$ref", "$defs",
}
_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


class SchemaError(Exception):
    """El esquema no es válido en este subconjunto."""


@dataclass(frozen=True)
class ValidationError:
    path: str
    code: str
    params: dict = field(default_factory=dict)


def is_kind_id(s: Any) -> bool:
    return isinstance(s, str) and _KIND_ID.fullmatch(s) is not None


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _resolve(root: Any, ref: str) -> Any:
    if ref == "#":
        return root
    if not ref.startswith("#/"):
        raise SchemaError(f"$ref no local o mal formado: {ref!r}")
    node = root
    for raw in ref[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        else:
            raise SchemaError(f"$ref sin destino: {ref!r}")
    return node


def check_schema(schema: Any) -> None:
    """Lanza SchemaError si el esquema no es válido; recorre todo, también ``$defs``."""
    _check(schema, schema, "")


def _check(node: Any, root: Any, where: str) -> None:
    at = where or "/"
    if not isinstance(node, dict):
        raise SchemaError(f"el esquema en {at} debe ser un objeto")
    for key in sorted(node):
        if key not in _KEYWORDS:
            raise SchemaError(f"palabra clave no admitida {key!r} en {at}")
    for key in sorted(node):
        value = node[key]
        here = f"{where}/{_escape(key)}"
        if key == "type":
            names = [value] if isinstance(value, str) else value
            if (not isinstance(names, list) or not names
                    or any(not isinstance(n, str) or n not in _TYPES for n in names)):
                raise SchemaError(f"type mal formado en {here}: {value!r}")
        elif key == "properties" or key == "$defs":
            if not isinstance(value, dict):
                raise SchemaError(f"{key} debe ser un objeto en {here}")
            for name in sorted(value):
                _check(value[name], root, f"{here}/{_escape(name)}")
        elif key == "required":
            if not isinstance(value, list) or any(not isinstance(n, str) for n in value):
                raise SchemaError(f"required debe ser una lista de cadenas en {here}")
        elif key == "additionalProperties":
            if not isinstance(value, bool):
                _check(value, root, here)
        elif key in ("propertyNames", "items"):
            _check(value, root, here)
        elif key in ("minProperties", "minItems", "maxItems", "minLength", "maxLength"):
            if not _is_int(value) or value < 0:
                raise SchemaError(f"{key} debe ser un entero >= 0 en {here}")
        elif key == "enum":
            if not isinstance(value, list) or not value:
                raise SchemaError(f"enum debe ser una lista no vacía en {here}")
        elif key == "pattern":
            if not isinstance(value, str):
                raise SchemaError(f"pattern debe ser una cadena en {here}")
            try:
                re.compile(value)
            except re.error as exc:
                raise SchemaError(f"pattern no compila en {here}: {exc}") from exc
        elif key in ("minimum", "maximum"):
            if not _is_num(value):
                raise SchemaError(f"{key} debe ser un número en {here}")
        elif key == "$ref":
            if not isinstance(value, str) or not (value == "#" or re.fullmatch(r"#/\$defs/[^/]+", value)):
                raise SchemaError(f"$ref local: solo puede ser '#' o '#/$defs/<nombre>': {value!r} en {here}")
            seen = set()
            target = _resolve(root, value)
            ref = value
            while isinstance(target, dict) and "$ref" in target:
                if ref in seen:
                    raise SchemaError(f"$ref circular sin avanzar: {value!r}")
                seen.add(ref)
                ref = target["$ref"]
                if not isinstance(ref, str):
                    raise SchemaError(f"$ref mal formado en {here}")
                target = _resolve(root, ref)
            if not isinstance(target, dict):
                raise SchemaError(f"$ref {value!r} no apunta a un esquema")
        # const y las anotaciones admiten cualquier valor


def _eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        return False
    return a == b


def _type_ok(value: Any, name: str) -> bool:
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "integer":
        return _is_int(value)
    if name == "number":
        return _is_num(value)
    if name == "boolean":
        return isinstance(value, bool)
    return value is None


def validate(artifact: Any, schema: Any) -> list[ValidationError]:
    """Errores del artefacto frente al esquema; solo lanza SchemaError si el esquema es malo."""
    check_schema(schema)
    errors: list[ValidationError] = []
    _walk(artifact, schema, schema, "", errors)
    return errors


def _walk(data: Any, sch: dict, root: dict, path: str, out: list[ValidationError]) -> None:
    def err(code: str, **params: Any) -> None:
        out.append(ValidationError(path, code, params))

    if "$ref" in sch:
        _walk(data, _resolve(root, sch["$ref"]), root, path, out)
    if "type" in sch:
        t = sch["type"]
        names = [t] if isinstance(t, str) else t
        if not any(_type_ok(data, n) for n in names):
            err("type", expected=t)
    if "enum" in sch and not any(_eq(data, v) for v in sch["enum"]):
        err("enum", allowed=sch["enum"])
    if "const" in sch and not _eq(data, sch["const"]):
        err("const", expected=sch["const"])
    if isinstance(data, str):
        if "minLength" in sch and len(data) < sch["minLength"]:
            err("minLength", limit=sch["minLength"])
        if "maxLength" in sch and len(data) > sch["maxLength"]:
            err("maxLength", limit=sch["maxLength"])
        if "pattern" in sch and re.search(sch["pattern"], data) is None:
            err("pattern", pattern=sch["pattern"])
    if _is_num(data):
        if "minimum" in sch and data < sch["minimum"]:
            err("minimum", limit=sch["minimum"])
        if "maximum" in sch and data > sch["maximum"]:
            err("maximum", limit=sch["maximum"])
    if isinstance(data, dict):
        for name in sorted(sch.get("required", [])):
            if name not in data:
                err("required", property=name)
        props = sch.get("properties", {})
        for name in sorted(props):
            if name in data:
                _walk(data[name], props[name], root, f"{path}/{_escape(name)}", out)
        if "additionalProperties" in sch:
            extra = sch["additionalProperties"]
            for name in sorted(k for k in data if k not in props):
                if extra is False:
                    err("additionalProperties", property=name)
                elif extra is not True:
                    _walk(data[name], extra, root, f"{path}/{_escape(name)}", out)
        if "propertyNames" in sch:
            for name in sorted(data):
                for e in _sub(name, sch["propertyNames"], root):
                    out.append(ValidationError(path, "propertyNames", {"property": name, "code": e.code}))
        if "minProperties" in sch and len(data) < sch["minProperties"]:
            err("minProperties", limit=sch["minProperties"])
    if isinstance(data, list):
        if "minItems" in sch and len(data) < sch["minItems"]:
            err("minItems", limit=sch["minItems"])
        if "maxItems" in sch and len(data) > sch["maxItems"]:
            err("maxItems", limit=sch["maxItems"])
        if "items" in sch:
            for i, item in enumerate(data):
                _walk(item, sch["items"], root, f"{path}/{i}", out)


def _sub(data: Any, sch: dict, root: dict) -> list[ValidationError]:
    out: list[ValidationError] = []
    _walk(data, sch, root, "", out)
    return out
