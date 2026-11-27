<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | W0 cerrada y fusionada en `main` (PR #1, `ea214e2`, CI en verde, fusión confirmada por la persona el 2026-11-27). W1 (versión 0.1): PCK-1 a PCK-7 hechos |
| **Último punto estable** | `chore(W1): aplicar la retro de W1 decidida por la persona` |
| **Siguiente paso** | PR #2 de 0.1 a `main` abierto (marca de revisión `e02a1b6`); esperar el CI en verde y la confirmación de la persona para fusionar; luego la bitácora y `/clear` |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

0.1 (W1 Paquete y canon): PCK-1 a PCK-7 de `docs/plan.md`

## Hecho (5 últimas)

1. 2026-11-27 — Retro de W1 decidida (Q-17 a Q-24): todo aprobado salvo A1 (en la nube no se desactivan conectores); `taskRecord` activado, tests relacionados para `gworld/schemas/`, PCK-8 en 0.2.
2. 2026-11-27 — PCK-7: paquete de Tarkor de prueba sobre `docs/rpgtarkor/` de WMF, solo lectura; 518 hechos, ids estables.
3. 2026-11-27 — W0 fusionada en `main` (PR #1): flujo, DDD v1, ADR, plan 0.1-1.0 y retro de F0 aprobada.
4. 2026-11-26 — F0: plan de versiones 0.1-1.0 en `docs/plan.md` (W4 antes que W2 y W3), registrado en `plan` de `.claude/gw.json`.
5. 2026-11-26 — F-1 cerrada: decisiones D1-D13 según las recomendaciones; ADR 0001-0006.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
