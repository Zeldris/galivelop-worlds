# 2026-11-27 · gw-worker · pending · MAP-4

## Why

Paso 1: el esquema no tiene `oneOf`, así que los parámetros de cada tipo van en una tabla de código (`PARAMS`) que
`bind` comprueba y el motor del paso 3 reutilizará. El esquema deja los parámetros libres y `bind` da `bad_params`
por sobrantes, en vez de un error de esquema, para que cada fallo tenga el código y el id de la regla.

## Alternatives

Un `$defs` por tipo con `additionalProperties: false`: obliga a repetir los campos comunes y da errores de esquema
sin id de regla. `mapRules` con un solo código de error en el paquete: se separó en fuera, ausente e inválido,
como el canon.

## Changed because

—
