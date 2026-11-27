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
- Arranque fijo ~89k por llamada (75 % en F0, 83 % en W1): conectores y MCP. En Claude en la nube no se pueden
  desactivar (Q-17): no proponerlo otra vez.
- `docs/plan.md` y `docs/ddd.md` leídos para escribir encargos (W1: 11 y 8 veces, ~540k): el encargo nombra la tarea
  y los encabezados de sus secciones, y el `gw-worker` las lee; devuelve sus dudas antes de escribir código (Q-20).

## Ajustes en vigor

- Esperar el CI con una sola orden en segundo plano que avisa al acabar, no con `send_later` ni recordatorios
  repetidos (Q-18).
- Revisiones: `/code-review` desde la sesión principal, sin envolverlo en un `gw-reviewer` Opus que solo lo lanza
  (Q-19).

- Esperar el CI (Q-35): hasta que el flujo tenga `ci-status.py --wait`, una sola orden en segundo plano
  (`until python3 .claude/gw/scripts/ci-status.py >/dev/null; do sleep 60; done`, con `run_in_background`); nunca
  `send_later` + `ReadNotifications` (0.2: ~20 llamadas, ~2,4 M).
- Revisiones (Q-36, refuerza Q-19): ningún `gw-reviewer` con Opus que solo lance `/code-review` (0.2: 5).
- `gw-worker` con `sonnet` también para el esquema de una tarea y los arreglos de revisión (Q-38); `opus` solo para
  ganchos, guardas, seguridad y los scripts que los llaman.
- Menos llamadas sueltas (Q-39): `git status`, `git log` y `ci-status` en una sola orden; las filas del plan con
  `roadmap.py show <id>`, no con `sed` de `docs/plan.md` (0.2: 12 lecturas).

- Ventana de compactación automática: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en `.claude/settings.json`.

## Referencias medidas

<!-- Cifras medidas con las que comparar: fecha, sesión, contexto medio, llamadas, total. -->
- 2026-11-27, 0.2 (W4): 267 llamadas, contexto medio 119k, techo 161k, 31,8 M de entrada (98 % caché); subagentes
  17,6 M en 25 registros (sonnet 12,7 M, opus 4,9 M), sumados a mano: `measure.py` solo ve la carpeta de la sesión
  actual (Q-37, pedido al flujo).
- 2026-11-27, W1: 137 llamadas, contexto medio 107k, techo 152k, 14,6 M de entrada (98 % caché); subagentes 0,74 M.
- 2026-11-26, F0: 82 llamadas, contexto medio 118k, techo 151k, 9,7 M de entrada (98 % caché); subagentes 1,5 M.
