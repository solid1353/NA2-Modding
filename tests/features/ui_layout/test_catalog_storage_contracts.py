"""Production-catalog contracts for the UI-layout runtime hooks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
CATALOG = REPOSITORY / "na228_builder" / "catalog"


class UiLayoutRuntimeContractTests(unittest.TestCase):
    def test_runtime_injection_keeps_the_exact_fifteen_ui_hooks(self) -> None:
        injections = json.loads(
            (CATALOG / "injections.json").read_text(encoding="utf-8")
        )
        hooks = injections["i__localization__ui_layout__runtime"]["hooks"]
        expected = {
            "apply_home_state_1_cross_offset": (
                "na2_etc", "0x6B0", "60F20D0C00000000",
                "localization_ui_common_prompt_x_offset", "jal26",
                "0000000C40C1033C",
            ),
            "apply_home_state_2_play_offset": (
                "na2_etc", "0x6D4", "60F20D0C00000000",
                "localization_ui_common_prompt_x_offset", "jal26",
                "0000000CC0C1033C",
            ),
            "apply_home_state_3_triangle_offset": (
                "na2_etc", "0x738", "60F20D0C00000000",
                "localization_ui_common_prompt_x_offset", "jal26",
                "0000000C00C1033C",
            ),
            "apply_home_state_4_stop_offset": (
                "na2_etc", "0x764", "60F20D0C00000000",
                "localization_ui_common_prompt_x_offset", "jal26",
                "0000000C00C0033C",
            ),
            "draw_jutsu_selector_lower_arrow": (
                "na2_btl", "0x9BFC", "10EF0D0C00000000",
                "localization_ui_jutsu_selector_arrow_draw_lower", "jal26", None,
            ),
            "draw_jutsu_selector_upper_arrow": (
                "na2_btl", "0x9BA0", "10EF0D0C00000000",
                "localization_ui_jutsu_selector_arrow_draw_upper", "jal26", None,
            ),
            "fit_battle_hud_name_width": (
                "na2_btl", "0x67F44", "42010146640060C4",
                "localization_ui_battle_hud_fit_width_adapter", "jal26",
                "0000000CA0000424",
            ),
            "fit_stage_name_width": (
                "na2_btl", "0x61580", "40EF0D0C00000000",
                "localization_ui_stage_select_name_draw", "jal26", None,
            ),
            "place_vs_confirmation_jutsu_label": (
                "na2_btl", "0x9188", "06AB0046",
                "localization_ui_vs_confirmation_jutsu_label_place", "jal26", None,
            ),
            "render_fixed_item_status": (
                "na2_btl", "0x5B0F0", "90FFBD275000BFFF",
                "localization_item_status_fixed_draw", "j26",
                "0000000800000000",
            ),
            "render_numeric_item_status": (
                "na2_btl", "0x5A290", "D0FFBD272000BFFF",
                "localization_item_status_numeric_draw", "j26",
                "0000000800000000",
            ),
            "render_paired_item_status": (
                "na2_btl", "0x5ADC0", "90FFBD275000BFFF",
                "localization_item_status_paired_draw", "j26",
                "0000000800000000",
            ),
            "render_single_item_status": (
                "na2_btl", "0x5AB90", "C0FFBD272000BFFF",
                "localization_item_status_single_draw", "j26",
                "0000000800000000",
            ),
            "suppress_jutsu_selector_horizontal_arrows": (
                "na2_btl", "0x9ABC", "4400448E0400838C",
                "localization_ui_jutsu_selector_arrows_suppress_horizontal",
                "j26", None,
            ),
            "update_item_status_tail": (
                "na2_btl", "0x59F30", "9E41023C67664234",
                "localization_item_status_update_tail_bridge", "j26",
                "000000082D200002",
            ),
        }

        observed = {
            name: (
                hook["target_id"],
                hook["offset"],
                hook["expected_hex"],
                hook["symbol"],
                hook["encoding"],
                hook.get("replacement_hex"),
            )
            for name, hook in hooks.items()
        }
        self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
