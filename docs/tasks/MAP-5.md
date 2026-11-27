# MAP-5 · Equivalencia con el `map-generator/` de WMF

## Goal

Probar que `gworld/` da lo mismo que `map-generator/` de WMF sobre Helek: el import del `.map`, las medidas contra
el canon y las reglas de mapa, con los tests de `map-generator/tests/` como oráculo.

## Scope

Decidido (Q-31: a, Q-32: b, Q-33: a, Q-34: b): entran `test_importar`, `test_medir`, `test_comprobar`, la parte de
lectura de `test_consultar` (vecinos, caminos por tierra, distancias) y `test_visor.py:66` (medidas). El resto
(banco, editar, historial, trazos, zonas, exportar, UI) queda fuera. Las cifras de WMF se sacan corriendo sus scripts
en solo lectura y se congelan en los tests, con la línea de WMF de donde salen.

Inventario de los 11 tests (subagente, 2026-11-27):

| test WMF | módulo WMF | equivalente en gworld | falta | capa |
|---|---|---|---|---|
| `test_importar` | `importar.py`, `fmg/*` | `maps.FmgImporter`, `_delaunay` | cifras de Helek (5 regiones, 5 lugares, provincias en la región 18), salida estable, `mismatch` por área (19808 km²), «revisar» | mundo |
| `test_medir` | `medir.py`, `geometria.py` | `geometry`, `maprules` (`area`, `extent`, `distance`) | mutación del canon (un tercio de las Llanuras a la Ciénaga) | mundo |
| `test_comprobar` | `comprobar.py` | `maprules.check_rules`, `tools/tarkor_maprules.py` | 5 mutaciones que rompen una sola regla, `adelgaza` sin grosor | mundo |
| `test_consultar` | `consultar.py` | `Topology` (vecinos, `path`, `distance_km`) | celda por punto, frontera, costa, caminos por mar, JSON | consulta |
| `test_visor` | `servir.py` | `geometry.area_km2`, `extent_km` | solo `:66` (medidas) es del mundo; lo demás es UI | UI |
| `test_banco`, `test_editar`, `test_historial`, `test_trazos`, `test_zonas`, `test_exportar` | agente, edición, historial, viaje, exportación | ninguno | todo | fuera |

Diferencias aceptadas: WMF lanza `ValueError` con una zona o tipo desconocido (gworld, `MapError`
`unknown_ref`/`bad_params`); los detalles de gworld citan ids, no nombres.

Pasos, cada uno con su commit:

1. **[hecho] Fixtures e import.** `tests/fixtures/helek/`: `helek.json` copiado de `map-generator/mundo/` de WMF y
   `helek.gworld.json` (el `gworld.map/0` que da `FmgImporter` sobre `Helek_World.map`), con un `README.md` de
   procedencia (commit de WMF, huellas, licencia) y un script que lo regenera. Test cruzado en el CI: cada celda
   tiene en `helek.gworld.json` la misma altura, región, provincia y continente que en `helek.json`, y los mismos
   lugares. Paridad con `test_importar`: cifras de Helek, salida estable (dos imports iguales y igual al fixture),
   versión distinta, `mismatch` por área con su número, Delaunay vacío. Informe «revisar» (Q-34: b):
   `FmgImporter.import_with_review(path) -> (doc, ImportReview)` con los marcadores automáticos y los burgs
   borrados como WMF; `import_map` sigue dando solo el doc. Los tests que leen el `.map` se saltan sin el clon de WMF.
2. **[hecho] Medidas** (`test_medir`, `test_visor.py:66`): área y envolvente de cada zona de Helek iguales a las de WMF
   (`places=3`); la mutación del canon (un tercio de las Llanuras a la Ciénaga) saca área y envolvente de tolerancia.
3. **[hecho] Reglas** (`test_comprobar`): las 5 mutaciones rompen esa regla; el conjunto exacto de reglas rotas es el que da WMF (en 3 de las 5 rompen más de una también allí); `adelgaza` sin grosor da su
   detalle sin excepción; `corridor` con región 0 pisable (Q-33: a) con su test y su nota en el esquema.
4. **[hecho] Consultas** (lectura de `test_consultar`): vecinos, `path` por tierra y `distance_km` de los casos de WMF
   (`ordinum`→`nabieus` y el rodeo cuando la recta cruza mar) con sus cifras.

## Acceptance

- Cada caso elegido de los tests de WMF tiene su test en `tests/`, con la línea de WMF en un comentario.
- Los tests de los pasos 2 a 4 y el cruzado del paso 1 corren en el CI sin el clon de WMF.
- Un test nuevo falla sin el código que prueba (`red-without-fix.sh`) cuando hay código nuevo.
- El check, en verde.

## Files

`tests/fixtures/helek/` (nuevo), `gworld/maps.py` (paso 1), `gworld/maprules.py` y
`gworld/schemas/maprules-0.json` (paso 3, si hace falta), `tests/test_maps.py`, `tests/test_helek_parity.py` (nuevo).

## Change log

- 2026-11-27: pasos 2 a 4 hechos y fusionados. Medidas: las 11 zonas de Helek (5 regiones, 4 provincias, 2 continentes) dan el área y la envolvente de WMF con `places=3`; la mutación del canon rompe `area-region-18`, `extent-region-18` y `extent-region-19`. Reglas: `helek.maprules.json` congelado (procedencia en el README); las 13 reglas del lore dan `ok`; las 5 mutaciones rompen el mismo conjunto que en WMF (comprobado ejecutando `comprobar.py` sobre las mismas mutaciones), no siempre una sola; `corridor` con región 0 pisable con su test y su nota en el esquema. Consultas: los caminos por tierra coinciden celda a celda con el Dijkstra de `consultar.py:344-357`; los km difieren 0.03-0.07 por el redondeo de los centros en `helek.gworld.json`.
- 2026-11-27: paso 1 hecho: `tests/fixtures/helek/` (helek.json, helek.gworld.json, regen.py, README), `tests/test_helek_parity.py` e `ImportReview`/`FmgImporter.import_with_review` en `gworld/maps.py` (40 marcadores, 610 burgs borrados). Diferencia con WMF: el lugar 614 (Nabieus) esta movido en `helek.json`.
- 2026-11-27: Q-31 a Q-34 contestadas; alcance, pasos y aceptación fijados. `helek.gworld.json` también va a fixtures para que el CI pruebe reglas y medidas.
- 2026-11-27: ficha abierta con el inventario de los 11 tests y las preguntas Q-31 a Q-34.

## Verification

`python3 -m unittest discover -s tests -t .` y el check del proyecto.
