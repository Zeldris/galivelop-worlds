"""Lector del canon de solo lectura (PCK-5; ADR 0005, invariantes 4 y 5).

Trocea cada ``.md`` del canon (recursivo, orden por ruta relativa POSIX en bytes UTF-8) en un ``Fact``
por sección. No escribe nada: solo ``Path.read_bytes``.

Troceo: encabezados ATX (``#`` a ``######``, hasta 3 espacios de sangría, ``#`` finales de cierre
quitados). Se ignoran los de dentro de bloques cercados (``` o ~~~). Los de Setext no cuentan. El
texto previo al primer encabezado es una sección con ``headings == []``. Cada sección lleva el texto
hasta el siguiente encabezado de cualquier nivel, sin la línea del encabezado. Las secciones de texto
vacío no dan ``Fact``.

Normalización del texto: ``\\r\\n`` y ``\\r`` pasan a ``\\n``; en cada línea los espacios y tabuladores
se colapsan en un espacio y se quitan los de los extremos; las líneas en blanco consecutivas se
reducen a una; se quitan las líneas en blanco del principio y del final. Se mantiene el resto
(mayúsculas, signos, contenido de los bloques de código).

Huella del hecho: ``"sha256:" + sha256(texto normalizado en UTF-8)``.

Id: ``"fact:" + sha256(archivo \\0 encabezados unidos por \\0 \\0 n \\0 huella_hex)[:32]``, con
``archivo`` la ruta relativa POSIX, ``n`` el número de orden (desde 0) entre las secciones del mismo
archivo con la misma ruta de encabezados (así los encabezados repetidos dan ids distintos y
estables). Cambiar el texto de una sección cambia solo su id; ``n`` solo cambia si se añade o quita
otra sección con la misma ruta antes de ella.

Fallos como ``PackError`` (``gworld.pack``): ``unreadable`` (E/S), ``bad_encoding`` (no es UTF-8),
``canon_outside`` (enlace fuera del canon), ``schema`` (el índice no cumple ``gworld.canon/0``).
"""

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from gworld.pack import PackError, WorldPack
from gworld.schema import validate
from gworld.schemas import load_schema

_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


@dataclass(frozen=True)
class Fact:
    id: str
    file: str
    headings: tuple[str, ...]
    text: str
    sha256: str

    def to_json(self) -> dict:
        return {"id": self.id, "file": self.file, "headings": list(self.headings),
                "text": self.text, "sha256": self.sha256}


def normalize(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    for line in lines:
        line = re.sub(r"[ \t]+", " ", line).strip(" ")
        if not line and (not out or not out[-1]):
            continue
        out.append(line)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def _fact_id(file: str, headings: tuple[str, ...], n: int, digest_hex: str) -> str:
    key = "\0".join([file, "\0".join(headings), str(n), digest_hex])
    return "fact:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


def split_sections(source: str) -> list[tuple[tuple[str, ...], str]]:
    """(ruta de encabezados, texto sin normalizar) de cada sección, en orden."""
    sections: list[tuple[tuple[str, ...], str]] = []
    stack: list[tuple[int, str]] = []
    buf: list[str] = []
    fence: str | None = None

    def flush() -> None:
        sections.append((tuple(t for _, t in stack), "\n".join(buf)))
        buf.clear()

    for line in source.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = _FENCE.match(line)
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and not line.strip().strip(fence[0]):
                fence = None
            buf.append(line)
            continue
        if m:
            fence = m.group(1)
            buf.append(line)
            continue
        h = _HEADING.match(line)
        if h:
            flush()
            level = len(h.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, (h.group(2) or "").strip()))
            continue
        buf.append(line)
    flush()
    return sections


def _files(path: Path) -> list[tuple[str, Path]]:
    if path.is_file():
        return [(path.name, path)]
    base = path.resolve()
    found: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        for name in filenames:
            f = Path(dirpath, name)
            if not name.endswith(".md") or not f.is_file():
                continue
            if f.is_symlink() and base not in f.resolve().parents:
                raise PackError("canon_outside", f"el archivo del canon {f} apunta fuera del canon")
            found.append((f.relative_to(path).as_posix(), f))
    found.sort(key=lambda e: e[0].encode("utf-8"))
    return found


def read_facts(path: "str | os.PathLike") -> tuple[Fact, ...]:
    """Los ``Fact`` de un directorio de canon (o de un único ``.md``), solo lectura."""
    facts: list[Fact] = []
    for rel, f in _files(Path(path)):
        try:
            source = f.read_bytes().decode("utf-8")
        except OSError as e:
            raise PackError("unreadable", f"no se puede leer {f}: {e}") from e
        except UnicodeDecodeError as e:
            raise PackError("bad_encoding", f"{f} no es UTF-8: {e}") from e
        seen: dict[tuple[str, ...], int] = {}
        for headings, raw in split_sections(source):
            n = seen.get(headings, 0)
            seen[headings] = n + 1
            text = normalize(raw)
            if not text:
                continue
            hx = hashlib.sha256(text.encode("utf-8")).hexdigest()
            facts.append(Fact(_fact_id(rel, headings, n, hx), rel, headings, text, "sha256:" + hx))
    return tuple(facts)


def canon_index(pack: WorldPack) -> dict:
    """Índice ``gworld.canon/0`` del canon del paquete, validado contra su esquema."""
    index = {
        "kind": "gworld.canon/0",
        "pack": {"id": pack.ref.id, "version": pack.ref.version, "sha256": pack.ref.sha256},
        "facts": [f.to_json() for f in read_facts(pack.canon_path)],
    }
    errors = validate(index, load_schema("gworld.canon/0"))
    if errors:
        desc = "; ".join(f"{e.path or '/'} {e.code} {e.params}" for e in errors)
        raise PackError("schema", f"el índice no cumple gworld.canon/0: {desc}", errors)
    ids = [f["id"] for f in index["facts"]]
    if len(set(ids)) != len(ids):
        raise PackError("schema", "ids de hecho repetidos")
    return index
