from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPOSITORY))
    suite = unittest.defaultTestLoader.discover(
        str(REPOSITORY / "tests"),
        pattern="test_*.py",
        top_level_dir=str(REPOSITORY),
    )
    result = unittest.TextTestRunner().run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
