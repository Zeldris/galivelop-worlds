<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `claude/rag-3` (desde `ccr-8aaeec3a-h97oxt`, sesión de la nube parada según la persona el 2026-11-28) |
| **Fase / tarea** | RAG-3 hecho y con su revisión de bloque (`gworld/machine_lock.py` `grun.lock/1`, `gworld/ollama.py` `bge-m3`, `gworld/sqlite_store.py`, suite `tests/store_contract.py`; 2 medios arreglados en `abe94fc`: vectores sin valores válidos y fallos de URL de Ollama; 7 leves a pendientes). Antes: RAG-2 y RAG-1 hechos y revisados; 0.2.0 en `main` (PR #5). Presupuesto de compactaciones: 1 |
| **Último punto estable** | Revisión de bloque de RAG-3 (`Findings: 2`, `abe94fc`); antes, RAG-3 (`31d9997`) |
| **Siguiente paso** | RAG-4 (`index` y `retrieve(query, k)`; consultar con otro modelo falla y pide reindexar), mirando antes los leves de RAG-3 en pendientes que le tocan (reentrada del candado, `version` bajo el candado). Pendiente de la persona: probar `OllamaEmbedder` con Ollama real y `bge-m3`. La rama `claude/release-0.1.0` queda superada por `main` y sin uso |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

_(nada todavía: 0.3 empieza con MAP-6)_

## Hecho (5 últimas)

1. 2026-11-28 — Release `v0.2.0` publicada sobre `6c14104` (autorizada por la persona); test de Tarkor (`tests/test_tarkor_pack.py`) en verde, comprobado solo en local (Steam Deck) con `GW_WMF_DIR=../World-Maker-Fantasy` en `19f3f10d`: 518 hechos; en CI se salta.
2. 2026-11-28 — MAP-6: `gworld/maps.py` salta rutas inválidas y burgos sin nombre, `parent` solo de regiones existentes, `_C_RIVER` fuera y `_MIN_RECORDS = 45` explicado; `code_of` comprueba el mensaje.
3. 2026-11-28 — 0.2.0 publicada en `main` (PR #5, `6c14104`): versión 0.2.0 y notas en `docs/releases/v0.2.0.md`; la etiqueta y la release, pendientes de la persona.
4. 2026-11-28 — 0.2 fusionada en `main` (PR #4, `45884d4`) con el CI en verde; fase 2 aplicada (Q-35 a Q-45: notas de ahorro, `tests/wmf.py`, MAP-6 en 0.3).
5. 2026-11-27 — MAP-5: equivalencia con `map-generator/` de WMF sobre Helek (import, medidas, reglas, caminos); fixtures en `tests/fixtures/helek/`; revisión de bloque con 2 arreglos.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
