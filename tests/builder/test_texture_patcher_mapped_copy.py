from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from na228_builder.modules.texture_patcher import engine


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


def synthetic_indexed_ccs(
    name: str,
    width: int,
    height: int,
    *,
    palette_reference: int,
    opaque_outside_top_left_crop: bool = False,
) -> bytes:
    """Create one 4-bit indexed texture whose visual rows are bottom-to-top."""
    toc_data = bytearray(0x20 + 0x20 + 0x20 + 2 * 0x20)
    _write_name(toc_data, 0x20, name, 0x20)
    object_cursor = 0x20 + 0x20 + 0x20
    for suffix in ("tex", "clt"):
        _write_name(toc_data, object_cursor, f"{name}.{suffix}", 0x1E)
        struct.pack_into("<H", toc_data, object_cursor + 0x1E, 1)
        object_cursor += 0x20

    result = bytearray(
        struct.pack(
            "<IIII",
            engine.SECTION_TOC,
            len(toc_data) // 4,
            2,
            3,
        )
    )
    result.extend(toc_data)

    pixels = [0] * (width * height)
    pixels[(height - 1) * width] = 1
    if opaque_outside_top_left_crop:
        pixels[width - 1] = 1
    encoded = bytes(
        pixels[index] | (pixels[index + 1] << 4)
        for index in range(0, len(pixels), 2)
    )
    tex_data = bytearray(0x18)
    struct.pack_into("<I", tex_data, 0, palette_reference)
    tex_data[0xC] = width.bit_length() - 1
    tex_data[0xD] = height.bit_length() - 1
    struct.pack_into("<I", tex_data, 0x14, len(encoded) // 4)
    tex_data.extend(encoded)
    result.extend(
        struct.pack(
            "<III",
            engine.SECTION_TEXTURE,
            51 + len(tex_data) // 4,
            1,
        )
    )
    result.extend(tex_data)

    clt_data = bytearray(0x10 + 16 * 4)
    clt_data[0x14:0x18] = bytes((0x20, 0x40, 0x60, 0x80))
    result.extend(
        struct.pack(
            "<III",
            engine.SECTION_PALETTE,
            (12 + len(clt_data) - 8) // 4,
            2,
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

    def test_transparent_top_left_crop_preserves_all_visible_donor_pixels(self) -> None:
        name = "cropped.bmp"
        target = synthetic_indexed_ccs(
            name,
            64,
            64,
            palette_reference=0x100,
        )
        donor = synthetic_indexed_ccs(
            name,
            256,
            128,
            palette_reference=0x200,
        )
        crop = engine.Mapping(
            mapping_id="crop",
            container_id="mapped",
            target_texture=name,
            donor_texture=name,
            transform="indexed_crop_transparent_top_left_128x64",
            reason="test",
        )
        output = engine.expected_payload(
            strategy("mapped"),
            target,
            donor,
            [crop],
        )
        target_entry = engine.parse_ccs(target)[name]
        donor_entry = engine.parse_ccs(donor)[name]
        output_entry = engine.parse_ccs(output)[name]
        self.assertEqual(
            engine.texture_dimensions(output, output_entry.textures[0]),
            (128, 64),
        )
        self.assertEqual(
            output[
                output_entry.textures[0].data_offset :
                output_entry.textures[0].data_offset + 4
            ],
            target[
                target_entry.textures[0].data_offset :
                target_entry.textures[0].data_offset + 4
            ],
        )
        donor_width, donor_height, donor_rgba = engine.decoded_rgba(
            donor,
            donor_entry,
        )
        output_width, output_height, output_rgba = engine.decoded_rgba(
            output,
            output_entry,
        )
        expected = b"".join(
            donor_rgba[
                (row * donor_width) * 4 :
                (row * donor_width + output_width) * 4
            ]
            for row in range(donor_height - output_height, donor_height)
        )
        self.assertEqual(output_rgba, expected)

    def test_transparent_top_left_crop_rejects_visible_discarded_pixels(self) -> None:
        name = "cropped.bmp"
        target = synthetic_indexed_ccs(
            name,
            64,
            64,
            palette_reference=0x100,
        )
        donor = synthetic_indexed_ccs(
            name,
            256,
            128,
            palette_reference=0x200,
            opaque_outside_top_left_crop=True,
        )
        crop = engine.Mapping(
            mapping_id="crop",
            container_id="mapped",
            target_texture=name,
            donor_texture=name,
            transform="indexed_crop_transparent_top_left_128x64",
            reason="test",
        )
        with self.assertRaisesRegex(ValueError, "discard visible donor pixels"):
            engine.expected_payload(
                strategy("mapped"),
                target,
                donor,
                [crop],
            )

    def test_whole_mapping_declares_dimension_changing_donor_visual(self) -> None:
        name = "whole.bmp"
        target = synthetic_indexed_ccs(
            name,
            64,
            64,
            palette_reference=0x100,
        )
        donor = synthetic_indexed_ccs(
            name,
            256,
            128,
            palette_reference=0x200,
        )
        whole = engine.Mapping(
            mapping_id="whole",
            container_id="mapped",
            target_texture=name,
            donor_texture=name,
            transform="whole",
            reason="test",
        )
        self.assertEqual(
            engine.expected_payload(strategy("whole"), target, donor, [whole]),
            donor,
        )
        with self.assertRaisesRegex(
            ValueError,
            "copy/transparent-crop mappings",
        ):
            engine.expected_payload(strategy("mapped"), target, donor, [whole])

    def test_derivation_worker_count_is_bounded_and_overridable(self) -> None:
        with patch.object(engine.os, "cpu_count", return_value=16):
            self.assertEqual(engine.derivation_worker_count(None, 34), 16)
        with patch.object(engine.os, "cpu_count", return_value=2):
            self.assertEqual(engine.derivation_worker_count(None, 34), 2)
        self.assertEqual(engine.derivation_worker_count(8, 3), 3)
        self.assertEqual(engine.derivation_worker_count(1, 34), 1)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            engine.derivation_worker_count(0, 34)

    def test_texture_cache_round_trip_and_corruption_falls_back_to_miss(self) -> None:
        stream = engine.gzip.compress(b"cached payload", mtime=0)
        replacement = stream + b"\0" * 7
        cached = engine.CachedDerivation(
            replacement=replacement,
            payload_sha256=engine.sha256(b"cached payload"),
            compressed_stream_size=len(stream),
            padding_size=7,
        )
        key = "A" * 64
        with tempfile.TemporaryDirectory() as directory:
            cache_root = Path(directory)
            engine.write_cached_derivation(cache_root, key, cached)
            self.assertEqual(
                engine.read_cached_derivation(cache_root, key, len(replacement)),
                cached,
            )
            engine.cache_file(cache_root, key).write_bytes(b"corrupt")
            self.assertIsNone(
                engine.read_cached_derivation(cache_root, key, len(replacement))
            )

    def test_texture_cache_key_covers_bytes_and_derivation_inputs(self) -> None:
        base = engine.texture_cache_key(
            b"target",
            b"donor",
            strategy("mapped"),
            [self.mappings[0]],
        )
        changed_mapping = engine.Mapping(
            mapping_id=self.mappings[0].mapping_id,
            container_id=self.mappings[0].container_id,
            target_texture=self.mappings[0].target_texture,
            donor_texture=self.mappings[0].donor_texture,
            transform="split_left",
            reason=self.mappings[0].reason,
        )
        self.assertNotEqual(
            base,
            engine.texture_cache_key(
                b"changed target",
                b"donor",
                strategy("mapped"),
                [self.mappings[0]],
            ),
        )
        self.assertNotEqual(
            base,
            engine.texture_cache_key(
                b"target",
                b"changed donor",
                strategy("mapped"),
                [self.mappings[0]],
            ),
        )
        self.assertNotEqual(
            base,
            engine.texture_cache_key(
                b"target",
                b"donor",
                strategy("mapped"),
                [changed_mapping],
            ),
        )

    def test_texture_cache_io_failure_does_not_fail_derivation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_root = Path(directory) / "not-a-directory"
            cache_root.write_bytes(b"occupied")
            cached = engine.CachedDerivation(
                replacement=b"replacement",
                payload_sha256="A" * 64,
                compressed_stream_size=11,
                padding_size=0,
            )
            engine.write_cached_derivation(cache_root, "B" * 64, cached)
            self.assertIsNone(
                engine.read_cached_derivation(cache_root, "B" * 64, 11)
            )

    def test_texture_cache_hit_skips_container_derivation(self) -> None:
        spec = engine.ContainerSpec("mapped", "file.ccs", "A" * 64, "B" * 64)
        package = engine.Package(
            Path("."),
            {"mapped": spec},
            (self.mappings[0],),
            {"mapped": strategy("mapped")},
        )
        record = SimpleNamespace(is_dir=False, byte_offset=0x200)
        target = SimpleNamespace(
            by_path={"FILE.CCS": record},
            read_file=lambda _record: b"targetbytes",
        )
        donor = SimpleNamespace(
            by_path={"FILE.CCS": record},
            read_file=lambda _record: b"donor bytes",
        )
        cached = engine.CachedDerivation(
            replacement=b"replacement",
            payload_sha256="C" * 64,
            compressed_stream_size=11,
            padding_size=0,
        )
        with (
            patch.object(engine, "read_cached_derivation", return_value=cached),
            patch.object(
                engine.gzip,
                "decompress",
                side_effect=AssertionError("cache hit derived again"),
            ),
        ):
            result = engine.derive_container(
                "mapped",
                package=package,
                target_iso=target,
                donor_iso=donor,
                target_header_size=0x40,
                mappings_by_container={"mapped": [self.mappings[0]]},
                cache_root=Path("cache"),
            )
        self.assertEqual(result.replacement, cached.replacement)
        self.assertEqual(result.outer_cvm_offset, 0x240)
        self.assertEqual(result.mapping_ids, (self.mappings[0].mapping_id,))
        self.assertTrue(result.cache_reused)


if __name__ == "__main__":
    unittest.main()
