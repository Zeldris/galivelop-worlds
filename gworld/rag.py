"""Interfaces del RAG: ``Embedder`` y ``Store`` (RAG-2; ADR 0006, invariantes 12 y 13).

Solo contratos y utilidades de stdlib. Las implementaciones por defecto (RAG-3) viven en
``gworld.sqlite_store`` y ``gworld.ollama``.

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


class StoreError(RagError, ValueError):
    """Argumentos que el ``Store`` no admite (longitudes, dimensión o ``k`` fuera de contrato)."""


@dataclass(frozen=True)
class IndexMeta:
    model: str
    version: str

    def __post_init__(self):
        for name in ("model", "version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise RagError(f"IndexMeta.{name} tiene que ser un texto no vacío, no {value!r}")


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
    """Similitud coseno; vectores de otra longitud o de norma 0 dan ``EmbedError``, y un resultado no finito
    (valores enormes) también. Se normaliza antes de multiplicar para no desbordar."""
    if len(a) != len(b):
        raise EmbedError(f"vectores de longitud distinta: {len(a)} y {len(b)}")
    na = math.hypot(*a)
    nb = math.hypot(*b)
    if na == 0 or nb == 0:
        raise EmbedError("vector de norma 0: no hay coseno")
    if not (math.isfinite(na) and math.isfinite(nb)):
        raise EmbedError("vector de norma no finita: no hay coseno")
    result = sum((x / na) * (y / nb) for x, y in zip(a, b))
    if not math.isfinite(result):
        raise EmbedError("el coseno no es finito")
    return result


class Embedder(ABC):
    """Convierte textos en vectores. Las subclases declaran ``model`` y ``version`` (atributo de clase o
    propiedad); sin ellos no se pueden instanciar."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Nombre del modelo de embeddings."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Versión del modelo (p. ej. su digest): cambia si el modelo cambia."""

    @property
    def meta(self) -> IndexMeta:
        return IndexMeta(self.model, self.version)

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[Vector]:
        """Un vector por texto, en el mismo orden y todos de la misma longitud."""

    def embed_checked(self, texts: Sequence[str]) -> list[Vector]:
        """``embed`` con la forma comprobada: ``len(texts)`` vectores no vacíos, numéricos, finitos y de igual
        longitud."""
        raw = self.embed(texts)
        try:
            out = [tuple(float(x) for x in v) for v in raw]
        except (TypeError, ValueError, OverflowError) as exc:
            raise EmbedError(f"un vector trae elementos no numéricos: {exc}") from exc
        if len(out) != len(texts):
            raise EmbedError(f"se pidieron {len(texts)} vectores y llegaron {len(out)}")
        if any(len(v) == 0 for v in out):
            raise EmbedError("un vector llegó vacío")
        if len({len(v) for v in out}) > 1:
            raise EmbedError("los vectores no tienen todos la misma longitud")
        if any(not math.isfinite(x) for v in out for x in v):
            raise EmbedError("un vector trae valores no finitos")
        return out


class Store(ABC):
    """Almacén de fragmentos con vector. Contrato (lo comprueba ``tests/store_contract.py``):

    - ``add``: ``len(chunks) != len(vectors)`` o una dimensión distinta de la del índice (o vectores de
      distinta longitud entre sí) fallan con ``StoreError`` sin guardar nada; mismo id sustituye; un ``add``
      vacío no fija el meta; el primer ``add`` con filas fija el meta y la dimensión en el mismo paso que
      las filas (todo o nada).
    - ``search``: ``k <= 0`` falla con ``StoreError``; un vector de otra dimensión, también; el resultado va
      de mayor a menor ``score`` y, a igualdad, por id.
    - Otro ``meta`` que el del índice falla con ``IndexMismatchError`` en ambos.
    """

    @abstractmethod
    def meta(self) -> IndexMeta | None:
        """Modelo y versión del índice, o ``None`` si está vacío y sin estrenar."""

    @abstractmethod
    def dimension(self) -> int | None:
        """Longitud de los vectores del índice, o ``None`` si está vacío y sin estrenar."""

    @abstractmethod
    def add(self, meta: IndexMeta, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        """Guarda los fragmentos con sus vectores (mismo id: se sustituye). Falla con
        ``IndexMismatchError`` si ``meta`` difiere del del índice y con ``StoreError`` si la forma es mala."""

    @abstractmethod
    def search(self, meta: IndexMeta, vector: Vector, k: int) -> list[Hit]:
        """Los ``k`` fragmentos más cercanos por coseno, de mayor a menor ``score`` (a igualdad, por id).
        Falla con ``IndexMismatchError`` si ``meta`` difiere del del índice y con ``StoreError`` si ``k <= 0``
        o la dimensión no es la del índice."""

    @abstractmethod
    def clear(self) -> None:
        """Vacía el índice y olvida su ``IndexMeta`` (el paso previo a reindexar con otro modelo)."""

    def check_add(self, meta: IndexMeta, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> int | None:
        """Valida un ``add`` antes de guardar y devuelve la dimensión de los vectores (``None`` si no hay)."""
        self.check_meta(meta)
        if len(chunks) != len(vectors):
            raise StoreError(f"{len(chunks)} fragmentos y {len(vectors)} vectores: tienen que ser tantos como tantos")
        dims = {len(v) for v in vectors}
        if not dims:
            return None
        if len(dims) > 1 or 0 in dims:
            raise StoreError("los vectores tienen que ser no vacíos y de la misma longitud")
        (dim,) = dims
        have = self.dimension()
        if have is not None and have != dim:
            raise StoreError(f"los vectores tienen dimensión {dim} y el índice {have}: reindexa si cambió el modelo")
        return dim

    def check_search(self, meta: IndexMeta, vector: Sequence[float], k: int) -> None:
        """Valida un ``search`` antes de consultar."""
        self.check_meta(meta)
        if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
            raise StoreError(f"k tiene que ser un entero mayor que 0, no {k!r}")
        have = self.dimension()
        if have is not None and len(vector) != have:
            raise StoreError(f"el vector de consulta tiene dimensión {len(vector)} y el índice {have}")

    def check_meta(self, meta: IndexMeta) -> None:
        have = self.meta()
        if have is not None and have != meta:
            raise IndexMismatchError(
                f"el índice se hizo con {have.model} {have.version} y se usa {meta.model} {meta.version}: "
                "reindexa (vacía el índice y vuelve a indexar el canon)"
            )
