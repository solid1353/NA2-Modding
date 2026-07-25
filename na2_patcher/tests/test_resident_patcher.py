from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.resident_patcher import engine
from na2_patcher.payload_builder.builder import (
    build_resident_payload,
    load_config,
)


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
    def test_canonical_font_helpers_use_only_resident_payload_storage(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        directory = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "resident_patcher"
        )
        declaration = engine.load_package(
            directory, owner="localization.resident_patcher"
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
        for fragment in declaration.fragments:
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
