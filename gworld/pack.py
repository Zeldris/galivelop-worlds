"""Carga de un paquete de mundo: ``load_pack(path) -> WorldPack`` (PCK-4, invariante 8).

No escribe nada. Fallos como ``PackError`` con ``code`` estable: ``no_manifest``, ``bad_json``,
``schema``, ``canon_outside``, ``canon_missing``, ``canon_hash``, ``canon_special`` (FIFO, socket o dispositivo en el canon),
``canon_name`` (nombre no UTF-8), ``too_deep`` (JSON demasiado anidado), ``unreadable`` (error de E/S).
"""

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gworld.schema import validate
from gworld.schemas import load_schema


class PackError(Exception):
    def __init__(self, code: str, message: str, detail: Any = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = detail if detail is not None else message


@dataclass(frozen=True)
class Licence:
    spdx: str | None
    text: str | None
    conditions: str | None


@dataclass(frozen=True)
class PackRef:
    id: str
    version: str
    sha256: str  # huella del canon


@dataclass(frozen=True)
class WorldPack:
    root: Path
    manifest: dict
    ref: PackRef
    licence: Licence
    canon_path: Path
    rules: tuple[str, ...]


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def _read(f: Path) -> bytes:
    try:
        return f.read_bytes()
    except OSError as e:
        raise PackError("unreadable", f"no se puede leer {f}: {e}") from e


def canon_digest(path: "str | os.PathLike") -> str:
    """Huella del canon, ``"sha256:<hex>"``.

    Archivo: sha256 de sus bytes. Directorio: todos los archivos regulares bajo él (recursivo,
    sin seguir symlinks a directorios), ordenados por ruta relativa POSIX en bytes UTF-8; por
    cada uno se añade al hash ``ruta_relativa_utf8 + b"\\0" + sha256(contenido).digest()``.
    Determinista e independiente del SO. Un symlink a archivo que apunta fuera del directorio
    del canon da ``PackError('canon_outside')``.
    """
    p = Path(path)
    if p.is_file():
        return "sha256:" + hashlib.sha256(_read(p)).hexdigest()
    if p.exists() and not p.is_dir():
        raise PackError("canon_special", f"el canon {p} no es un archivo regular ni un directorio")
    base = p.resolve()
    entries: list[tuple[bytes, Path]] = []
    def onerror(e: OSError) -> None:
        raise PackError("unreadable", f"no se puede leer {e.filename}: {e}") from e

    for dirpath, dirnames, filenames in os.walk(p, followlinks=False, onerror=onerror):
        for d in dirnames:
            if Path(dirpath, d).is_symlink():
                raise PackError("canon_outside", f"el canon contiene un enlace a directorio: {Path(dirpath, d)}")
        for name in filenames:
            f = Path(dirpath, name)
            if not f.is_file():
                if f.exists():
                    raise PackError("canon_special", f"el canon contiene un archivo especial (FIFO, socket o dispositivo): {f}")
                continue
            if f.is_symlink() and not _inside(f.resolve(), base):
                raise PackError("canon_outside", f"el archivo del canon {f} apunta fuera del canon")
            try:
                rel = f.relative_to(p).as_posix().encode("utf-8")
            except UnicodeEncodeError as e:
                raise PackError("canon_name", f"nombre de archivo no UTF-8 en el canon: {str(f)!r}") from e
            entries.append((rel, f))
    entries.sort(key=lambda e: e[0])
    h = hashlib.sha256()
    for rel, f in entries:
        h.update(rel + b"\0" + hashlib.sha256(_read(f)).digest())
    return "sha256:" + h.hexdigest()


def load_pack(path: "str | os.PathLike") -> WorldPack:
    root = Path(path)
    manifest_path = root / "pack.json"
    if not root.is_dir() or not manifest_path.is_file():
        raise PackError("no_manifest", f"no hay pack.json en {root}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as e:
        raise PackError("unreadable", f"no se puede leer pack.json: {e}") from e
    except RecursionError as e:
        raise PackError("bad_json", "pack.json demasiado anidado") from e
    except (ValueError, UnicodeDecodeError) as e:
        raise PackError("bad_json", f"pack.json no es JSON válido: {e}") from e
    try:
        errors = validate(manifest, load_schema("gworld.pack/0"))
    except RecursionError as e:
        raise PackError("too_deep", "pack.json demasiado anidado para validarlo") from e
    if errors:
        desc = "; ".join(f"{e.path or '/'} {e.code} {e.params}" for e in errors)
        raise PackError("schema", f"pack.json no cumple gworld.pack/0: {desc}", errors)
    lic = manifest["licence"]
    if "spdx" not in lic and "text" not in lic:
        raise PackError("schema", "pack.json no cumple gworld.pack/0: licence exige spdx o text")

    rel = manifest["canon"]["path"]
    if "\0" in rel:
        raise PackError("canon_outside", f"canon.path {rel!r} contiene un carácter nulo")
    try:
        root_r = root.resolve()
        if Path(rel).is_absolute() or Path(rel).drive:
            raise PackError("canon_outside", f"canon.path {rel!r} es absoluta")
        canon = root / rel
        if os.path.normpath(root_r / rel) == str(root_r) or canon.resolve() == root_r:
            raise PackError("canon_outside", f"canon.path {rel!r} es la raíz del paquete")
        outside = not _inside(Path(os.path.normpath(root_r / rel)), root_r) or not _inside(canon.resolve(), root_r)
    except (ValueError, OSError) as e:
        raise PackError("canon_outside", f"canon.path {rel!r} no se puede resolver: {e}") from e
    if outside:
        raise PackError("canon_outside", f"canon.path {rel!r} sale del paquete")
    if not canon.exists():
        raise PackError("canon_missing", f"no existe el canon {rel!r}")
    expected = manifest["canon"]["sha256"]
    actual = canon_digest(canon)
    if actual != expected:
        raise PackError("canon_hash", f"la huella del canon no cuadra: esperada {expected}, real {actual}")

    return WorldPack(
        root=root,
        manifest=manifest,
        ref=PackRef(manifest["id"], manifest["version"], expected),
        licence=Licence(lic.get("spdx"), lic.get("text"), lic.get("conditions")),
        canon_path=canon,
        rules=tuple(manifest["rules"]),
    )
