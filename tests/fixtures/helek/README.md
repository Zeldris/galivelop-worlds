# Fixtures de Helek

Mundo de la persona (Helek) para probar a `gworld/` contra el `map-generator/` de World-Maker-Fantasy (WMF).
Los usa `tests/test_helek_parity.py` (MAP-5), que corre en el CI sin el clon de WMF.

## Procedencia

- Repositorio de origen: World-Maker-Fantasy, commit `cad662d73714f4ce4ce155aed2ce003bc4b6275c`.
- `helek.json`: copia byte a byte de `map-generator/mundo/helek.json` (sha256
  `90c4029169bb6d257ecc4edd4f89636c803cdd5d575f6634ab9f1d54addb892a`).
- `helek.gworld.json`: lo que da `FmgImporter().import_map` sobre `docs/map/Helek_World.map` de WMF (sha256 del
  `.map`: `2773180ce7e5763fcd7432bde0b0359bc147e15c661040dc7665c2b18a53c579`; FMG 1.137.6). JSON con claves
  ordenadas y sin espacios, una sola linea. Su sha256: `c20d01fa7263841a869e9d8b7769f3984f532dc3ec96dd169d5def74ef682105`.
- Diferencia conocida: en `helek.json` el lugar 614 (Puesto Nabieus del Margen) esta en la celda 3237, (650, 318), por
  una edicion posterior en WMF; el `.map` lo guarda en la celda 3227, (581.38, 317.03). El test lo fija.

## Licencia

`mundo/helek.json` es contenido del mundo de Tarkor: lo cubre `LICENSE-CONTENIDO` de WMF (CC BY-NC-SA 4.0,
Galivelop y Alvaro Garcia Grana, "Zeldris"), no la MIT del codigo (`LICENSE`). Los dos fixtures son obra derivada y se
comparten bajo la misma licencia, con atribucion y sin uso comercial. Cambios: `helek.gworld.json` es el mismo mapa en
el formato `gworld.map/0`.

## Regenerar

```
python3 tests/fixtures/helek/regen.py /ruta/a/Helek_World.map
```

Reescribe `helek.gworld.json`; si cambia el importador o el `.map`, actualiza aqui las huellas.
