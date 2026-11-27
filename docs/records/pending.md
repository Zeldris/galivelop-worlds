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
- Repo Galivelop-workflow (error del flujo): la instalación dejó sus 3 primeros commits (`5f8d1e2`, `260d7e8`, `44bab3e`) con autor `Claude <noreply@anthropic.com>`. Al instalar, el flujo debe pedir siempre a la persona su `user.name` y `user.email` y fijarlos en el `git config` del repo antes del primer commit; tarea de ese repo. Aquí esos commits se dejan como están (decisión de la persona, 2026-11-27).
- Leve (revisión de bloque W1): `gworld/schema.py:62` usa `token.isdigit()`, verdadero para `'²'`; usar `token.isascii() and token.isdigit()`. Y `KIND_ID_RE` acepta puntos dobles o al final (`gworld.pack./0`); ajustarlo si gart lo permite.
- El test de Tarkor (`tests/test_tarkor_pack.py`) se salta en CI (sin WMF); se comprueba en local con `GW_WMF_DIR=<ruta de World-Maker-Fantasy>`.
- Leve (revisión de bloque W1): `tests/test_example_world.py` escribe `gworld/_tmp_inv9.json` en el paquete fuente; usar carpeta temporal.
- Leve (revisión de bloque W1): `tests/test_canon.py`, el grep de escrituras del invariante 4 da falsos positivos con `open()` de lectura y no ve `shutil.copy*`/`os.replace`/`unlink`/`touch`/`os.open`.
- Leve (revisión de bloque W1): `tests/test_example_world.py`, invariante 9: frases comunes («el Detonante», «el Estallido», «la Concordia») sin distinguir mayúsculas dan falsos positivos.
- Leve (revisión de bloque W1): `gworld/canon.py`: el texto de los encabezados no normaliza espacios y un cambio de espacios cambia los ids.
- Leve (revisión de bloque W1): `gworld/canon.py` `_FENCE` acepta info string con comilla invertida y `# #` da un encabezado `#`.
- Leve (revisión de bloque W1): `gworld/canon.py` filtra `.md` distinguiendo mayúsculas y `canon_digest` hashea todo; un `.MD` entra en la huella sin dar hechos.
- Leve (revisión de bloque W1): `tests/test_tarkor_pack.py` fija 34 archivos y exige un hecho por `.md`; un `.md` vacío en WMF lo rompe.
- Leve (revisión de bloque MAP): `gworld/maps.py` da `parent: region:N` a una provincia cuyo estado está borrado o es el 0; filtrar con `known` como `capitalOf`.
- Leve (revisión de bloque MAP): `gworld/pack.py` da `canon_special` en vez de `canon_outside` a un symlink del canon que apunta fuera a un FIFO o dispositivo.
- Leve (revisión de bloque MAP): `gworld/maps.py` `_MIN_RECORDS = 45` cuando FMG guarda 46 (o explicar por qué el último es opcional); `_C_RIVER` sin uso.
- Leve (revisión de bloque MAP): `gworld/maps.py` tumba el mapa entero por una ruta de grupo no slug, una ruta de menos de 2 puntos o un burgo sin `name`.
- Leve (revisión de bloque MAP): `tests/test_maps.py` `code_of` solo mira `.code`; los tests de `malformed` deben comprobar también el mensaje.
- Leve (revisión de bloque MAP): `tests/test_maps.py` fija la ruta del mapa real en `/home/user/World-Maker-Fantasy`; leerla de una variable de entorno y apuntar en el plan quién lo comprueba.
- Leve (revisión de bloque MAP-3): `gworld/topology.py` `check_map` no comprueba `places[].cell`, `places[].capitalOf` ni `routes[].zone`; añadir `unknown_place_cell`, `unknown_capital_zone` y `unknown_route_zone` con su test.
- Leve (revisión de bloque MAP-3): `gworld/topology.py` `check_map` no detecta una vecina repetida en `neighbours` (el esquema no tiene `uniqueItems`); añadir `duplicate_neighbour` con su test.
- Leve (revisión de bloque MAP-3): `tests/test_topology.py` `test_empate_se_decide_por_id` pasa también sin la regla de desempate (la cubre `path(4, 0)` en `test_camino_mas_corto`); buscarle un caso que dependa de ella.
- Repo Galivelop-workflow (retro W1, Q-18/Q-19/Q-21): `ci-status.py --wait` para esperar el CI en segundo plano; `gw-orchestrate-dealer` sin envolver `/code-review` en un `gw-reviewer` Opus; `check.sh`/`ci-local.py` con los tests en cada versión de Python de la matriz instalada en local (el CI rojo de PCK-4 por 3.11/3.12).
