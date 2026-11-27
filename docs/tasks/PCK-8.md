# PCK-8 · Barrido de leves de gworld/pack.py

## Goal

Cerrar los 4 leves de `gworld/pack.py` de la retro W1 (Q-24), sin tocar `gworld/canon.py`.

## Scope

`canon.path` raíz, FIFO/socket, mensaje y nombres no UTF-8 en `canon_digest`, `RecursionError` de `validate`.

## Acceptance

- [x] `"."` y `"sub/.."` dan `canon_outside`.
- [x] FIFO/socket en el canon da `canon_special`.
- [x] Mensaje «fuera del canon»; nombre no UTF-8 da `canon_name`.
- [x] `RecursionError` de `validate` da `too_deep`.

## Files

`gworld/pack.py`, `tests/test_pack.py`, `docs/plan.md` (marca PCK-8 hecha).

## Change log

2026-11-27: los cuatro arreglos con un test cada uno que comprueba el código y el mensaje.  `docs/plan.md`: PCK-8 marcada como hecha.

## Verification

`python3 -m unittest discover -s tests -t .` en verde; `red-without-fix.sh` confirma que los tests fallan sin el arreglo.

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
