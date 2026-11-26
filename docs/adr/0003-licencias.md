# ADR 0003: licencias del código y de los mundos

- **Estado:** aceptada (2026-11-26), pendiente de la confirmación de Álvaro para Tarkor · **Decisión:** D3 del
  [DDD](../ddd.md)

## Contexto

El código del kit es MIT. WMF declara su contenido CC BY-NC-SA 4.0 (`LICENSE-CONTENIDO`, autoras Galivelop y Álvaro
García Graña); el Instalador-WMF-Tarkor dice «todos los derechos reservados».

## Decisión

- El kit es MIT y no lleva contenido de ningún mundo.
- Cada paquete de mundo declara su licencia en `gworld.pack/0`; un paquete sin licencia no carga.
- Los artefactos derivados (estado, mapa, narración) heredan la licencia del paquete.
- Para Tarkor vale CC BY-NC-SA 4.0, la de WMF. El instalador se corrige en su repo.

## Consecuencias

Hace falta que Álvaro lo confirme y una tarea en el repo del instalador (`docs/records/pending.md`).
