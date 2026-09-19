from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.modules.payload_builder import ee_c_fragments
from na228_builder.infrastructure.orchestration import catalog, jsonc
from scripts.lib.paths import load_local_paths


PATCH_ID = "general.music_override"
SELECT_SYMBOL = "select"
STOP_ADDRESS = 0x001D9760
SELECT_ADDRESS = 0x001D95D0
VOLUME_ADDRESS = 0x001D9D40
CHARACTER_SELECT_UPDATE_ADDRESS = 0x003BCDA0
CONTROL_POINTER_ADDRESS = 0x0060755C
STREAMS_POINTER_ADDRESS = 0x00607558


def words(payload: bytes) -> tuple[int, ...]:
    if len(payload) % 4:
        raise AssertionError("MIPS payload is not word aligned")
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


def calls_materialized_address(payload_words: tuple[int, ...], value: int) -> int:
    upper = value >> 16
    lower = value & 0xFFFF
    calls = 0
    for index in range(len(payload_words) - 2):
        first = payload_words[index]
        second = payload_words[index + 1]
        if first >> 26 != 0x0F or first & 0xFFFF != upper:
            continue
        register = (first >> 16) & 0x1F
        if (
            second >> 26 != 0x0D
            or (second >> 21) & 0x1F != register
            or (second >> 16) & 0x1F != register
            or second & 0xFFFF != lower
        ):
            continue
        call = payload_words[index + 2]
        if (
            call >> 26 == 0
            and (call >> 21) & 0x1F == register
            and call & 0x3F == 0x09
        ):
            calls += 1
    return calls


def loads_pointer_at_address(payload_words: tuple[int, ...], value: int) -> int:
    upper = value >> 16
    lower = value & 0xFFFF
    loads = 0
    for index in range(len(payload_words) - 1):
        first = payload_words[index]
        second = payload_words[index + 1]
        if first >> 26 != 0x0F or first & 0xFFFF != upper:
            continue
        register = (first >> 16) & 0x1F
        if (
            second >> 26 == 0x23
            and (second >> 21) & 0x1F == register
            and second & 0xFFFF == lower
        ):
            loads += 1
    return loads


class MusicOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.base_path = cls.builder / "configurations" / "base.jsonc"
        cls.selection = catalog.load_selection(cls.catalog_path, cls.base_path)

    def test_setting_selects_both_patch_packages_and_can_disable_them(self) -> None:
        node = next(
            node
            for node in self.selection.nodes
            if node.path == ("features", "general", "music_override")
        )
        self.assertTrue(node.enabled)
        self.assertEqual(PATCH_ID, node.patch)
        self.assertIn(PATCH_ID, self.selection.edits)
        self.assertIn(PATCH_ID, self.selection.injections)

        base = jsonc.loads(self.base_path.read_text(encoding="utf-8"))
        base["features"]["general"]["music_override"] = False
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "disabled.jsonc"
            configuration.write_text(
                json.dumps(base, indent=2) + "\n",
                encoding="utf-8",
            )
            disabled = catalog.load_selection(self.catalog_path, configuration)

        disabled_node = next(
            node
            for node in disabled.nodes
            if node.path == ("features", "general", "music_override")
        )
        self.assertFalse(disabled_node.enabled)
        binary_package = catalog.load_binary_package(
            disabled,
            "general",
            self.builder / "infrastructure" / "targets.tsv",
            self.repository,
            self.builder
            / "infrastructure"
            / "modules"
            / "binary_patcher"
            / "operations",
        )
        runtime_package = catalog.load_runtime_package(
            disabled,
            "general",
            self.builder / "infrastructure" / "targets.tsv",
            self.repository,
            "general.runtime_injector",
        )
        self.assertFalse(
            any(edit.patch_id == disabled_node.node_id for edit in binary_package.edits)
        )
        self.assertFalse(
            any(edit.patch_id == disabled_node.node_id for edit in runtime_package.edits)
        )
        self.assertNotIn(SELECT_SYMBOL, {item.symbol for item in runtime_package.fragments})

    def test_dispatcher_sites_select_the_accepted_tracks(self) -> None:
        edits = self.selection.edits[PATCH_ID]["edits"]
        self.assertEqual(
            {
                name: (
                    edit["destination_offset"],
                    edit["expected_hex"],
                    edit["replacement_hex"],
                )
                for name, edit in edits.items()
            },
            {
                "select_mode_music_track": (
                    "0xD38D0",
                    "01000424",
                    "3E000424",
                ),
                "select_character_music_track": (
                    "0xD3954",
                    "01000424",
                    "44000424",
                ),
            },
        )

        hooks = self.selection.injections[PATCH_ID]["hooks"]
        self.assertEqual(
            {
                name: (
                    hook["offset"],
                    hook["expected_hex"],
                    hook["symbol"],
                )
                for name, hook in hooks.items()
            },
            {
                "route_mode_music_through_native_replacement_sequence": (
                    "0xD38D8",
                    "8C66070C",
                    SELECT_SYMBOL,
                ),
                "route_character_music_through_native_replacement_sequence": (
                    "0xD395C",
                    "8C66070C",
                    SELECT_SYMBOL,
                ),
                "restart_character_music_after_completion": (
                    "0xED73C",
                    "68F30E0C",
                    SELECT_SYMBOL,
                ),
            },
        )

    def test_wrapper_keeps_native_selection_and_channel_gain_calls(self) -> None:
        source = self.selection.injections[PATCH_ID]["payload"][
            "music_override"
        ]
        toolchain_bin = ee_c_fragments.default_toolchain_bin(self.repository)
        compiler = toolchain_bin / "ee-gcc.exe"
        if not compiler.is_file():
            self.skipTest(f"local EE compiler is unavailable: {compiler}")

        with tempfile.TemporaryDirectory() as directory:
            compiled = ee_c_fragments.compile_and_extract(
                self.repository / source["path"],
                Path(directory) / "music_override.c.o",
                namespace=source["namespace"],
                toolchain_bin=toolchain_bin,
            )

        self.assertEqual(1, len(compiled.fragments))
        payload_words = words(compiled.fragments[0].payload)
        self.assertEqual(1, calls_materialized_address(payload_words, STOP_ADDRESS))
        self.assertEqual(
            1,
            calls_materialized_address(payload_words, SELECT_ADDRESS),
        )
        self.assertEqual(
            1,
            calls_materialized_address(payload_words, VOLUME_ADDRESS),
        )
        self.assertEqual(
            1,
            calls_materialized_address(
                payload_words,
                CHARACTER_SELECT_UPDATE_ADDRESS,
            ),
        )
        self.assertEqual(
            1,
            loads_pointer_at_address(payload_words, CONTROL_POINTER_ADDRESS),
        )
        self.assertEqual(
            1,
            loads_pointer_at_address(payload_words, STREAMS_POINTER_ADDRESS),
        )


if __name__ == "__main__":
    unittest.main()
