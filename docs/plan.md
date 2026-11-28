# Plan: versiones de galivelop-worlds

Reparto, confirmado el 2026-11-26 (Q-14 a Q-16), de los hitos de [`ddd.md` §7](ddd.md#7-escalera-de-hitos) en versiones. Este archivo dice qué está
implementado; la bitácora, qué se está haciendo. Una tarea se marca `[x]` en el commit que la cierra.

**`## Files` de una tarea:** un esquema nuevo lista también `gworld/schemas/__init__.py`; una herramienta nueva,
`tools/__init__.py` (retro 0.2, Q-41).

**Ids:** un prefijo por hito, con el patrón `taskId` de `.claude/gw.json` (`[A-Z]{2,5}-\d+`): `PCK` paquete y
canon, `CHK` comprobador, `RAG` recuperación, `MAP` mapas, `VIV` mundo vivo, `NAR` Narrador.

**Versiones:** una versión menor por hito mientras el contrato es `/0`; `1.0.0` cuando Tarkor consume el kit (W6) y
los artefactos `gworld.*` se congelan por huella. Cada versión sale de `main` con su etiqueta `vX.Y.Z`.

| Versión | Hito | Depende de | Bloqueos externos |
|---|---|---|---|
| 0.0 | W0 Diseño | — | — (cerrada: D1-D13, ADR 0001-0006) |
| 0.1 | W1 Paquete y canon | 0.0 | — |
| 0.2 | W4 Mapas | 0.1 | — |
| 0.3 | W2 Comprobador | 0.1 | Leer el GVE (privado, sin acceso aún) |
| 0.4 | W3 RAG | 0.1 | Turno de embeddings de grun (D7); mientras, `Embedder` propio |
| 0.5 | W5 Mundo vivo | 0.1, 0.2 | Fin de la congelación de WMF (hito 0.3 «Reino profundo») |
| 1.0 | W6 Narrador | 0.3, 0.4, 0.5 | grun en R5 y WMF fuera de su congelación |

W4 va antes que W2 y W3 porque no tiene bloqueos externos y W5 lo necesita (zonas y caminos); W2 y W3 esperan al GVE
y a grun. Si el acceso al GVE llega antes, 0.2 y 0.3 se pueden intercambiar.

## 0.1 — W1 Paquete y canon

Lo decide: tests. Invariantes: 4, 5, 8, 9 y 13.

- [x] PCK-1 Esqueleto del paquete `gworld/` (Python ≥ 3.10, solo stdlib), `pyproject.toml` con extras vacíos, tests
  con `unittest` y su orden en el check (`relatedTests` y `testMap` de `.claude/gw.json`).
- [x] PCK-2 Comprobación mínima propia de esquemas en formato gart (D4), a cambiar por la copia vendorizada de gart.
- [x] PCK-3 Esquemas `gworld.pack/0` y `gworld.canon/0`, con `required` para licencia y huella.
- [x] PCK-4 `load_pack(path) -> WorldPack`: estructura, licencia obligatoria, huella del canon (invariante 8).
- [x] PCK-5 Lector del canon de solo lectura: troceo por encabezados y ids de hecho derivados (ADR 0005; invariantes
  4 y 5).
- [x] PCK-6 Mundo de ejemplo mínimo, sin términos de Tarkor, y el `grep` del invariante 9.
- [x] PCK-7 Paquete de Tarkor de prueba que lee `docs/rpgtarkor/` de WMF sin escribir (D11) y exporta
  `gworld.canon/0`.

## 0.2 — W4 Mapas

Lo decide: tests. Invariante: 3.

- [x] MAP-1 Esquema `gworld.map/0` con origen (archivo importado y huella).
- [x] MAP-2 `MapImporter` e importador FMG 1.137.6, reescrito desde `map-generator/importar.py` de WMF.
- [x] MAP-3 Topología: celdas, vecinas, regiones, rutas, ríos y distancias; grafo conexo sin celdas huérfanas.
- [x] MAP-4 Comprobador de mapas contra el canon, desde `map-generator/comprobar.py` y `medir.py`, con las reglas
  en el paquete (`gworld.maprules/0`; Q-27 a Q-30).
- [x] MAP-5 Equivalencia con el `map-generator/` de WMF sobre `Helek_World.map` (sus 11 archivos de test como
  oráculo).
- [x] PCK-8 Barrido de leves de `gworld/pack.py` (retro W1, Q-24): `canon.path` `"."`/`"sub/.."` rechazado;
  FIFO/socket como `PackError`; mensaje «fuera del canon» y nombres no UTF-8 como `PackError` en `canon_digest`;
  `RecursionError` de `validate` con su propio error, no `bad_json`. Los leves de `gworld/canon.py` siguen aparte.

## 0.3 — W2 Comprobador

Lo decide: el GVE. Invariantes: 6 y 7.

- [ ] CHK-1 Leer el GVE y fijar el formato de su batería de contradicciones (pendiente de acceso).
- [ ] CHK-2 Esquema `gworld.check/0` (`fact_id` y fuente `required` en cada contradicción).
- [ ] CHK-3 Capa determinista: nombres, fechas y relaciones de las tablas del canon; veredictos `clear`,
  `conflict` y `unknown` con la cita.
- [ ] CHK-4 Interfaz `Judge` opcional, apuntada en `gworld.check/0` (D8).
- [ ] CHK-5 Batería del GVE y su línea base.
- [x] MAP-6 Barrido de leves de `gworld/maps.py` (retro 0.2, Q-45): `parent: region:N` de una provincia con estado
  borrado o 0, filtrado con `known` como `capitalOf`; `_MIN_RECORDS = 45` frente a los 46 de FMG (o el porqué) y
  `_C_RIVER` sin uso; una ruta de grupo no slug, una ruta de menos de 2 puntos o un burgo sin `name` no tumban el
  mapa entero. Los leves de `gworld/topology.py` siguen aparte.

## 0.4 — W3 RAG

Lo decide: el GVE con umbral. Invariantes: 12 y 13.

- [x] RAG-1 Troceado del canon en `Chunk` con los ids de hecho.
- [x] RAG-2 Interfaces `Store` y `Embedder`; un extra que falte falla con la orden que lo instala.
- [x] RAG-3 `Store` SQLite y `Embedder` con `bge-m3` y `grun.lock/1`, modelo y versión guardados en el
  índice (ADR 0006).
- [ ] RAG-4 `index` y `retrieve(query, k)`; consultar con otro modelo falla y pide reindexar.
- [ ] RAG-5 Acierto de recuperación en el GVE, empezando por `rag-casos.jsonl` de WMF, y su umbral.

## 0.5 — W5 Mundo vivo

Lo decide: tests y la persona. Invariantes: 1, 2 y 10. Empieza tras la congelación de WMF.

- [ ] VIV-1 `Seed`, `Rng` y `Clock` de juego; el `grep` del invariante 2.
- [ ] VIV-2 `World`, `WorldState` y `apply(turn) -> (WorldState', Events)`; esquema `gworld.state/0`.
- [ ] VIV-3 Interfaz `Rule` pura y su test con red y archivos bloqueados.
- [ ] VIV-4 `Save`, historial de turnos, sucesos y registro de eventos.
- [ ] VIV-5 Escenarios dorados sacados del comportamiento de WMF (D1).
- [ ] VIV-6 Las reglas de Tarkor en su paquete (combate, caza, razas).

## 1.0 — W6 Narrador

Lo decide: la persona. Invariantes: 6 y 11. Empieza con grun en R5 y WMF fuera de su congelación.

- [ ] NAR-1 Adaptador `Narrator` por el turno de Ollama de grun; sin grun falla cerrado (invariante 11).
- [ ] NAR-2 Orden de bloques, tres intentos y plantilla de respaldo (D10).
- [ ] NAR-3 Comprobación obligatoria antes de `NarrationPublished` (invariante 6).
- [ ] NAR-4 Tarkor consume el kit (tarea en su repo) y los artefactos `gworld.*` se congelan por huella.
