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

## Revisión 2026-11-28 (RAG-3, Q-48 a Q-50)

- grun publicó el protocolo como `grun.lock/1` (solo cambia el campo `schema`; mismo `flock` y misma ruta): el
  `Embedder` usa `/1`.
- WMF pasó a `bge-m3` (1024 dimensiones) como modelo de embeddings por defecto: es el de gworld. `nomic-embed-text`
  sigue valiendo pasándolo a mano.
- gworld toma el candado con su propia implementación sobre `fcntl.flock` (stdlib), sin depender de grun; fuera de
  POSIX el `Embedder` de Ollama falla con un error claro.
