# ADR 0001: reescribir el núcleo en vez de extraerlo de WMF

- **Estado:** aceptada (2026-11-26) · **Decisión:** D1 del [DDD](../ddd.md)

## Contexto

El turno de World-Maker-Fantasy vive en `backend/src/services/turnResolution.ts` (unas 7.400 líneas), escribe en
Postgres con Prisma, usa `Math.random()` en varios servicios y `Date.now()`, y `Save` no tiene semilla. Su mapa se
importa de Azgaar FMG y se edita a mano. No hay un motor separable ni determinista.

## Decisión

El núcleo se escribe de nuevo contra el contrato del DDD: reglas puras, azar con semilla (`Rng`) y reloj de juego
(`Clock`). El oráculo de equivalencia son escenarios dorados sacados del comportamiento de WMF, no sus tests, que
usan la base real y azar sin semilla. Tarkor pasa a usar el kit solo en W6, con una tarea en su propio repo.

## Consecuencias

- Hay que escribir los escenarios dorados antes de W5.
- WMF no se toca hasta W6.
- El determinismo es una propiedad nueva del kit, no heredada: lleva sus invariantes 1 y 2.
