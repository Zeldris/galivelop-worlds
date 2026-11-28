# 2026-11-28 · code-review · pending · RAG-2

## Why

Revisión corta de RAG-2 (diff desde `94440b9`, subagente `gw-reviewer` con sonnet): 1 hallazgo medio y 7 leves.
El medio: `require_extra` solo daba `MissingExtraError` si faltaba el paquete raíz; con `pgvector.psycopg` ausente
(versión vieja del extra) salía un `ModuleNotFoundError` sin la orden de instalar (invariante 13).

## Alternatives

- Capturar todo `ImportError` como extra ausente: descartado, disfraza un import interno roto del propio extra.
- Arreglar también los leves aquí: descartado, casi todos tocan el contrato de `Store` y se deciden con el `Store`
  real en RAG-3; van a `docs/records/pending.md`.

## Changed because

Se trata como extra ausente que falte `module` o cualquiera de sus paquetes padre; un test nuevo lo cubre (rojo sin
el arreglo) y el de fallo interno comprueba el nombre del módulo que falta.
