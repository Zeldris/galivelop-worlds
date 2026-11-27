# MAP-5 · Equivalencia con el `map-generator/` de WMF

## Goal

Probar que `gworld/` da lo mismo que `map-generator/` de WMF sobre Helek: el import del `.map`, las medidas contra
el canon y las reglas de mapa, con los tests de `map-generator/tests/` como oráculo.

## Scope

Pendiente de Q-31 a Q-34 (`docs/questions.md`). Inventario de los 11 tests (subagente, 2026-11-27):

| test WMF | módulo WMF | equivalente en gworld | falta | capa |
|---|---|---|---|---|
| `test_importar` | `importar.py`, `fmg/*` | `maps.FmgImporter`, `_delaunay` | cifras de Helek (5 regiones, 5 lugares, provincias en la región 18), salida estable, `mismatch` por área (19808 km²), «revisar» | mundo |
| `test_medir` | `medir.py`, `geometria.py` | `geometry`, `maprules` (`area`, `extent`, `distance`) | mutación del canon (un tercio de las Llanuras a la Ciénaga) | mundo |
| `test_comprobar` | `comprobar.py` | `maprules.check_rules`, `tools/tarkor_maprules.py` | 5 mutaciones que rompen una sola regla, `adelgaza` sin grosor | mundo |
| `test_consultar` | `consultar.py` | `Topology` (vecinos, `path`, `distance_km`) | celda por punto, frontera, costa, caminos por mar, JSON | consulta |
| `test_visor` | `servir.py` | `geometry.area_km2`, `extent_km` | solo `:66` (medidas) es del mundo; lo demás es UI | UI |
| `test_banco`, `test_editar`, `test_historial`, `test_trazos`, `test_zonas`, `test_exportar` | agente, edición, historial, viaje, exportación | ninguno | todo | fuera |

Diferencias ya vistas: WMF lanza `ValueError` con una zona o tipo desconocido (gworld, `MapError`
`unknown_ref`/`bad_params`); los detalles de gworld citan ids, no nombres; `corridor` con región 0 (Q-33).

## Acceptance

Por fijar tras Q-31 a Q-34. Como mínimo: cada caso de los tests elegidos tiene su test en `tests/`, que falla sin el
código que prueba, y las cifras de Helek de `test_importar` salen iguales.

## Files

Por fijar.

## Change log

- 2026-11-27: ficha abierta con el inventario de los 11 tests y las preguntas Q-31 a Q-34.

## Verification

Por fijar.
