"""Interfaces del RAG: ``Embedder`` y ``Store`` (RAG-2; ADR 0006, invariantes 12 y 13).

Solo contratos y utilidades de stdlib: ninguna implementación (SQLite y Ollama llegan en RAG-3).

- ``Embedder``: convierte textos en vectores y declara ``model`` y ``version``.
- ``Store``: guarda ``Chunk`` con su vector y busca por coseno. El índice recuerda el ``IndexMeta``
  (modelo y versión) con que se hizo; ``check_meta`` falla con ``IndexMismatchError`` si se consulta o
  se añade con otro y pide reindexar (invariante 12).
- ``require_extra``: importa un módulo opcional; si falta, ``MissingExtraError`` nombra el extra y la
  orden que lo instala (invariante 13).
"""

import importlib
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from gworld.chunks import Chunk

Vector = tuple[float, ...]


class RagError(Exception):
    """Error base del RAG."""


class MissingExtraError(RagError, ImportError):
    """Falta un paquete opcional; el mensaje trae la orden que lo instala."""


class IndexMismatchError(RagError):
    """El índice se hizo con otro modelo o versión de embeddings: hay que reindexar."""


class EmbedError(RagError):
    """El ``Embedder`` no devolvió lo pedido."""


@dataclass(frozen=True)
class IndexMeta:
    model: str
    version: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


def require_extra(module: str, extra: str):
    """Importa ``module``; si falta, ``MissingExtraError`` con ``pip install "gworld[extra]"``."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        # falta el extra si lo ausente es ``module`` o uno de sus paquetes padre (``a`` o ``a.b`` de ``a.b.c``);
        # cualquier otro nombre es un import interno roto y se relanza tal cual
        if exc.name is not None and not (module == exc.name or module.startswith(exc.name + ".")):
            raise
        raise MissingExtraError(
            f"falta el paquete '{module}' del extra '{extra}': instálalo con: pip install \"gworld[{extra}]\""
        ) from exc


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Similitud coseno; vectores de otra longitud o de norma 0 dan ``EmbedError``."""
    if len(a) != len(b):
        raise EmbedError(f"vectores de longitud distinta: {len(a)} y {len(b)}")
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        raise EmbedError("vector de norma 0: no hay coseno")
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


class Embedder(ABC):
    model: str
    version: str

    @property
    def meta(self) -> IndexMeta:
        return IndexMeta(self.model, self.version)

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[Vector]:
        """Un vector por texto, en el mismo orden y todos de la misma longitud."""

    def embed_checked(self, texts: Sequence[str]) -> list[Vector]:
        """``embed`` con la forma comprobada: ``len(texts)`` vectores finitos de igual longitud."""
        out = [tuple(float(x) for x in v) for v in self.embed(texts)]
        if len(out) != len(texts):
            raise EmbedError(f"se pidieron {len(texts)} vectores y llegaron {len(out)}")
        if len({len(v) for v in out}) > 1:
            raise EmbedError("los vectores no tienen todos la misma longitud")
        if any(not math.isfinite(x) for v in out for x in v):
            raise EmbedError("un vector trae valores no finitos")
        return out


class Store(ABC):
    @abstractmethod
    def meta(self) -> "IndexMeta | None":
        """Modelo y versión del índice, o ``None`` si está vacío y sin estrenar."""

    @abstractmethod
    def add(self, meta: IndexMeta, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        """Guarda los fragmentos con sus vectores (mismo id: se sustituye). Falla con
        ``IndexMismatchError`` si ``meta`` difiere del del índice."""

    @abstractmethod
    def search(self, meta: IndexMeta, vector: Vector, k: int) -> list[Hit]:
        """Los ``k`` fragmentos más cercanos por coseno, de mayor a menor ``score``. Falla con
        ``IndexMismatchError`` si ``meta`` difiere del del índice."""

    @abstractmethod
    def clear(self) -> None:
        """Vacía el índice y olvida su ``IndexMeta`` (el paso previo a reindexar con otro modelo)."""

    def check_meta(self, meta: IndexMeta) -> None:
        have = self.meta()
        if have is not None and have != meta:
            raise IndexMismatchError(
                f"el índice se hizo con {have.model} {have.version} y se usa {meta.model} {meta.version}: "
                "reindexa (vacía el índice y vuelve a indexar el canon)"
            )
