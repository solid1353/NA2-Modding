from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from scripts.lib.paths import load_local_paths


class ControlSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _base_features(self) -> dict[str, object]:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        return base["features"]

    def _write_full_configuration(self, features: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(
            json.dumps({"features": features}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_controls_and_shared_settings_are_independently_selectable(
        self,
    ) -> None:
        for controls_enabled, shared_enabled in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            with self.subTest(controls=controls_enabled, shared=shared_enabled):
                features = self._base_features()
                features["settings"]["new_controls"] = controls_enabled
                shared = features["settings"]["in_game"]["shared"]
                features["settings"]["in_game"]["shared"] = shared if shared_enabled else False
                selection = catalog.load_selection(
                    self.catalog_path,
                    self._write_full_configuration(features),
                )
                controls = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == ("features", "settings", "new_controls")
                )
                shared = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == ("features", "settings", "in_game", "shared")
                )
                self.assertEqual(controls.enabled, controls_enabled)
                self.assertEqual(shared.enabled, shared_enabled)
                active_edits = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.edits
                }
                active_injections = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.injections
                }
                self.assertEqual(
                    "settings.new_controls" in active_edits,
                    controls_enabled,
                )
                self.assertEqual(
                    "settings.new_controls" in active_injections,
                    controls_enabled,
                )
                self.assertEqual(
                    "settings.shared.substitution"
                    in active_injections,
                    shared_enabled,
                )

    def test_owned_default_layout_and_action_separation(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        route = selection.edits["settings.new_controls"]["edits"]
        self.assertEqual(
            {
                name: (
                    edit["destination_target_id"],
                    edit["destination_offset"],
                    edit["expected_hex"],
                    edit["replacement_hex"],
                )
                for name, edit in route.items()
            },
            {
                "allow_substitution_while_guard_is_held": (
                    "na2_elf",
                    "0x129720",
                    "10004228",
                    "01000224",
                ),
                "default_battle_overlay_bindings": (
                    "na2_btl",
                    "0x1E4250",
                    "10002000400080000400080001000200",
                    "10002000400080000100020008000400",
                ),
                "default_control_settings_reset_selections": (
                    "na2_elf",
                    "0x4D5350",
                    (
                        "01000000000000000300000002000000"
                        "04000000050000000600000007000000"
                        "01000000"
                    ),
                    (
                        "01000000000000000300000002000000"
                        "07000000060000000400000005000000"
                        "01000000"
                    ),
                ),
                "default_resident_bindings": (
                    "na2_elf",
                    "0x4C07A0",
                    "10002000400080000400080001000200",
                    "10002000400080000100020008000400",
                ),
                "include_substitution_in_shoulder_assignment_selector": (
                    "na2_elf",
                    "0x2883FC",
                    "06000324",
                    "07000324",
                ),
                "preserve_substitution_when_opening_assignment": (
                    "na2_elf",
                    "0x287FBC",
                    "0000A3AC",
                    "00000000",
                ),
                "remove_substitution_action_from_logical_block_mask": (
                    "na2_btl",
                    "0x3C02C",
                    "0E002286",
                    "2D100000",
                ),
                "search_substitution_action_in_first_input_history_arm": (
                    "na2_elf",
                    "0x129740",
                    "06000524",
                    "07000524",
                ),
            },
        )

    def test_control_settings_injection_owns_label_and_assignment(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        controls = selection.injections["settings.new_controls"]
        hook = controls["hooks"]["label_substitution_action"]
        self.assertEqual(hook["target_id"], "na2_elf")
        self.assertEqual(hook["offset"], "0x4B26AC")
        self.assertEqual(hook["expected_hex"], "40466000")
        self.assertEqual(hook["symbol"], "control_settings_substitution_label")
        self.assertEqual(hook["encoding"], "abs32")
        self.assertEqual(
            controls["payload"]["control_settings_substitution_label"],
            {
                "kind": "rodata",
                "alignment": 1,
                "value": "537562737469747574696F6E00",
            },
        )
        assignment_hook = controls["hooks"][
            "replace_paired_action_assignment"
        ]
        self.assertEqual(
            assignment_hook,
            {
                "description": (
                    "Replace the native Guard-pair assignment helper with an "
                    "owned one-action swap so Guard, Substitution, Item "
                    "Select, and Linked Attack remain independently assignable."
                ),
                "target_id": "na2_elf",
                "offset": "0x287C90",
                "expected_hex": "8030050001000324",
                "symbol": "control_settings_assign_action",
                "encoding": "j26",
                "replacement_hex": "0000000800000000",
            },
        )
        self.assertEqual(
            controls["payload"]["control_settings"],
            {
                "kind": "c",
                "path": "src/battle_logic/control_settings.c",
                "namespace": "battle.control.settings",
                "imports": {},
                "fragments": {
                    "control_settings_assign_action": {
                        "object": (
                            "battle.control.settings.text.control.settings."
                            "assign.action"
                        ),
                    },
                },
            },
        )

        gauge = selection.injections[
            "settings.shared.substitution"
        ]
        self.assertNotIn("label_substitution_action", gauge["hooks"])
        self.assertNotIn(
            "control_settings_substitution_label",
            gauge["payload"],
        )


if __name__ == "__main__":
    unittest.main()
