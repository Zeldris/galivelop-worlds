# 2026-11-27 · gw-orchestrate-dealer · pending · MAP-5

## Why

Paso 1 de MAP-5: probar a `gworld/` contra el `map-generator/` de WMF sobre Helek. Los fixtures van al repo para que el cruce corra en el CI sin el clon, y `ImportReview` replica el `revisar` de WMF (marcadores automáticos y burgs borrados) sin cambiar `import_map`.

## Alternatives

Dejar el informe solo en un test sin código nuevo: descartado, la ficha pide `import_with_review`. `helek.json` con el lugar 614 corregido: descartado, se copia byte a byte y la diferencia se fija en el test.

## Changed because

—
