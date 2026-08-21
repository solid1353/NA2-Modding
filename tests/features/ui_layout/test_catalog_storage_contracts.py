"""Production-catalog contracts for the collapsed UI-layout edit storage."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
CATALOG = REPOSITORY / "na228_builder" / "catalog"
STAGE_LOGICAL_ORDER = (1, 2, 23, 24, *range(5, 23), 3, 4)


class UiLayoutCatalogStorageContractTests(unittest.TestCase):
    def test_affected_edit_groups_keep_only_static_data_and_site_edits(
        self,
    ) -> None:
        edits = json.loads(
            (CATALOG / "edits.json").read_text(encoding="utf-8")
        )
        expected_members = {
            "e__localization__font__glyphs": {
                "decoder_horizontal_scale_default",
                "secondary_font_descriptor",
                "secondary_glyph_atlas",
                "secondary_metric_hash_values",
            },
            "e__localization__font__layout": {
                "command_relationships_suppress_second_auxiliary_draw",
                "practice_commands_on_off_table",
                "practice_damage_on_off_table",
                "practice_guide_ninja_sound_on_off_table",
            },
            "e__localization__ui_layout__battle_hud_names": {
                "mirrored_x_anchor_74",
            },
            "e__localization__ui_layout__common_prompts": {
                "collection_root_cross_x",
                "collection_root_triangle_x",
                "play_label_local_x",
                "record_2_next",
                "record_4_cancel_label",
                "record_5_cancel_tail",
                "record_6_triangle_icon",
                "stop_label_local_x",
                "stop_rectangle",
            },
            "e__localization__ui_layout__item_status_numeric": {
                "chakra_record",
                "health_record",
                "recovery_record",
            },
            "e__localization__ui_layout__item_status_paired": {
                "rank_offset_table",
                "records_8e_through_94",
                "records_9b_and_9c",
            },
            "e__localization__ui_layout__item_status_single": {
                "records_96_through_9a",
            },
            "e__localization__ui_layout__jutsu_selector_arrows": {
                "green_arrow_rectangle",
            },
            "e__localization__ui_layout__stage_select": {
                "random_prompt_x",
                *(
                    f"stage_s{row:02d}_logical_{logical:02d}_name_rectangle"
                    for row, logical in enumerate(
                        STAGE_LOGICAL_ORDER,
                        start=1,
                    )
                ),
            },
            "e__localization__ui_layout__vs_confirmation": {
                "battle_settings_rectangle",
                "battle_settings_x_94",
                "customize_jutsu_rectangle",
                "customize_jutsu_x_260",
                "disable_back_separate_glyph",
                "disable_ok_separate_glyph",
                "jutsu_1_label_rectangle",
                "jutsu_2_label_rectangle",
                "jutsu_input_glyph_1_rectangle",
                "jutsu_input_glyph_2_rectangle",
                "jutsu_input_glyph_3_rectangle",
                "jutsu_input_glyph_offset_40_accumulate",
                "jutsu_input_glyph_offset_40_load",
                "ok_back_prompt_records",
                "two_arrow_control_rectangle",
            },
        }

        self.assertNotIn(
            "e__localization__ui_layout__item_status_fixed",
            edits,
        )
        for group, expected in expected_members.items():
            self.assertEqual(set(edits[group]["edits"]), expected, group)

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
