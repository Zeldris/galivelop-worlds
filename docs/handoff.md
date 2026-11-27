<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | 0.2 (W4 Mapas): MAP-1 a MAP-5 y PCK-8 hechas y revisadas (bloque MAP-5: 2 medios arreglados en `eb7ada7`, 8 leves en pending). Presupuesto de compactaciones: 1 |
| **Último punto estable** | Fusión de `main` con la release 0.1.0 (PR #3, `7e03ed1`) en la rama |
| **Siguiente paso** | Fase 3 de 0.2: `532a13f` revisado (1 leve arreglado); `reviewed.sh`, push y el PR de 0.2 a `main` con la skill `pr` |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

0.2 (W4 Mapas): MAP-1 a MAP-5 y PCK-8 de `docs/plan.md`

## Hecho (5 últimas)

1. 2026-11-27 — MAP-5: equivalencia con `map-generator/` de WMF sobre Helek (import, medidas, reglas, caminos); fixtures en `tests/fixtures/helek/`; revisión de bloque con 2 arreglos.
2. 2026-11-27 — MAP-4: comprobador de mapas contra el canon (gworld.maprules/0, geometría, motor check_rules, conversor de Tarkor; humo con Helek 13+9 ok, 3 sin decidir); revisión de bloque con 12 arreglos
3. 2026-11-27 — MAP-1 a MAP-4 y PCK-8 hechas y revisadas: esquema map/0, importador FMG, check_map y Topology; Helek_World.map (5120 celdas) pasa.
4. 2026-11-27 — W1 fusionada en `main` (PR #2, `6d2d4e7`): paquete `gworld/` con esquemas, `load_pack` y lector del canon; retro de W1 aplicada.
5. 2026-11-27 — Retro de W1 decidida (Q-17 a Q-24): todo aprobado salvo A1 (en la nube no se desactivan conectores); `taskRecord` activado, tests relacionados para `gworld/schemas/`, PCK-8 en 0.2.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
