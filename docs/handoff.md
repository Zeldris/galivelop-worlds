<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | MAP-6 hecho y con su revisión de bloque (1 hallazgo arreglado: ruta que no es objeto tumbaba el mapa). 0.2.0 en `main` (PR #5, `6c14104`); falta la etiqueta y la release `v0.2.0`, que crea la persona en GitHub. Presupuesto de compactaciones: 1 |
| **Último punto estable** | Revisión de bloque de MAP-6 (`Findings: 1`) |
| **Siguiente paso** | La persona crea la etiqueta y la release `v0.2.0` sobre `6c14104` con `docs/releases/v0.2.0.md` (el 2026-11-28 aún no existía); comprobar con `list_releases`. CHK-1 sigue esperando el acceso al GVE |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

_(nada todavía: 0.3 empieza con MAP-6)_

## Hecho (5 últimas)

1. 2026-11-28 — MAP-6: `gworld/maps.py` salta rutas inválidas y burgos sin nombre, `parent` solo de regiones existentes, `_C_RIVER` fuera y `_MIN_RECORDS = 45` explicado; `code_of` comprueba el mensaje.
2. 2026-11-28 — 0.2.0 publicada en `main` (PR #5, `6c14104`): versión 0.2.0 y notas en `docs/releases/v0.2.0.md`; la etiqueta y la release, pendientes de la persona.
3. 2026-11-28 — 0.2 fusionada en `main` (PR #4, `45884d4`) con el CI en verde; fase 2 aplicada (Q-35 a Q-45: notas de ahorro, `tests/wmf.py`, MAP-6 en 0.3).
4. 2026-11-27 — MAP-5: equivalencia con `map-generator/` de WMF sobre Helek (import, medidas, reglas, caminos); fixtures en `tests/fixtures/helek/`; revisión de bloque con 2 arreglos.
5. 2026-11-27 — MAP-4: comprobador de mapas contra el canon (gworld.maprules/0, geometría, motor check_rules, conversor de Tarkor; humo con Helek 13+9 ok, 3 sin decidir); revisión de bloque con 12 arreglos

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
