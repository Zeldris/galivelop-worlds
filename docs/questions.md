# Questions

Questions for the user, one entry each; `python3 .claude/gw/scripts/questions.py` reads and rewrites this
file (format: header of scripts/questions.py). Answer by number: `questions.py answer "5. a, 6. ok"`.

## Q-1
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.1: ¿extraer el código de Tarkor o reescribir el núcleo?
- Recommendation: Reescribir contra el DDD con escenarios dorados de WMF
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-2
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.2: ¿cómo se llama el adaptador de narración, si en WMF «Cronista» es la simulación?
- Recommendation: Narrator / Narrador; no usar «Cronista»
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-3
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.3: ¿licencia del contenido de Tarkor (WMF dice CC BY-NC-SA 4.0, el instalador «todos los derechos reservados»)?
- Recommendation: CC BY-NC-SA 4.0 y corregir el instalador; confirmar con Álvaro
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-4
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.4: ¿qué hacer mientras gart, gmod y grun solo tienen diseño?
- Recommendation: Esquemas en formato gart con comprobación mínima propia; perfil fijo de Steam Deck; W6 espera a grun R5
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-5
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.5: ¿núcleo en Python o en TypeScript?
- Recommendation: Contrato gart y núcleo Python stdlib; el turno de Tarkor en TS hasta W5
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-6
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.6: ¿cómo se dan ids a los hechos si el canon no se puede tocar?
- Recommendation: Ids derivados al cargar (archivo, encabezados, huella) en gworld.canon/0
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-7
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.7: ¿de dónde salen los embeddings si grun no los promete?
- Recommendation: Pedir a grun un turno de embeddings; mientras, Embedder con grun.lock/0 y nomic-embed-text versionado
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-8
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.8: ¿comprobador determinista o juez con IA?
- Recommendation: Dos capas: determinista obligatoria y Judge opcional marcado
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-9
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.9: ¿generar mapas por semilla o importarlos?
- Recommendation: Importar FMG primero; generación por semilla después como MapImporter
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-10
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.10: ¿de quién son los prompts del Narrador?
- Recommendation: El kit pone el adaptador; el paquete, prompts, tono y modelos
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-11
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.11: ¿qué capa del canon de Tarkor indexa el RAG?
- Recommendation: Indexar y citar solo docs/rpgtarkor/
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-12
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.12: ¿son oficiales las abreviaturas gart, gmod, grun, gforge y gworld?
- Recommendation: Usar gworld y pedir que el portal lo recoja
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-13
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: DDD §8.13: ¿cuándo empieza cada hito?
- Recommendation: W0 ya; W1-W4 cuando quieras; W5-W6 tras la congelación de WMF
- Answer: según la recomendación
- Answered: 2026-11-26

## Q-14
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: Plan §Versiones: ¿qué escalera de versiones?
- Recommendation: Una versión menor por hito (0.1-0.5) y 1.0 cuando Tarkor consume el kit (W6)
- Answer: ok
- Answered: 2026-11-26

## Q-15
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: Plan §Versiones: ¿en qué orden van los hitos?
- Recommendation: W1, W4, W2, W3, W5, W6: W4 sube porque no tiene bloqueos externos y W5 lo necesita
- Answer: ok
- Answered: 2026-11-26

## Q-16
- Refs: W0
- Status: answered
- Asked: 2026-11-26
- Question: Plan §Ids: ¿qué prefijos de tarea?
- Recommendation: Prefijos PCK, MAP, CHK, RAG, VIV, NAR por hito
- Answer: ok
- Answered: 2026-11-26

## Q-17
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: A1. Arranque fijo (83 %): desactivar conectores/MCP sin uso (Claude Docs, Google…)?
- Recommendation: ok: lo haces tú en claude.ai mirando /context
- Answer: no se puede: en Claude en la nube los conectores no se desactivan; queda sin aplicar
- Answered: 2026-11-27

## Q-18
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: A2. Esperar el CI con una sola orden en segundo plano en vez de recordatorios?
- Recommendation: ok: espera única en segundo plano; apuntar ci-status.py --wait para el flujo
- Answer: ok
- Answered: 2026-11-27

## Q-19
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: A3. Revisión sin doble envoltorio (gw-reviewer Opus que solo lanza /code-review)?
- Recommendation: ok: /code-review desde la sesión principal; apuntar para gw-orchestrate-dealer
- Answer: ok
- Answered: 2026-11-27

## Q-20
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: A4. Encargos que nombran secciones de plan.md/ddd.md en vez de leerlas en la sesión principal?
- Recommendation: ok: nota en .claude/gw/gw-opt-tokens.md
- Answer: ok
- Answered: 2026-11-27

## Q-21
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: C1. Check local con cada versión de Python de la matriz instalada (el CI rojo de PCK-4)?
- Recommendation: ok: apuntar para el flujo (check.sh/ci-local.py), no se toca aquí
- Answer: ok
- Answered: 2026-11-27

## Q-22
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: C2. relatedTests/testMap también para .json (gworld/schemas/ → test_schemas_pack_canon.py)?
- Recommendation: ok: ampliar relatedTests/testMap a .json en esta rama
- Answer: ok
- Answered: 2026-11-27

## Q-23
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: C3. Activar taskRecord para registrar desviaciones del alcance?
- Recommendation: ok: activar taskRecord en esta rama
- Answer: ok
- Answered: 2026-11-27

## Q-24
- Refs: W1
- Status: answered
- Asked: 2026-11-27
- Question: C4. Barrido de leves PCK-8 sobre gworld/pack.py para 0.2 (¿sumar los 3 de canon.py?)?
- Recommendation: ok: PCK-8 para 0.2 con los 4 leves de pack.py, sin los 3 de canon.py
- Answer: ok: PCK-8 solo con los 4 leves de pack.py
- Answered: 2026-11-27

## Q-25
- Refs: MAP-1
- Status: answered
- Asked: 2026-11-27
- Question: MAP-1 a MAP-5 se reescriben desde map-generator/ de WMF, que no está en esta sesión. ¿a) me dejas adjuntar World-Maker-Fantasy (solo lectura), b) diseño gworld.map/0 solo desde ddd.md y lo ajusto en MAP-5, o c) otra cosa?
- Recommendation: a) permitir adjuntar zeldris/World-Maker-Fantasy en solo lectura (add_repo); el modo automático lo ha denegado
- Answer: a
- Answered: 2026-11-27

## Q-26
- Refs: MAP-5
- Status: answered
- Asked: 2026-11-27
- Question: Caminos: WMF (consultar.py:321-323) va solo por tierra por defecto; Topology.path va por todas las celdas salvo que se pase passable. a) por defecto solo tierra, como WMF; b) por defecto todas y MAP-5 pasa el filtro de tierra.
- Recommendation: b) Mantener passable=None = todas las celdas (sirve también para rutas por mar) y que MAP-5 pase passable de tierra al comparar con WMF.
- Answer: b
- Answered: 2026-11-27

## Q-27
- Refs: MAP-4
- Status: answered
- Asked: 2026-11-27
- Question: ¿Dónde viven las reglas de mapa de un mundo? a) archivo estructurado propio del paquete (gworld.maprules/0) con fuente = id de hecho; b) gworld lee lore.json/canon.json de WMF en su formato.
- Recommendation: a) Archivo de reglas de mapa en el paquete (artefacto nuevo gworld.maprules/0, citado desde el manifiesto), cada regla con su fuente como id de hecho; el de Tarkor se genera con un script que lee lore.json y canon.json de WMF en solo lectura.
- Answer: a
- Answered: 2026-11-27

## Q-28
- Refs: MAP-4
- Status: answered
- Asked: 2026-11-27
- Question: ¿MAP-4 incluye las medidas de canon.json (medir.py: área, envolvente, distancia ±3 %)? a) sí; b) no, tarea aparte MAP-6.
- Recommendation: a) Sí: MAP-4 cubre lore.json y las medidas de canon.json (área, envolvente y distancia con tolerancia, portando lo necesario de geometria.py); el oráculo de MAP-5 incluye los tests de medir.
- Answer: a
- Answered: 2026-11-27

## Q-29
- Refs: MAP-4
- Status: answered
- Asked: 2026-11-27
- Question: ¿Cómo citan las reglas regiones, provincias y continentes? a) por id de zona; b) por nombre, como WMF.
- Recommendation: a) Por id (region:18, landmass:2), sin ambigüedad entre capas y estable; el conversor de Tarkor resuelve los nombres y el informe muestra id y nombre.
- Answer: a
- Answered: 2026-11-27

## Q-30
- Refs: MAP-4
- Status: answered
- Asked: 2026-11-27
- Question: Tipos de regla: a) portar los 11 tipos tal cual, con las direcciones que admite WMF (solo norte-sur, oeste, sur); b) generalizar direcciones.
- Recommendation: b) Generalizar las direcciones (norte/sur/este/oeste en todos los tipos que tienen eje o lado): cuesta poco y un segundo mundo no depende de la geografía de Tarkor.
- Answer: b
- Answered: 2026-11-27

## Q-31
- Refs: MAP-5
- Status: answered
- Asked: 2026-11-27
- Question: Alcance de MAP-5 entre los 11 tests de map-generator: a) solo los de mapas del mundo (importar, medir, comprobar, lectura de consultar, medidas de visor); b) también consultar entero (celda por punto, frontera, costa, caminos por mar); c) los 11, edición y visor incluidos.
- Recommendation: a) Los 4 de «mapas del mundo»: importar, medir, comprobar y la parte de lectura de consultar (vecinos, path, distance_km), más la comprobación de medidas de test_visor (:66). Los otros 6 (banco, editar, historial, trazos, zonas, exportar) son edición, UI, agente o exportación y no tienen sitio en gworld hoy.
- Answer: a
- Answered: 2026-11-27

## Q-32
- Refs: MAP-5
- Status: answered
- Asked: 2026-11-27
- Question: Fixture del oráculo: a) leer Helek_World.map y helek.json del clon de WMF y saltar los tests sin él (como ahora); b) copiar helek.json (1 MB) a tests/fixtures; c) copiar los dos (4 MB).
- Recommendation: b) Copiar helek.json (1 MB) a tests/fixtures con su procedencia y la licencia de WMF: el CI no tiene el clon de WMF y hoy esos tests se saltan allí, así que la equivalencia solo se probaría en local. El .map (3 MB) se sigue leyendo de WMF si está; con helek.json basta para comprobar reglas, medidas y topología, y una prueba cruzada .map→gworld frente a helek.json corre donde estén los dos.
- Answer: b
- Answered: 2026-11-27

## Q-33
- Refs: MAP-5
- Status: answered
- Asked: 2026-11-27
- Question: corridor con región 0 (asunto abierto de MAP-4): a) paridad con WMF, las celdas sin provincia son pisables; b) no pisables; c) parámetro opcional con a) por defecto.
- Recommendation: a) Paridad con WMF: una celda de tierra sin provincia (región 0) se puede pisar en corridor. MAP-5 es de equivalencia, y cambiarlo haría fallar reglas que en WMF pasan; se documenta en el esquema y, si un mundo lo necesita, se añade luego un parámetro.
- Answer: a
- Answered: 2026-11-27

## Q-34
- Refs: MAP-5
- Status: answered
- Asked: 2026-11-27
- Question: Lo que WMF manda a «revisar» al importar (40 marcadores, 610 burgs borrados): a) ignorarlo; b) darlo en un informe del import, fuera del mapa; c) guardarlo en gworld.map/0.
- Recommendation: b) Llevar los marcadores automáticos y los burgs borrados a una lista de revisión en el informe de import (no al mapa): es lo que WMF pide a la persona que revise y no cambia el esquema gworld.map/0. a) sería perder ese aviso.
- Answer: b
- Answered: 2026-11-27

## Q-35
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Esperar el CI: pedir al flujo ci-status.py --wait (en segundo plano, avisa al acabar) y, hasta tenerlo, un bucle 'until ci-status.py; do sleep 60; done' con run_in_background en vez de send_later + ReadNotifications (20 llamadas en 0.2, ~2,4 M)
- Recommendation: sí: hoy no hay herramienta para esperar el CI, por eso se volvió a usar send_later
- Answer: sí
- Answered: 2026-11-27

## Q-36
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Revisiones: lanzar /code-review desde la sesión principal y, para el flujo, que gw-orchestrate-dealer deje de ofrecer el gw-reviewer Opus (5 en 0.2 pese a Q-19)
- Recommendation: sí: la regla Q-19 ya existe y no se siguió; convertirla en comprobación
- Answer: sí
- Answered: 2026-11-27

## Q-37
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Medición: pedir al flujo que measure.py sume los subagentes de todas las carpetas de sesión del proyecto (tras un relevo del contenedor se guardan en carpetas de otra sesión)
- Recommendation: sí: sin esto las mediciones mienten (ven 1 de 25 subagentes)
- Answer: sí
- Answered: 2026-11-27

## Q-38
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Modelo de los gw-worker: sonnet también para el esquema de una tarea y los arreglos de revisión (MAP-1 y 'Arreglos medios' fueron con opus)
- Recommendation: sí, con la excepción de AGENTS.md (ganchos, guardas, seguridad)
- Answer: sí
- Answered: 2026-11-27

## Q-39
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Agrupar en una orden git status/log/ci-status y leer filas del plan con roadmap.py show <id> en vez de sed de docs/plan.md (12 lecturas)
- Recommendation: sí: coste casi nulo
- Answer: sí
- Answered: 2026-11-27

## Q-40
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 1: tests/wmf.py único para localizar WMF y un test que rechace /home/ en tests/*.py
- Recommendation: sí
- Answer: sí
- Answered: 2026-11-27

## Q-41
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 2: línea en docs/plan.md para listar gworld/schemas/__init__.py y tools/__init__.py en ## Files
- Recommendation: sí
- Answer: sí
- Answered: 2026-11-27

## Q-42
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 3 (flujo): pasos en paralelo con firmas compartidas en el encargo y paso de integración antes de la revisión
- Recommendation: sí, como pendiente del flujo
- Answer: sí, como pendiente del flujo
- Answered: 2026-11-27

## Q-43
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 4 (flujo): el encargo del dealer abre la tarea con task.py start <id>
- Recommendation: sí, como pendiente del flujo
- Answer: sí, como pendiente del flujo
- Answered: 2026-11-27

## Q-44
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 5 (flujo): measure.py suma subagentes de todas las carpetas de sesión
- Recommendation: sí (ya pedido)
- Answer: sí
- Answered: 2026-11-27

## Q-45
- Refs: W4
- Status: answered
- Asked: 2026-11-27
- Question: Retro 0.2, candidato 6: barrido MAP-6 en 0.3 con los 3 leves de gworld/maps.py (¿y los 2 de topology.py?)
- Recommendation: sí, solo maps.py; topology.py en otro barrido
- Answer: sí, solo maps.py
- Answered: 2026-11-27

## Q-46
- Refs: W3
- Status: answered
- Asked: 2026-11-28
- Question: W2 (0.3) está bloqueado por el GVE. ¿Qué hago ahora? a) adelantar W3 (0.4) con RAG-1 (troceado del canon en Chunk) y RAG-2 (interfaces Store y Embedder); b) barrido de los 3 leves de gworld/topology.py (MAP-3); c) esperar al GVE
- Recommendation: a: empezar 0.4 por RAG-1 y RAG-2, que no esperan a nadie (D7 permite un Embedder propio mientras tanto)
- Answer: a
- Answered: 2026-11-28

## Q-47
- Refs: W3
- Status: answered
- Asked: 2026-11-28
- Question: ¿Saco 0.3 sin W2, solo con MAP-6 y el barrido de topology.py?
- Recommendation: no; si se adelanta 0.4, el barrido de topology.py va dentro de 0.4
- Answer: no
- Answered: 2026-11-28

## Q-48
- Refs: RAG-3
- Status: answered
- Asked: 2026-11-28
- Question: grun ya publicó el protocolo como grun.lock/1 (solo cambia el campo schema; /0 queda superado y su test lo rechaza). ¿a) implemento /1; b) /0 como dice la ADR?
- Recommendation: a: grun.lock/1 (mismo flock y ruta; el registro escribe schema grun.lock/1) y se corrige ADR 0006 y el plan
- Answer: a
- Answered: 2026-11-28

## Q-49
- Refs: RAG-3
- Status: answered
- Asked: 2026-11-28
- Question: WMF cambió su modelo de embeddings por defecto a bge-m3 (1024 dims); nomic-embed-text (768) queda en evals viejas. ¿Modelo por defecto: a) bge-m3; b) nomic-embed-text como dice la ADR?
- Recommendation: a: bge-m3, que es el de WMF hoy (la ADR dice «el de WMF») y hace comparable RAG-5 con sus rag-casos; nomic-embed-text sigue valiendo pasándolo a mano
- Answer: a
- Answered: 2026-11-28

## Q-50
- Refs: RAG-3
- Status: answered
- Asked: 2026-11-28
- Question: ¿Cómo toma gworld el candado? a) implementación propia con fcntl.flock (stdlib) según el protocolo; b) importar grun como extra opcional
- Recommendation: a: candado propio con fcntl (stdlib) siguiendo el protocolo, sin depender de grun; fuera de POSIX, error claro
- Answer: a
- Answered: 2026-11-28
