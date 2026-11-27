# MAP-3 · Topología del mapa

## Goal

Comprobar que un `gworld.map/0` es un grafo coherente (referencias que existen, vecinas simétricas, conexo y sin
celdas huérfanas: invariante 3) y dar consultas de topología sobre él: vecinas, zonas, rutas, ríos y distancias.

## Scope

`gworld/topology.py`:

- `check_map(doc) -> None`: sobre un documento ya válido contra el esquema, falla con `MapError` (de `gworld/maps.py`)
  y un código propio por caso, con el id afectado en `detail`: id de celda repetido o celdas fuera de orden, vecina
  inexistente, vecina de sí misma, vecindad no simétrica, índice de vértice fuera de `geometry.vertices`, zona
  inexistente citada por una celda, `parent` o `centerCell` inexistentes, capa que no casa con el prefijo del id,
  dos zonas de una misma capa en una celda, celda inexistente en una ruta o un río, celda sin vecinas (huérfana) y
  grafo no conexo (el id más bajo de la componente que no contiene la celda de id más bajo).
- `Topology(doc)`: llama a `check_map` y da `neighbours(cell)`, `zones_of(cell)`, `zone_of(cell, layer)`,
  `cells_in(zone)`, `zones(layer=None)`, `routes(group=None)`, `rivers()`, `distance_km(a, b)` (recta entre
  centros por `unitKm`), `hops(a, b)` (BFS) y `path(a, b, passable=None)` (camino más corto por vecinas, pesado por
  distancia entre centros, desempate determinista por id) con su longitud en km.
- `FmgImporter.import_map` llama a `check_map` antes de devolver.

Fuera: comprobación contra el canon (MAP-4) y equivalencia con WMF (MAP-5).

## Acceptance

- [x] Importar dos veces `tests/fixtures/mini.map` da el mismo documento (misma huella) y pasa `check_map`.
- [x] Un mapa con una celda aislada falla con el id de esa celda; cada otro caso de `check_map` tiene su test con
  código y id.
- [x] Consultas de `Topology` probadas sobre un mapa pequeño hecho a mano, con valores calculados a mano.

## Files

- `gworld/topology.py`, `gworld/maps.py`
- `tests/test_topology.py`, `tests/test_maps.py`
- `docs/plan.md`, `docs/handoff.md`, `docs/ddd.md` si cambia el contrato

## Change log

- 2026-11-27: contrato escrito por la sesión principal.
- 2026-11-27: distancias como WMF (`medir.py:64-67`: `math.dist` de centros por `kmPorUnidad`; `consultar.py:343-357`:
  Dijkstra con coste la distancia entre centros y vecinas ordenadas por id). Diferencia: WMF pasa por defecto solo por
  tierra (`consultar.py:321-323`, `h >= TIERRA`; `--mar` por agua); aquí `passable=None` deja pasar por todas, como
  dice el contrato, y la tierra se pide con `passable=lambda c: c["height"] >= doc["seaLevel"]` (a MAP-5, a decidir).
- 2026-11-27: `detail` de `MapError` en `check_map` es siempre un dict con `id` (+ `neighbour`, `cell`, `zone`...).
  Códigos: `duplicate_cell`, `cells_unordered`, `duplicate_zone`, `layer_mismatch`, `unknown_parent`,
  `unknown_center_cell`, `vertex_out_of_range`, `self_neighbour`, `unknown_neighbour`, `unknown_zone`,
  `duplicate_layer`, `asymmetric_neighbour`, `unknown_route_cell`, `unknown_river_cell`, `orphan_cell`, `disconnected`.
- 2026-11-27: `path` devuelve `(celdas, km)` o `None` si no hay camino (también si un extremo no es transitable);
  empate de longitud: gana la celda previa de id menor. Consulta de celda o zona inexistente: `unknown_cell` /
  `unknown_zone`. Dos celdas con la misma zona repetida en `zones` cuentan como `duplicate_layer`.
- 2026-11-27: `import_map` importa `check_map` dentro de la función (import circular con `MapError`).

## Verification

`python3 -m unittest tests.test_topology tests.test_maps`; humo sobre `Helek_World.map` de WMF (5120 celdas) si
existe: importa y pasa `check_map`.

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
