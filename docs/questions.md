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
- Status: open
- Asked: 2026-11-27
- Question: MAP-1 a MAP-5 se reescriben desde map-generator/ de WMF, que no está en esta sesión. ¿a) me dejas adjuntar World-Maker-Fantasy (solo lectura), b) diseño gworld.map/0 solo desde ddd.md y lo ajusto en MAP-5, o c) otra cosa?
- Recommendation: a) permitir adjuntar zeldris/World-Maker-Fantasy en solo lectura (add_repo); el modo automático lo ha denegado
