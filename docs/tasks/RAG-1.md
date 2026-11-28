# RAG-1 · Troceado del canon en Chunk con los ids de hecho

## Goal

Trocear los `Fact` del canon en `Chunk` listos para indexar, cada uno con el id del hecho de que sale, sin
embeddings ni almacén (eso es RAG-2 y siguientes).

## Scope

`gworld/chunks.py` (nuevo) y `tests/test_chunks.py` (nuevo). Solo lee `Fact` de `gworld/canon.py`; no lo cambia.

## Acceptance

- [x] `Chunk` (inmutable): `id`, `fact_id`, `n`, `text`, con `to_json`.
- [x] `chunk_facts(facts, max_words=200)`: un hecho corto es un solo `Chunk`; uno largo se parte por párrafos y, si un
  párrafo aún pasa del tope, por frases y por último por palabras; ningún `Chunk` pasa de `max_words`.
- [x] Ids deterministas (`chunk:` + huella de `fact_id`, `n` y texto): mismo canon, mismos ids; cambiar un hecho cambia
  solo los ids de sus fragmentos.
- [x] Todo el texto del hecho queda cubierto (sin pérdidas) y el orden se conserva; un hecho vacío no da `Chunk`.
- [x] Prueba con el canon de ejemplo del paquete (`tests/test_example_world.py` usa uno) y `max_words` inválido falla
  con su motivo.

## Files

`gworld/chunks.py`, `tests/test_chunks.py`, `docs/plan.md` (marca de RAG-1), `docs/handoff.md`.

## Change log

- `gworld/chunks.py`: `Chunk`, `ChunkError(ValueError)` y `chunk_facts` (párrafos, frases, palabras; ids `chunk:` + huella de `fact_id`, `n` y texto).
- `tests/test_chunks.py`: 15 pruebas (bordes, unicode, ids deterministas, cobertura en orden, canon de ejemplo).

## Verification

`python3 -m unittest discover -s tests -t .` en verde; los tests nuevos fallan sin su código (`red-without-fix.sh`).

Preguntas abiertas: van a [docs/questions.md](../questions.md), no aquí.
