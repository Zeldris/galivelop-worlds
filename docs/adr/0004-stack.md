# ADR 0004: núcleo en Python stdlib con contrato en artefactos gart

- **Estado:** aceptada (2026-11-26) · **Decisión:** D5 y D4 del [DDD](../ddd.md)

## Contexto

WMF es TypeScript (Fastify, Prisma, React); el resto de Galivelop es Python ≥ 3.10 solo con stdlib. gart, gmod y
grun solo tienen diseño.

## Decisión

- El contrato entre lenguajes son los artefactos `gworld.*` validados con gart.
- El núcleo es Python ≥ 3.10 con stdlib; lo que necesite extras (`Store`, `Embedder`) es opcional y falla con la
  orden que lo instala.
- El turno de Tarkor sigue en TypeScript hasta W5; entonces se decide con datos si se porta o se publica un paquete
  npm con el mismo contrato.
- Mientras gart no publique su validador, los esquemas se escriben en su formato y se validan con una comprobación
  mínima propia, que se cambia por su copia vendorizada. Sin `gmod.machine/0`, un perfil fijo de Steam Deck. W6
  espera a grun R5.
