<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `ccr-8aaeec3a-h97oxt` |
| **Fase / tarea** | Flujo Galivelop-workflow v0.9.1 aplicado. F-1 (mejorar, ampliar y cerciorar el DDD) en curso: borrador 2 en `docs/ddd.md`, comprobado contra gart, gmod, grun, WMF y consumidores; 13 preguntas abiertas en `docs/questions.md` (Q-1 a Q-13); F0 (decisiones a `main` y reparto en versiones) después |
| **Último punto estable** | el commit «Flujo Galivelop-workflow v0.9.1»: flujo instalado, licencia MIT |
| **Siguiente paso** | F-1: apuntar las respuestas de la persona a Q-1…Q-13 (`questions.py answer`), pasarlas a «Decisiones» del DDD y a ADR en `docs/adr/`, y cerrar F-1 |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde. Deuda: aún no hay código ni tests propios (llegan en W1) |

## Para la próxima publicación

F0: el DDD cerrado con sus decisiones y la escalera de versiones; espera a terminar F-1

## Hecho (5 últimas)

1. 2026-11-26 — DDD borrador 2: comprobado contra los repos hermanos y WMF; el mundo vivo se rediseña, el mapa se importa, ids de hecho derivados, «Narrador» en vez de «Cronista».
2. 2026-11-26 — Galivelop-workflow v0.9.1 aplicado (idioma es, PR a `main`, sin firmas del agente, prefijo `gwd-`,
   licencia MIT).

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recover.py --state`.
