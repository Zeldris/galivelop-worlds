"""``Store`` en SQLite con coseno en Python (RAG-3; ADR 0006). Solo ``sqlite3`` de stdlib.

Tablas:

- ``meta(key, value)``: ``model``, ``version`` y ``dim`` del índice (vacía = índice sin estrenar).
- ``chunks(id PRIMARY KEY, fact_id, n, text, vector)``: ``vector`` son ``dim`` dobles little-endian (``struct``).

El primer ``add`` con filas escribe el meta en la misma transacción que ellas: o entra todo o nada.
"""

import sqlite3
import struct
from typing import Sequence

from gworld.chunks import Chunk
from gworld.rag import Hit, IndexMeta, Store, Vector, cosine

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY, fact_id TEXT NOT NULL, n INTEGER NOT NULL, text TEXT NOT NULL, vector BLOB NOT NULL);
"""


def _pack(v: Sequence[float]) -> bytes:
    return struct.pack(f"<{len(v)}d", *v)


def _unpack(b: bytes) -> Vector:
    return struct.unpack(f"<{len(b) // 8}d", b)


class SqliteStore(Store):
    def __init__(self, path):
        self._db = sqlite3.connect(str(path), isolation_level=None)  # transacciones explícitas
        self._db.executescript(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _meta_dict(self) -> dict:
        return dict(self._db.execute("SELECT key, value FROM meta"))

    def meta(self) -> IndexMeta | None:
        m = self._meta_dict()
        return IndexMeta(m["model"], m["version"]) if "model" in m else None

    def dimension(self) -> int | None:
        m = self._meta_dict()
        return int(m["dim"]) if "dim" in m else None

    def add(self, meta: IndexMeta, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            dim = self.check_add(meta, chunks, vectors)
            if dim is not None:
                self._db.executemany(
                    "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                    [("model", meta.model), ("version", meta.version), ("dim", str(dim))])
                self._db.executemany(
                    "INSERT OR REPLACE INTO chunks (id, fact_id, n, text, vector) VALUES (?, ?, ?, ?, ?)",
                    [(c.id, c.fact_id, c.n, c.text, _pack(v)) for c, v in zip(chunks, vectors)])
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def search(self, meta: IndexMeta, vector: Vector, k: int) -> list[Hit]:
        self.check_search(meta, vector, k)
        hits = [Hit(Chunk(id=i, fact_id=f, n=n, text=t), cosine(vector, _unpack(b)))
                for i, f, n, t, b in self._db.execute("SELECT id, fact_id, n, text, vector FROM chunks")]
        hits.sort(key=lambda h: (-h.score, h.chunk.id))
        return hits[:k]

    def clear(self) -> None:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            self._db.execute("DELETE FROM chunks")
            self._db.execute("DELETE FROM meta")
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise
