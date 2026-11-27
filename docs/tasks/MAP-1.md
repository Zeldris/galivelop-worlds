# MAP-1 · Esquema `gworld.map/0` con origen

## Goal

Esquema gart del mapa importado: celdas, vecinas, zonas, rutas, ríos y geometría, con su origen (archivo y huella)
obligatorio.

## Scope

Solo el esquema y su registro en `load_schema`; referencias que existan y conexidad son de MAP-3.

## Acceptance

- [x] Un mapa mínimo valida; sin origen o huella falla con ruta y código `required`.
- [x] Una vecina o zona mal formada falla con su ruta y código.

## Files

- `gworld/schemas/map-0.json`, `gworld/schemas/__init__.py`
- `tests/test_schema_map.py`, `.claude/gw.json` (testMap)
- `docs/ddd.md`, `docs/plan.md`

## Change log

- 2026-11-27: esquema creado. Decisión: celdas con id entero (índice del origen), zonas `<capa>:<índice>`,
  vértices compartidos citados por índice (forma del `helek.json` de WMF), `attrs` libres para lo propio del origen.

## Verification

`python3 -m unittest tests.test_schema_map`; `red-without-fix.sh` en rojo sin `map-0.json`.

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
