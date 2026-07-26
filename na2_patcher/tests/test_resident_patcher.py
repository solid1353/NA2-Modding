from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from na2_patcher.build_profile import apply_binary_patch_set
from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.binary_patcher import engine as binary_engine
from na2_patcher.modules.resident_patcher import engine
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


class ResidentPatcherTests(unittest.TestCase):
    def test_all_disabled_resident_package_composes_as_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = directory / "na2"
            root.mkdir()
            target_data = bytes(range(16))
            (root / "SLPS_258.37").write_bytes(target_data)
            package = binary_engine.Package(
                directory=directory,
                package_id="feature.resident_patcher",
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
                        name="Layout",
                        description="Retained disabled layout.",
                        review_notes="",
                    )
                },
                patches={
                    "layout_hook": binary_engine.Patch(
                        patch_id="layout_hook",
                        group_id="layout",
                        default_enabled=False,
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
                allow_empty_defaults=True,
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
            / "resident_patcher"
        )
        disabled_declaration = engine.load_package(
            directory, owner="localization.resident_patcher"
        )
        self.assertFalse(
            any(
                patch.default_enabled
                for patch in disabled_declaration.patches.values()
            )
        )
        self.assertEqual(disabled_declaration.payload_fragments, ())
        self.assertEqual(disabled_declaration.symbolic_patches, ())
        disabled_package = engine.build_binary_package(
            disabled_declaration, ()
        )
        self.assertEqual(disabled_package.edits, [])

        declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(patch, default_enabled=True)
                for patch_id, patch in disabled_declaration.patches.items()
            },
        )
        build = build_resident_payload(declaration.fragments)
        resolved = resolve_symbolic_patches(
            build, declaration.symbolic_patches
        )
        package = engine.build_binary_package(declaration, resolved)

        self.assertLessEqual(build.memory_end, load_config().maximum_end)
        self.assertEqual(
            {edit.destination_offset for edit in package.edits},
            {
                0x88070,
                0x88704,
                0x88B7C,
                0x893EC,
                0x897D8,
                0x279250,
                0x279B20,
                0x288848,
            },
        )
        self.assertTrue(
            all(
                not 0x2D3F00 <= edit.destination_offset < 0x2D4488
                for edit in package.edits
            )
        )
        ui = build.symbols["localization.font.ui_helper"]
        ui_payload = build.payload[ui.file_offset:ui.file_offset + ui.size]
        self.assertNotIn((0x003FAD20).to_bytes(4, "little"), ui_payload)
        widths = build.symbols["localization.font.ascii_widths"]
        width_payload = build.payload[
            widths.file_offset:widths.file_offset + widths.size
        ]
        self.assertEqual(len(width_payload), 95)
        for text, expected in (
            ("Susanoo's Blade", 142),
            ("Reverse Halo", 115),
            (
                "Fire Style: Phoenix Flower Jutsu @Petal Shower@",
                440,
            ),
        ):
            self.assertEqual(
                sum(width_payload[ord(character) - 0x20] for character in text),
                expected,
            )
        for fragment in declaration.fragments:
            if fragment.kind != "code":
                continue
            linked = build.symbols[fragment.symbol]
            payload = build.payload[
                linked.file_offset:linked.file_offset + linked.size
            ]
            for offset in range(0, len(payload), 4):
                word = int.from_bytes(payload[offset:offset + 4], "little")
                opcode = word >> 26
                if opcode not in {1, 4, 5, 6, 7}:
                    continue
                immediate = word & 0xFFFF
                if immediate & 0x8000:
                    immediate -= 0x10000
                target = linked.runtime_address + offset + 4 + immediate * 4
                self.assertLessEqual(linked.runtime_address, target)
                self.assertLess(target, linked.runtime_address + linked.size)
        self.assertTrue(
            all(
                len(bytes.fromhex(edit.expected_hex))
                == len(bytes.fromhex(edit.replacement_hex))
                for edit in package.edits
            )
        )
        scale = build.symbols["localization.font.scale_advance"]
        edits = {edit.edit_id: edit for edit in package.edits}
        for edit_id, addend in (
            ("font_controls_auto_fit_01", 0x00),
            ("font_controls_auto_fit_02", 0x18),
            ("font_controls_auto_fit_03", 0x2C),
        ):
            word = int.from_bytes(
                bytes.fromhex(edits[edit_id].replacement_hex)[:4],
                "little",
            )
            self.assertEqual(word >> 26, 0x02)
            self.assertEqual(
                (word & 0x03FFFFFF) << 2,
                scale.runtime_address + addend,
            )

        v2_declaration = replace(
            disabled_declaration,
            patches={
                patch_id: replace(
                    patch,
                    default_enabled=patch_id == "font_v2_layout_core",
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
        self.assertEqual(v2_width_payload, width_payload)
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
        self.assertIn(mips.r_type(25, 0, 31, 0x09), adapter_words)
        for argument_register, offset in (
            (4, 0x50),
            (5, 0x54),
            (6, 0x58),
            (7, 0x5C),
        ):
            self.assertIn(
                mips.i_type(0x23, 16, argument_register, offset),
                adapter_words,
            )
        for expected_word in (
            mips.i_type(0x2B, 16, 9, 0x00),
            mips.i_type(0x2B, 16, 9, 0x60),
            mips.i_type(0x2B, 16, 9, 0x64),
            mips.i_type(0x2B, 18, 0, 0x3C),
            mips.i_type(0x23, 16, 9, 0x38),
            mips.i_type(0x2B, 17, 16, 0x00),
            mips.i_type(0x2B, 17, 9, 0x00),
            mips.i_type(0x23, 16, 9, 0x60),
            mips.i_type(0x23, 16, 9, 0x64),
            mips.r_type(2, 0, 19, 0x21),
            mips.r_type(19, 0, 2, 0x21),
        ):
            self.assertIn(expected_word, adapter_words)
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
                    default_enabled=patch_id
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
        controls_edit = next(
            edit
            for edit in controls_package.edits
            if edit.edit_id == "font_v2_controls_01"
        )
        self.assertEqual(controls_edit.destination_offset, 0x288848)
        self.assertEqual(
            bytes.fromhex(controls_edit.expected_hex),
            bytes.fromhex("90E40D0C00000000"),
        )
        controls_adapter = controls_build.symbols[
            "localization.font.v2.controls_adapter"
        ]
        controls_hook = bytes.fromhex(controls_edit.replacement_hex)
        self.assertEqual(len(controls_hook), 8)
        controls_jump = int.from_bytes(controls_hook[:4], "little")
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
            mips.i_type(0x0F, 0, 8, 0x4284),
            controls_adapter_words,
        )
        for expected_word in (
            mips.i_type(0x2B, 29, 8, 0x10),
            mips.i_type(0x2B, 29, 8, 0x14),
            mips.i_type(0x2B, 29, 8, 0x18),
            mips.i_type(0x2B, 29, 8, 0x20),
            mips.i_type(0x2B, 29, 8, 0x24),
            mips.i_type(0x2B, 29, 9, 0x58),
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
                    "default_enabled": 1,
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
                directory, owner="feature.resident_patcher"
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
