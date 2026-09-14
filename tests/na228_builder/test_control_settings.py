from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
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

    def test_controls_and_substitution_settings_are_independently_selectable(
        self,
    ) -> None:
        for controls_enabled, substitution_enabled in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            with self.subTest(
                controls=controls_enabled,
                substitution=substitution_enabled,
            ):
                features = self._base_features()
                features["settings"]["mod_settings"][
                    "new_controls"
                ] = controls_enabled
                mechanics = features["settings"]["submenus"][
                    "battle_mechanics_submenu"
                ]
                substitution = mechanics["substitution"]
                mechanics["substitution"] = (
                    substitution if substitution_enabled else False
                )
                selection = catalog.load_selection(
                    self.catalog_path,
                    self._write_full_configuration(features),
                )
                controls = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == (
                        "features", "settings", "mod_settings", "new_controls"
                    )
                )
                substitution = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == (
                        "features", "settings", "submenus",
                        "battle_mechanics_submenu", "substitution",
                    )
                )
                self.assertTrue(controls.enabled)
                self.assertEqual(controls.configured_value, controls_enabled)
                self.assertEqual(substitution.enabled, substitution_enabled)
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
                    True,
                )
                self.assertEqual(
                    "settings.new_controls" in active_injections,
                    True,
                )
                self.assertEqual(
                    "settings.battle_mechanics.substitution"
                    in active_injections,
                    substitution_enabled,
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
                "path": "na228_builder/patches/settings/new_controls/control_settings.c",
                "namespace": "battle.control.settings",
                "imports": {
                    "mod_settings_option_get": "mod_settings_option_get",
                },
                "fragments": {
                    "control_settings_history_action": {
                        "object": (
                            "battle.control.settings.text.control.settings."
                            "history.action"
                        ),
                    },
                    "control_settings_substitution_held": {
                        "object": (
                            "battle.control.settings.text.control.settings."
                            "substitution.held"
                        ),
                    },
                    "control_settings_assign_action": {
                        "object": (
                            "battle.control.settings.text.control.settings."
                            "assign.action"
                        ),
                    },
                },
            },
        )
        self.assertEqual(
            set(controls["payload"]["control_scheme_abi"]["fragments"]),
            {
                "control_scheme_held_guard_bridge",
                "control_scheme_logical_block_bridge",
            },
        )

        gauge = selection.injections[
            "settings.battle_mechanics.substitution"
        ]
        self.assertNotIn("label_substitution_action", gauge["hooks"])
        self.assertNotIn(
            "control_settings_substitution_label",
            gauge["payload"],
        )


if __name__ == "__main__":
    unittest.main()
