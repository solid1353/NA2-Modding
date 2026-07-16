from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na2_patcher.modules.pnach.render import GAMETITLE, render_sections


class PnachRenderTests(unittest.TestCase):
    def test_preserves_section_order_content_and_disabled_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "20_second.pnach").write_text(
                "// # Second\n// patch=second\n", encoding="utf-8"
            )
            (root / "10_first.pnach").write_text(
                "// # First\npatch=first\n", encoding="utf-8"
            )
            rendered = render_sections(root)
            self.assertTrue(rendered.startswith(GAMETITLE + "\n\n// # First"))
            self.assertIn("patch=first", rendered)
            self.assertIn("// patch=second", rendered)
            self.assertLess(rendered.index("// # First"), rendered.index("// # Second"))


if __name__ == "__main__":
    unittest.main()
