from __future__ import annotations

import json
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from scripts.lib.game_catalog import resolve_game


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: resolve_game.py <selector>")
    print(json.dumps(resolve_game(sys.argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
