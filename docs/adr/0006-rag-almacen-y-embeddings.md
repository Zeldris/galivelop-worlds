# ADR 0006: almacén del RAG y embeddings

- **Estado:** aceptada (2026-11-26) · **Decisión:** D7 del [DDD](../ddd.md)

## Contexto

WMF usa pgvector con `nomic-embed-text` por Ollama; el instalador ya migró a SQLite. grun solo promete el turno de
texto; gmod recomienda modelos `embed`.

## Decisión

- `Store` como interfaz: por defecto SQLite con coseno en Python (stdlib); pgvector como extra.
- `Embedder` como interfaz: se pide a grun un turno de embeddings bajo el mismo candado; mientras, el `Embedder`
  llama a Ollama tomando el candado con el protocolo `grun.lock/0`.
- Modelo por defecto `nomic-embed-text`; el índice guarda modelo y versión, y consultar con otro falla y pide
  reindexar (invariante 12).
