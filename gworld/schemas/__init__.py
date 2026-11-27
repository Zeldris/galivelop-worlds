"""Esquemas gart de gworld (JSON empaquetado) y su cargador, solo stdlib."""

import json
from importlib import resources

_FILES = {"gworld.pack/0": "pack-0.json", "gworld.canon/0": "canon-0.json", "gworld.map/0": "map-0.json"}


def load_schema(kind: str) -> dict:
    """Devuelve el esquema de `kind`; un kind desconocido es ValueError."""
    if kind not in _FILES:
        raise ValueError(f"esquema desconocido: {kind!r}; conocidos: {sorted(_FILES)}")
    return json.loads(resources.files(__package__).joinpath(_FILES[kind]).read_text(encoding="utf-8"))
