<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | 0.2 (W4 Mapas): MAP-1 a MAP-3 y PCK-8 hechas y revisadas (`gworld/maps.py`, `gworld/topology.py`); WMF clonado en solo lectura en `../World-Maker-Fantasy` (Q-25: a); MAP-4 empezada: ficha `docs/tasks/MAP-4.md` (4 pasos), Q-26 a Q-30 contestadas. Presupuesto de compactaciones: 1 |
| **Último punto estable** | Fusión del PR #2 en `main` (`6d2d4e7`) |
| **Siguiente paso** | MAP-4 pasos 1 (artefacto `gworld.maprules/0` y `bind`) y 2 (geometría) en paralelo; luego 3 (motor) y 4 (conversor de Tarkor) |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

0.2 (W4 Mapas): MAP-1 a MAP-5 y PCK-8 de `docs/plan.md`

## Hecho (5 últimas)

1. 2026-11-27 — MAP-1 a MAP-3 y PCK-8 hechas y revisadas: esquema map/0, importador FMG, check_map y Topology; Helek_World.map (5120 celdas) pasa.
2. 2026-11-27 — W1 fusionada en `main` (PR #2, `6d2d4e7`): paquete `gworld/` con esquemas, `load_pack` y lector del canon; retro de W1 aplicada.
3. 2026-11-27 — Retro de W1 decidida (Q-17 a Q-24): todo aprobado salvo A1 (en la nube no se desactivan conectores); `taskRecord` activado, tests relacionados para `gworld/schemas/`, PCK-8 en 0.2.
4. 2026-11-27 — PCK-7: paquete de Tarkor de prueba sobre `docs/rpgtarkor/` de WMF, solo lectura; 518 hechos, ids estables.
5. 2026-11-27 — W0 fusionada en `main` (PR #1): flujo, DDD v1, ADR, plan 0.1-1.0 y retro de F0 aprobada.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
