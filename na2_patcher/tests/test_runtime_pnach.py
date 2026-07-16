from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.raw_binary.tools.render_runtime_pnach import render_package


class RuntimePnachTests(unittest.TestCase):
    def test_rendering_patch_set_preserves_disabled_state(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = (
            repository
            / "na2_patcher"
            / "modules"
            / "raw_binary"
            / "patch_sets"
            / "rendering"
        )
        self.assertEqual(
            render_package(package),
            "gametitle=Naruto Shippuuden: Narutimate Accel 2 (SLPS-25837)\n\n"
            "// # Rendering\n\n"
            "// [Widescreen 16:9]\n"
            "// patch=1,EE,20AF3694,extended,3F400000\n",
        )


if __name__ == "__main__":
    unittest.main()
