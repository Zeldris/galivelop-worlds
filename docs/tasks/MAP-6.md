# MAP-6 · Barrido de leves de `gworld/maps.py`

## Goal

Que un `.map` con rutas o burgos ilegibles se importe saltando esos registros en vez de fallar entero, y que una
provincia solo lleve `parent` si su región existe.

## Scope

`gworld/maps.py` (rutas, burgos, provincias, mensaje de truncado) y `tests/test_maps.py` (motivo en los fallos
esperados y casos de salto). Nada fuera del importador.

## Acceptance

- [x] Ruta de grupo no slug, de menos de 2 puntos, con puntos ilegibles o que no es objeto: se salta.
- [x] Burgo sin `name` o sin posición legible: se salta.
- [x] Provincia de estado inexistente: sin `parent`.
- [x] Los tests de fallo comprueban el motivo.

## Files

`gworld/maps.py`, `tests/test_maps.py`.

## Change log

`e4a5ce4` el barrido; revisión de bloque: la ruta que no es objeto tumbaba el mapa (`AttributeError`).

## Verification

`python3 -m unittest discover -s tests -t .` en verde; el test de rutas falla sin el arreglo (`red-without-fix.sh`).

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
