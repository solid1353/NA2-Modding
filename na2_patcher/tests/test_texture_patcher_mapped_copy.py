from __future__ import annotations

import struct
import unittest
from unittest.mock import patch

from na2_patcher.modules.texture_patcher import engine


def _write_name(buffer: bytearray, offset: int, value: str, size: int) -> None:
    encoded = value.encode("ascii")
    if len(encoded) >= size:
        raise ValueError(value)
    buffer[offset : offset + len(encoded)] = encoded


def synthetic_ccs(
    textures: list[tuple[str, int, tuple[int, int, int]]],
    *,
    palette_reference_base: int,
) -> bytes:
    """Create a small CCS with one TEX and one CLT object per BMP file."""
    file_count = len(textures)
    object_count = file_count * 2
    toc_data = bytearray(0x20 + file_count * 0x20 + 0x20 + object_count * 0x20)

    for index, (name, _pixel_index, _color) in enumerate(textures):
        _write_name(toc_data, 0x20 + index * 0x20, name, 0x20)

    object_cursor = 0x20 + file_count * 0x20 + 0x20
    for file_index, (name, _pixel_index, _color) in enumerate(textures, 1):
        for suffix in ("tex", "clt"):
            _write_name(toc_data, object_cursor, f"{name}.{suffix}", 0x1E)
            struct.pack_into("<H", toc_data, object_cursor + 0x1E, file_index)
            object_cursor += 0x20

    result = bytearray(
        struct.pack(
            "<IIII",
            engine.SECTION_TOC,
            len(toc_data) // 4,
            file_count + 1,
            object_count + 1,
        )
    )
    result.extend(toc_data)

    for index, (_name, pixel_index, color) in enumerate(textures):
        texture_object_id = index * 2 + 1
        palette_object_id = texture_object_id + 1

        tex_data = bytearray(0x1C)
        struct.pack_into("<I", tex_data, 0, palette_reference_base + index)
        tex_data[0xC] = 1
        tex_data[0xD] = 1
        tex_data[0x18:] = bytes([pixel_index]) * 4
        tex_size_words = 51 + len(tex_data) // 4
        result.extend(
            struct.pack(
                "<III", engine.SECTION_TEXTURE, tex_size_words, texture_object_id
            )
        )
        result.extend(tex_data)

        clt_data = bytearray(0x18)
        clt_data[0x10:0x14] = bytes((*color, 0x80))
        clt_data[0x14:0x18] = bytes((0, 0, 0, 0))
        clt_size_words = (12 + len(clt_data) - 8) // 4
        result.extend(
            struct.pack(
                "<III", engine.SECTION_PALETTE, clt_size_words, palette_object_id
            )
        )
        result.extend(clt_data)

    return bytes(result)


def mapping(mapping_id: str, texture: str) -> engine.Mapping:
    return engine.Mapping(
        mapping_id=mapping_id,
        container_id="mapped",
        target_texture=texture,
        donor_texture=texture,
        transform="copy",
        reason="test",
    )


def strategy(kind: str) -> engine.Strategy:
    return engine.Strategy(
        container_id="mapped",
        strategy=kind,
        replacement_sha256="",
        payload_sha256="",
        reason="test",
    )


class MappedCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.names = ("mapped_a.bmp", "mapped_b.bmp", "unmapped.bmp")
        self.target = synthetic_ccs(
            [
                (self.names[0], 0, (0x10, 0x20, 0x30)),
                (self.names[1], 0, (0x20, 0x30, 0x40)),
                (self.names[2], 0, (0x30, 0x40, 0x50)),
            ],
            palette_reference_base=0x100,
        )
        self.donor = synthetic_ccs(
            [
                (self.names[0], 0, (0xA0, 0xB0, 0xC0)),
                (self.names[1], 0, (0xB0, 0xC0, 0xD0)),
                (self.names[2], 0, (0xC0, 0xD0, 0xE0)),
            ],
            palette_reference_base=0x200,
        )
        self.mappings = [
            mapping("copy-a", self.names[0]),
            mapping("copy-b", self.names[1]),
        ]

    def test_multiple_copy_mappings_replace_only_paired_tex_and_clt_data(self) -> None:
        output = engine.expected_payload(
            strategy("mapped"),
            self.target,
            self.donor,
            self.mappings,
        )
        target_entries = engine.parse_ccs(self.target)
        donor_entries = engine.parse_ccs(self.donor)
        output_entries = engine.parse_ccs(output)

        allowed: set[int] = set()
        for name in self.names[:2]:
            target_entry = target_entries[name]
            donor_entry = donor_entries[name]
            output_entry = output_entries[name]
            for target_part, donor_part, output_part in zip(
                target_entry.textures,
                donor_entry.textures,
                output_entry.textures,
                strict=True,
            ):
                target_range = slice(
                    target_part.data_offset,
                    target_part.data_offset + target_part.data_size,
                )
                donor_range = slice(
                    donor_part.data_offset,
                    donor_part.data_offset + donor_part.data_size,
                )
                output_range = slice(
                    output_part.data_offset,
                    output_part.data_offset + output_part.data_size,
                )
                self.assertNotEqual(
                    self.target[target_range.start : target_range.start + 4],
                    self.donor[donor_range.start : donor_range.start + 4],
                )
                self.assertEqual(
                    output[output_range.start : output_range.start + 4],
                    self.target[target_range.start : target_range.start + 4],
                )
                self.assertEqual(
                    output[output_range.start + 4 : output_range.stop],
                    self.donor[donor_range.start + 4 : donor_range.stop],
                )
                allowed.update(range(target_range.start + 4, target_range.stop))
            for target_part, donor_part, output_part in zip(
                target_entry.palettes,
                donor_entry.palettes,
                output_entry.palettes,
                strict=True,
            ):
                target_range = slice(
                    target_part.data_offset,
                    target_part.data_offset + target_part.data_size,
                )
                donor_range = slice(
                    donor_part.data_offset,
                    donor_part.data_offset + donor_part.data_size,
                )
                output_range = slice(
                    output_part.data_offset,
                    output_part.data_offset + output_part.data_size,
                )
                self.assertEqual(output[output_range], self.donor[donor_range])
                allowed.update(range(target_range.start, target_range.stop))

        changed = {
            index
            for index, (before, after) in enumerate(zip(self.target, output))
            if before != after
        }
        self.assertTrue(changed)
        self.assertTrue(changed <= allowed)
        unmapped = target_entries[self.names[2]]
        unmapped_differs_from_donor = False
        for part in unmapped.textures + unmapped.palettes:
            section = slice(part.data_offset, part.data_offset + part.data_size)
            self.assertEqual(output[section], self.target[section])
            if output[section] != self.donor[section]:
                unmapped_differs_from_donor = True
        self.assertTrue(unmapped_differs_from_donor)

    def test_mapped_strategy_accepts_uncovered_donor_visual_differences(self) -> None:
        target_entries = engine.parse_ccs(self.target)
        donor_entries = engine.parse_ccs(self.donor)
        engine.validate_visual_coverage(
            strategy("mapped"),
            self.mappings,
            self.target,
            self.donor,
            target_entries,
            donor_entries,
        )
        with self.assertRaisesRegex(ValueError, "uncovered decoded visual changes"):
            engine.validate_visual_coverage(
                strategy("whole"),
                self.mappings,
                self.target,
                self.donor,
                target_entries,
                donor_entries,
            )

    def test_copy_mapping_rejects_component_layout_mismatch(self) -> None:
        donor = bytearray(self.donor)
        donor_entry = engine.parse_ccs(donor)[self.names[0]]
        donor[donor_entry.textures[0].data_offset + 0xC] = 2
        with self.assertRaisesRegex(ValueError, "component layouts differ"):
            engine.expected_payload(
                strategy("mapped"),
                self.target,
                bytes(donor),
                [self.mappings[0]],
            )

    def test_derivation_worker_count_is_bounded_and_overridable(self) -> None:
        with patch.object(engine.os, "cpu_count", return_value=16):
            self.assertEqual(engine.derivation_worker_count(None, 34), 4)
        with patch.object(engine.os, "cpu_count", return_value=2):
            self.assertEqual(engine.derivation_worker_count(None, 34), 2)
        self.assertEqual(engine.derivation_worker_count(8, 3), 3)
        self.assertEqual(engine.derivation_worker_count(1, 34), 1)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            engine.derivation_worker_count(0, 34)


if __name__ == "__main__":
    unittest.main()
