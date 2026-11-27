# ADR 0005: ids de hecho derivados fuera del canon

- **Estado:** aceptada (2026-11-26) · **Decisión:** D6 y D11 del [DDD](../ddd.md)

## Contexto

El canon de Tarkor (`docs/rpgtarkor/`, 34 archivos de prosa Markdown) no tiene ids y solo lo cambia Álvaro. Las
contradicciones tienen que citar un `Fact` con su id.

## Decisión

- El id de cada `Fact` se deriva al cargar: archivo, ruta de encabezados y huella del texto normalizado.
- Se guarda en `gworld.canon/0`; nada se escribe en el canon.
- Se indexa y se cita solo `docs/rpgtarkor/`; `docs/canon-opencode/` es un resumen y nunca es fuente de un `Fact`.

## Consecuencias

Un cambio en una sección cambia solo los ids de esa sección (invariante 5), y el índice lo detecta por la huella.
