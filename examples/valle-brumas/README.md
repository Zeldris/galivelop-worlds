# Valle de las Brumas

Mundo de ejemplo mínimo e inventado, para probar el núcleo sin ningún paquete real. Su huella del canon se
comprueba en `tests/test_example_world.py`; para regenerarla tras editar `canon/`:

    python3 -c "from gworld.pack import canon_digest; print(canon_digest('examples/valle-brumas/canon'))"
