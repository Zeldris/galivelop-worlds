<!-- galivelop-workflow v0.9.1 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | `claude/release-0.1.0` |
| **Fase / tarea** | 0.1.0 publicada el 2026-11-27: PR #3 fusionado (`7e03ed1`), etiqueta y release `v0.1.0`. Sin tarea en curso |
| **Último punto estable** | `docs(W1): 0.1.0 publicada` |
| **Siguiente paso** | Empezar 0.2 (MAP-1) desde esta rama, que lleva esta bitácora por delante de `main` |
| **Check** | `python3 .claude/gw/scripts/md-links.py`, `python3 .claude/gw/scripts/agent-map.py`, `python3 .claude/gw/scripts/tests-after-main.py`, `python3 -m unittest discover -s tests -t .`, `python3 .claude/gw/scripts/ci-local.py --validate`: verde (los tests ya van en el check) |

## Para la próxima publicación

(nada todavía)

## Hecho (5 últimas)

1. 2026-11-28 — Test de Tarkor (`tests/test_tarkor_pack.py`) en verde, comprobado solo en local (Steam Deck), con `GW_WMF_DIR=../World-Maker-Fantasy` en `19f3f10d`: 518 hechos; en CI se salta.
2. 2026-11-27 — 0.1.0 publicada: release `v0.1.0` sobre `7e03ed1` (PR #3, CI en verde; retro omitida y fusión autorizadas por la persona).
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
