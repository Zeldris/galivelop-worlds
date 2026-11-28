# MAP-2 · `MapImporter` e importador FMG 1.137.6

## Goal

Interfaz `MapImporter` e importador de Azgaar's Fantasy Map Generator 1.137.6 que produce un `gworld.map/0` válido,
reescrito desde `map-generator/importar.py` de WMF (solo lectura).

## Scope

Lectura del `.map`, rehecho de celdas y documento con origen y huella. Fuera: GeoJSON, `revisar.json`, nombres de
continente del mundo de WMF y volcado a disco (no son del importador); topología es MAP-3.

## Acceptance

- [x] Un `.map` mínimo importa y valida contra `gworld.map/0`, con huella y origen.
- [x] Versión distinta, truncado, JSON roto, descuadre y E/S fallan con `MapError` y código propio.

## Files

- `gworld/maps.py`, `gworld/_delaunay.py`
- `tests/test_maps.py`, `tests/fixtures/mini.map`
- `docs/plan.md`, `docs/handoff.md`

## Change log

- 2026-11-27: importador creado. Decisión: las celdas se rehacen con una triangulación de orden Delaunator
  (los arrays del `.map` siguen ese orden) y se comprueba con áreas de regiones y celdas de masas de tierra;
  biomas por índice (`"0"`), masas de tierra como zonas `landmass:<n>` y `origin.file.name` solo el nombre base.

## Verification

`python3 -m unittest tests.test_maps`; humo sobre `Helek_World.map` de WMF (5120 celdas) si existe.

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
