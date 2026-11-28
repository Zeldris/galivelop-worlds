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
- Leve (revisión de bloque MAP): `gworld/pack.py` da `canon_special` en vez de `canon_outside` a un symlink del canon que apunta fuera a un FIFO o dispositivo.
- Leve (revisión de bloque MAP-3): `gworld/topology.py` `check_map` no comprueba `places[].cell`, `places[].capitalOf` ni `routes[].zone`; añadir `unknown_place_cell`, `unknown_capital_zone` y `unknown_route_zone` con su test.
- Leve (revisión de bloque MAP-3): `gworld/topology.py` `check_map` no detecta una vecina repetida en `neighbours` (el esquema no tiene `uniqueItems`); añadir `duplicate_neighbour` con su test.
- Leve (revisión de bloque MAP-3): `tests/test_topology.py` `test_empate_se_decide_por_id` pasa también sin la regla de desempate (la cubre `path(4, 0)` en `test_camino_mas_corto`); buscarle un caso que dependa de ella.
- Repo Galivelop-workflow (retro W1, Q-18/Q-19/Q-21): `ci-status.py --wait` para esperar el CI en segundo plano; `gw-orchestrate-dealer` sin envolver `/code-review` en un `gw-reviewer` Opus; `check.sh`/`ci-local.py` con los tests en cada versión de Python de la matriz instalada en local (el CI rojo de PCK-4 por 3.11/3.12).
- Repo Galivelop-workflow (gw-opt-tokens 0.2, Q-35/Q-36/Q-37): `ci-status.py --wait` sigue faltando y sin él se vuelve a `send_later`; `gw-orchestrate-dealer` sigue ofreciendo el `gw-reviewer` Opus; `measure.py` debe sumar los subagentes de todas las carpetas de sesión del proyecto (tras un relevo del contenedor quedan en las de otra sesión).
- Repo Galivelop-workflow (retro 0.2, Q-42/Q-43): en `gw-orchestrate-dealer`, los pasos en paralelo reciben las firmas compartidas en el encargo y un paso de integración corre el check entero antes de la revisión de bloque (MAP-4: 12 hallazgos); el encargo de cada subagente abre su tarea con `task.py start <id>` (MAP-1 entró con PCK-8 en curso).

## Leve (revisión de bloque MAP-4)

- Leve (revisión de bloque MAP-4): `tools/tarkor_maprules.py`: una referencia dict de clase desconocida (ni `continente` ni `provincia`) se lee como provincia.
- Leve (revisión de bloque MAP-4): `tools/tarkor_maprules.py`: una clave ausente en `lore.json` o `canon.json` da `KeyError` sin el id de la regla; convertirlo en `MapError` con el id.
- Observación (revisión de bloque MAP-4): en `geometry.polygons` una primera celda de área 0 deja todo como huecos (igual que WMF).
- Leve (revisión de bloque MAP-5): `gworld/schemas/maprules-0.json:18`: el `enum` de `type` repite `"order"`.
- Leve (revisión de bloque MAP-5): `gworld/schemas/maprules-0.json:18`: la nota de `corridor` dice «la region de su capa»; es la de la celda de partida (id menor) en la capa de `to`.
- Leve (revisión de bloque MAP-5): `tests/test_helek_topology.py:64`: `delta=0.1` en 131.97 km; bajar a 0.01 y citar la cifra de WMF (131.90).
- Leve (revisión de bloque MAP-5): `tests/test_helek_measures.py:20-32`: las cajas de WMF de diez zonas se congelan y no se comprueban (solo Berig); comprobarlas o quitarlas.
- Leve (revisión de bloque MAP-5): `tests/test_helek_rules.py:45`: el filtro de `decided` no filtra nada; quitarlo o filtrar `r.ok is not None`.
- Leve (revisión de bloque MAP-5): `tests/test_helek_measures.py:16`: `SHA` sin usar, parsea el fixture otra vez.
- Leve (revisión de bloque MAP-5): `tests/fixtures/helek/README.md:4`: solo nombra `test_helek_parity.py` (también lo leen measures, rules y topology) y no da la orden que regenera `helek.maprules.json`.
- Observación (revisión de bloque MAP-5): `Marker` redondea como JS (`_round`) y WMF con `round` de Python; en un .5 exacto podrían diferir (en Helek, ninguno).
- Observación (revisión de bloque MAP-5): los nombres de zonas, lugares y rutas pueden traer surrogates sueltos y `regen.dump` falla al escribir UTF-8 (anterior a MAP-5).
- Leve (revisión RAG-1): `tests/test_chunks.py`: los tests de cobertura solo comparan `text.split()` y no el separador entre frases; añadir un caso con texto exacto (frases separadas por `\n` y por dos espacios). Y `test_unicode` no comprueba dónde se parte (quitar `?` o `…` de `_SENTENCE` no rompe nada).
- Leve (revisión RAG-1): `tests/test_chunks.py`: ningún test usa entrada sin normalizar (`\r\n\r\n`, espacios en los extremos) y `_PARAGRAPH` no cuenta `\r\n\r\n`; inocuo con el canon (`normalize` da `\n`), pero decir en el docstring de `gworld/chunks.py` que `Fact.text` llega normalizado.
- Leve (revisión RAG-1): `tests/test_chunks.py:110-121`: el canon de ejemplo (7 hechos de 13 a 17 palabras, sin `\n`) solo ejercita el nivel de palabras y el caso «cabe»; la última aserción es una tautología: sustituirla por `n == 0..k-1` por hecho.
- Observación (revisión RAG-1): un texto sin espacios (CJK, una URL) cuenta como una palabra: `"龍"*50 + " 龍"` con `max_words=2` da un `Chunk` de 50 caracteres. Si RAG-2 mide en tokens, hará falta un tope por caracteres. `Chunk` guarda un solo `fact_id` (ddd §3 dice «hecho o hechos»), `max_words=200` no cita fuente y no hay solapamiento ni encabezado en el texto del `Chunk`; decidir con el `Embedder` real en RAG-3.
- Leve (revisión RAG-3): `gworld/machine_lock.py` `hold`: no es reentrante por hilo (grun sí, `_owner`); un `hold` anidado choca con su propio `flock` y vence a los 120 s. Hoy nadie anida; arreglarlo antes de que RAG-4 o NAR-1 recuperen dentro de un turno.
- Leve (revisión RAG-3): `gworld/sqlite_store.py` `search`: `check_search` y el `SELECT` van en autocommit sueltos; un `clear()` + `add(M2)` de otro proceso entre ambos puntúa contra vectores de M2 sin `IndexMismatchError`. Envolverlos en `BEGIN`…`COMMIT`.
- Leve (revisión RAG-3): `gworld/sqlite_store.py` `add`/`clear`: el `ROLLBACK` del `except` lanza «no transaction is active» si SQLite ya revirtió (SQLITE_FULL, IOERR) y tapa el error real; hacerlo solo `if self._db.in_transaction`. Y si `executescript` falla en `__init__` la conexión queda abierta.
- Leve (revisión RAG-3): `gworld/rag.py` `embed_checked`: `float(x)` acepta cadenas numéricas y bools, y un vector que sea cadena se itera por caracteres (`['12']` da `[(1.0, 2.0)]`); exigir `list`/`tuple` de `int`/`float` no `bool`.
- Leve (revisión RAG-3): `gworld/ollama.py` `version`: con un registro con puerto (`localhost:5000/bge-m3`) no prueba `:latest` y da el modelo por ausente; mirar el tag solo en el último segmento.
- Leve (revisión RAG-3): `tests/test_ollama.py` `test_candado_ocupado_vence`: no comprueba que el hijo tomó el candado ni el mensaje de `LockBusyError`. Y el `import fcntl` arriba del módulo lo rompe fuera de POSIX en vez de saltarlo.
- Observación (revisión RAG-3): `OllamaEmbedder.version` pide `/api/tags` en cada lectura y fuera del candado: un `ollama pull` entre `meta` y `embed` guarda un digest que no es el de los vectores; decidir caché o lectura bajo el candado en RAG-4. `hold`/`busy` solo prueban `O_RDWR` (el protocolo admite solo lectura), como grun. `test_add_fallido_no_deja_meta_a_medias` pasa también sin transacción.
