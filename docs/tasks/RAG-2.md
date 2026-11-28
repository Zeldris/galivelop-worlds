# RAG-2 · Interfaces Store y Embedder

## Goal

Fijar los contratos del RAG (ADR 0006): `Embedder` y `Store`, con modelo y versión en el índice y un extra ausente
que falla con la orden que lo instala. Sin implementaciones (SQLite y Ollama son RAG-3).

## Scope

`gworld/rag.py` (nuevo) y `tests/test_rag.py` (nuevo). Solo stdlib; usa `Chunk` de `gworld/chunks.py` sin cambiarlo.

## Acceptance

- [x] `Embedder` abstracto con `model`, `version`, `meta` y `embed`; `embed_checked` comprueba cantidad, longitud
  común y valores finitos.
- [x] `Store` abstracto (`meta`, `add`, `search`, `clear`); `check_meta` falla con `IndexMismatchError` que pide
  reindexar si el modelo o la versión difieren (invariante 12).
- [x] `require_extra(módulo, extra)` falla con `MissingExtraError` (un `ImportError`) que nombra el extra y
  `pip install "gworld[extra]"`; un fallo interno del módulo no se disfraza de extra (invariante 13).
- [x] Importar `gworld.rag` no trae ningún extra.

## Files

`gworld/rag.py`, `tests/test_rag.py`, `docs/plan.md` (marca de RAG-2), `docs/handoff.md`.

## Change log

- `gworld/rag.py`: `Embedder`, `Store`, `IndexMeta`, `Hit`, `cosine`, `require_extra` y los errores `RagError`,
  `MissingExtraError`, `IndexMismatchError`, `EmbedError`.
- `tests/test_rag.py`: 12 pruebas (contrato con un `Store` en memoria, forma de los vectores, extra ausente).

## Verification

`python3 -m unittest discover -s tests -t .` en verde; los tests nuevos fallan sin `gworld/rag.py`
(`red-without-fix.sh`).

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
