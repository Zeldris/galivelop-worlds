"""Troceado del canon en fragmentos para el RAG (RAG-1; ADR 0006).

Parte cada ``Fact`` (``gworld.canon``) en ``Chunk`` de como mucho ``max_words`` palabras (palabra =
trozo entre espacios en blanco, como ``str.split()``). No calcula embeddings ni usa almacén.

Troceo: un hecho que cabe es un solo ``Chunk``. Si no, se parte por párrafos (separados por líneas en
blanco); un párrafo que pasa del tope se parte por frases (tras ``.``, ``!``, ``?`` o ``…``) y una frase
que aún pasa, por palabras. Las piezas se agrupan en orden, sin pasarse del tope, y se unen con el
separador que tenían (``\\n\\n`` entre párrafos, el espacio en blanco original entre frases, un espacio
entre palabras). El texto de cada ``Chunk`` no lleva espacios en blanco en los extremos. Un hecho sin
palabras no da ``Chunk``.

Id: ``"chunk:" + sha256(JSON [fact_id, n, texto])[:32]``, con ``n`` el orden (desde 0) del fragmento en
su hecho. Mismo canon, mismos ids; cambiar un hecho cambia solo los ids de sus fragmentos.

``max_words`` que no es un ``int`` mayor que 0 (un ``bool`` tampoco vale) falla con ``ChunkError``.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Iterable

from gworld.canon import Fact

_PARAGRAPH = re.compile(r"(\n[ \t]*\n\s*)")
_SENTENCE = re.compile(r"(?<=[.!?…])(\s+)")
_LINE = re.compile(r"(\n)")


class ChunkError(ValueError):
    """Parámetro inválido al trocear."""


@dataclass(frozen=True)
class Chunk:
    id: str
    fact_id: str
    n: int
    text: str

    def to_json(self) -> dict:
        return {"id": self.id, "fact_id": self.fact_id, "n": self.n, "text": self.text}


def _chunk_id(fact_id: str, n: int, text: str) -> str:
    key = json.dumps([fact_id, n, text], ensure_ascii=False)
    return "chunk:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


def _words(text: str) -> int:
    return len(text.split())


def _pieces(text: str, pattern: "re.Pattern[str]") -> list[tuple[str, str]]:
    """(separador previo, trozo) de cada trozo no vacío; el primero lleva separador vacío."""
    parts = pattern.split(text)
    out: list[tuple[str, str]] = []
    sep = ""
    for i, part in enumerate(parts):
        if i % 2:
            sep = part
        elif part.strip():
            out.append((sep if out else "", part.strip()))
            sep = ""
    return out


def _units(text: str, max_words: int) -> list[tuple[str, str]]:
    """Piezas de como mucho ``max_words`` palabras, con su separador previo, en orden."""
    if _words(text) <= max_words:
        return [("", text)]
    out: list[tuple[str, str]] = []
    for pattern in (_PARAGRAPH, _SENTENCE, _LINE):
        pieces = _pieces(text, pattern)
        if len(pieces) > 1:
            for i, (sep, piece) in enumerate(pieces):
                sub = _units(piece, max_words)
                out += [((sep if j == 0 else s) if i or j else "", t) for j, (s, t) in enumerate(sub)]
            return out
    words = text.split()
    return [("" if i == 0 else " ", " ".join(words[i:i + max_words])) for i in range(0, len(words), max_words)]


def chunk_facts(facts: Iterable[Fact], max_words: int = 200) -> tuple[Chunk, ...]:
    if isinstance(max_words, bool) or not isinstance(max_words, int) or max_words < 1:
        raise ChunkError(f"max_words debe ser un entero mayor que 0, no {max_words!r}")
    chunks: list[Chunk] = []
    for fact in facts:
        text = fact.text.strip()
        if not text:
            continue
        groups: list[str] = []
        size = 0
        for sep, piece in _units(text, max_words):
            w = _words(piece)
            if groups and size + w <= max_words:
                groups[-1] += sep + piece
                size += w
            else:
                groups.append(piece)
                size = w
        for n, body in enumerate(groups):
            chunks.append(Chunk(_chunk_id(fact.id, n, body), fact.id, n, body))
    return tuple(chunks)
