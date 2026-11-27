# ADR 0002: el adaptador de narración se llama «Narrador»

- **Estado:** aceptada (2026-11-26) · **Decisión:** D2 del [DDD](../ddd.md)

## Contexto

En WMF, «Cronista» es la simulación del mundo vivo (`backend/src/services/cronista/*`: sucesos, misiones, economía,
facciones), y quien narra es `narrador.ts`. El instalador llama «Cronista» a un modelo que clasifica acciones. El
borrador 1 usaba «Cronista» para el adaptador de narración.

## Decisión

El adaptador se llama `Narrator` / «Narrador». El kit no usa «Cronista» en ningún nombre.

## Consecuencias

El glosario y el código del kit no chocan con los nombres de WMF; el adaptador de Tarkor traduce.
