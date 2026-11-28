"""Localizador único de la carpeta de World-Maker-Fantasy (WMF) para los tests."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def wmf_dir() -> Path | None:
    """``GW_WMF_DIR`` o ``../World-Maker-Fantasy`` junto al repo; ``None`` si la carpeta no existe."""
    base = Path(os.environ.get("GW_WMF_DIR") or ROOT.parent / "World-Maker-Fantasy")
    return base if base.is_dir() else None
