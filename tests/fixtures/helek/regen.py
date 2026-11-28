"""Regenera helek.gworld.json desde un .map de FMG: ``python3 tests/fixtures/helek/regen.py <ruta/Helek_World.map>``."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from gworld.maps import FmgImporter  # noqa: E402

OUT = Path(__file__).with_name("helek.gworld.json")


def dump(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    OUT.write_text(dump(FmgImporter().import_map(argv[1])), encoding="utf-8", newline="\n")
    print(f"escrito {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
