# DDD: galivelop-worlds (borrador 1, 2026-11-26)

**Uso:** kit para hacer mundos de ficción vivos con IA local. Saca de Tarkor lo que no es de Tarkor: el motor de
mundo vivo (turnos y simulación), el generador de mapas, el RAG del lore y el comprobador de canon. Tarkor pasa a
ser el primer «paquete de mundo» que corre sobre este kit.

- **Nombre:** Galivelop Worlds · **paquete:** `gworld` · **espacio de artefactos:** `gworld`
- **Visibilidad:** público. El código es MIT; el contenido de cada mundo lleva su propia licencia (la de Tarkor es
  CC BY-NC-SA).
- **Stack:** abierto (§8.2). La propuesta es un núcleo con contrato en Python ≥ 3.10 y solo stdlib, con un adaptador
  TypeScript para WMF.
- **Depende de:**
  - `galivelop-artifacts` (gart): valida los artefactos `gworld.*`.
  - `galivelop-models` (gmod): qué modelo de texto y de embeddings cabe en la máquina.
  - `galivelop-runtime` (grun): el turno de Ollama bajo el candado de máquina.
  - `galivelop-evaluator` (GVE): mide la narración y el RAG.

## 1. Propósito

Que cualquier proyecto monte un mundo persistente con su propio canon y que lo narre una IA local sin contradecirlo.
La simulación avanza por turnos de forma determinista. El mapa sale de una semilla. El narrador recupera lore del
canon, y nada de lo que genera se publica sin pasar antes por el comprobador de canon.

**Éxito:**
1. Tarkor corre sobre `gworld` como paquete de mundo, y sus tests de turno, zona y mapa siguen en verde sin código
   de Tarkor dentro del kit.
2. Un segundo mundo de ejemplo, pequeño y con licencia libre, se monta solo con un paquete (datos, canon y reglas)
   y sin tocar el núcleo.
3. Con la misma semilla y las mismas acciones salen el mismo estado y el mismo mapa, en la Deck y en el CI.
4. El GVE mide en la batería de Tarkor la tasa de contradicciones con el canon de la narración. Con el comprobador
   activado, esa tasa baja respecto a la línea base sin él.

## 2. Lenguaje

| Término | Código | Significado |
|---|---|---|
| Mundo | `World` | Una instancia viva: su estado, su paquete, su semilla y su reloj. |
| Paquete de mundo | `WorldPack` | El contenido de un mundo (canon, tablas, reglas, plantillas de mapa y licencia), aparte del código. |
| Canon | `Canon` | Los hechos aprobados de un mundo, de solo lectura para el kit. En Tarkor, los cambia solo Álvaro. |
| Hecho | `Fact` | Una afirmación atómica del canon, con su id y su fuente (archivo y sección). |
| Estado | `WorldState` | La foto del mundo en un turno: zonas, facciones, reinos, personajes y recursos. |
| Turno | `Turn` | Un paso de la simulación: entran acciones y salen el estado nuevo y sus eventos. |
| Acción | `Action` | Lo que pide un jugador o un actor del mundo en un turno. |
| Regla | `Rule` | Una función pura del paquete que transforma el estado dentro de un turno. |
| Zona | `Zone` | Una región del mapa con su tipo, sus vecinas y su estado. |
| Facción | `Faction` | Un grupo con sus relaciones, objetivos y recursos. |
| Reino | `Realm` | El territorio y los súbditos que gobierna un jugador o un actor. |
| Mapa | `Map` | El grafo de zonas y su geometría, generados desde una semilla y una plantilla. |
| Semilla | `Seed` | El número que fija la simulación y el mapa. |
| Fragmento | `Chunk` | Un trozo del canon indexado para el RAG, con su hecho o hechos de origen. |
| Recuperación | `Retrieval` | Los fragmentos que el RAG devuelve para una consulta, con su puntuación. |
| Narración | `Narration` | El texto que genera el narrador para un turno o un evento. |
| Cronista | `Chronicler` | El adaptador que pide la narración al modelo con el estado y la recuperación. |
| Comprobación | `CanonCheck` | El veredicto sobre una narración: hechos citados, contradicciones y desconocidos. |
| Contradicción | `Contradiction` | Una afirmación de la narración que choca con un `Fact`, con los dos ids. |

## 3. Contextos acotados

1. **Mundo vivo** (núcleo): `World`, `WorldState`, `Turn`, `Action` y `Rule`; el bucle de turno y el registro de
   eventos. Se abstrae del sistema de turno, zona, reino y súbditos de WMF, que el mapa del agente señala como
   puntos de entrada. Lo propio de Tarkor (combate, caza, razas) se queda en su paquete como `Rule`.
2. **Mapas:** la generación por semilla y plantilla, la topología (vecinas, distancias) y la exportación. Viene del
   generador de mapas de WMF. El render en imagen no está aquí: lo hace gimg desde un `gworld.map/0`.
3. **Lore RAG:** troceado del canon, embeddings, índice y recuperación. El almacén va detrás de una interfaz
   (`Store`) y se elige en §8.3.
4. **Comprobador de canon:** extrae las afirmaciones de una narración, las cruza con los `Fact` y da un veredicto.
   Su primera capa es determinista (nombres, fechas, relaciones de las tablas) y puede llevar un juez opcional
   (§8.4).
5. **Cronista:** el adaptador de narración. Monta la consulta con el estado y la recuperación, pide el texto por el
   turno de Ollama de grun y lo manda al comprobador. Quién es su dueño se decide en §8.6.
6. **Paquetes:** carga y validación de un `WorldPack` (estructura, licencia, ids de hecho únicos).

**Mapa con los demás repos:**
- **gart:** núcleo compartido. Valida `gworld.*`.
- **gmod:** cliente-proveedor. Indica el modelo de narración y el de embeddings según `gmod.machine/0`.
- **grun:** cliente-proveedor. Toda llamada al modelo va por el turno de Ollama bajo el candado de máquina.
- **GVE:** mide la narración (contradicciones y coherencia) y el RAG (acierto de la recuperación) con `gworld.check/0`.
- **gforge:** su fuente de Tarkor podrá leer `gworld.state/0` y `gworld.check/0` como datos de destilación y DPO
  (las contradicciones son buenas parejas rechazadas).
- **gimg / gvoice:** pintan el mapa y dan voz a la narración; leen artefactos y no importan `gworld`.
- **World-Maker-Fantasy (Tarkor):** conformista y primer consumidor. Su canon (`docs/rpgtarkor/`,
  `docs/canon-opencode/00-nucleo.md`) se lee y nunca se modifica desde aquí.
- **Instalador-WMF-Tarkor:** instala el paquete de Tarkor y los modelos que pida gmod.

## 4. Modelo

- **Agregado raíz:** `World`. Un turno es una transacción: `apply(turn) -> (WorldState', Events)`, y el estado no
  cambia fuera de ella.
- **Segundo agregado:** `Canon`, de solo lectura. Se carga del paquete y lo usan el RAG y el comprobador.
- **Entidades:** `Zone`, `Faction`, `Realm`, `Character`, `Fact`.
- **Objetos de valor:** `Seed`, `Turn`, `Action`, `Chunk`, `Retrieval`, `Narration`, `CanonCheck`, `Contradiction`,
  `Licence` (SPDX y condiciones) y `PackRef` (id, versión y hash).
- **Servicios:**
  - `load_pack(path) -> WorldPack`
  - `new_world(pack, seed) -> World`
  - `World.apply(turn)`
  - `generate_map(template, seed) -> Map`
  - `index(canon, store)`
  - `retrieve(query, k) -> Retrieval`
  - `narrate(state, events) -> Narration` (vía grun)
  - `check(narration, canon) -> CanonCheck`
- **Interfaces que pone el paquete o el consumidor:** `Rule`, `MapTemplate`, `Store` (el almacén del RAG),
  `Embedder` y `Judge` (opcional).
- **Eventos** (líneas del registro del mundo): `TurnApplied`, `ZoneChanged`, `FactionShifted`, `MapGenerated`,
  `NarrationDrafted`, `CanonChecked`, `NarrationRejected`, `NarrationPublished`.
- **Artefactos gart:**
  - `gworld.pack/0`: el manifiesto del paquete (id, versión, licencia, hash del canon y lista de reglas).
  - `gworld.map/0`: el mapa (zonas, vecinas y geometría), con su semilla y su plantilla.
  - `gworld.state/0`: la foto del estado en un turno, con el hash del paquete y la semilla.
  - `gworld.canon/0`: el índice de hechos (id, texto normalizado y fuente).
  - `gworld.check/0`: el veredicto de una narración (citados, contradicciones y desconocidos, con ids).

## 5. Invariantes

Cada una lleva su test.

1. **Simulación determinista:** la misma semilla, el mismo paquete y las mismas acciones dan el mismo
   `gworld.state/0`, byte a byte. Test: dos ejecuciones de 100 turnos con el mismo hash final; una semilla distinta
   da un hash distinto.
2. **Mapas por semilla:** la misma plantilla y la misma semilla dan el mismo `gworld.map/0`. Test: el mapa generado
   dos veces es idéntico, y el grafo es conexo y sin zonas huérfanas.
3. **El canon no se escribe:** ningún módulo abre los archivos del canon en modo escritura, y el kit nunca genera
   lore. Test: un `grep` que falle si hay escritura sobre la ruta del canon, y un test que cargue el canon con
   permisos de solo lectura.
4. **Nada se publica sin comprobar:** `NarrationPublished` exige un `gworld.check/0` de esa misma narración (por
   hash) sin contradicciones. Test: publicar sin comprobación o con una contradicción falla con el motivo y los ids
   del hecho.
5. **Las contradicciones citan su fuente:** cada `Contradiction` lleva el id del `Fact` y su archivo de origen.
   Test: un `gworld.check/0` con una contradicción sin `fact_id` no valida en gart.
6. **Licencias separadas:** el paquete declara su licencia y el kit no la mezcla con MIT. Un artefacto derivado
   (estado, mapa o narración) hereda la del paquete. Test: un paquete sin licencia no carga, y un `gworld.state/0`
   de Tarkor lleva CC BY-NC-SA.
7. **El núcleo no sabe de Tarkor:** ningún módulo del núcleo nombra términos de Tarkor. Test: un `grep` de una
   lista de nombres del paquete de Tarkor sobre `gworld/`, y el mundo de ejemplo corriendo sin ese paquete.
8. **Las reglas son puras:** una `Rule` no hace E/S ni llama al modelo. La IA solo entra por el Cronista, fuera del
   turno. Test: correr un turno con red y archivos bloqueados.
9. **El modelo pasa por grun:** ninguna llamada al modelo sale fuera del turno de Ollama. Test: `narrate` sin grun
   falla cerrado.
10. **Núcleo stdlib:** el núcleo importa sin extras; un `Store` o `Embedder` que no esté instalado falla con la
    orden que lo instala. Test: importar `gworld` en un entorno limpio, y comprobar que el mensaje nombra el extra.

## 6. Alcance

**Dentro:**
- el bucle de turno y las reglas como interfaz;
- el generador de mapas;
- el troceado, índice y recuperación del canon;
- el comprobador de canon;
- el adaptador del Cronista;
- el formato y la validación de paquetes;
- un mundo de ejemplo pequeño.

**Fuera:**
- el contenido de Tarkor (su canon, sus reglas de combate, caza y razas): va en su paquete, en su repo;
- escribir o proponer lore: lo hace la sesión de lore de WMF en `docs/borradores-opencode/`;
- la interfaz del juego, el backend, la base `tarkor` y las cuentas;
- pintar mapas (gimg) y voces (gvoice);
- medir (GVE);
- ajustar modelos (gforge);
- el multijugador en red.

## 7. Escalera de hitos

| Hito | Nivel | Qué | Lo decide |
|---|---|---|---|
| W0 | Diseño | Este DDD, el glosario y los ADR de stack, licencias y almacén del RAG. Nada más mientras Tarkor esté congelado. | Usuario |
| W1 | Paquete y canon | `gworld.pack/0` y `gworld.canon/0`, con un lector del canon de Tarkor que solo lee; mundo de ejemplo mínimo. | Tests |
| W2 | Comprobador | La capa determinista sobre las tablas del canon y la batería del GVE de contradicciones con línea base. | GVE |
| W3 | RAG | Troceado, embeddings locales e índice; el GVE mide el acierto de recuperación. | GVE + umbral |
| W4 | Mapas | Generador por semilla, `gworld.map/0` y equivalencia con el generador de WMF sobre sus semillas de test. | Tests |
| W5 | Mundo vivo | Bucle de turno y reglas; zonas, facciones y reino abstraídos, con las de Tarkor en su paquete. | Tests + usuario |
| W6 | Cronista | Narración vía grun con comprobación obligatoria; Tarkor pasa a consumir el kit. | Usuario (Tarkor descongelado) |

Las fases W2 y W3 se pueden adelantar con Tarkor congelado: solo leen el canon y no cambian el juego.

## 8. Preguntas abiertas

1. **¿Extraer de Tarkor o reescribir?** El código de WMF está atado a su backend y a su base.
   **Recomendación:** reescribir el núcleo contra el contrato de este DDD, usando los tests de WMF como oráculo de
   equivalencia (mismas semillas, mismo resultado). Tarkor cambia a usar el kit solo en W6, en una tarea de su
   propio repo.
2. **¿Python o TypeScript?** WMF es TypeScript y el resto de Galivelop es Python con stdlib.
   **Recomendación:** el contrato son los artefactos gart y el núcleo es Python con stdlib (comprobador, mapas y
   canon, que también sirven a gforge y al GVE). El bucle de turno de Tarkor se queda en TypeScript hasta W5, y
   entonces se decide con datos si se porta o se publica un paquete npm que siga el mismo contrato.
3. **¿Postgres con pgvector o un almacén stdlib para el RAG?**
   **Recomendación:** una interfaz `Store` con dos implementaciones. Por defecto, una stdlib (SQLite y coseno en
   Python, que basta para un canon del tamaño de Tarkor en la Deck). Como extra, pgvector, para quien ya lo tenga,
   como WMF.
4. **¿El comprobador es determinista o un juez con IA?** El pilar del GVE pide medir de forma determinista donde
   se pueda.
   **Recomendación:** dos capas. La primera, determinista y obligatoria: entidades, fechas y relaciones contra las
   tablas del canon. La segunda, un `Judge` local opcional para lo que la primera marque como «desconocido»,
   marcado como juez de IA en el `gworld.check/0`.
5. **¿Cuándo empieza la extracción, si Tarkor está congelado?**
   **Recomendación:** W0 ahora. W1 a W3 cuando quieras, porque solo leen el canon. W4 a W6 cuando se cierren las
   pruebas de juego y vuelva el roadmap de WMF.
6. **¿De quién es el Cronista?** WMF tiene su Cronista con prompts y tono propios.
   **Recomendación:** el kit pone el adaptador (consulta, recuperación, grun y comprobación) y el paquete pone los
   prompts y el estilo. El Cronista de Tarkor queda como configuración de su paquete.

## Decisiones

_(ninguna aún: pendientes de §8)_
