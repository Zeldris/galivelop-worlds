# 2026-11-27 · gw-orchestrate-dealer · pending · MAP-3

## Why

Las distancias y el camino siguen a WMF (`medir.py:64-67`, `consultar.py:343-357`): recta entre centros por la
unidad en km y Dijkstra sobre vecinas con coste la distancia entre centros, para que MAP-5 compare sin traducir.

## Alternatives

Pasar por defecto solo por tierra como WMF (`consultar.py:321-323`): contradice el contrato (`passable=None` = todo);
se deja a `passable` y la diferencia va a la sesión principal.

## Changed because

—
