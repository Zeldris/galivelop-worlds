# DDD: galivelop-worlds (v1, 2026-11-26)

**Uso:** kit para hacer mundos de ficción vivos con IA local. Saca de Tarkor lo que no es de Tarkor: el mundo vivo
(turnos y simulación), los mapas, el RAG del lore y el comprobador de canon. Tarkor pasa a ser el primer «paquete de
mundo» que corre sobre el kit.

- **Nombre:** Galivelop Worlds · **paquete:** `gworld` · **espacio de artefactos:** `gworld` (gart no tiene registro
  de espacios: cada repo declara el suyo en su DDD, y este es el de `gworld`).
- **Visibilidad:** público. El código es MIT; el contenido de cada mundo lleva su propia licencia (§8, P3).
- **Stack:** núcleo en Python ≥ 3.10 y solo stdlib, como el resto de Galivelop (P5).
- **Depende de** (todos solo tienen diseño hoy; ninguno tiene código publicado):
  - `galivelop-artifacts` (gart): valida los artefactos `gworld.*`. API prevista `validate(artifact, registry)`, que
    devuelve una lista de errores, y CLI `gart validate`. Llega en sus hitos H1 a H8.
  - `galivelop-models` (gmod): qué modelo de texto (`chat`) y de embeddings (`embed`) cabe en la máquina, con
    `recommend(task, machine, license_use)` sobre `gmod.machine/0`.
  - `galivelop-runtime` (grun): el turno de Ollama (`OllamaTurn`) bajo el candado de máquina (`flock` sobre
    `gpu.lock`; protocolo `grun.lock/0`). Llega en su hito R5, solo POSIX, y no promete embeddings (P7).
  - `galivelop-evaluator` (GVE): mide la narración y el RAG. Es privado; no se ha podido leer para este borrador.

> **Cambios desde el borrador 1** (comprobado leyendo gart, gmod, grun, WMF, el instalador, gimg, gvoice, gforge y el
> portal):
> - WMF no tiene un motor de turnos separable ni determinista: el mundo vivo se **diseña de nuevo**, no se extrae (§3.1).
> - El mapa de WMF no se genera por semilla: se **importa** de Azgaar FMG y se edita a mano. W4 pasa a importar (§3.2).
> - El canon de Tarkor no tiene ids de hecho y no se puede tocar: los ids se **derivan** fuera del canon (§3.3).
> - En WMF, «Cronista» es la simulación del mundo vivo, no el narrador: el adaptador de narración pasa a llamarse
>   **Narrador** (P2).
> - Se añaden lo que WMF tiene y el borrador no recogía: partidas, reloj, memoria del mundo y la batería `rag-eval`.

## 1. Propósito

Que cualquier proyecto monte un mundo persistente con su propio canon y que lo narre una IA local sin contradecirlo.
La simulación avanza por turnos de forma determinista: el código decide (tiradas, costes, efectos) y la IA solo narra
lo ya decidido, como hace hoy WMF. El narrador recupera lore del canon y nada de lo que genera se publica sin pasar
por el comprobador de canon.

**Éxito:**
1. Tarkor corre sobre `gworld` como paquete de mundo, y unos **escenarios dorados** sacados del comportamiento actual
   de WMF (turno, zona, reino y mapa) dan el mismo resultado sin código de Tarkor dentro del kit. Los tests de WMF no
   sirven de oráculo tal cual: usan la base real y azar sin semilla.
2. Un segundo mundo de ejemplo, pequeño y con licencia libre, se monta solo con un paquete (datos, canon y reglas) y
   sin tocar el núcleo.
3. Con la misma semilla y las mismas acciones salen el mismo estado y el mismo mapa, en la Steam Deck y en el CI.
4. El GVE mide en la batería de Tarkor la tasa de contradicciones con el canon de la narración. Con el comprobador
   activado, esa tasa baja respecto a la línea base sin él. La línea base hay que medirla: hoy WMF no la mide.

## 2. Lenguaje

| Término | Código | Significado |
|---|---|---|
| Mundo | `World` | Una instancia viva: su estado, su paquete, su semilla y su reloj. |
| Partida | `Save` | Una copia del mundo para una jugadora, con su propio estado. En WMF, `Save` y `mundoPartida.ts#clonarConCandado`. |
| Paquete de mundo | `WorldPack` | El contenido de un mundo (canon, tablas, reglas, mapa y licencia), aparte del código. |
| Canon | `Canon` | Los hechos aprobados de un mundo, de solo lectura para el kit. En Tarkor, los cambia solo Álvaro. |
| Hecho | `Fact` | Una afirmación del canon, con un id derivado (archivo, sección y texto) y su fuente. |
| Estado | `WorldState` | La foto del mundo en un turno: zonas, facciones, personajes, recursos y memoria. |
| Reloj | `Clock` | El tiempo de juego (días, turnos). Nunca el reloj real: el estado no lee `Date.now`. |
| Turno | `Turn` | Un paso de la simulación: entran acciones y salen el estado nuevo y sus eventos. |
| Acción | `Action` | Lo que pide una jugadora o un actor del mundo en un turno. |
| Regla | `Rule` | Una función pura del paquete que transforma el estado dentro de un turno, con el azar que le da el turno. |
| Azar | `Rng` | El generador con semilla que el turno pasa a las reglas; ninguna regla usa otro. |
| Suceso | `Happening` | Un hecho del mundo vivo con causas y consecuencias (en WMF, `Suceso`). |
| Memoria | `Memory` | Lo que un personaje o una facción recuerda y sabe de los sucesos (en WMF, `Recuerdo` y `Conocimiento`). |
| Zona | `Zone` | Una región del mapa con su tipo, sus vecinas y su estado (en WMF, `Location` y `ZonePoint`). |
| Facción | `Faction` | Un grupo con sus relaciones, objetivos y recursos. |
| Reino | `Realm` | Una facción que gobierna una jugadora o un actor (en WMF, la `Faction` con `saveId` y `origenSlug: null`). |
| Mapa | `Map` | El grafo de celdas y zonas con su geometría, importado (o, más adelante, generado). |
| Semilla | `Seed` | El número que fija la simulación (y la generación de mapas, si la hay). |
| Fragmento | `Chunk` | Un trozo del canon indexado para el RAG, con su hecho o hechos de origen. |
| Recuperación | `Retrieval` | Los fragmentos que el RAG devuelve para una consulta, con su puntuación. |
| Narración | `Narration` | El texto que genera el narrador para un turno o un suceso. |
| Narrador | `Narrator` | El adaptador que pide la narración al modelo con el estado y la recuperación. No es el «Cronista» de WMF. |
| Comprobación | `CanonCheck` | El veredicto sobre una narración: hechos citados, contradicciones y desconocidos. |
| Contradicción | `Contradiction` | Una afirmación de la narración que choca con un `Fact`, con los dos ids. |

## 3. Contextos acotados

1. **Mundo vivo** (núcleo): `World`, `Save`, `WorldState`, `Clock`, `Turn`, `Action`, `Rule`, `Rng`, sucesos y
   memoria; el bucle de turno y el registro de eventos.
   - **Origen en WMF:** no hay un motor aparte. Todo pasa por `backend/src/services/turnResolution.ts` (unas 7.400
     líneas, `narrateAndPersistTurn`), que escribe en Postgres con Prisma, usa `Math.random()` en varios servicios
     (`caza.ts`, `avanceDiario.ts`, `moralCombate.ts`, `caravanas.ts`…) y `Date.now()`. Solo `dice.ts` admite un
     azar inyectado. `Save` no tiene semilla.
   - **Consecuencia:** el núcleo se diseña de nuevo con lo que WMF ya acierta (el código decide antes de narrar) y lo
     que le falta (semilla, reloj de juego, reglas puras). Sus entradas de referencia en el mapa del agente de WMF
     (`docs/mapa-agente.md`) son turno, zona (`zonaPosicion.ts#calcularCamino`, `murosZona.ts`), reino
     (`construction.ts`, `defensaReino.ts`, `guerraReino.ts`), súbditos y llegadas, y el Cronista
     (`services/cronista/*`: sucesos, misiones, economía, facciones).
   - Lo propio de Tarkor (las dos formas de combate de su ADR 0002, la caza, las razas) va en su paquete como `Rule`.
2. **Mapas:** importar un mapa, su topología (celdas, vecinas, regiones, rutas, ríos, distancias) y la exportación a
   `gworld.map/0`.
   - **Origen en WMF:** `map-generator/` (Python stdlib, 11 archivos de test) importa una vez un `.map` de Azgaar FMG
     1.137.6 (`importar.py`), monta la malla Voronoi/Delaunay (`fmg/grafo.py`, `fmg/delaunator.py`) y luego se edita
     con `editar.py` y el visor. No hay generación por semilla: la «semilla» es un metadato copiado del `.map`.
   - El kit trae el importador de FMG y la topología. La generación por semilla y plantilla es código nuevo y queda
     fuera de las primeras versiones (P9).
   - `map-generator/comprobar.py` ya comprueba el mapa contra el lore: es la base del comprobador de mapas.
   - El render en imagen no está aquí: gimg no lee artefactos (su entrada son pedidos `order.json` con prompt y
     semilla), así que hace falta un adaptador de `gworld.map/0` a pedido, del lado del consumidor.
3. **Lore RAG:** troceado del canon, embeddings, índice y recuperación. El almacén va detrás de una interfaz
   (`Store`) y el modelo de embeddings detrás de `Embedder`.
   - **Origen en WMF:** `retrieveLore` (`services/retrieval.ts`), pgvector con distancia coseno sobre `LoreChunk`
     (`vector(768)`), embeddings `nomic-embed-text` por Ollama, y una evaluación `npm run rag-eval` sobre
     `backend/ia/rag-casos.jsonl`. El instalador ya migró de pgvector a SQLite.
   - **Ids de hecho:** el canon de Tarkor es prosa Markdown sin ids (34 archivos y unas 115.000 palabras en
     `docs/rpgtarkor/`), y no se puede tocar. El id de cada `Fact` se deriva al cargarlo: archivo, ruta de
     encabezados y huella del texto normalizado. Un cambio de Álvaro en una sección cambia solo los ids de esa
     sección, y el índice lo detecta por la huella (P6).
   - **Embeddings con versión:** el índice guarda el modelo y la versión con que se hizo; consultar con otro falla
     y pide reindexar.
4. **Comprobador de canon:** extrae las afirmaciones de una narración, las cruza con los `Fact` y da un veredicto
   (`clear`, `conflict` o `unknown` por afirmación, con la cita comprobada).
   - **Origen en WMF:** no existe; hay filtros y *grounding* en `narrador.ts` con reintento, y la idea del
     comprobador con esos tres veredictos está investigada y pendiente en
     `docs/ia/investigacion-2026-10-31-generador-lore.md`.
   - Su primera capa es determinista (nombres, fechas, relaciones de las tablas del canon) y puede llevar un juez
     opcional (P8).
5. **Narrador:** el adaptador de narración. Monta la consulta con el estado y la recuperación, pide el texto por el
   turno de Ollama de grun y lo manda al comprobador.
   - **Origen en WMF:** `services/narrador.ts` (`classifyAction`, `narrateAction`, `buildNarrationPrompt`,
     `deterministicFallbackNarration`): bloques fijos primero por la caché del prompt, tres intentos y una narración
     de plantilla si fallan. El kit copia ese esquema: los intentos y la plantilla de respaldo son parte del contrato.
   - El kit pone el adaptador; el paquete pone los prompts, el tono y los modelos (P10).
6. **Paquetes:** carga y validación de un `WorldPack` (estructura, licencia, ids de hecho únicos, huella del canon).

**Mapa con los demás repos:**
- **gart:** núcleo compartido. Valida `gworld.*`. No exige licencia ni huella por sí mismo: lo exigen los esquemas
  `gworld.*` con `required`. Los consumidores reciben una copia vendorizada con su huella sha256.
- **gmod:** cliente-proveedor. Indica el modelo de narración y el de embeddings según `gmod.machine/0`. Hoy gmod no
  cuenta a worlds entre sus consumidores: hay que pedírselo en su repo (P7).
- **grun:** cliente-proveedor. Toda llamada al modelo de texto va por su turno de Ollama bajo el candado de máquina.
  No dice qué pasa sin Ollama: aquí se falla cerrado con un mensaje que lo diga.
- **GVE:** mide la narración (contradicciones y coherencia) y el RAG (acierto de la recuperación) con
  `gworld.check/0`. Puede empezar con `rag-casos.jsonl` de WMF como batería inicial.
- **gforge:** hoy su repo está vacío. Cuando tenga una fuente de Tarkor, podrá leer `gworld.state/0` y
  `gworld.check/0` como datos de destilación y DPO (las contradicciones son buenas parejas rechazadas).
- **gimg:** pinta el mapa con un adaptador de `gworld.map/0` a `order.json`, del lado del consumidor.
- **gvoice:** herramienta de desarrollo que pregenera frases; no lee artefactos. La voz en vivo del juego la pone
  qwentts (`tts-server`). Ninguno de los dos importa `gworld`.
- **World-Maker-Fantasy (Tarkor):** conformista y primer consumidor. Su canon se lee y nunca se modifica desde aquí:
  `docs/rpgtarkor/` (la fuente de verdad), `docs/canon-opencode/` (resumen denso que dice no ser la fuente) y, en el
  mapa, `map-generator/canon.json` y `lore.json`, que cambia solo su autora.
- **Instalador-WMF-Tarkor:** Tauri con Ollama como *sidecar* y SQLite. Hoy tiene su propio catálogo de modelos
  (`app/catalogo/catalogo.json`, sin gmod); instalará el paquete de Tarkor y los modelos que pida gmod cuando se
  cambie a él (tarea de su repo).

## 4. Modelo

- **Agregado raíz:** `World`. Un turno es una transacción: `apply(turn) -> (WorldState', Events)`, y el estado no
  cambia fuera de ella. Una `Save` es un `World` con su semilla y su historial de turnos.
- **Segundo agregado:** `Canon`, de solo lectura. Se carga del paquete y lo usan el RAG y el comprobador.
- **Entidades:** `Zone`, `Faction` (y `Realm` como su caso particular), `Character`, `Fact`, `Happening`.
  Son abstracciones nuevas: WMF usa otros nombres (§2) y el adaptador de Tarkor hace la traducción.
- **Objetos de valor:** `Seed`, `Clock`, `Turn`, `Action`, `Memory`, `Chunk`, `Retrieval`, `Narration`,
  `CanonCheck`, `Contradiction`, `Licence` (SPDX o texto, y condiciones) y `PackRef` (id, versión y huella).
- **Servicios:**
  - `load_pack(path) -> WorldPack`
  - `new_world(pack, seed) -> World`
  - `World.apply(turn)`
  - `import_map(source) -> Map` (FMG en la primera versión)
  - `index(canon, store, embedder)`
  - `retrieve(query, k) -> Retrieval`
  - `narrate(state, events) -> Narration` (vía grun)
  - `check(narration, canon) -> CanonCheck`
- **Interfaces que pone el paquete o el consumidor:** `Rule`, `MapImporter`, `Store` (el almacén del RAG),
  `Embedder`, `Judge` (opcional) y los prompts del `Narrator`.
- **Eventos** (líneas del registro del mundo): `TurnApplied`, `ZoneChanged`, `FactionShifted`, `HappeningOccurred`,
  `MapImported`, `NarrationDrafted`, `CanonChecked`, `NarrationRejected`, `NarrationPublished`.
- **Artefactos gart** (todos `/0`, provisionales hasta su primera versión estable, que se congela por huella):
  - `gworld.pack/0`: el manifiesto del paquete (id, versión, licencia, huella del canon y lista de reglas).
  - `gworld.map/0`: el mapa (celdas, vecinas, zonas y geometría), con su origen (archivo importado y su huella).
    Celdas con id entero (su índice en el origen) y zonas con id `<capa>:<índice>` (`region:17`); la geometría es
    una lista de vértices compartidos que cada celda cita por índice, en unidades del lienzo con `unitKm`. Que las
    referencias existan y el grafo sea conexo lo comprueba MAP-3, no el esquema.
  - `gworld.maprules/0`: las reglas de mapa de un mundo (topología, orden y medidas con tolerancia) contra un mapa
    concreto (huella de su origen), con zonas y lugares por id y su fuente en el canon; no son `Rule`: no transforman
    estado, son condiciones que el mapa cumple (MAP-4).
  - `gworld.state/0`: la foto del estado en un turno, con la huella del paquete, la semilla y el reloj.
  - `gworld.canon/0`: el índice de hechos (id derivado, texto normalizado, fuente y huella).
  - `gworld.check/0`: el veredicto de una narración (citados, contradicciones y desconocidos, con ids), con la
    huella de la narración y, si hubo juez, cuál.

## 5. Invariantes

Cada una lleva su test.

1. **Simulación determinista:** la misma semilla, el mismo paquete y las mismas acciones dan el mismo
   `gworld.state/0`, byte a byte. Test: dos ejecuciones de 100 turnos con la misma huella final; una semilla
   distinta da una huella distinta.
2. **Sin reloj ni azar externos:** ninguna regla ni el bucle de turno leen el reloj real ni un azar que no sea el
   `Rng` del turno. Test: un `grep` de `time.time`, `datetime.now` y `random.` fuera de `Rng`, y un turno con el
   reloj del sistema cambiado que da la misma huella.
3. **Importación estable:** el mismo archivo de origen da el mismo `gworld.map/0`, y su grafo es conexo y sin celdas
   huérfanas. Test: importar dos veces el mapa de ejemplo y comparar huellas; un mapa con una celda aislada falla
   con el id de la celda.
4. **El canon no se escribe:** ningún módulo abre los archivos del canon en modo escritura, y el kit nunca genera
   lore. Test: un `grep` que falle si hay escritura sobre la ruta del canon, y un test que cargue el canon con
   permisos de solo lectura.
5. **Ids de hecho estables:** el mismo canon da los mismos ids, y cambiar una sección cambia solo los ids de esa
   sección. Test: cargar dos veces; editar una sección de una copia del canon de ejemplo y comparar.
6. **Nada se publica sin comprobar:** `NarrationPublished` exige un `gworld.check/0` de esa misma narración (por
   huella) sin contradicciones. Test: publicar sin comprobación o con una contradicción falla con el motivo y los
   ids del hecho.
7. **Las contradicciones citan su fuente:** cada `Contradiction` lleva el id del `Fact` y su archivo de origen.
   Test: un `gworld.check/0` con una contradicción sin `fact_id` no valida en gart (`required` en el esquema).
8. **Licencias separadas:** el paquete declara su licencia y el kit no la mezcla con MIT. Un artefacto derivado
   (estado, mapa o narración) hereda la del paquete. Test: un paquete sin licencia no carga, y un `gworld.state/0`
   de Tarkor lleva la licencia de su paquete.
9. **El núcleo no sabe de Tarkor:** ningún módulo del núcleo nombra términos de Tarkor. Test: un `grep` de la lista
   de nombres del paquete de Tarkor sobre `gworld/` (Tarkor, Helek Sirik, Berig, Vaelira, Goirntes, Nabieus, Faerus,
   Maktor, Goirno, Cristal Helado, Clan Serhu, la Concordia, Gorhorn, Kegi, Hashma, el Estallido, el Detonante, la
   Isla Cambiante…), y el mundo de ejemplo corriendo sin ese paquete.
10. **Las reglas son puras:** una `Rule` no hace E/S ni llama al modelo. La IA solo entra por el Narrador, fuera del
    turno. Test: correr un turno con red y archivos bloqueados.
11. **El modelo pasa por grun:** ninguna llamada al modelo de texto sale fuera del turno de Ollama. Test: `narrate`
    sin grun falla cerrado, con un mensaje que lo nombra.
12. **Embeddings con versión:** un índice no se consulta con un modelo de embeddings distinto del que lo hizo. Test:
    consultar con otro modelo falla y pide reindexar.
13. **Núcleo stdlib:** el núcleo importa sin extras; un `Store` o `Embedder` que no esté instalado falla con la
    orden que lo instala. Test: importar `gworld` en un entorno limpio, y comprobar que el mensaje nombra el extra.

## 6. Alcance

**Dentro:**
- el bucle de turno, el reloj de juego, el azar con semilla y las reglas como interfaz;
- partidas, sucesos y memoria del mundo;
- el importador de mapas FMG, la topología y el comprobador de mapas;
- el troceado, índice y recuperación del canon, con ids de hecho derivados;
- el comprobador de canon;
- el adaptador del Narrador, con reintentos y plantilla de respaldo;
- el formato y la validación de paquetes;
- un mundo de ejemplo pequeño.

**Fuera:**
- el contenido de Tarkor (canon, combate, caza, razas, prompts y tono): va en su paquete, en su repo;
- escribir o proponer lore: lo hace la sesión de lore de WMF en `docs/borradores-opencode/`;
- la interfaz del juego, el backend, la base y las cuentas;
- la generación de mapas por semilla, en las primeras versiones (P9);
- pintar mapas (gimg) y voces (gvoice, qwentts);
- medir (GVE) y ajustar modelos (gforge);
- el multijugador en red (en WMF, `/multijugador` es solo un marcador).

## 7. Escalera de hitos

| Hito | Nivel | Qué | Lo decide |
|---|---|---|---|
| W0 | Diseño | Este DDD, el glosario y los ADR de stack, licencias, almacén del RAG, ids de hecho y nombre del Narrador. | Usuario |
| W1 | Paquete y canon | `gworld.pack/0` y `gworld.canon/0` con sus esquemas; lector del canon de Tarkor que solo lee y deriva ids; mundo de ejemplo mínimo. | Tests |
| W2 | Comprobador | La capa determinista sobre las tablas del canon y la batería del GVE de contradicciones con su línea base. | GVE |
| W3 | RAG | Troceado, embeddings locales con versión e índice SQLite; el GVE mide el acierto de recuperación, empezando por `rag-casos.jsonl`. | GVE + umbral |
| W4 | Mapas | Importador FMG, topología, `gworld.map/0` y comprobador de mapas, equivalentes al `map-generator/` de WMF sobre `Helek_World.map`. | Tests |
| W5 | Mundo vivo | Bucle de turno con semilla y reloj de juego, reglas, partidas y sucesos; escenarios dorados de WMF; las reglas de Tarkor en su paquete. | Tests + usuario |
| W6 | Narrador | Narración vía grun con comprobación obligatoria; Tarkor pasa a consumir el kit. | Usuario (WMF fuera de su congelación) |

- W1 a W4 solo leen de WMF (canon, mapa, casos del RAG) y no cambian el juego: se pueden hacer con WMF congelado.
- W5 y W6 chocan con la congelación de funcionalidades grandes de WMF (su hito 0.3, «Reino profundo», con la
  «Puerta de pruebas» como único frente): esperan a que acabe.
- Hasta que gart publique su validador, los esquemas `gworld.*` se escriben en su formato y se validan con una
  comprobación mínima propia, que se cambia por la copia vendorizada de gart en cuanto exista (P4).

## 8. Preguntas abiertas

Todas decididas el 2026-11-26 según su recomendación: se quedan aquí como registro del porqué; lo que vale es la
tabla de «Decisiones» y los ADR de `docs/adr/`.

1. **¿Extraer de Tarkor o reescribir?** El turno de WMF es un monolito sobre Prisma y Postgres, con azar sin semilla
   y reloj real; su mapa se importa, no se genera.
   **Recomendación:** reescribir el núcleo contra este DDD. El oráculo son escenarios dorados sacados del
   comportamiento de WMF (no sus tests, que usan la base real). Tarkor cambia a usar el kit solo en W6, en una tarea
   de su propio repo.
2. **¿Cómo se llama el adaptador de narración?** En WMF, «Cronista» es la simulación del mundo vivo
   (`services/cronista/*`) y el narrador es `narrador.ts`.
   **Recomendación:** `Narrator` / «Narrador», y no usar «Cronista» en el kit para no chocar con WMF.
3. **¿Cuál es la licencia del contenido de Tarkor?** WMF dice CC BY-NC-SA 4.0 (`LICENSE-CONTENIDO`, autoras
   Galivelop y Álvaro García Graña); el instalador dice «todos los derechos reservados».
   **Recomendación:** CC BY-NC-SA 4.0, la de WMF, y corregir el instalador en su repo. Confirmarlo con Álvaro.
4. **¿Qué se hace mientras gart, gmod y grun solo tienen diseño?**
   **Recomendación:** escribir los esquemas en el formato de gart y validarlos con una comprobación mínima propia
   hasta que gart publique su validador; leer `gmod.machine/0` si existe y, si no, un perfil fijo de Steam Deck;
   y no empezar W6 hasta que grun llegue a R5.
5. **¿Python o TypeScript?** WMF es TypeScript (Fastify, Prisma, React) y el resto de Galivelop es Python stdlib.
   **Recomendación:** el contrato son los artefactos gart y el núcleo es Python stdlib (comprobador, mapas y canon,
   que también sirven a gforge y al GVE). El turno de Tarkor sigue en TypeScript hasta W5, y entonces se decide con
   datos si se porta o se publica un paquete npm con el mismo contrato.
6. **¿Cómo se dan ids a los hechos si el canon no se puede tocar?**
   **Recomendación:** derivarlos al cargar (archivo, ruta de encabezados y huella del texto normalizado) y
   guardarlos en `gworld.canon/0`, sin escribir nada en el canon.
7. **¿De dónde salen los embeddings?** grun solo promete el turno de texto, y gmod sí recomienda modelos `embed`.
   **Recomendación:** pedir a grun un turno de embeddings bajo el mismo candado; hasta entonces, un `Embedder` que
   llama a Ollama tomando el candado con el protocolo `grun.lock/0`. Modelo por defecto, el de WMF
   (`nomic-embed-text`), guardado con su versión en el índice.
8. **¿El comprobador es determinista o un juez con IA?**
   **Recomendación:** dos capas. La primera, determinista y obligatoria: entidades, fechas y relaciones contra las
   tablas del canon. La segunda, un `Judge` local opcional para lo que la primera marque como `unknown`, apuntado
   como juez de IA en el `gworld.check/0`.
9. **¿Generar mapas por semilla o importarlos?** WMF importa un mapa de Azgaar FMG hecho a mano y lo edita.
   **Recomendación:** importar en las primeras versiones; la generación por semilla, después, como una
   implementación más de `MapImporter` (un «importador» que genera).
10. **¿De quién son los prompts del Narrador?** WMF tiene los suyos (ejemplo de buena narración, instrucciones
    fijas, *grounding*) y su propio Modelfile.
    **Recomendación:** el kit pone el adaptador (orden de bloques, recuperación, grun, reintentos, plantilla de
    respaldo y comprobación) y el paquete pone los prompts, el tono y los modelos.
11. **¿Qué capa del canon de Tarkor indexa el RAG?** `docs/rpgtarkor/` es la fuente de verdad; `docs/canon-opencode/`
    es un resumen que dice no serlo.
    **Recomendación:** indexar y citar solo `docs/rpgtarkor/`; el resumen puede ir fijo en el prompt, pero nunca
    como fuente de un `Fact`.
12. **¿Son oficiales las abreviaturas `gart`, `gmod`, `grun`, `gforge` y `gworld`?** El portal solo recoge GVE y
    GalivelopCode (gvc), y no nombra Worlds.
    **Recomendación:** usar `gworld` como nombre de paquete y de espacio de artefactos (hace falta uno), y pedir
    que el portal lo recoja junto a los demás.
13. **¿Cuándo empieza cada hito?**
    **Recomendación:** W0 ahora; W1 a W4 cuando quieras, porque solo leen de WMF; W5 y W6 cuando WMF salga de su
    congelación.

## Decisiones

Tomadas el 2026-11-26 (Q-1 a Q-13 de `docs/questions.md`).

| id | pregunta | respuesta | sección |
|---|---|---|---|
| D1 | ¿Extraer de Tarkor o reescribir? | Reescribir el núcleo contra este DDD; oráculo de escenarios dorados de WMF. [ADR 0001](adr/0001-reescribir-el-nucleo.md) | §3.1, §8.1 |
| D2 | ¿Nombre del adaptador de narración? | `Narrator` / «Narrador»; «Cronista» no se usa en el kit. [ADR 0002](adr/0002-narrador-no-cronista.md) | §2, §3.5 |
| D3 | ¿Licencia del contenido de Tarkor? | CC BY-NC-SA 4.0, la de WMF; falta la confirmación de Álvaro y corregir el instalador. [ADR 0003](adr/0003-licencias.md) | §4, §5.8 |
| D4 | ¿Qué hacer mientras gart, gmod y grun solo tienen diseño? | Esquemas en formato gart con comprobación mínima propia; perfil fijo de Steam Deck sin `gmod.machine/0`; W6 espera a grun R5. | §7 |
| D5 | ¿Python o TypeScript? | Contrato en artefactos gart; núcleo Python ≥ 3.10 stdlib; el turno de Tarkor sigue en TypeScript hasta W5. [ADR 0004](adr/0004-stack.md) | §5.13 |
| D6 | ¿Ids de hecho sin tocar el canon? | Derivados al cargar (archivo, ruta de encabezados, huella del texto normalizado) y guardados en `gworld.canon/0`. [ADR 0005](adr/0005-ids-de-hecho.md) | §3.3, §5.5 |
| D7 | ¿De dónde salen los embeddings? | Se pide a grun un turno de embeddings; mientras, `Embedder` con `grun.lock/0` y `nomic-embed-text` versionado en el índice. [ADR 0006](adr/0006-rag-almacen-y-embeddings.md) | §3.3, §5.12 |
| D8 | ¿Comprobador determinista o juez con IA? | Dos capas: determinista obligatoria y `Judge` opcional apuntado en `gworld.check/0`. | §3.4 |
| D9 | ¿Generar mapas o importarlos? | Importar FMG en las primeras versiones; generación por semilla después como un `MapImporter` más. | §3.2 |
| D10 | ¿De quién son los prompts del Narrador? | El kit pone el adaptador (orden de bloques, recuperación, grun, reintentos, plantilla de respaldo y comprobación); el paquete, prompts, tono y modelos. | §3.5 |
| D11 | ¿Qué capa del canon indexa el RAG? | Solo `docs/rpgtarkor/`; `docs/canon-opencode/` puede ir fijo en el prompt, nunca como fuente de un `Fact`. | §3.3 |
| D12 | ¿Abreviaturas oficiales? | `gworld` como paquete y espacio de artefactos; se pide al portal que lo recoja. | cabecera |
| D13 | ¿Cuándo empieza cada hito? | W0 ya; W1 a W4 cuando se quiera (solo leen de WMF); W5 y W6 tras la congelación de WMF. | §7 |
