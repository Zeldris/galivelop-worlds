<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | F0: plan de versiones escrito en `docs/plan.md` (confirmado: Q-14 a Q-16). Falta llevar F0 a `main` |
| **Último punto estable** | el commit «Flujo Galivelop-workflow v0.9.1»: flujo instalado, licencia MIT |
| **Siguiente paso** | Fase 1 hecha (0 hallazgos graves o medios). Fase 2: gw-opt-tokens y retro, presentadas a la persona; luego reviewed.sh y PR |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde. Deuda: aún no hay código ni tests propios (llegan en W1) |

## Para la próxima publicación

F0: el DDD cerrado con sus decisiones (D1-D13, ADR 0001-0006) y el plan de versiones (`docs/plan.md`)

## Hecho (5 últimas)

1. 2026-11-26 — F0: plan de versiones 0.1-1.0 en `docs/plan.md` (W4 antes que W2 y W3), registrado en `plan` de `.claude/gw.json`.
2. 2026-11-26 — F-1 cerrada: decisiones D1-D13 según las recomendaciones; ADR 0001-0006.
3. 2026-11-26 — DDD borrador 2: comprobado contra los repos hermanos y WMF; el mundo vivo se rediseña, el mapa se importa, ids de hecho derivados, «Narrador» en vez de «Cronista».
4. 2026-11-26 — Galivelop-workflow v0.9.1 aplicado (idioma es, PR a `main`, sin firmas del agente, prefijo `gwd-`,
   licencia MIT).

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
