# RAG-3 · Store SQLite y Embedder Ollama con grun.lock/1

## Goal

Las implementaciones por defecto de los contratos de RAG-2 (ADR 0006 y su revisión del 2026-11-28): un `Store` en
SQLite con coseno en Python y un `Embedder` que llama a Ollama (`bge-m3`) tomando el candado de máquina con el
protocolo `grun.lock/1`. Modelo y versión quedan guardados en el índice (invariante 12). Todo stdlib (invariante 13).

## Scope

- `gworld/machine_lock.py` (nuevo): candado de máquina según
  `galivelop-runtime/docs/protocol/grun.lock.1.md` (ruta `<estado>/gpu.lock` por `GALIVELOP_STATE_HOME`,
  `XDG_STATE_HOME/galivelop`, `~/.local/state/galivelop`; `mkdir -p`; `fcntl.flock` `LOCK_EX | LOCK_NB` sondeando
  cada 0,05 s, tope por defecto 120 s y `LockBusyError` al vencer; registro del titular `grun.lock/1` de una línea
  como en grun, escrito sin reemplazar el archivo y truncado al soltar; nunca borra ni sustituye el archivo; abrirlo
  no es «libre» si falla). Sin `fcntl` (fuera de POSIX), error claro.
- `gworld/ollama.py` (nuevo): `OllamaEmbedder(model="bge-m3", base_url=$OLLAMA_BASE_URL o http://localhost:11434)`.
  `version` = digest del modelo en `GET /api/tags` (falta el modelo: `EmbedError` que dice `ollama pull <modelo>`).
  `embed` toma el candado y hace `POST /api/embed` con `{"model", "input": [textos]}`; respuesta `embeddings`.
  Errores de red, HTTP o JSON dan `EmbedError` con el motivo. Solo `urllib`.
- `gworld/sqlite_store.py` (nuevo): `SqliteStore(path)`. Tablas de meta (modelo, versión, dimensión) y de fragmentos
  (id, fact_id, n, text, vector). El primer `add` fija el meta en la misma transacción que las filas. Mismo id:
  se sustituye. `search` ordena por `score` descendente y, a igualdad, por id.
- Contrato de `Store` fijado en `gworld/rag.py` y comprobado por una suite reutilizable (`tests/store_contract.py`)
  que corre contra el `MemStore` de los tests y contra `SqliteStore`: `len(chunks) != len(vectors)` y una dimensión
  distinta de la del índice fallan; `k <= 0` falla; `add` vacío no fija meta.
- Leves de la revisión de RAG-2 (`docs/records/pending.md`): `embed_checked` (vector vacío y elementos no numéricos
  dan `EmbedError`), `cosine` sin desbordar (`math.hypot`, resultado no finito rechazado), `Embedder.model` y
  `version` obligatorios en las subclases, `IndexMeta` con campos vacíos rechazados.

Fuera: `index`/`retrieve` (RAG-4), pgvector, el tamaño de los fragmentos en tokens.

## Acceptance

- [x] `machine_lock` excluye a otro proceso que tenga el candado (prueba con un hijo que lo toma) y vence con
  `LockBusyError`; respeta el orden de rutas; no borra el archivo; escribe y trunca el registro.
- [x] `OllamaEmbedder` contra un servidor HTTP falso local: vectores, versión por digest, modelo ausente, error HTTP;
  la llamada a `/api/embed` ocurre con el candado tomado.
- [x] `SqliteStore` pasa la suite de contrato, persiste entre aperturas (meta incluido) y consultar con otro modelo
  pide reindexar.
- [x] Importar `gworld.rag`, `gworld.sqlite_store` y `gworld.ollama` no trae nada fuera de stdlib.
- [x] Los tests nuevos fallan sin su arreglo (`red-without-fix.sh`).

## Files

`gworld/machine_lock.py`, `gworld/ollama.py`, `gworld/sqlite_store.py`, `gworld/rag.py`, `tests/store_contract.py`,
`tests/test_machine_lock.py`, `tests/test_ollama.py`, `tests/test_sqlite_store.py`, `tests/test_rag.py`,
`docs/plan.md`, `docs/records/pending.md`, `docs/handoff.md`.

## Change log

- `gworld/machine_lock.py`: `grun.lock/1` con stdlib (`hold`, `busy`, `holder`, `lock_path`; `LockBusyError`,
  `LockUnavailableError`, `MachineLockError` sobre `RagError`); regla de Flatpak como `grun/paths.py`.
- `gworld/ollama.py`: `OllamaEmbedder` (`model` y `version` son propiedades; `version` consulta `/api/tags` en cada
  lectura, sin caché); `embed` toma el candado y llama a `/api/embed`; `lock_timeout` y `timeout` configurables.
- `gworld/sqlite_store.py`: `SqliteStore`; tablas `meta(key, value)` con `model`/`version`/`dim` y
  `chunks(id, fact_id, n, text, vector)`; vector = `dim` dobles little-endian (`struct`); `add` y `clear` en una
  transacción (`BEGIN IMMEDIATE`).
- `gworld/rag.py`: `StoreError(RagError, ValueError)`, `Store.dimension()`, `check_add`/`check_search`; `Embedder.model`
  y `version` propiedades abstractas; `IndexMeta` rechaza campos vacíos; `cosine` normaliza con `math.hypot` y
  rechaza lo no finito; `embed_checked` rechaza vectores vacíos y no numéricos con `EmbedError`.
- Tests: `tests/store_contract.py` (mixin), `test_sqlite_store.py`, `test_ollama.py`, `test_machine_lock.py`,
  `test_rag.py` (MemStore al contrato). Retirados de `pending.md` los leves y la observación de la revisión de RAG-2.

## Verification

- `python3 -m unittest discover -s tests -t .` en verde; `md-links.py`, `agent-map.py`, `tests-after-main.py` en verde.
- `red-without-fix.sh "python3 -m unittest tests.test_sqlite_store tests.test_ollama tests.test_machine_lock"
  gworld/sqlite_store.py gworld/ollama.py gworld/machine_lock.py`: rojo sin el arreglo, verde con él.
- Sin Ollama real ni estado real: servidor HTTP falso y `GALIVELOP_STATE_HOME` temporal. Pendiente de la persona: una
  prueba con Ollama real y `bge-m3` en la máquina.

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
