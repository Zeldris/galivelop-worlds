<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | W0 cerrada y fusionada en `main` (PR #1, `ea214e2`, CI en verde, fusión confirmada por la persona el 2026-11-27). W1 (versión 0.1): PCK-1 a PCK-7 hechos |
| **Último punto estable** | `fix(PCK-5): arreglos de la revisión del resto del bloque W1` |
| **Siguiente paso** | Decisión de la persona sobre la retro de W1 (`docs/records/retro-2026-11-27-w1.md`, A1-A4 y candidatos 1-4); aplicar lo aprobado, escribir el `**Estado:**`, luego reviewed.sh y PR de 0.1 a main |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

0.1 (W1 Paquete y canon): PCK-1 a PCK-7 de `docs/plan.md`

## Hecho (5 últimas)

1. 2026-11-27 — PCK-7: paquete de Tarkor de prueba sobre `docs/rpgtarkor/` de WMF, solo lectura; 518 hechos, ids estables.
2. 2026-11-27 — W0 fusionada en `main` (PR #1): flujo, DDD v1, ADR, plan 0.1-1.0 y retro de F0 aprobada.
3. 2026-11-26 — F0: plan de versiones 0.1-1.0 en `docs/plan.md` (W4 antes que W2 y W3), registrado en `plan` de `.claude/gw.json`.
4. 2026-11-26 — F-1 cerrada: decisiones D1-D13 según las recomendaciones; ADR 0001-0006.
5. 2026-11-26 — DDD borrador 2: comprobado contra los repos hermanos y WMF; el mundo vivo se rediseña, el mapa se importa, ids de hecho derivados, «Narrador» en vez de «Cronista».

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
