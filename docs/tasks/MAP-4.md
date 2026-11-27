# MAP-4 · Comprobador de mapas contra el canon

## Goal

Comprobar un `gworld.map/0` contra las reglas de mapa de su mundo: las de topología y orden de
`map-generator/comprobar.py` de WMF (sobre `lore.json`) y las medidas con tolerancia de `map-generator/medir.py`
(sobre `canon.json`), con las reglas guardadas en el paquete (Q-27: a, Q-28: a), citando zonas y lugares por id
(Q-29: a) y con direcciones generales (Q-30: b).

## Scope

Cuatro pasos, cada uno con su commit:

1. **Artefacto `gworld.maprules/0`** (`gworld/schemas/maprules-0.json`, registrado en `load_schema`):
   `kind`, `map` (huella `sha256:` del archivo de origen del mapa, la de `origin` de `gworld.map/0`), `tolerance`
   (relativa, por defecto 0.03), `rules` y `undecided`. Cada regla: `id` (slug, único), `type`, `text`, `source`
   (texto de la fuente, como en WMF) y `facts` opcional (ids de hecho del canon), más sus parámetros. El esquema no
   tiene `oneOf`: los parámetros de cada tipo los comprueba el código. Manifiesto `gworld.pack/0`: `mapRules`
   opcional (ruta relativa al paquete, dentro de él como el canon); `load_pack` lo valida contra el esquema y lo da
   en `WorldPack.map_rules`. `gworld/maprules.py`: `load_map_rules(path)` y `bind(rules, doc)`, que falla con
   `MapError` si la huella no casa (`map_mismatch`), si cita una zona o lugar que no existe (`unknown_ref`), si una
   zona no es de la capa que pide el parámetro (`wrong_layer`), si faltan o sobran parámetros (`bad_params`) o si una
   dirección no vale (`bad_direction`); `check_facts(rules, index)` da los ids de `facts` que no están en el canon.
2. **Geometría** (`gworld/geometry.py`, desde `geometria.py`): anillos de contorno de un conjunto de celdas por sus
   vértices compartidos, polígonos con huecos (el giro de la primera celda es «exterior»), `area` (shoelace,
   exteriores menos huecos) y `extent` (ancho E-O y alto N-S de los vértices de los exteriores). En km: aplica
   `unitKm` (WMF no lo aplica en área y envolvente porque su `kmPorUnidad` es 1; aquí sí).
3. **Motor** (`gworld/maprules.py`): `check_rules(doc, rules) -> tuple[RuleResult, ...]`, con
   `RuleResult(id, type, ok, detail)`; `ok` es `None` en las de `undecided`. Tierra: `height >= seaLevel`. Punto de
   una celda: `center * unitKm`. Centroide de una zona: media de los puntos de sus celdas de tierra. Norte, sur, este
   y oeste según `geometry.yDown`. Una celda sin zona de una capa es la «región 0» de WMF: no cuenta como vecina de
   otra región. Tipos (nombre WMF → aquí, parámetros):
   - `orden` → `order` (`axis`: `north-south`, `south-north`, `west-east`, `east-west`; `groups`): la coordenada
     media de los centroides de cada grupo crece estrictamente en el sentido del eje.
   - `oeste-de` → `side-of` (`a`, `b`: zona o masa de tierra; `side`): `a` está al `side` de `b` por centroide.
   - `frontera` → `border` (`a`, `b`, `orientation`: `north-south` o `east-west`): pares de tierra a↔b; extensión
     en y frente a x, como `comprobar.py:72-95`.
   - `costa-a-costa` → `coast-to-coast` (`zone`, `axis`: `west-east` o `north-south`; umbral 0.15 del ancho).
   - `solo-linda` → `only-borders` (`zone`, `with`).
   - `lindan` → `borders` (`a`, `b`).
   - `cierra-por` → `closes-by` (`zone`, `edge`, `by`, `min`; franjas de 10 km, `strip` opcional).
   - `adelgaza` → `narrows` (`zone`, `toward`, `between`, `and` (listas de zonas), `max`; cuartos a lo largo del eje de `toward`).
   - `corredor` → `corridor` (`from`: provincia, `to`, `along`, `side`): Dijkstra multi-origen por tierra, como
     `comprobar.py:188-227`.
   - `dentro-de` → `inside` (`landmass`, `zones`).
   - `sin-tierra-fuera` → `no-land-outside` (`landmasses`, `name`: subcadena de lugar prohibida).
   - medidas de `canon.json`: `area` (`zone`), `extent` (`zone`), `distance` (`places`: dos ids de lugar, recta entre
     sus `point` por `unitKm`), con `value` (número o par) o `range`; dentro si `|m-e| <= e*tol`, o
     `lo*(1-tol) <= m <= hi*(1+tol)`.
   - `undecided`: `edge` (`landmass`, `side`: coordenada extrema de su tierra), `area`, `extent`, `distance` (se mide
     sin juzgar) y `shape` (sin medida).
   Los detalles siguen los de WMF (`y de los centros: 82 < 226 < …`, `96% de 28 pares (mínimo 90%)`,
   `camino de 35 km`, `sin camino por tierra`) con números redondeados como allí.
4. **Conversor de Tarkor** (`tools/tarkor_maprules.py`): lee `map-generator/lore.json` y `canon.json` de WMF en
   solo lectura y un `gworld.map/0` importado de `Helek_World.map`, resuelve los nombres a ids (zona por `name` y
   capa; lugar por `name`) y escribe un `gworld.maprules/0`; un nombre que no resuelve es un error con el nombre.
   No escribe nunca en WMF.

Fuera: CLI con códigos de salida (MAP-5 compara por la biblioteca), equivalencia exacta de valores con WMF (MAP-5),
resolver `source` a ids de hecho automáticamente (`facts` lo rellena quien escribe las reglas).

## Acceptance

- [x] `gworld.maprules/0` valida; `bind` falla con cada código y su id; `load_pack` con y sin `mapRules`.
- [x] Geometría: bloque 2×2 de celdas cuadradas de 10 da 1 polígono, área 400 y envolvente (20, 20); celdas 0 y 3
  dan área 200; un anillo con hueco resta el hueco; `unitKm` 2 multiplica el área por 4.
- [x] Cada tipo de regla tiene un test que pasa y otro que falla con su detalle, sobre mapas hechos a mano, y un
  test por dirección generalizada (al menos `side-of` y `order` en los cuatro sentidos, con `yDown` verdadero y falso).
- [x] Humo, si existe WMF: `Helek_World.map` importado y las reglas convertidas de Tarkor dan las 13 reglas y las 9
  medidas en `ok` y `?` en las 3 sin decidir; si alguna sale `MAL`, se apunta con su valor para MAP-5 en vez de
  forzarla.

## Files

- `gworld/schemas/maprules-0.json`, `gworld/schemas/pack-0.json`, `gworld/schemas/__init__.py` (registro; `gworld/schema.py` no cambia)
- `gworld/pack.py`, `gworld/geometry.py`, `gworld/maprules.py`
- `tools/__init__.py`, `tools/tarkor_maprules.py`
- `tests/test_maprules.py`, `tests/test_geometry.py`, `tests/test_pack.py`, `tests/test_tarkor_maprules.py`
- `docs/plan.md`, `docs/handoff.md`, `docs/ddd.md` (artefacto nuevo)

## Change log

- 2026-11-27: contrato escrito por la sesión principal con Q-26 a Q-30 contestadas (recomendaciones aceptadas).
  `comprobar.py` no lee `canon.json`: las reglas son de `lore.json` y las medidas de `medir.py`; aquí van juntas.
- 2026-11-27: paso 1. Tabla `gworld.maprules.PARAMS` (nombre → `Param(kind, arg, required)`; zona `any` = cualquier capa).
  Tipos: `order` axis (north-south, south-north, west-east, east-west), groups (≥2 listas de zonas); `side-of` a, b,
  side (north/south/east/west); `border` a, b, orientation (north-south, east-west); `coast-to-coast` zone, axis
  (west-east, north-south); `only-borders` zone, with (lista); `borders` a, b; `closes-by` zone, edge (cardinal), by,
  min, strip opcional; `narrows` zone, toward (cardinal), between, and, max; `corridor` from (capa province), to,
  along, side (cardinal); `inside` landmass (capa landmass), zones; `no-land-outside` landmasses (capa landmass),
  name; `area`/`extent` zone; `distance` places (2 ids enteros de lugar); `value` (número; extent: par) o `range`
  (par lo ≤ hi), exactamente uno (en `undecided`, como mucho uno); `edge` landmass, side; `shape` zone opcional.
  Esquema con parámetros libres (los comprueba `bind`); `tolerance` ≥ 0, `undecided` opcional. `load_map_rules`: `unreadable`,
  `malformed`, `schema`, `duplicate_rule` (id repetido también entre `rules` y `undecided`). `bind` comprueba en orden
  map_mismatch, bad_params (tipo no admitido en su lista, sobran, faltan, forma), y por parámetro bad_direction /
  unknown_ref / wrong_layer. `check_facts` da los ids de hecho ausentes, sin repetir. `mapRules` en el paquete:
  `map_rules_outside`, `map_rules_missing`, `map_rules_invalid` (detail de `MapError`).
- 2026-11-27: paso 2 hecho: `gworld/geometry.py` con `rings`, `polygons`, `area_km2` y `extent_km` (sobre el doc, en km);
  anillos en orden del menor vértice de salida, cada uno por la salida de mayor índice (como WMF), exteriores por
  `(min punto, longitud)`; dos celdas que solo comparten un vértice salen en un único anillo en ocho.
- 2026-11-27: paso 3 hecho: `check_rules(doc, rules)` y `RuleResult(id, type, ok, detail)` en `gworld/maprules.py`
  (llama a `bind`; `rules` y luego `undecided`). Diferencias con WMF decididas: zona sin celdas de tierra da `ok`
  falso con `<zona> sin celdas de tierra` (WMF lanza ValueError); `closes-by` y `narrows` admiten las cuatro
  direcciones y `strip` (por defecto 10 km) corta en la coordenada a lo largo del borde; `corridor` toma como region
  de la provincia su zona en la capa de `to` y la mitad de `along` por el centroide de `along` en `side`; las
  medidas dicen `medido 1.600 km² (canon 1.560, ±3%)`; `edge` da `y mínima|máxima|x … de la tierra de <zona>: N km
  (<lado>)`; sin `height` una celda es agua y sin `seaLevel` vale 20; los detalles citan zonas por id.
- 2026-11-27: paso 4 hecho: `tools/tarkor_maprules.py` (`convert(lore, canon, doc)`, `convert_dir(wmf)`, `main --wmf --out`).
  Humo con Helek: 13 reglas y 9 medidas con `ok` True y 3 sin decidir con `ok` None; ninguna sale False, así que
  no hay fallo conocido para MAP-5 (`KNOWN_FALSE` vacío en `tests/test_tarkor_maprules.py`). Conteos del contrato
  iguales a los reales. Valores medidos (MAP-5 los compara con WMF): franjas y 82 < 226 < 332 < 412, Margen cierra
  96% de 28 pares, corredor 35 km, adelgaza 0.73, área Llanuras 19.907, distancias 122 y 104 km. Interpretaciones:
  los continentes no tienen nombre en FMG: Berig es la masa con la región «Cristal Helado» y Vaelira la otra (como
  `importar.py`); `oeste-de` es siempre `side` west; `costa-a-costa` es `west-east` (el único uso de WMF);
  `borde-norte` → `edge` north; `forma` → `shape` sobre la masa; los ids de las medidas se generan
  (`area-<región>`, `extent-<zona>`, `distance-<lore>`). **Cambio en el motor (hueco del paso 3):** en `narrows`,
  `between` y `and` pasan de zona a lista de zonas (unión de sus celdas, como `entre` e `y` de WMF): la regla
  `margen-se-adelgaza` tiene dos regiones en `entre` y no se podía expresar; `gworld/maprules.py` (`PARAMS`,
  `_narrows`) y las llamadas de `tests/test_maprules.py` actualizadas. `tools/__init__.py` vacío para importar el módulo.

## Verification

`python3 -m unittest tests.test_maprules tests.test_geometry tests.test_pack tests.test_tarkor_maprules`; humo con
`Helek_World.map` y `lore.json`/`canon.json` de WMF si existen (`GW_WMF_DIR` o `../World-Maker-Fantasy`).

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
