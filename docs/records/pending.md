# Pendiente

Lo que queda abierto; la bitácora solo apunta aquí. Se añade y se quita en este archivo.

## Pendiente
- Confirmar con Álvaro la licencia CC BY-NC-SA 4.0 del contenido de Tarkor (D3, ADR 0003).
- Repo Instalador-WMF-Tarkor: corregir «todos los derechos reservados» (D3); tarea de ese repo.
- Repo galivelop-runtime: pedir un turno de embeddings bajo el candado (D7); tarea de ese repo.
- Repo galivelop-models: añadir worlds entre sus consumidores (`chat`, `embed`); tarea de ese repo.
- Portal: pedir que recoja Galivelop Worlds y la abreviatura `gworld` (D12).
- Leer el GVE (privado; acceso denegado en esta sesión) antes de W2.
- Leve (revisión F0): AGENTS.md y REVIEW.md citan tres órdenes del check; `check` de `.claude/gw.json` lleva también `ci-local.py --validate`. Arreglar al regenerar el flujo.
- Leve (revisión F0): `workflowClone` y `workflowCloneAlso` de `.claude/gw.json` son rutas del entorno de instalación; comprobar que `review-scope.py --workflow` resuelve una antes de la fase 3.
- Al llegar W1 con código: activar `taskRecord` en `.claude/gw.json`.
- Repo Galivelop-workflow (error del flujo): la instalación dejó sus 3 primeros commits (`5f8d1e2`, `260d7e8`, `44bab3e`) con autor `Claude <noreply@anthropic.com>`. Al instalar, el flujo debe pedir siempre a la persona su `user.name` y `user.email` y fijarlos en el `git config` del repo antes del primer commit; tarea de ese repo. Aquí esos commits se dejan como están (decisión de la persona, 2026-11-27).
- Leve (revisión de bloque W1): `relatedTests` y `testMap` de `.claude/gw.json` solo casan `.py` (un cambio en `gworld/schemas/*.json` no corre tests en el `pre-push`) y `gworld/schemas/__init__.py` se mapea a un `tests/test_schemas___init__.py` inexistente; ampliar a `.json` y mapear `gworld/schemas/` a `tests/test_schemas_pack_canon.py`.
- Leve (revisión de bloque W1): `load_pack` con `canon.path` `"."` o `"sub/.."` toma la raíz del paquete como canon (incluye `pack.json`, que contiene la huella) y siempre da `canon_hash`; rechazarlo con mensaje claro.
- Leve (revisión de bloque W1): `canon_digest` trata una ruta que no es archivo ni directorio (FIFO, socket) como directorio vacío; dar `PackError`.
- Leve (revisión de bloque W1): en `canon_digest`, el mensaje de `canon_outside` dice «fuera del paquete» cuando es «fuera del canon», y un nombre de archivo no UTF-8 da `UnicodeEncodeError` en vez de `PackError`.
- Leve (revisión de bloque W1): `gworld/schema.py:62` usa `token.isdigit()`, verdadero para `'²'`; usar `token.isascii() and token.isdigit()`. Y `KIND_ID_RE` acepta puntos dobles o al final (`gworld.pack./0`); ajustarlo si gart lo permite.
