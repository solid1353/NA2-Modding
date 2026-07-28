from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from na2_patcher.build_profile import apply_binary_patch_set
from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.binary_patcher import engine as binary_engine
from na2_patcher.modules.runtime_injector import engine
from na2_patcher.payload_builder.builder import (
    build_resident_payload,
    load_config,
)
from scripts.research.localization import mips


def write_tsv(
    path: Path, fields: list[str], rows: list[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


class RuntimeInjectorTests(unittest.TestCase):
    def test_all_disabled_resident_package_composes_as_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = directory / "na2"
            root.mkdir()
            target_data = bytes(range(16))
            (root / "SLPS_258.37").write_bytes(target_data)
            package = binary_engine.Package(
                directory=directory,
                package_id="feature.runtime_injector",
                targets={
                    "boot": binary_engine.Target(
                        target_id="boot",
                        root_id="na2",
                        role="destination",
                        path=PurePosixPath("SLPS_258.37"),
                        expected_size=len(target_data),
                        expected_sha256=hashlib.sha256(target_data).hexdigest().upper(),
                    )
                },
                groups={
                    "layout": binary_engine.Group(
                        group_id="layout",
                        enabled=True,
                        name="Layout",
                        description="Retained disabled layout.",
                        review_notes="",
                    )
                },
                patches={
                    "layout_hook": binary_engine.Patch(
                        patch_id="layout_hook",
                        group_id="layout",
                        enabled=False,
                        status="runtime_proven",
                        confidence="high",
                        name="Layout hook",
                        description="Retained disabled hook.",
                        source_mapping_id="TEST-LAYOUT",
                        runtime_classification="resident",
                        review_notes="",
                    )
                },
                edits=[],
            )
            payloads: dict[str, bytearray] = {}
            owners: dict[str, str] = {}

            result = apply_binary_patch_set(
                directory,
                package=package,
                roots={"na2": root},
                feature_id="feature",
                source=object(),  # The no-op branch never reads the image.
                payloads=payloads,
                owners=owners,
                allow_empty_enabled=True,
            )

            self.assertEqual(result["selected"], [])
            self.assertEqual(result["edits"], [])
            self.assertEqual(result["patched_paths"], [])
            self.assertEqual(payloads, {})
            self.assertEqual(owners, {})

    def test_canonical_font_helpers_use_only_resident_payload_storage(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        directory = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector"
        )
        canonical_declaration = engine.load_package(
            directory, owner="localization.runtime_injector"
        )
        self.assertEqual(
            {
                patch_id
                for patch_id, patch in canonical_declaration.patches.items()
                if patch.enabled
            },
            {
                "font_v2_layout_core",
                "font_v2_controls",
                "font_v2_titles",
                "font_v2_pause_controls_list",
                "font_v2_quit_confirmation",
                "font_v2_special_controls_body",
                "font_v2_practice_explanations",
                "font_ninja_song_ascii_numbers",
            },
        )
        canonical_build = build_resident_payload(
            canonical_declaration.fragments
        )
        canonical_resolved = resolve_symbolic_patches(
            canonical_build, canonical_declaration.symbolic_patches
        )
        canonical_package = engine.build_binary_package(
            canonical_declaration, canonical_resolved
        )
        self.assertEqual(
            {edit.edit_id for edit in canonical_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_controls_01",
                "font_v2_titles_01",
                "font_v2_titles_02",
                "font_v2_pause_controls_list_01",
                "font_v2_pause_controls_list_02",
                "font_v2_quit_confirmation_01",
                "font_v2_quit_confirmation_02",
                "font_v2_quit_confirmation_03",
                "font_v2_quit_confirmation_04",
                "font_v2_special_controls_body_01",
                "font_v2_practice_explanations_01",
                "font_ninja_song_ascii_numbers_01",
                "font_ninja_song_ascii_numbers_02",
                "font_ninja_song_ascii_numbers_03",
                "font_ninja_song_ascii_numbers_04",
                "font_ninja_song_ascii_numbers_05",
            },
        )

        disabled_declaration = replace(
            canonical_declaration,
            patches={
                patch_id: replace(patch, enabled=False)
                for patch_id, patch in canonical_declaration.patches.items()
            },
        )
        self.assertEqual(disabled_declaration.payload_fragments, ())
        self.assertEqual(disabled_declaration.symbolic_patches, ())
        disabled_package = engine.build_binary_package(
            disabled_declaration, ()
        )
        self.assertEqual(disabled_package.edits, [])

        group_disabled_declaration = replace(
            canonical_declaration,
            groups={
                group_id: replace(group, enabled=False)
                for group_id, group in canonical_declaration.groups.items()
            },
        )
        self.assertEqual(group_disabled_declaration.payload_fragments, ())
        self.assertEqual(group_disabled_declaration.symbolic_patches, ())

        v2_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id == "font_v2_layout_core",
                )
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        v2_build = build_resident_payload(v2_declaration.fragments)
        v2_resolved = resolve_symbolic_patches(
            v2_build, v2_declaration.symbolic_patches
        )
        v2_package = engine.build_binary_package(
            v2_declaration, v2_resolved
        )
        self.assertEqual(
            {edit.edit_id for edit in v2_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
            },
        )
        self.assertEqual(
            {edit.destination_offset for edit in v2_package.edits},
            {0x88070, 0x88704, 0x88B7C, 0x893EC, 0x897D8},
        )
        session = v2_build.symbols["localization.font.v2.session_pointer"]
        self.assertEqual(session.size, 4)
        self.assertEqual(
            v2_build.payload[
                session.file_offset:session.file_offset + session.size
            ],
            b"\0" * 4,
        )
        v2_widths = v2_build.symbols["localization.font.v2.ascii_widths"]
        v2_width_payload = v2_build.payload[
            v2_widths.file_offset:v2_widths.file_offset + v2_widths.size
        ]
        self.assertEqual(len(v2_width_payload), 95)
        for text, expected in (
            ("Susanoo's Blade", 142),
            ("Reverse Halo", 115),
            (
                "Fire Style: Phoenix Flower Jutsu @Petal Shower@",
                440,
            ),
        ):
            self.assertEqual(
                sum(
                    v2_width_payload[ord(character) - 0x20]
                    for character in text
                ),
                expected,
            )
        self.assertEqual(
            sum(
                v2_width_payload[ord(character) - 0x20]
                for character in "Ultimate Jutsu Prep"
            ),
            178,
        )
        self.assertEqual(
            min(1.0, 128.0 / 178.0),
            128.0 / 178.0,
        )
        adapter_fragment = next(
            fragment
            for fragment in v2_declaration.fragments
            if fragment.symbol == "localization.font.v2.adapter_call"
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in adapter_fragment.relocations
            },
            {
                ("jal26", "localization.font.v2.prepare"),
                ("hi16", "localization.font.v2.session_pointer"),
                ("lo16", "localization.font.v2.session_pointer"),
            },
        )
        adapter = v2_build.symbols["localization.font.v2.adapter_call"]
        adapter_payload = v2_build.payload[
            adapter.file_offset:adapter.file_offset + adapter.size
        ]
        adapter_words = [
            int.from_bytes(adapter_payload[offset:offset + 4], "little")
            for offset in range(0, len(adapter_payload), 4)
        ]
        prepare = v2_build.symbols["localization.font.v2.prepare"]
        self.assertIn(
            mips.jump(0x03, prepare.runtime_address),
            adapter_words,
        )
        self.assertIn(mips.r_type(2, 0, 31, 0x09), adapter_words)
        for argument_register, offset in (
            (4, 0x50),
            (5, 0x54),
            (6, 0x58),
            (7, 0x5C),
        ):
            self.assertIn(
                mips.i_type(0x23, 17, argument_register, offset),
                adapter_words,
            )
        for expected_word in (
            mips.i_type(0x2B, 17, 3, 0x00),
            mips.i_type(0x2B, 17, 2, 0x60),
            mips.i_type(0x2B, 17, 3, 0x64),
            mips.i_type(0x2B, 18, 0, 0x3C),
            mips.i_type(0x31, 17, 0, 0x38),
            mips.i_type(0x23, 17, 2, 0x60),
            mips.i_type(0x23, 17, 3, 0x64),
            mips.r_type(2, 0, 5, 0x2D),
            mips.r_type(5, 0, 2, 0x2D),
        ):
            self.assertIn(expected_word, adapter_words)
        self.assertTrue(
            any(
                word & 0xFFFF0000
                == mips.i_type(0x2B, 16, 17, 0) & 0xFFFF0000
                for word in adapter_words
            )
        )
        self.assertTrue(
            any(
                word & 0xFFFF0000
                == mips.i_type(0x2B, 16, 3, 0) & 0xFFFF0000
                for word in adapter_words
            )
        )
        v2_symbols = {
            "font_v2_layout_core_01": "localization.font.v2.plain_space",
            "font_v2_layout_core_02": (
                "localization.font.v2.newline_advance"
            ),
            "font_v2_layout_core_03": "localization.font.v2.right_edge",
            "font_v2_layout_core_04": "localization.font.v2.half_space",
            "font_v2_layout_core_05": (
                "localization.font.v2.glyph_advance"
            ),
        }
        for edit in v2_package.edits:
            linked = v2_build.symbols[v2_symbols[edit.edit_id]]
            jump = int.from_bytes(
                bytes.fromhex(edit.replacement_hex)[:4], "little"
            )
            self.assertEqual(jump >> 26, 0x02)
            self.assertEqual(
                (jump & 0x03FFFFFF) << 2,
                linked.runtime_address,
            )
            self.assertEqual(
                bytes.fromhex(edit.replacement_hex)[4:],
                b"\0" * 4,
            )
        inactive_words = {
            "localization.font.v2.plain_space": {
                0xC6600004,
                0x46010040,
            },
            "localization.font.v2.newline_advance": {
                0xC6600040,
                0x46000840,
            },
            "localization.font.v2.right_edge": {
                0x46000D40,
                0xC6200020,
            },
            "localization.font.v2.half_space": {
                0x4603101C,
                0xE660001C,
            },
            "localization.font.v2.glyph_advance": {
                0x46020040,
                0xC660001C,
            },
        }
        for symbol, expected_words in inactive_words.items():
            linked = v2_build.symbols[symbol]
            payload = v2_build.payload[
                linked.file_offset:linked.file_offset + linked.size
            ]
            words = {
                int.from_bytes(payload[offset:offset + 4], "little")
                for offset in range(0, len(payload), 4)
            }
            self.assertTrue(
                expected_words.issubset(words),
                f"{symbol}: missing "
                f"{sorted(expected_words - words)}",
            )
            self.assertTrue(
                any(
                    word >> 26 == 0x04
                    and (word >> 21) & 0x1F == 3
                    and (word >> 16) & 0x1F == 0
                    for word in words
                )
            )

        controls_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {"font_v2_layout_core", "font_v2_controls"},
                )
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        controls_build = build_resident_payload(
            controls_declaration.fragments
        )
        controls_resolved = resolve_symbolic_patches(
            controls_build, controls_declaration.symbolic_patches
        )
        controls_package = engine.build_binary_package(
            controls_declaration, controls_resolved
        )
        self.assertEqual(
            {edit.edit_id for edit in controls_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_controls_01",
            },
        )
        controls_edits = {
            edit.edit_id: edit
            for edit in controls_package.edits
            if edit.patch_id == "font_v2_controls"
        }
        self.assertEqual(
            {
                edit_id: edit.destination_offset
                for edit_id, edit in controls_edits.items()
            },
            {
                "font_v2_controls_01": 0x288848,
            },
        )
        controls_adapter = controls_build.symbols[
            "localization.font.v2.controls_adapter"
        ]
        for edit_id in ("font_v2_controls_01",):
            controls_edit = controls_edits[edit_id]
            self.assertEqual(
                bytes.fromhex(controls_edit.expected_hex),
                bytes.fromhex("90E40D0C00000000"),
            )
            controls_hook = bytes.fromhex(
                controls_edit.replacement_hex
            )
            self.assertEqual(len(controls_hook), 8)
            controls_jump = int.from_bytes(
                controls_hook[:4], "little"
            )
            self.assertEqual(controls_jump >> 26, 0x03)
            self.assertEqual(
                (controls_jump & 0x03FFFFFF) << 2,
                controls_adapter.runtime_address,
            )
            self.assertEqual(controls_hook[4:], b"\0" * 4)

        controls_adapter_fragment = next(
            fragment
            for fragment in controls_declaration.fragments
            if fragment.symbol
            == "localization.font.v2.controls_adapter"
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in controls_adapter_fragment.relocations
            },
            {
                (
                    "hi16",
                    "localization.font.v2.controls_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.controls_callback",
                ),
                (
                    "jal26",
                    "localization.font.v2.adapter_call",
                ),
            },
        )
        controls_adapter_payload = controls_build.payload[
            controls_adapter.file_offset:
            controls_adapter.file_offset + controls_adapter.size
        ]
        controls_adapter_words = {
            int.from_bytes(
                controls_adapter_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(controls_adapter_payload), 4)
        }
        generic_adapter = controls_build.symbols[
            "localization.font.v2.adapter_call"
        ]
        self.assertIn(
            mips.jump(0x03, generic_adapter.runtime_address),
            controls_adapter_words,
        )
        self.assertIn(
            mips.i_type(0x0F, 0, 1, 0x4280),
            controls_adapter_words,
        )
        for expected_word in (
            mips.cop1(0x01, 12, 12, 0),
            mips.i_type(0x39, 29, 12, 0x08),
            mips.i_type(0x39, 29, 13, 0x0C),
            mips.i_type(0x2B, 29, 2, 0x10),
            mips.i_type(0x2B, 29, 3, 0x14),
            mips.i_type(0x2B, 29, 6, 0x18),
            mips.i_type(0x2B, 29, 0, 0x1C),
            mips.i_type(0x2B, 29, 6, 0x20),
            mips.i_type(0x2B, 29, 6, 0x24),
            mips.i_type(0x2B, 29, 29, 0x58),
        ):
            self.assertIn(expected_word, controls_adapter_words)

        controls_callback = controls_build.symbols[
            "localization.font.v2.controls_callback"
        ]
        controls_callback_payload = controls_build.payload[
            controls_callback.file_offset:
            controls_callback.file_offset + controls_callback.size
        ]
        controls_callback_words = {
            int.from_bytes(
                controls_callback_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(controls_callback_payload), 4)
        }
        for expected_word in (
            mips.jump(0x03, 0x003798E0),
            mips.jump(0x03, 0x00379240),
            mips.r_type(0, 2, 8, 0x03, shift=1),
            mips.i_type(0x31, 18, 12, 0x48),
            mips.i_type(0x31, 18, 13, 0x4C),
        ):
            self.assertIn(expected_word, controls_callback_words)

        titles_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {"font_v2_layout_core", "font_v2_titles"},
                )
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        titles_build = build_resident_payload(
            titles_declaration.fragments
        )
        titles_resolved = resolve_symbolic_patches(
            titles_build, titles_declaration.symbolic_patches
        )
        titles_package = engine.build_binary_package(
            titles_declaration, titles_resolved
        )
        self.assertEqual(
            {edit.edit_id for edit in titles_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_titles_01",
                "font_v2_titles_02",
            },
        )
        title_edits = {
            edit.edit_id: edit
            for edit in titles_package.edits
            if edit.edit_id.startswith("font_v2_titles_")
        }
        self.assertEqual(
            {
                edit_id: edit.destination_offset
                for edit_id, edit in title_edits.items()
            },
            {
                "font_v2_titles_01": 0x1C6A28,
                "font_v2_titles_02": 0x1C4B98,
            },
        )
        title_symbols = {
            "font_v2_titles_01": (
                "localization.font.v2.command_title_entry"
            ),
            "font_v2_titles_02": (
                "localization.font.v2.practice_title_entry"
            ),
        }
        for edit_id, edit in title_edits.items():
            self.assertEqual(
                bytes.fromhex(edit.expected_hex),
                bytes.fromhex("C4080E0C00000000"),
            )
            hook = bytes.fromhex(edit.replacement_hex)
            self.assertEqual(len(hook), 8)
            jump = int.from_bytes(hook[:4], "little")
            self.assertEqual(jump >> 26, 0x03)
            self.assertEqual(
                (jump & 0x03FFFFFF) << 2,
                titles_build.symbols[
                    title_symbols[edit_id]
                ].runtime_address,
            )
            self.assertEqual(hook[4:], b"\0" * 4)

        title_adapter_fragment = next(
            fragment
            for fragment in titles_declaration.fragments
            if fragment.symbol == "localization.font.v2.title_adapter"
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in title_adapter_fragment.relocations
            },
            {
                ("hi16", "localization.font.v2.title_callback"),
                ("lo16", "localization.font.v2.title_callback"),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )
        title_adapter = titles_build.symbols[
            "localization.font.v2.title_adapter"
        ]
        title_adapter_payload = titles_build.payload[
            title_adapter.file_offset:
            title_adapter.file_offset + title_adapter.size
        ]
        title_adapter_words = {
            int.from_bytes(
                title_adapter_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(title_adapter_payload), 4)
        }
        line_height_bits = struct.unpack(
            "<I", struct.pack("<f", 20.0)
        )[0]
        for expected_word in (
            mips.cop1(0x00, 12, 12, 14),
            mips.i_type(0x0F, 0, 1, line_height_bits >> 16),
            mips.i_type(0x39, 29, 13, 0x08),
            mips.i_type(0x39, 29, 12, 0x0C),
            mips.i_type(0x2B, 29, 7, 0x10),
            mips.i_type(0x2B, 29, 2, 0x14),
            mips.i_type(0x2B, 29, 0, 0x18),
            mips.i_type(0x2B, 29, 0, 0x1C),
            mips.i_type(0x2B, 29, 3, 0x20),
            mips.i_type(0x2B, 29, 3, 0x24),
            mips.i_type(0x2B, 29, 29, 0x5C),
            mips.jump(
                0x03,
                titles_build.symbols[
                    "localization.font.v2.adapter_call"
                ].runtime_address,
            ),
        ):
            self.assertIn(expected_word, title_adapter_words)

        title_callback = titles_build.symbols[
            "localization.font.v2.title_callback"
        ]
        title_callback_payload = titles_build.payload[
            title_callback.file_offset:
            title_callback.file_offset + title_callback.size
        ]
        title_callback_words = {
            int.from_bytes(
                title_callback_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(title_callback_payload), 4)
        }
        self.assertEqual(
            title_callback_words,
            {
                mips.i_type(0x31, 7, 12, 0x48),
                mips.i_type(0x31, 7, 13, 0x4C),
                mips.jump(0x02, 0x00382310),
                0,
            },
        )

        title_adapter_address = title_adapter.runtime_address
        for symbol, box_x, y_offset, width in (
            (
                "localization.font.v2.command_title_entry",
                27.2,
                -3.8,
                288,
            ),
            (
                "localization.font.v2.practice_title_entry",
                31.2,
                -6.8,
                352,
            ),
        ):
            entry = titles_build.symbols[symbol]
            entry_payload = titles_build.payload[
                entry.file_offset:entry.file_offset + entry.size
            ]
            entry_words = [
                int.from_bytes(
                    entry_payload[offset:offset + 4], "little"
                )
                for offset in range(0, len(entry_payload), 4)
            ]
            self.assertIn(mips.cop1(0x06, 12, 13, 0), entry_words)
            for value, float_register in (
                (y_offset, 14),
                (box_x, 13),
            ):
                bits = struct.unpack("<I", struct.pack("<f", value))[0]
                self.assertIn(
                    mips.i_type(0x0F, 0, 1, bits >> 16),
                    entry_words,
                )
                self.assertIn(
                    mips.i_type(0x0D, 1, 1, bits & 0xFFFF),
                    entry_words,
                )
                self.assertIn(mips.mtc1(1, float_register), entry_words)
            self.assertIn(
                mips.i_type(0x09, 0, 7, width),
                entry_words,
            )
            self.assertIn(
                mips.jump(0x03, title_adapter_address),
                entry_words,
            )

        pause_list_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {
                        "font_v2_layout_core",
                        "font_v2_pause_controls_list",
                    },
                )
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        pause_list_build = build_resident_payload(
            pause_list_declaration.fragments
        )
        pause_list_resolved = resolve_symbolic_patches(
            pause_list_build,
            pause_list_declaration.symbolic_patches,
        )
        pause_list_package = engine.build_binary_package(
            pause_list_declaration,
            pause_list_resolved,
        )
        self.assertEqual(
            {edit.edit_id for edit in pause_list_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_pause_controls_list_01",
                "font_v2_pause_controls_list_02",
            },
        )
        pause_list_edit = next(
            edit
            for edit in pause_list_package.edits
            if edit.edit_id == "font_v2_pause_controls_list_01"
        )
        self.assertEqual(pause_list_edit.destination_offset, 0x1C97D8)
        self.assertEqual(
            bytes.fromhex(pause_list_edit.expected_hex),
            bytes.fromhex("1C090E0C00000000"),
        )
        pause_list_selected_edit = next(
            edit
            for edit in pause_list_package.edits
            if edit.edit_id == "font_v2_pause_controls_list_02"
        )
        self.assertEqual(
            pause_list_selected_edit.destination_offset,
            0x1C9794,
        )
        self.assertEqual(
            bytes.fromhex(pause_list_selected_edit.expected_hex),
            bytes.fromhex("E8090E0C00000000"),
        )
        for text, expected_width in (
            ("Controls", 77),
            ("1P Commands", 119),
            ("Command Chart", 140),
            ("Simple Display", 124),
            ("Back to Game Mode Screen", 245),
            ("Back to Character Select", 231),
        ):
            measured_width = sum(
                v2_width_payload[ord(character) - 0x20]
                for character in text
            )
            self.assertEqual(measured_width, expected_width)
            self.assertEqual(
                measured_width > 216,
                text.startswith("Back to "),
            )
        pause_list_hook = bytes.fromhex(
            pause_list_edit.replacement_hex
        )
        self.assertEqual(len(pause_list_hook), 8)
        pause_list_jump = int.from_bytes(
            pause_list_hook[:4],
            "little",
        )
        self.assertEqual(pause_list_jump >> 26, 0x03)
        self.assertEqual(
            (pause_list_jump & 0x03FFFFFF) << 2,
            pause_list_build.symbols[
                "localization.font.v2.pause_list_adapter"
            ].runtime_address,
        )
        self.assertEqual(pause_list_hook[4:], b"\0" * 4)
        pause_list_selected_hook = bytes.fromhex(
            pause_list_selected_edit.replacement_hex
        )
        self.assertEqual(len(pause_list_selected_hook), 8)
        pause_list_selected_jump = int.from_bytes(
            pause_list_selected_hook[:4],
            "little",
        )
        self.assertEqual(pause_list_selected_jump >> 26, 0x03)
        self.assertEqual(
            (pause_list_selected_jump & 0x03FFFFFF) << 2,
            pause_list_build.symbols[
                "localization.font.v2.pause_list_selected_adapter"
            ].runtime_address,
        )
        self.assertEqual(pause_list_selected_hook[4:], b"\0" * 4)

        pause_list_adapter_fragment = next(
            fragment
            for fragment in pause_list_declaration.fragments
            if fragment.symbol
            == "localization.font.v2.pause_list_adapter"
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in pause_list_adapter_fragment.relocations
            },
            {
                (
                    "hi16",
                    "localization.font.v2.pause_list_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.pause_list_callback",
                ),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )
        pause_list_adapter = pause_list_build.symbols[
            "localization.font.v2.pause_list_adapter"
        ]
        pause_list_adapter_payload = pause_list_build.payload[
            pause_list_adapter.file_offset:
            pause_list_adapter.file_offset + pause_list_adapter.size
        ]
        pause_list_adapter_words = {
            int.from_bytes(
                pause_list_adapter_payload[offset:offset + 4],
                "little",
            )
            for offset in range(
                0,
                len(pause_list_adapter_payload),
                4,
            )
        }
        for value in (4.0, 20.0):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                pause_list_adapter_words,
            )
        for expected_word in (
            mips.i_type(0x2B, 29, 8, 0x10),
            mips.i_type(0x2B, 29, 8, 0x14),
            mips.i_type(0x2B, 29, 0, 0x18),
            mips.i_type(0x2B, 29, 0, 0x1C),
            mips.i_type(0x2B, 29, 8, 0x20),
            mips.i_type(0x2B, 29, 8, 0x24),
            mips.i_type(0x2B, 29, 9, 0x5C),
            mips.i_type(0x0D, 8, 8, 216),
            mips.cop1(0x01, 0, 13, 0),
            mips.jump(
                0x03,
                pause_list_build.symbols[
                    "localization.font.v2.adapter_call"
                ].runtime_address,
            ),
        ):
            self.assertIn(expected_word, pause_list_adapter_words)

        pause_list_callback = pause_list_build.symbols[
            "localization.font.v2.pause_list_callback"
        ]
        pause_list_callback_payload = pause_list_build.payload[
            pause_list_callback.file_offset:
            pause_list_callback.file_offset + pause_list_callback.size
        ]
        pause_list_callback_words = {
            int.from_bytes(
                pause_list_callback_payload[offset:offset + 4],
                "little",
            )
            for offset in range(
                0,
                len(pause_list_callback_payload),
                4,
            )
        }
        self.assertEqual(
            pause_list_callback_words,
            {
                mips.i_type(0x31, 7, 12, 0x48),
                mips.i_type(0x31, 7, 13, 0x4C),
                mips.jump(0x02, 0x00382470),
                0,
            },
        )

        pause_list_selected_adapter_fragment = next(
            fragment
            for fragment in pause_list_declaration.fragments
            if fragment.symbol
            == "localization.font.v2.pause_list_selected_adapter"
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation
                in pause_list_selected_adapter_fragment.relocations
            },
            {
                (
                    "hi16",
                    "localization.font.v2.pause_list_selected_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.pause_list_selected_callback",
                ),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )
        pause_list_selected_adapter = pause_list_build.symbols[
            "localization.font.v2.pause_list_selected_adapter"
        ]
        pause_list_selected_adapter_payload = pause_list_build.payload[
            pause_list_selected_adapter.file_offset:
            pause_list_selected_adapter.file_offset
            + pause_list_selected_adapter.size
        ]
        pause_list_selected_adapter_words = {
            int.from_bytes(
                pause_list_selected_adapter_payload[offset:offset + 4],
                "little",
            )
            for offset in range(
                0,
                len(pause_list_selected_adapter_payload),
                4,
            )
        }
        for value in (2.0, 4.0, 20.0):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                pause_list_selected_adapter_words,
            )
        for expected_word in (
            mips.i_type(0x2B, 29, 8, 0x68),
            mips.mtc1(5, 0),
            mips.mtc1(6, 0),
            mips.cop1(0x20, 0, 0, fmt=20),
            mips.cop1(0x00, 0, 0, 1),
            mips.cop1(0x01, 0, 0, 1),
            mips.i_type(0x0D, 8, 8, 216),
            mips.jump(
                0x03,
                pause_list_build.symbols[
                    "localization.font.v2.adapter_call"
                ].runtime_address,
            ),
        ):
            self.assertIn(
                expected_word,
                pause_list_selected_adapter_words,
            )

        pause_list_selected_callback = pause_list_build.symbols[
            "localization.font.v2.pause_list_selected_callback"
        ]
        pause_list_selected_callback_payload = pause_list_build.payload[
            pause_list_selected_callback.file_offset:
            pause_list_selected_callback.file_offset
            + pause_list_selected_callback.size
        ]
        pause_list_selected_callback_words = {
            int.from_bytes(
                pause_list_selected_callback_payload[offset:offset + 4],
                "little",
            )
            for offset in range(
                0,
                len(pause_list_selected_callback_payload),
                4,
            )
        }
        self.assertEqual(
            pause_list_selected_callback_words,
            {
                mips.i_type(0x31, 7, 0, 0x48),
                mips.cop1(0x24, 0, 0),
                mips.mfc1(5, 0),
                mips.i_type(0x31, 7, 1, 0x4C),
                mips.cop1(0x24, 1, 1),
                mips.mfc1(6, 1),
                mips.i_type(0x23, 7, 8, 0x68),
                mips.i_type(0x23, 7, 7, 0x04),
                mips.jump(0x02, 0x003827A0),
                0,
            },
        )

        practice_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {
                        "font_v2_layout_core",
                        "font_v2_practice_explanations",
                    },
                )
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        practice_build = build_resident_payload(
            practice_declaration.fragments
        )
        practice_resolved = resolve_symbolic_patches(
            practice_build, practice_declaration.symbolic_patches
        )
        practice_package = engine.build_binary_package(
            practice_declaration, practice_resolved
        )
        self.assertEqual(
            {edit.edit_id for edit in practice_package.edits},
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_practice_explanations_01",
            },
        )
        practice_edit = next(
            edit
            for edit in practice_package.edits
            if edit.edit_id == "font_v2_practice_explanations_01"
        )
        self.assertEqual(practice_edit.destination_offset, 0x1C4BA0)
        self.assertEqual(
            bytes.fromhex(practice_edit.expected_hex),
            bytes.fromhex(
                "0042023C00A882440000000000AD16462D"
                "8800008400001000000000"
            ),
        )
        practice_hook = bytes.fromhex(practice_edit.replacement_hex)
        self.assertEqual(len(practice_hook), 28)
        self.assertEqual(
            practice_hook[:12],
            bytes.fromhex("2128000206B300464804868E"),
        )
        practice_jump = int.from_bytes(practice_hook[12:16], "little")
        self.assertEqual(practice_jump >> 26, 0x03)
        self.assertEqual(
            (practice_jump & 0x03FFFFFF) << 2,
            practice_build.symbols[
                "localization.font.v2.practice_adapter"
            ].runtime_address,
        )
        self.assertEqual(
            practice_hook[16:],
            bytes.fromhex("212080028900001000000000"),
        )

        practice_tokens = practice_build.symbols[
            "localization.font.v2.practice_tokens"
        ]
        practice_token_payload = practice_build.payload[
            practice_tokens.file_offset:
            practice_tokens.file_offset + practice_tokens.size
        ]
        expected_tokens = (
            "<iconUP>",
            "<iconDOWN>",
            "<iconRIGHT>",
            "<iconLEFT>",
            "<iconCIRCLE>",
            "<iconTRIANGLE>",
            "<iconSQUARE>",
            "<iconCROSS>",
            "<iconETC0>",
            "<iconL1>",
            "<iconR1>",
            "<iconL2>",
            "<iconR2>",
        )
        expected_token_payload = b"".join(
            (token.encode("ascii") + b"\0").ljust(16, b"\0")
            for token in expected_tokens
        ) + b" \0"
        self.assertEqual(practice_token_payload, expected_token_payload)

        practice_icon_map = practice_build.symbols[
            "localization.font.v2.practice_icon_map"
        ]
        self.assertEqual(
            practice_build.payload[
                practice_icon_map.file_offset:
                practice_icon_map.file_offset + practice_icon_map.size
            ],
            bytes(
                (
                    5,
                    4,
                    7,
                    6,
                    9,
                    11,
                    10,
                    12,
                    0xFF,
                    0xFF,
                    0xFF,
                    0,
                    1,
                    3,
                    2,
                    0xFF,
                    0xFF,
                    8,
                )
            ),
        )

        practice_fragments = {
            fragment.symbol: fragment
            for fragment in practice_declaration.fragments
        }
        self.assertEqual(
            [
                (relocation.kind, relocation.symbol)
                for relocation in practice_fragments[
                    "localization.font.v2.wrap_native"
                ].relocations
            ],
            [
                ("jal26", "localization.font.v2.native_measure"),
                ("jal26", "localization.font.v2.native_measure"),
                ("jal26", "localization.font.v2.native_measure"),
            ],
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in practice_fragments[
                    "localization.font.v2.practice_adapter"
                ].relocations
            },
            {
                ("hi16", "localization.font.v2.practice_tokens"),
                ("lo16", "localization.font.v2.practice_tokens"),
                ("jal26", "localization.font.v2.practice_append"),
                (
                    "hi16",
                    "localization.font.v2.practice_icon_metric",
                ),
                (
                    "lo16",
                    "localization.font.v2.practice_icon_metric",
                ),
                (
                    "hi16",
                    "localization.font.v2.practice_icon_draw",
                ),
                (
                    "lo16",
                    "localization.font.v2.practice_icon_draw",
                ),
                ("jal26", "localization.font.v2.wrap_native"),
                (
                    "hi16",
                    "localization.font.v2.practice_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.practice_callback",
                ),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )

        practice_adapter = practice_build.symbols[
            "localization.font.v2.practice_adapter"
        ]
        practice_adapter_payload = practice_build.payload[
            practice_adapter.file_offset:
            practice_adapter.file_offset + practice_adapter.size
        ]
        practice_adapter_words = {
            int.from_bytes(
                practice_adapter_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(practice_adapter_payload), 4)
        }
        for value in (39.2, 21.2, 28.0, 14.0):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                practice_adapter_words,
            )
            if bits & 0xFFFF:
                self.assertIn(
                    mips.i_type(0x0D, 8, 8, bits & 0xFFFF),
                    practice_adapter_words,
                )
        for expected_word in (
            mips.i_type(0x0D, 8, 8, 364),
            mips.i_type(0x0D, 8, 8, 48),
            mips.i_type(0x0D, 8, 8, 0x1D),
            mips.i_type(0x2B, 29, 19, 0x6C),
            mips.i_type(0x2B, 29, 18, 0x70),
            mips.i_type(0x2B, 29, 8, 0x24),
            mips.i_type(0x23, 8, 9, 0x7C),
            mips.i_type(0x23, 8, 9, 0x78),
            mips.i_type(0x2B, 8, 9, 0x7C),
            mips.i_type(0x2B, 8, 9, 0x78),
        ):
            self.assertIn(expected_word, practice_adapter_words)
        self.assertIn(
            struct.pack(
                "<2I",
                mips.i_type(0x0F, 0, 8, 0),
                mips.i_type(0x2B, 29, 8, 0x24),
            ),
            practice_adapter_payload,
        )

        practice_icon_draw = practice_build.symbols[
            "localization.font.v2.practice_icon_draw"
        ]
        practice_icon_draw_payload = practice_build.payload[
            practice_icon_draw.file_offset:
            practice_icon_draw.file_offset + practice_icon_draw.size
        ]
        practice_icon_draw_words = {
            int.from_bytes(
                practice_icon_draw_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(practice_icon_draw_payload), 4)
        }
        for expected_word in (
            mips.jump(0x03, 0x0037BB40),
            mips.i_type(0x23, 8, 4, 0x6C),
            mips.i_type(0x23, 8, 4, 0x70),
            mips.i_type(0x0F, 0, 9, 0x008D),
            mips.i_type(0x0D, 9, 9, 0x14C0),
        ):
            self.assertIn(expected_word, practice_icon_draw_words)

        practice_callback = practice_build.symbols[
            "localization.font.v2.practice_callback"
        ]
        practice_callback_payload = practice_build.payload[
            practice_callback.file_offset:
            practice_callback.file_offset + practice_callback.size
        ]
        self.assertEqual(
            {
                int.from_bytes(
                    practice_callback_payload[offset:offset + 4],
                    "little",
                )
                for offset in range(0, len(practice_callback_payload), 4)
            },
            {
                mips.i_type(0x31, 7, 12, 0x48),
                mips.i_type(0x31, 7, 13, 0x4C),
                mips.jump(0x02, 0x00382310),
                0,
            },
        )

        practice_prepare = practice_build.symbols[
            "localization.font.v2.prepare"
        ]
        practice_prepare_payload = practice_build.payload[
            practice_prepare.file_offset:
            practice_prepare.file_offset + practice_prepare.size
        ]
        practice_prepare_words = {
            int.from_bytes(
                practice_prepare_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(practice_prepare_payload), 4)
        }
        for expected_word in (
            mips.i_type(0x0C, 5, 2, 0x10),
            mips.i_type(0x0C, 6, 2, 0x08),
            mips.i_type(0x31, 16, 2, 0x68),
        ):
            self.assertIn(expected_word, practice_prepare_words)
        practice_prepare_fragment = next(
            fragment
            for fragment in practice_declaration.fragments
            if fragment.symbol == "localization.font.v2.prepare"
        )
        self.assertEqual(
            {
                ("jal26", "localization.font.v2.measure"),
            },
            {
                (relocation.kind, relocation.symbol)
                for relocation in practice_prepare_fragment.relocations
            },
        )
        practice_measure_fragment = next(
            fragment
            for fragment in practice_declaration.fragments
            if fragment.symbol == "localization.font.v2.measure"
        )
        self.assertEqual(
            {
                ("hi16", "localization.font.v2.ascii_widths"),
                ("lo16", "localization.font.v2.ascii_widths"),
                ("jal26", "localization.font.v2.c.is_br"),
            },
            {
                (relocation.kind, relocation.symbol)
                for relocation in practice_measure_fragment.relocations
            },
        )

    def test_v2_quit_confirmation_is_scoped_and_mapping_neutral(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        directory = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector"
        )
        canonical = engine.load_package(
            directory, owner="localization.runtime_injector"
        )
        declaration = replace(
            canonical,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {
                        "font_v2_layout_core",
                        "font_v2_quit_confirmation",
                    },
                )
                for patch_id, patch in canonical.patches.items()
            },
        )
        build = build_resident_payload(declaration.fragments)
        resolved = resolve_symbolic_patches(
            build, declaration.symbolic_patches
        )
        package = engine.build_binary_package(declaration, resolved)
        edits = {edit.edit_id: edit for edit in package.edits}
        self.assertEqual(
            set(edits),
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_quit_confirmation_01",
                "font_v2_quit_confirmation_02",
                "font_v2_quit_confirmation_03",
                "font_v2_quit_confirmation_04",
            },
        )
        expected_hooks = {
            "font_v2_quit_confirmation_01": (
                0x1C4048,
                "800D0E0C00000000",
                "localization.font.v2.quit_choices_scope",
            ),
            "font_v2_quit_confirmation_02": (
                0x1C407C,
                "6C090E0C00000000",
                "localization.font.v2.quit_body_adapter",
            ),
            "font_v2_quit_confirmation_03": (
                0x283914,
                "54E40D0C00000000",
                "localization.font.v2.quit_selected_adapter",
            ),
            "font_v2_quit_confirmation_04": (
                0x283A60,
                "88E60D0C00000000",
                "localization.font.v2.quit_unselected_adapter",
            ),
        }
        for edit_id, (offset, expected_hex, symbol) in expected_hooks.items():
            edit = edits[edit_id]
            self.assertEqual(edit.destination_offset, offset)
            self.assertEqual(edit.expected_hex, expected_hex)
            replacement = bytes.fromhex(edit.replacement_hex)
            self.assertEqual(replacement[4:], b"\0" * 4)
            jump = int.from_bytes(replacement[:4], "little")
            self.assertEqual(jump >> 26, 0x03)
            self.assertEqual(
                (jump & 0x03FFFFFF) << 2,
                build.symbols[symbol].runtime_address,
            )

        fragments = {
            fragment.symbol: fragment
            for fragment in declaration.fragments
        }
        active = fragments["localization.font.v2.quit_active"]
        self.assertEqual(active.kind, "data")
        self.assertEqual(active.payload, b"\0" * 4)

        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in fragments[
                    "localization.font.v2.quit_choices_scope"
                ].relocations
            },
            {
                ("hi16", "localization.font.v2.quit_active"),
                ("lo16", "localization.font.v2.quit_active"),
            },
        )
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in fragments[
                    "localization.font.v2.quit_body_adapter"
                ].relocations
            },
            {
                ("jal26", "localization.font.v2.wrap_native"),
                (
                    "hi16",
                    "localization.font.v2.quit_body_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.quit_body_callback",
                ),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )

        selected = build.symbols[
            "localization.font.v2.quit_selected_adapter"
        ]
        selected_payload = build.payload[
            selected.file_offset:selected.file_offset + selected.size
        ]
        selected_word_list = [
            int.from_bytes(
                selected_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(selected_payload), 4)
        ]
        selected_words = set(selected_word_list)
        for value in (
            24.0,
            56.0,
            64.5,
            31.5,
            68.5,
            49.0,
            66.0,
            31.0,
        ):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                selected_words,
            )
        self.assertIn(
            mips.i_type(0x0F, 0, 8, 0x0060),
            selected_words,
        )
        self.assertIn(
            mips.i_type(0x0D, 8, 8, 0x59F0),
            selected_words,
        )
        self.assertIn(
            mips.i_type(0x0D, 8, 8, 0x59F8),
            selected_words,
        )
        self.assertIn(
            mips.jump(0x02, 0x00379150),
            selected_words,
        )
        selected_on = selected_word_list.index(
            mips.i_type(0x0D, 8, 8, 0x59F0)
        )
        selected_off = selected_word_list.index(
            mips.i_type(0x0D, 8, 8, 0x59F8)
        )
        selected_on_branch = selected_word_list[selected_on + 1]
        self.assertEqual(selected_on_branch >> 26, 0x04)
        selected_on_delta = selected_on_branch & 0xFFFF
        if selected_on_delta & 0x8000:
            selected_on_delta -= 0x10000
        selected_on_target = selected_on + 2 + selected_on_delta
        self.assertEqual(
            selected_word_list[selected_on_target],
            mips.i_type(0x0F, 0, 8, 0x4284),
        )
        self.assertEqual(
            selected_word_list[selected_off + 3],
            mips.i_type(0x0F, 0, 8, 0x426C),
        )

        unselected = build.symbols[
            "localization.font.v2.quit_unselected_adapter"
        ]
        unselected_payload = build.payload[
            unselected.file_offset:unselected.file_offset + unselected.size
        ]
        unselected_word_list = [
            int.from_bytes(
                unselected_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(unselected_payload), 4)
        ]
        unselected_words = set(unselected_word_list)
        self.assertIn(
            mips.jump(0x02, 0x00379A20),
            unselected_words,
        )
        self.assertIn(
            mips.jump(0x03, 0x00379A20),
            unselected_words,
        )
        for value, register in ((59.0, 8), (49.0, 9), (31.0, 9)):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, register, bits >> 16),
                unselected_words,
            )
        self.assertIn(
            mips.i_type(0x0F, 0, 8, 0x0060),
            unselected_words,
        )
        self.assertIn(
            mips.i_type(0x0D, 8, 8, 0x59F8),
            unselected_words,
        )
        self.assertIn(
            mips.i_type(0x0D, 8, 8, 0x59F0),
            unselected_words,
        )
        unselected_on = unselected_word_list.index(
            mips.i_type(0x0D, 8, 8, 0x59F0)
        )
        unselected_off = unselected_word_list.index(
            mips.i_type(0x0D, 8, 8, 0x59F8)
        )
        unselected_on_branch = unselected_word_list[unselected_on + 1]
        self.assertEqual(unselected_on_branch >> 26, 0x04)
        unselected_on_delta = unselected_on_branch & 0xFFFF
        if unselected_on_delta & 0x8000:
            unselected_on_delta -= 0x10000
        unselected_on_target = unselected_on + 2 + unselected_on_delta
        self.assertEqual(
            unselected_word_list[unselected_on_target],
            mips.i_type(0x0F, 0, 8, 0x4284),
        )
        self.assertEqual(
            unselected_word_list[unselected_off + 3],
            mips.i_type(0x0F, 0, 8, 0x426C),
        )

        body = build.symbols[
            "localization.font.v2.quit_body_adapter"
        ]
        body_payload = build.payload[
            body.file_offset:body.file_offset + body.size
        ]
        body_words = {
            int.from_bytes(body_payload[offset:offset + 4], "little")
            for offset in range(0, len(body_payload), 4)
        }
        for expected_word in (
            mips.i_type(0x09, 0, 5, 420),
            mips.i_type(0x09, 0, 6, 2),
            mips.i_type(0x09, 0, 8, 0x14),
            mips.i_type(0x09, 29, 19, 0x80),
            mips.i_type(0x2B, 29, 2, 0x30),
            mips.i_type(0x2B, 29, 3, 0x34),
        ):
            self.assertIn(expected_word, body_words)

        callback = build.symbols[
            "localization.font.v2.quit_body_callback"
        ]
        callback_payload = build.payload[
            callback.file_offset:callback.file_offset + callback.size
        ]
        callback_words = {
            int.from_bytes(
                callback_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(callback_payload), 4)
        }
        for value in (19.0, 12.0):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                callback_words,
            )
        self.assertIn(
            mips.jump(0x03, 0x00379A20),
            callback_words,
        )

        mappings_path = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "translation_importer"
            / "mappings.tsv"
        )
        with mappings_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            rows = {
                row["id"]: row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["id"] in {"T63", "T64", "T65", "T66", "T67"}
            }
        self.assertEqual(set(rows), {"T63", "T64", "T65", "T66", "T67"})
        expected_donors = {
            "T63": "Are you sure you want to quit %1 and return to %2?",
            "T64": "Are you sure you want to quit %1 and return to %2?",
            "T65": "Do you want to quit %1?",
            "T66": "Are you sure you want to quit %1 and return to %2?",
            "T67": "Are you sure you want to quit %1 and return to %2?",
        }
        for mapping_id, row in rows.items():
            self.assertEqual(
                row["donor"],
                expected_donors[mapping_id],
            )
            self.assertEqual(row["replacement"], "")
            self.assertNotIn("\n", row["donor"])

    def test_v2_special_controls_body_uses_exact_nun5_box(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        directory = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector"
        )
        canonical = engine.load_package(
            directory, owner="localization.runtime_injector"
        )
        declaration = replace(
            canonical,
            patches={
                patch_id: replace(
                    patch,
                    enabled=patch_id
                    in {
                        "font_v2_layout_core",
                        "font_v2_special_controls_body",
                    },
                )
                for patch_id, patch in canonical.patches.items()
            },
        )
        build = build_resident_payload(declaration.fragments)
        resolved = resolve_symbolic_patches(
            build, declaration.symbolic_patches
        )
        package = engine.build_binary_package(declaration, resolved)
        edits = {edit.edit_id: edit for edit in package.edits}
        self.assertEqual(
            set(edits),
            {
                "font_v2_layout_core_01",
                "font_v2_layout_core_02",
                "font_v2_layout_core_03",
                "font_v2_layout_core_04",
                "font_v2_layout_core_05",
                "font_v2_special_controls_body_01",
            },
        )

        hook = edits["font_v2_special_controls_body_01"]
        self.assertEqual(hook.destination_offset, 0x1C3D38)
        self.assertEqual(hook.expected_hex, "6C090E0C00000000")
        replacement = bytes.fromhex(hook.replacement_hex)
        self.assertEqual(replacement[4:], b"\0" * 4)
        jump = int.from_bytes(replacement[:4], "little")
        self.assertEqual(jump >> 26, 0x03)
        self.assertEqual(
            (jump & 0x03FFFFFF) << 2,
            build.symbols[
                "localization.font.v2.special_controls_body_adapter"
            ].runtime_address,
        )

        fragments = {
            fragment.symbol: fragment
            for fragment in declaration.fragments
        }
        self.assertEqual(
            {
                (relocation.kind, relocation.symbol)
                for relocation in fragments[
                    "localization.font.v2.special_controls_body_adapter"
                ].relocations
            },
            {
                ("jal26", "localization.font.v2.wrap_native"),
                (
                    "hi16",
                    "localization.font.v2.special_controls_body_callback",
                ),
                (
                    "lo16",
                    "localization.font.v2.special_controls_body_callback",
                ),
                ("jal26", "localization.font.v2.adapter_call"),
            },
        )

        body = build.symbols[
            "localization.font.v2.special_controls_body_adapter"
        ]
        body_payload = build.payload[
            body.file_offset:body.file_offset + body.size
        ]
        body_words = {
            int.from_bytes(body_payload[offset:offset + 4], "little")
            for offset in range(0, len(body_payload), 4)
        }
        for expected_word in (
            mips.i_type(0x09, 0, 5, 400),
            mips.i_type(0x09, 0, 6, 2),
            mips.i_type(0x09, 0, 8, 0x14),
            mips.i_type(0x09, 29, 19, 0x80),
            mips.i_type(0x2B, 29, 2, 0x30),
            mips.i_type(0x2B, 29, 3, 0x34),
        ):
            self.assertIn(expected_word, body_words)
        self.assertIn(
            mips.i_type(0x0D, 8, 8, 60),
            body_words,
        )

        callback = build.symbols[
            "localization.font.v2.special_controls_body_callback"
        ]
        callback_payload = build.payload[
            callback.file_offset:callback.file_offset + callback.size
        ]
        callback_words = {
            int.from_bytes(
                callback_payload[offset:offset + 4], "little"
            )
            for offset in range(0, len(callback_payload), 4)
        }
        for value in (24.0, 12.0):
            bits = struct.unpack("<I", struct.pack("<f", value))[0]
            self.assertIn(
                mips.i_type(0x0F, 0, 8, bits >> 16),
                callback_words,
            )
        self.assertIn(
            mips.jump(0x03, 0x00379A20),
            callback_words,
        )

        mappings_path = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "translation_importer"
            / "mappings.tsv"
        )
        with mappings_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            row = next(
                row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["id"] == "T1880"
            )
        self.assertEqual(
            row["donor"],
            "A feature to display the special controls for the game.",
        )
        self.assertEqual(row["replacement"], "")
        self.assertNotIn("\n", row["donor"])

    def test_loads_fragments_and_compiles_symbolic_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            blob = b"\0" * 8 + b"\x00\x00\x80\x3F"
            blob_path = directory / "assets" / "resident.bin"
            blob_path.parent.mkdir()
            blob_path.write_bytes(blob)
            digest = hashlib.sha256(blob).hexdigest().upper()
            write_tsv(
                directory / "targets.tsv",
                engine.TARGET_FIELDS,
                [{
                    "target_id": "boot",
                    "root_id": "na2",
                    "role": "destination",
                    "path": "SLPS_258.37",
                    "expected_size": 64,
                    "expected_sha256": "1" * 64,
                }],
            )
            write_tsv(
                directory / "groups.tsv",
                engine.GROUP_FIELDS,
                [{
                    "group_id": "layout",
                    "enabled": 1,
                    "name": "Layout",
                    "description": "Resident layout test.",
                    "review_notes": "",
                }],
            )
            write_tsv(
                directory / "patches.tsv",
                engine.PATCH_FIELDS,
                [{
                    "patch_id": "layout_hook",
                    "group_id": "layout",
                    "enabled": 1,
                    "status": "approved_for_test",
                    "confidence": "high",
                    "name": "Layout hook",
                    "description": "Route one hook.",
                    "source_mapping_id": "TEST-LAYOUT",
                    "runtime_classification": "resident",
                    "review_notes": "",
                }],
            )
            write_tsv(
                directory / "fragments.tsv",
                engine.FRAGMENT_FIELDS,
                [
                    {
                        "fragment_id": "test.code",
                        "kind": "code",
                        "alignment": 4,
                        "blob_path": "assets/resident.bin",
                        "blob_offset": 0,
                        "length": 8,
                        "blob_sha256": digest,
                        "init": 0,
                    },
                    {
                        "fragment_id": "test.scale",
                        "kind": "data",
                        "alignment": 4,
                        "blob_path": "assets/resident.bin",
                        "blob_offset": 8,
                        "length": 4,
                        "blob_sha256": digest,
                        "init": 0,
                    },
                ],
            )
            write_tsv(
                directory / "relocations.tsv",
                engine.RELOCATION_FIELDS,
                [{
                    "relocation_id": "test.code.scale",
                    "fragment_id": "test.code",
                    "order": 10,
                    "offset": 0,
                    "kind": "abs32",
                    "symbol": "test.scale",
                    "addend": 0,
                }],
            )
            write_tsv(
                directory / "edits.tsv",
                engine.EDIT_FIELDS,
                [{
                    "edit_id": "layout_hook_jump",
                    "patch_id": "layout_hook",
                    "order": 10,
                    "target_id": "boot",
                    "offset": 16,
                    "expected_hex": "1122334455667788",
                    "replacement_hex": "0000000000000000",
                    "relocation_offset": 0,
                    "symbol": "test.code",
                    "encoding": "j26",
                    "addend": 0,
                    "reason": "Route the test hook.",
                }],
            )

            declaration = engine.load_package(
                directory, owner="feature.runtime_injector"
            )
            build = build_resident_payload(declaration.fragments)
            resolved = resolve_symbolic_patches(
                build, declaration.symbolic_patches
            )
            package = engine.build_binary_package(declaration, resolved)

            code = build.symbols["test.code"]
            scale = build.symbols["test.scale"]
            self.assertEqual(
                build.payload[code.file_offset:code.file_offset + 4],
                scale.runtime_address.to_bytes(4, "little"),
            )
            self.assertEqual(package.edits[0].replacement_hex[-8:], "00000000")
            self.assertEqual(package.edits[0].patch_id, "layout_hook")


if __name__ == "__main__":
    unittest.main()
