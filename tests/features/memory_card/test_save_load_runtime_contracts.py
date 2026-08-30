"""Static contracts for the visible first-record Save/Load controller."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.payload_builder import build_resident_payload
from na228_builder.payload_builder import ee_c_fragments
from na228_builder.payload_builder.operations import encode_symbol_reference
from na228_builder.scripts import catalog
from na228_builder.scripts.composer import resolve_symbolic_patches
from tests.na228_builder._fixtures import resident_payload_config


REPOSITORY = Path(__file__).resolve().parents[3]
BUILDER = REPOSITORY / "na228_builder"
SOURCE = REPOSITORY / "src" / "qol" / "save_load_display_only_first_save.c"
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"

PATCH_ID = "memory_card.display_only_first_save"
AUTOMATIC_PATCH_ID = "startup.auto_loading"
ENTRY_SYMBOL = "display_only_first_save_update"
OBJECT_SYMBOL = (
    "qol.save.load.display.only.first.save.text."
    "save.load.display.only.first.save.update"
)
NATIVE_UPDATE_ADDRESS = 0x001E3F20
LIVE_ACCEPT_INSTRUCTION_ADDRESS = 0x001E451C


def words(payload: bytes) -> tuple[int, ...]:
    if len(payload) % 4:
        raise AssertionError("MIPS payload is not word aligned")
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


def materializations(
    payload_words: tuple[int, ...],
    value: int,
) -> tuple[tuple[int, int], ...]:
    """Return (instruction index, register) pairs for one exact `li` value."""
    upper = value >> 16
    lower = value & 0xFFFF
    matches: list[tuple[int, int]] = []
    for index in range(len(payload_words) - 1):
        first = payload_words[index]
        second = payload_words[index + 1]
        if first >> 26 != 0x0F or first & 0xFFFF != upper:
            continue
        register = (first >> 16) & 0x1F
        if (
            second >> 26 == 0x0D
            and (second >> 21) & 0x1F == register
            and (second >> 16) & 0x1F == register
            and second & 0xFFFF == lower
        ):
            matches.append((index, register))
    return tuple(matches)


def calls_materialized_address(
    payload_words: tuple[int, ...],
    value: int,
) -> int:
    calls = 0
    for index, register in materializations(payload_words, value):
        if index + 2 >= len(payload_words):
            continue
        instruction = payload_words[index + 2]
        if (
            instruction >> 26 == 0
            and (instruction >> 21) & 0x1F == register
            and instruction & 0x3F == 0x09
        ):
            calls += 1
    return calls


class SaveLoadRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not COMPILER.is_file():
            raise unittest.SkipTest(
                f"local EE compiler is unavailable: {COMPILER}"
            )

        cls.selection = catalog.load_selection(
            BUILDER / "catalog.modcat",
            BUILDER / "configurations" / "release.jsonc",
        )
        cls.package = catalog.load_runtime_package(
            cls.selection,
            "memory_card",
            BUILDER / "modules" / "targets.tsv",
            REPOSITORY,
            "memory_card.runtime_injector",
        )
        cls.startup_package = catalog.load_runtime_package(
            cls.selection,
            "startup",
            BUILDER / "modules" / "targets.tsv",
            REPOSITORY,
            "startup.runtime_injector",
        )
        with tempfile.TemporaryDirectory() as temporary:
            cls.compiled = ee_c_fragments.compile_and_extract(
                SOURCE,
                Path(temporary) / "save_load_display_only_first_save.c.o",
                namespace="qol.save.load.display.only.first.save",
                toolchain_bin=TOOLCHAIN_BIN,
            )

    def test_catalog_selects_one_wrapper_beside_the_retained_edits(self) -> None:
        node = next(
            node
            for node in self.selection.nodes
            if node.path == (
                "features",
                "memory_card",
                "display_only_first_save",
            )
        )
        self.assertTrue(node.enabled)
        self.assertEqual(PATCH_ID, node.patch)

        injection = self.selection.injections[PATCH_ID]
        hook = injection["hooks"]["route_shared_save_load_update"]
        self.assertEqual("na2_elf", hook["target_id"])
        self.assertEqual("0xE4008", hook["offset"])
        self.assertEqual("C88F070C00000000", hook["expected_hex"])
        self.assertEqual(ENTRY_SYMBOL, hook["symbol"])
        self.assertEqual("jal26", hook["encoding"])

        source = injection["payload"]["display_only_first_save"]
        self.assertEqual("c", source["kind"])
        self.assertEqual(
            "src/qol/save_load_display_only_first_save.c",
            source["path"],
        )
        self.assertEqual(
            "qol.save.load.display.only.first.save",
            source["namespace"],
        )
        self.assertEqual(
            OBJECT_SYMBOL,
            source["fragments"][ENTRY_SYMBOL]["object"],
        )

    def test_visible_and_automatic_hooks_are_selected_and_disjoint(self) -> None:
        visible = next(
            edit
            for edit in self.package.active_edits
            if edit.symbolic_patch.symbol == ENTRY_SYMBOL
        )
        automatic = next(
            edit
            for edit in self.startup_package.active_edits
            if edit.symbolic_patch.symbol == "auto_loading_update"
        )
        self.assertEqual(0xE4008, visible.symbolic_patch.offset)
        self.assertEqual(0xEA084, automatic.symbolic_patch.offset)
        self.assertLess(
            visible.symbolic_patch.offset + len(visible.symbolic_patch.expected),
            automatic.symbolic_patch.offset,
        )

        automatic_hook = self.selection.injections[AUTOMATIC_PATCH_ID][
            "hooks"
        ]["replace_visible_save_load_controller_update"]
        self.assertEqual("C08F070C", automatic_hook["expected_hex"])

    def test_c_entry_exports_directly_without_an_abi_shim(self) -> None:
        self.assertEqual(1, len(self.compiled.fragments))
        fragment = self.compiled.fragments[0]
        self.assertEqual(OBJECT_SYMBOL, fragment.symbol)
        self.assertEqual((), fragment.relocations)
        self.assertEqual(
            ee_c_fragments.SymbolReference(OBJECT_SYMBOL, 0),
            self.compiled.symbols[ENTRY_SYMBOL],
        )

    def test_production_hook_links_to_jal_and_preserves_the_delay_nop(self) -> None:
        declaration = next(
            edit
            for edit in self.package.active_edits
            if edit.symbolic_patch.symbol == ENTRY_SYMBOL
        )
        fragment = next(
            fragment
            for fragment in self.package.fragments
            if fragment.symbol == ENTRY_SYMBOL
        )
        build = build_resident_payload(
            (fragment,),
            config=resident_payload_config(),
        )
        resolved = resolve_symbolic_patches(
            build,
            (declaration.symbolic_patch,),
        )[0]
        self.assertEqual(bytes.fromhex("C88F070C00000000"), resolved.expected)
        self.assertEqual(
            encode_symbol_reference(
                "jal26",
                build.symbols[ENTRY_SYMBOL].runtime_address,
            ) + bytes(4),
            resolved.replacement,
        )
        instruction = int.from_bytes(resolved.replacement[:4], "little")
        self.assertEqual(0x03, instruction >> 26)

    def test_wrapper_has_one_native_delegate_and_reads_the_live_accept_mask(
        self,
    ) -> None:
        payload_words = words(self.compiled.fragments[0].payload)
        self.assertEqual(
            1,
            calls_materialized_address(payload_words, NATIVE_UPDATE_ADDRESS),
        )
        self.assertGreaterEqual(
            len(materializations(payload_words, LIVE_ACCEPT_INSTRUCTION_ADDRESS)),
            1,
        )


if __name__ == "__main__":
    unittest.main()
