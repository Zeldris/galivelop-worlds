<!-- galivelop-workflow v0.9.1 -->
# gw-opt-tokens — notas del proyecto

Las lee la skill `gw-opt-tokens` antes de proponer nada, y se actualizan cuando la persona aprueba un cambio. El flujo
las crea una vez; desde entonces son del proyecto.

## Herramientas que ya ahorran

<!-- Una línea cada una, con cómo se corre. -->
- `python3 .claude/gw/scripts/recover.py --state` y `--search "<texto>"`: recuperar lo que se llevó una
  compactación.
- `gw-orchestrate-dealer`: el trabajo de más de un paso, repartido a subagentes de contexto limpio. Las tareas de
  `docs/plan.md` (desde PCK-1) van a un `gw-worker` con `sonnet`, con la tarea, sus secciones del DDD y el check.

## Costes conocidos

<!-- Lo que se ha visto que cuesta mucho en este proyecto (archivos grandes leídos enteros, salidas largas...). -->
- `docs/ddd.md` (326 líneas) se leyó 12 veces en F0 (254k arrastrados): leerlo por secciones, `grep -n '^#'` y
  `sed -n` de la que haga falta; entero solo en la revisión.
- Arranque fijo ~89k por llamada (75 % de la entrada en F0): conectores y MCP; quitar los que no se usen.

## Ajustes en vigor

- Ventana de compactación automática: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en `.claude/settings.json`.

## Referencias medidas

<!-- Cifras medidas con las que comparar: fecha, sesión, contexto medio, llamadas, total. -->
- 2026-11-26, F0: 82 llamadas, contexto medio 118k, techo 151k, 9,7 M de entrada (98 % caché); subagentes 1,5 M.
