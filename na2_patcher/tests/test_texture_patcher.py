from __future__ import annotations

import csv
import gzip
import re
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from na2_patcher.build_profile import write_texture_patch_log
from na2_patcher.modules.binary_patcher import engine as binary_patcher
from na2_patcher.modules.texture_patcher import engine
from na2_patcher.project_paths import load_project_paths


class UiTextureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository = Path(__file__).resolve().parents[2]
        paths = load_project_paths(repository, allow_missing=True)
        na2_root = paths.path("source_na2")
        nun5_root = paths.path("source_nun5")
        cls.na2_root = na2_root
        cls.nun5_root = nun5_root
        data_root = (
            Path(__file__).resolve().parents[1]
            / "features"
            / "localization"
            / "texture_patcher"
        )
        required = (
            na2_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.iso",
            na2_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.hdr",
            nun5_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.iso",
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest(
                "UI texture verification requires extracted NA2 and NUN5 sources"
            )
        cls.plan = engine.build_texture_patch_plan(
            na2_root=na2_root,
            nun5_root=nun5_root,
            data_root=data_root,
        )

    def test_module_has_no_stored_replacement_blobs(self) -> None:
        self.assertFalse((self.plan.package.directory / "blobs").exists())

    def result(self, container_id: str) -> engine.ContainerResult:
        return next(
            result
            for result in self.plan.containers
            if result.spec.container_id == container_id
        )

    def test_complete_package_is_source_derived_pinned_and_fixed_size(self) -> None:
        self.assertEqual(len(self.plan.containers), 96)
        self.assertEqual(self.plan.mapping_count, 210)
        for result in self.plan.containers:
            self.assertEqual(
                len(result.replacement), len(result.original), result.spec.path
            )
            self.assertEqual(
                engine.sha256(result.replacement),
                result.strategy.replacement_sha256,
            )
            self.assertEqual(result.payload_sha256, result.strategy.payload_sha256)

    def test_whole_container_payloads_equal_official_nun5_donors(self) -> None:
        whole = [
            result
            for result in self.plan.containers
            if result.strategy.strategy == "whole"
        ]
        self.assertEqual(len(whole), 92)
        for result in whole:
            self.assertEqual(
                gzip.decompress(result.replacement),
                gzip.decompress(result.donor),
                result.spec.path,
            )

    def test_mode2kdv_keeps_na2_palette_and_lower_visual_rows(self) -> None:
        result = self.result("mode2kdv")
        mapping = next(
            item
            for item in self.plan.package.mappings
            if item.container_id == "mode2kdv"
        )
        target_payload = gzip.decompress(result.original)
        output_payload = gzip.decompress(result.replacement)
        target_entry = engine.parse_ccs(target_payload)[
            mapping.target_texture.casefold()
        ]
        output_entry = engine.parse_ccs(output_payload)[
            mapping.target_texture.casefold()
        ]
        target_texture = target_entry.textures[0]
        output_texture = output_entry.textures[0]
        target_palette = target_entry.palettes[0]
        output_palette = output_entry.palettes[0]

        self.assertEqual(
            target_payload[
                target_palette.data_offset :
                target_palette.data_offset + target_palette.data_size
            ],
            output_payload[
                output_palette.data_offset :
                output_palette.data_offset + output_palette.data_size
            ],
        )
        width, height = engine.texture_dimensions(target_payload, target_texture)
        self.assertEqual((width, height), (256, 256))
        first_imported_byte = 0x18 + (height - 64) * width
        target_tex = target_payload[
            target_texture.data_offset :
            target_texture.data_offset + target_texture.data_size
        ]
        output_tex = output_payload[
            output_texture.data_offset :
            output_texture.data_offset + output_texture.data_size
        ]
        self.assertEqual(
            target_tex[:first_imported_byte], output_tex[:first_imported_byte]
        )
        self.assertNotEqual(
            target_tex[first_imported_byte:], output_tex[first_imported_byte:]
        )

        changed = {
            index
            for index, (before, after) in enumerate(zip(target_payload, output_payload))
            if before != after
        }
        allowed_start = target_texture.data_offset + first_imported_byte
        allowed_end = target_texture.data_offset + target_texture.data_size
        self.assertTrue(changed)
        self.assertTrue(all(allowed_start <= index < allowed_end for index in changed))

    def test_all_ordinary_awakening_labels_are_exact_nun5_visuals(self) -> None:
        target_iso, donor_iso, _ = engine.source_members(
            self.na2_root,
            self.nun5_root,
        )
        expected_paths = set()
        expected_texture_count = 0
        for path, record in target_iso.by_path.items():
            if record.is_dir or re.fullmatch(r"3EYE/3[A-Z0-9]{3}3PCT\.CCS", path) is None:
                continue
            payload = gzip.decompress(target_iso.read_file(record))
            mode_entries = [
                name
                for name in engine.parse_ccs(payload)
                if re.search(r"mode1name[1-3]\.bmp$", name, re.IGNORECASE)
            ]
            if mode_entries:
                expected_paths.add(path)
                expected_texture_count += len(mode_entries)

        results = [
            result
            for result in self.plan.containers
            if result.spec.container_id.startswith("mode1_")
        ]
        mappings = [
            mapping
            for mapping in self.plan.package.mappings
            if mapping.mapping_id.startswith("UI-MODE1-")
        ]
        self.assertEqual(len(results), 61)
        self.assertEqual(len(mappings), 72)
        self.assertEqual(expected_texture_count, 72)
        self.assertEqual(
            {result.spec.path for result in results},
            expected_paths,
        )
        self.assertEqual(
            {mapping.container_id for mapping in mappings},
            {result.spec.container_id for result in results},
        )

        mappings_by_container = {}
        for mapping in mappings:
            mappings_by_container.setdefault(mapping.container_id, []).append(mapping)

        for result in results:
            target_payload = gzip.decompress(result.original)
            donor_payload = gzip.decompress(result.donor)
            output_payload = gzip.decompress(result.replacement)
            target_entries = engine.parse_ccs(target_payload)
            donor_entries = engine.parse_ccs(donor_payload)
            output_entries = engine.parse_ccs(output_payload)
            if result.strategy.strategy == "whole":
                self.assertEqual(output_entries.keys(), donor_entries.keys())
            else:
                self.assertEqual(output_entries.keys(), target_entries.keys())

            for mapping in mappings_by_container[result.spec.container_id]:
                target_entry = target_entries[mapping.target_texture.casefold()]
                donor_entry = donor_entries[mapping.donor_texture.casefold()]
                output_key = (
                    mapping.donor_texture.casefold()
                    if result.strategy.strategy == "whole"
                    else mapping.target_texture.casefold()
                )
                output_entry = output_entries[output_key]
                self.assertEqual(
                    engine.decoded_rgba(output_payload, output_entry),
                    engine.decoded_rgba(donor_payload, donor_entry),
                    mapping.mapping_id,
                )

    def test_all_victory_names_are_derived_from_official_nun5_artwork(self) -> None:
        results = [
            result
            for result in self.plan.containers
            if result.spec.container_id.startswith("mode1_")
        ]
        mappings = [
            mapping
            for mapping in self.plan.package.mappings
            if mapping.mapping_id.startswith("UI-VICTORY-")
            and mapping.container_id.startswith("mode1_")
        ]
        self.assertEqual(len(results), 61)
        self.assertEqual(len(mappings), 61)
        self.assertEqual(
            Counter(result.strategy.strategy for result in results),
            {"whole": 59, "mapped": 2},
        )
        mappings_by_container = {mapping.container_id: mapping for mapping in mappings}
        self.assertEqual(
            mappings_by_container.keys(),
            {result.spec.container_id for result in results},
        )

        def by_object(
            entries: dict[str, engine.TextureEntry],
            object_name: str,
        ) -> engine.TextureEntry:
            matches = [
                entry
                for entry in entries.values()
                if any(part.object_name == object_name for part in entry.textures)
            ]
            self.assertEqual(len(matches), 1)
            return matches[0]

        def visible_bbox(
            payload: bytes,
            entry: engine.TextureEntry,
        ) -> tuple[int, int, int, int]:
            width, height, rgba = engine.decoded_rgba(payload, entry)
            points = [
                (x, height - 1 - raw_y)
                for raw_y in range(height)
                for x in range(width)
                if rgba[(raw_y * width + x) * 4 + 3]
            ]
            return (
                min(x for x, _ in points),
                min(y for _, y in points),
                max(x for x, _ in points) + 1,
                max(y for _, y in points) + 1,
            )

        for result in results:
            mapping = mappings_by_container[result.spec.container_id]
            target_payload = gzip.decompress(result.original)
            donor_payload = gzip.decompress(result.donor)
            output_payload = gzip.decompress(result.replacement)
            target_name = by_object(engine.parse_ccs(target_payload), "TEX_name")
            donor_name = by_object(engine.parse_ccs(donor_payload), "TEX_name")
            output_name = by_object(engine.parse_ccs(output_payload), "TEX_name")
            self.assertEqual(mapping.target_texture, target_name.name)
            self.assertEqual(mapping.donor_texture, donor_name.name)

            if result.strategy.strategy == "whole":
                self.assertEqual(mapping.transform, "whole")
                self.assertEqual(output_payload, donor_payload)
                self.assertEqual(
                    engine.decoded_rgba(output_payload, output_name),
                    engine.decoded_rgba(donor_payload, donor_name),
                )
                continue

            output_texture = output_name.textures[0]
            tex = output_payload[
                output_texture.data_offset :
                output_texture.data_offset + output_texture.data_size
            ]
            used_indexes = {
                index
                for value in tex[0x18:]
                for index in (value & 0x0F, value >> 4)
            }
            if result.spec.container_id == "mode1_hak":
                self.assertEqual(
                    mapping.transform,
                    (
                        "indexed_crop_transparent_top_left_128x64_nearest_palette_"
                        "0-1-2-3-4-7-14"
                    ),
                )
                self.assertEqual(
                    engine.texture_dimensions(output_payload, output_texture),
                    (128, 64),
                )
                self.assertEqual(used_indexes, {0, 1, 2, 3, 4, 7, 14})
                self.assertEqual(visible_bbox(donor_payload, donor_name), (4, 4, 116, 51))
                self.assertEqual(visible_bbox(output_payload, output_name), (5, 5, 116, 50))
                self.assertEqual(result.padding_size, 0)
            elif result.spec.container_id == "mode1_skn":
                self.assertEqual(
                    mapping.transform,
                    (
                        "indexed_crop_transparent_top_left_256x128_nearest_palette_"
                        "0-1-2-3-4-5-6-7-9-10-11-12-13-14"
                    ),
                )
                self.assertEqual(
                    engine.texture_dimensions(output_payload, output_texture),
                    (256, 128),
                )
                self.assertEqual(
                    used_indexes,
                    {0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14},
                )
                self.assertEqual(
                    visible_bbox(output_payload, output_name),
                    visible_bbox(donor_payload, donor_name),
                )
                self.assertEqual(result.padding_size, 9)
            else:
                self.fail(f"Unexpected mapped Victory exception {result.spec.container_id}")

    def test_victory_emblem_import_preserves_other_enddemo_textures(self) -> None:
        result = self.result("enddemo")
        self.assertEqual(result.strategy.strategy, "mapped")
        mapping = next(
            item
            for item in self.plan.package.mappings
            if item.mapping_id == "UI-VICTORY-001"
        )
        target_payload = gzip.decompress(result.original)
        donor_payload = gzip.decompress(result.donor)
        output_payload = gzip.decompress(result.replacement)
        target_entries = engine.parse_ccs(target_payload)
        donor_entries = engine.parse_ccs(donor_payload)
        output_entries = engine.parse_ccs(output_payload)
        selected = mapping.target_texture.casefold()
        self.assertEqual(
            engine.decoded_rgba(output_payload, output_entries[selected]),
            engine.decoded_rgba(
                donor_payload,
                donor_entries[mapping.donor_texture.casefold()],
            ),
        )
        for name in (
            r"x\enddemo\tex\enddemo02.bmp",
            r"x\enddemo\tex\enddemo03.bmp",
        ):
            key = name.casefold()
            for target_part, output_part in zip(
                target_entries[key].textures + target_entries[key].palettes,
                output_entries[key].textures + output_entries[key].palettes,
                strict=True,
            ):
                self.assertEqual(
                    output_payload[
                        output_part.data_offset :
                        output_part.data_offset + output_part.data_size
                    ],
                    target_payload[
                        target_part.data_offset :
                        target_part.data_offset + target_part.data_size
                    ],
                )

    def test_home_uses_the_complete_nun5_collection_container(self) -> None:
        result = self.result("home")
        self.assertEqual(result.strategy.strategy, "whole")
        self.assertEqual(
            result.payload_sha256,
            "9ADAC4D30DD9F2F9DE89732CD3B735F3531B48F90CD43F33711F9BCEF6434E20",
        )
        self.assertEqual(
            gzip.decompress(result.replacement),
            gzip.decompress(result.donor),
        )
        self.assertNotEqual(
            gzip.decompress(result.replacement),
            gzip.decompress(result.original),
        )

    def test_mapsel1_uses_the_complete_nun5_stage_container(self) -> None:
        result = self.result("mapsel1")
        self.assertEqual(result.strategy.strategy, "whole")
        self.assertEqual(
            result.payload_sha256,
            "D84507B403F6E607CFCD4EB7860D89EC7F56B3C593F591A537B5865582863A0E",
        )
        self.assertEqual(
            gzip.decompress(result.replacement),
            gzip.decompress(result.donor),
        )
        self.assertNotEqual(
            gzip.decompress(result.replacement),
            gzip.decompress(result.original),
        )

    def test_stage_layout_ports_both_index_consumers_and_nun5_prompt_x(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        vertical = next(
            item for item in package.edits if item.edit_id == "UI-BTL-002-02"
        )
        horizontal = next(
            item for item in package.edits if item.edit_id == "UI-BTL-002-03"
        )
        thumbnail = next(
            item for item in package.edits if item.edit_id == "UI-BTL-002-04"
        )
        random_prompt = next(
            item for item in package.edits if item.edit_id == "UI-BTL-002-05"
        )
        random_companion = next(
            item for item in package.edits if item.edit_id == "UI-BTL-002-06"
        )

        self.assertEqual(vertical.destination_offset, 0x61570)
        self.assertEqual(vertical.expected_hex, "00708244")
        self.assertEqual(vertical.replacement_hex, "00788244")
        self.assertEqual(horizontal.destination_offset, 0x6157C)
        self.assertEqual(horizontal.expected_hex, "C6730046")
        self.assertEqual(horizontal.replacement_hex, "04006EC4")
        self.assertEqual(thumbnail.destination_offset, 0x603B8)
        self.assertEqual(thumbnail.expected_hex, "0000448C")
        self.assertEqual(thumbnail.replacement_hex, "02210300")
        self.assertEqual(random_prompt.destination_offset, 0x61F40)
        self.assertEqual(random_prompt.source_target_id, "nun5_btl")
        self.assertEqual(random_prompt.source_offset, 0x64C50)
        self.assertEqual(random_prompt.source_expected_hex, "8243023C")
        self.assertEqual(random_companion.destination_offset, 0x61F64)
        self.assertEqual(random_companion.source_target_id, "nun5_btl")
        self.assertEqual(random_companion.source_offset, 0x64C78)
        self.assertEqual(random_companion.source_expected_hex, "8243023C")

    def test_ougi_import_replaces_two_part_layout_with_nun5_one_part_layout(self) -> None:
        result = self.result("ougi")
        target_payload = gzip.decompress(result.original)
        output_payload = gzip.decompress(result.replacement)
        donor_payload = gzip.decompress(result.donor)
        self.assertEqual(len(engine.parse_ccs(target_payload)), 24)
        self.assertEqual(len(engine.parse_ccs(output_payload)), 20)
        self.assertEqual(output_payload, donor_payload)

    def test_gauge_import_replaces_the_global_regional_button_legend(self) -> None:
        result = self.result("gauge")
        target_payload = gzip.decompress(result.original)
        output_payload = gzip.decompress(result.replacement)
        donor_payload = gzip.decompress(result.donor)
        texture_name = r"x\window\tex\xpanel.bmp"
        target_entry = engine.parse_ccs(target_payload)[texture_name]
        output_entry = engine.parse_ccs(output_payload)[texture_name]
        donor_entry = engine.parse_ccs(donor_payload)[texture_name]

        target_rgba = engine.decoded_rgba(target_payload, target_entry)
        output_rgba = engine.decoded_rgba(output_payload, output_entry)
        donor_rgba = engine.decoded_rgba(donor_payload, donor_entry)
        self.assertIsNotNone(target_rgba)
        self.assertIsNotNone(output_rgba)
        self.assertIsNotNone(donor_rgba)
        self.assertNotEqual(target_rgba, output_rgba)
        self.assertEqual(output_rgba, donor_rgba)

    def test_character_name_patch_uses_localized_table_not_portrait_grid(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edit = next(item for item in package.edits if item.edit_id == "UI-ELF-001-01")
        self.assertEqual(edit.source_target_id, "nun5_elf")
        self.assertEqual(edit.source_offset, 0x4DDDD0)
        self.assertEqual(edit.length, 96 * 8)

        _na2_root, nun5_root = engine.default_roots()
        nun5_elf = (nun5_root / "SLES_556.05").read_bytes()
        source = nun5_elf[edit.source_offset : edit.source_offset + edit.length]
        self.assertEqual(binary_patcher.data_sha256(source), edit.source_expected_sha256)
        records = list(struct.iter_unpack("<hhhh", source))
        nonblank = [record for record in records if record != (0, 0, 0, 0)]

        self.assertEqual(len(records), 96)
        self.assertGreater(len({width for _x, _y, width, _height in nonblank}), 10)
        self.assertEqual({height for _x, _y, _width, height in nonblank}, {30})
        self.assertTrue(
            all(
                0 <= x < 512
                and 0 <= y < 256
                and 0 < width <= 512 - x
                and 0 < height <= 256 - y
                for x, y, width, height in nonblank
            )
        )

        rejected = nun5_elf[0x4DC120 : 0x4DC120 + edit.length]
        rejected_records = list(struct.iter_unpack("<hhhh", rejected))
        self.assertEqual(
            {(width, height) for _x, _y, width, height in rejected_records},
            {(38, 46)},
        )

    def test_battle_name_patch_uses_localized_table_and_width_fitter(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        table = next(item for item in package.edits if item.edit_id == "UI-ELF-004-01")
        helper = next(item for item in package.edits if item.edit_id == "UI-BTL-003-01")
        hook = next(item for item in package.edits if item.edit_id == "UI-BTL-003-02")

        self.assertEqual(table.source_target_id, "nun5_elf")
        self.assertEqual(table.source_offset, 0x4DEA30)
        self.assertEqual(table.destination_offset, 0x4B14A0)
        self.assertEqual(table.length, 95 * 8)

        _na2_root, nun5_root = engine.default_roots()
        nun5_elf = (nun5_root / "SLES_556.05").read_bytes()
        source = nun5_elf[table.source_offset : table.source_offset + table.length]
        self.assertEqual(binary_patcher.data_sha256(source), table.source_expected_sha256)
        records = list(struct.iter_unpack("<hhhh", source))
        nonblank = [record for record in records if record != (0, 0, 0, 0)]
        self.assertEqual(len(records), 95)
        self.assertEqual({height for _x, _y, _width, height in nonblank}, {24})
        self.assertEqual(max(width for _x, _y, width, _height in nonblank), 208)

        self.assertEqual(helper.destination_target_id, "na2_btl")
        self.assertEqual(helper.destination_offset, 0x40)
        self.assertEqual(helper.length, 44)
        self.assertEqual(
            helper.replacement_hex,
            "0010844400000000A0108046341000460300004500000000000084442000804642"
            "0101460800E003640060C4",
        )
        self.assertEqual(hook.destination_offset, 0x67F44)
        self.assertEqual(hook.expected_hex, "42010146640060C4")
        self.assertEqual(hook.replacement_hex, "D0CF1A0CA0000424")
        self.assertEqual(min(208.0, 160.0), 160.0)
        self.assertEqual(min(112.0, 160.0), 112.0)

    def test_options_index_route_matches_nun5_valid_domain(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edit = next(item for item in package.edits if item.edit_id == "UI-ELF-003-01")

        self.assertEqual(edit.destination_offset, 0x28C40C)
        self.assertEqual(edit.length, 8)
        self.assertEqual(edit.expected_hex, "0500032405008310")
        self.assertEqual(edit.replacement_hex, "0400832C05006010")

        def uses_alternate_object(index: int) -> bool:
            below_four = int(index < 4)
            return below_four == 0 or index == 0

        self.assertEqual(
            {index for index in range(6) if uses_alternate_object(index)},
            {0, 4, 5},
        )

    def test_practice_settings_patch_uses_nun5_rectangle_and_anchor(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        anchor = next(item for item in package.edits if item.edit_id == "UI-BTL-004-01")
        rectangle = next(
            item for item in package.edits if item.edit_id == "UI-BTL-004-02"
        )

        self.assertEqual(anchor.destination_offset, 0xCFA0)
        self.assertEqual(anchor.expected_hex, "7042023C")
        self.assertEqual(anchor.operation, "copy")
        self.assertEqual(anchor.source_target_id, "nun5_btl")
        self.assertEqual(anchor.source_offset, 0xD500)
        self.assertEqual(anchor.source_expected_hex, "C842023C")
        self.assertEqual(rectangle.destination_offset, 0x20C9D8)
        self.assertEqual(rectangle.expected_hex, "0100190170001600")
        self.assertEqual(rectangle.source_target_id, "nun5_elf")
        self.assertEqual(rectangle.source_offset, 0x4DE0E0)
        self.assertEqual(rectangle.source_expected_hex, "00001801B0001800")
        self.assertEqual(
            struct.unpack("<hhhh", bytes.fromhex(rectangle.source_expected_hex)),
            (0, 280, 176, 24),
        )

    def test_mode_select_patch_uses_nun5_geometry_and_effective_prompt_anchors(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        patch = package.patches["UI-ELF-005"]
        edits = [item for item in package.edits if item.patch_id == "UI-ELF-005"]
        rectangle = next(
            item for item in package.edits if item.edit_id == "UI-ELF-005-01"
        )
        anchor = next(
            item for item in package.edits if item.edit_id == "UI-ELF-005-02"
        )

        self.assertEqual(len(edits), 4)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(rectangle.destination_offset, 0x504710)
        self.assertEqual(rectangle.expected_hex, "01008D01CE001600")
        self.assertEqual(rectangle.source_target_id, "nun5_elf")
        self.assertEqual(rectangle.source_offset, 0x4DE318)
        self.assertEqual(rectangle.source_expected_hex, "01008901FE001A00")
        self.assertEqual(
            struct.unpack("<hhhh", bytes.fromhex(rectangle.source_expected_hex)),
            (1, 393, 254, 26),
        )
        self.assertEqual(anchor.destination_offset, 0x285F28)
        self.assertEqual(anchor.expected_hex, "0243023C")
        self.assertEqual(anchor.replacement_hex, "1643023C")
        self.assertEqual(
            [
                (
                    item.edit_id,
                    item.destination_offset,
                    item.expected_hex,
                    item.replacement_hex,
                )
                for item in edits[2:]
            ],
            [
                ("UI-ELF-005-03", 0x285EE0, "C843023C", "C243023C"),
                ("UI-ELF-005-04", 0x285F04, "EB43023C", "E743023C"),
            ],
        )

    def test_shop_patch_uses_nun5_rectangles_and_label_anchors(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ETC-001"]
        patch = package.patches["UI-ETC-001"]

        self.assertEqual(len(edits), 5)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")
        rectangle = edits[0]
        self.assertEqual(rectangle.edit_id, "UI-ETC-001-01")
        self.assertEqual(rectangle.destination_offset, 0x30308)
        self.assertEqual(rectangle.source_target_id, "nun5_etc")
        self.assertEqual(rectangle.source_offset, 0x292F8)
        self.assertEqual(
            [
                (
                    item.edit_id,
                    item.destination_offset,
                    item.expected_hex,
                    item.source_target_id,
                    item.source_offset,
                    item.source_expected_hex,
                )
                for item in edits[1:]
            ],
            [
                (
                    "UI-ETC-001-02",
                    0x249A4,
                    "7A43023C",
                    "nun5_etc",
                    0x25E88,
                    "7E43023C",
                ),
                (
                    "UI-ETC-001-03",
                    0x249CC,
                    "4042023C",
                    "nun5_etc",
                    0x25EB0,
                    "4842023C",
                ),
                (
                    "UI-ETC-001-04",
                    0x24BB0,
                    "C842023C",
                    "nun5_etc",
                    0x26094,
                    "D242023C",
                ),
                (
                    "UI-ETC-001-05",
                    0x30340,
                    "81008900160016008100A1007A001600",
                    "nun5_etc",
                    0x29330,
                    "81008900160016008100A1007E001600",
                ),
            ],
        )

    def test_jutsu_patch_retains_the_nineteen_runtime_proven_edits(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-005"]
        patch = package.patches["UI-BTL-005"]

        self.assertEqual(len(edits), 19)
        self.assertEqual(
            {item.edit_id for item in edits},
            {f"UI-BTL-005-{index:02d}" for index in range(1, 20)},
        )
        self.assertNotIn(0xA0, {item.destination_offset for item in edits})
        self.assertNotIn(0x9E44, {item.destination_offset for item in edits})
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(edits[0].destination_offset, 0x30)
        self.assertEqual(edits[0].length, 16)
        self.assertEqual(
            edits[0].replacement_hex,
            "D041023C000082440800E00300031546",
        )
        self.assertEqual(edits[1].destination_offset, 0x9188)
        self.assertEqual(edits[1].replacement_hex, "CCCF1A0C")

        customize_anchor = next(
            item for item in edits if item.edit_id == "UI-BTL-005-05"
        )
        self.assertEqual(customize_anchor.destination_offset, 0xCF70)
        self.assertEqual(customize_anchor.operation, "copy")
        self.assertEqual(customize_anchor.length, 2)
        self.assertEqual(customize_anchor.expected_hex, "6643")
        self.assertEqual(customize_anchor.source_target_id, "nun5_btl")
        self.assertEqual(customize_anchor.source_offset, 0xD6A8)
        self.assertEqual(customize_anchor.source_expected_hex, "8243")

        prompt_records = next(
            item for item in edits if item.edit_id == "UI-BTL-005-15"
        )
        self.assertEqual(prompt_records.destination_target_id, "na2_elf")
        self.assertEqual(prompt_records.destination_offset, 0x4D4790)
        self.assertEqual(prompt_records.source_target_id, "nun5_elf")
        self.assertEqual(prompt_records.source_offset, 0x4DE9F0)
        self.assertEqual(
            struct.unpack("<hhhhhhhh", bytes.fromhex(prompt_records.source_expected_hex)),
            (1, 1, 56, 22, 1, 25, 64, 22),
        )

        one_draw = [
            item for item in edits if item.edit_id in {"UI-BTL-005-16", "UI-BTL-005-17"}
        ]
        self.assertEqual(
            [(item.destination_offset, item.replacement_hex) for item in one_draw],
            [(0xD014, "2D300000"), (0xD038, "2D300000")],
        )
        anchors = [
            item for item in edits if item.edit_id in {"UI-BTL-005-18", "UI-BTL-005-19"}
        ]
        self.assertEqual(
            [(item.destination_offset, item.replacement_hex) for item in anchors],
            [(0xCFFC, "C243023C"), (0xD020, "E743023C")],
        )

    def test_open_jutsu_selector_matches_the_nun5_arrow_state(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-007"]
        patch = package.patches["UI-BTL-007"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [f"UI-BTL-007-{index:02d}" for index in range(1, 11)],
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

        helper = edits[0]
        self.assertEqual(helper.destination_offset, 0x9ABC)
        self.assertEqual(helper.length, 104)
        self.assertEqual(len(bytes.fromhex(helper.expected_hex)), 104)
        self.assertEqual(len(bytes.fromhex(helper.replacement_hex)), 104)
        self.assertTrue(helper.replacement_hex.startswith("1E00001000000000"))
        self.assertNotIn(0x6C, {item.destination_offset for item in edits})

        angle_loads = [edits[index] for index in (1, 2, 5, 6)]
        self.assertEqual(
            [
                (
                    item.destination_offset,
                    item.source_target_id,
                    item.source_offset,
                    item.source_expected_hex,
                )
                for item in angle_loads
            ],
            [
                (0x9B78, "nun5_btl", 0xA06C, "C93F023C"),
                (0x9B84, "nun5_btl", 0xA070, "DB0F4334"),
                (0x9BD4, "nun5_btl", 0xA0F4, "C9BF023C"),
                (0x9BE0, "nun5_btl", 0xA0F8, "DB0F4334"),
            ],
        )
        self.assertEqual(
            [(edits[index].destination_offset, edits[index].replacement_hex) for index in (3, 7)],
            [(0x9BA0, "71F61A0C"), (0x9BFC, "71F61A0C")],
        )
        self.assertEqual(
            [(edits[index].destination_offset, edits[index].replacement_hex) for index in (4, 8)],
            [(0x9BA4, "4C0083AC"), (0x9C00, "4C0083AC")],
        )

        rectangle = edits[9]
        self.assertEqual(rectangle.destination_offset, 0x20C9E0)
        self.assertEqual(rectangle.source_target_id, "nun5_elf")
        self.assertEqual(rectangle.source_offset, 0x4DE0F0)
        self.assertEqual(
            struct.unpack("<hhhh", bytes.fromhex(rectangle.source_expected_hex)),
            (145, 385, 22, 38),
        )

    def test_command_views_share_one_exact_nun5_scroll_arrow_record(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-008"]
        patch = package.patches["UI-BTL-008"]

        self.assertEqual(len(edits), 1)
        rectangle = edits[0]
        self.assertEqual(rectangle.destination_offset, 0x21D648)
        self.assertEqual(rectangle.source_target_id, "nun5_btl")
        self.assertEqual(rectangle.source_offset, 0x2214D8)
        self.assertEqual(
            struct.unpack("<hhhh", bytes.fromhex(rectangle.source_expected_hex)),
            (1, 225, 20, 22),
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

    def test_mash_prompt_uses_complete_nun5_regional_rectangle_table(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-013"]
        patch = package.patches["UI-BTL-013"]

        self.assertEqual(len(edits), 1)
        table = edits[0]
        self.assertEqual(table.operation, "copy")
        self.assertEqual(table.destination_target_id, "na2_btl")
        self.assertEqual(table.destination_offset, 0x1DB730)
        self.assertEqual(table.length, 7 * 8)
        self.assertEqual(table.source_target_id, "nun5_elf")
        self.assertEqual(table.source_offset, 0x4DE630)
        self.assertEqual(
            list(struct.iter_unpack("<HHHH", bytes.fromhex(table.expected_hex))),
            [
                (0, 24, 48, 24),
                (48, 0, 48, 24),
                (0, 0, 48, 24),
                (48, 24, 64, 24),
                (0, 72, 94, 24),
                (0, 48, 112, 24),
                (0, 96, 48, 24),
            ],
        )
        self.assertEqual(
            list(
                struct.iter_unpack(
                    "<HHHH", bytes.fromhex(table.source_expected_hex)
                )
            ),
            [
                (0, 84, 64, 20),
                (64, 64, 64, 20),
                (0, 64, 64, 20),
                (0, 104, 64, 20),
                (0, 32, 128, 32),
                (0, 0, 128, 32),
                (64, 84, 64, 20),
            ],
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

    def test_victory_name_layouts_are_derived_from_nun5_tables(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-014"]
        patch = package.patches["UI-BTL-014"]
        na2_btl = (self.na2_root / "PRG" / "BTL.BIN").read_bytes()
        nun5_elf = (self.nun5_root / "SLES_556.05").read_bytes()
        nun5_btl = (self.nun5_root / "PRG" / "BTL.BIN").read_bytes()
        templates = (
            nun5_btl[0x21B9C0 : 0x21B9C0 + 24],
            nun5_btl[0x21B9E0 : 0x21B9E0 + 24],
        )
        pointers = struct.unpack_from("<188I", na2_btl, 0x1F1D40)
        widths_by_pointer: dict[int, set[int]] = {}
        frames_by_pointer: dict[int, set[int]] = {}

        for character_id in range(94):
            donor_widths = struct.unpack_from(
                "<HH",
                nun5_elf,
                0x4DE6D0 + character_id * 8,
            )
            for frame, donor_width in enumerate(donor_widths):
                pointer = pointers[character_id * 2 + frame]
                if pointer != 0:
                    widths_by_pointer.setdefault(pointer, set()).add(donor_width)
                    if donor_width != 0:
                        frames_by_pointer.setdefault(pointer, set()).add(frame)

        expected: dict[int, tuple[bytes, bytes]] = {}
        for pointer, widths in widths_by_pointer.items():
            nonzero_widths = widths - {0}
            self.assertLessEqual(len(nonzero_widths), 1)
            if not nonzero_widths:
                continue
            donor_width = next(iter(nonzero_widths))
            self.assertEqual(len(frames_by_pointer[pointer]), 1)
            frame = next(iter(frames_by_pointer[pointer]))
            destination_offset = pointer - 0x006B3F00
            original = na2_btl[destination_offset : destination_offset + 24]
            replacement_record = bytearray(templates[frame])
            struct.pack_into("<H", replacement_record, 4, donor_width - 2)
            replacement = bytes(replacement_record)
            if original != replacement:
                expected[destination_offset] = (original, replacement)

        self.assertEqual(len(edits), 78)
        self.assertEqual(
            {
                edit.destination_offset: (
                    bytes.fromhex(edit.expected_hex),
                    bytes.fromhex(edit.replacement_hex),
                )
                for edit in edits
            },
            expected,
        )
        self.assertEqual(
            (
                edits[0].destination_offset,
                edits[0].expected_hex,
                edits[0].replacement_hex,
            ),
            (
                0x2161B0,
                "01000100EC003E00000000000000F8C10000000000000000",
                "010001009A003E00000000000000F8C10000000000000000",
            ),
        )
        self.assertEqual(patch.status, "approved_for_test")
        self.assertEqual(patch.confidence, "high")

    def test_settings_footers_use_nun5_select_and_effective_ok_back_anchors(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-015"]
        self.assertEqual(
            [
                (
                    item.edit_id,
                    item.operation,
                    item.destination_offset,
                    item.expected_hex,
                    item.replacement_hex
                    if item.operation == "replace"
                    else (
                        item.source_target_id,
                        item.source_offset,
                        item.source_expected_hex,
                    ),
                )
                for item in edits
            ],
            [
                ("UI-BTL-015-01", "replace", 0x1CE634, "C843023C", "C243023C"),
                ("UI-BTL-015-02", "replace", 0x1CE658, "EB43023C", "E743023C"),
                (
                    "UI-BTL-015-03",
                    "copy",
                    0x1CE67C,
                    "6643023C",
                    ("nun5_btl", 0x1D866C, "4843023C"),
                ),
                (
                    "UI-BTL-015-04",
                    "copy",
                    0x1CE6A0,
                    "6643023C",
                    ("nun5_btl", 0x1D8694, "4843023C"),
                ),
                ("UI-BTL-015-05", "replace", 0x1CCA04, "C843023C", "C243023C"),
                ("UI-BTL-015-06", "replace", 0x1CCA28, "EB43023C", "E743023C"),
                (
                    "UI-BTL-015-07",
                    "copy",
                    0x1CCA4C,
                    "6643023C",
                    ("nun5_btl", 0x1D6750, "4843023C"),
                ),
                (
                    "UI-BTL-015-08",
                    "copy",
                    0x1CCA70,
                    "6643023C",
                    ("nun5_btl", 0x1D6778, "4843023C"),
                ),
            ],
        )
        self.assertEqual(
            (
                package.patches["UI-BTL-015"].status,
                package.patches["UI-BTL-015"].confidence,
            ),
            ("runtime_proven", "verified"),
        )

    def test_battle_results_uses_nun5_data_and_shared_rank_renderer(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-016"]
        patch = package.patches["UI-BTL-016"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [f"UI-BTL-016-{index:02d}" for index in range(1, 12)],
        )
        self.assertEqual(
            Counter(item.operation for item in edits),
            {"copy": 8, "replace": 3},
        )
        self.assertEqual(
            [
                (
                    item.destination_offset,
                    item.length,
                    item.source_target_id,
                    item.source_offset,
                )
                for item in edits
                if item.operation == "copy"
            ],
            [
                (0x210030, 48, "nun5_elf", 0x4DDCA0),
                (0x2100D8, 16, "nun5_btl", 0x2158E0),
                (0x2100F8, 8, "nun5_elf", 0x4DDCD0),
                (0x1E5CC0, 100, "nun5_btl", 0x1EE1F0),
                (0x65ECC, 4, "nun5_btl", 0x68F4C),
                (0x62B24, 2, "nun5_btl", 0x65878),
                (0x62B48, 8, "nun5_btl", 0x6589C),
                (0x62B54, 4, "nun5_btl", 0x658A8),
            ],
        )

        rank = edits[-1]
        replacement = bytes.fromhex(rank.replacement_hex)
        self.assertEqual(
            (rank.operation, rank.destination_offset, rank.length),
            ("replace", 0x634E8, 0xD0),
        )
        self.assertEqual(
            replacement[:92].hex().upper(),
            "6001628EFFFF4224C01802005B00023CA0134224212843004C01648E"
            "0C43023C0000824400000000000316469341023C1D85423400008244"
            "0000000040031446AC3F023CCDCC42340070824400000000C6730046"
            "40EF0D0C00000000",
        )
        self.assertEqual(replacement[92:], bytes(0xD0 - 92))
        self.assertEqual(
            (patch.status, patch.confidence),
            ("runtime_proven", "verified"),
        )

    def test_paired_item_status_layout_uses_exact_nun5_donors(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-009"]
        patch = package.patches["UI-BTL-009"]
        donors = [item for item in edits if item.operation == "copy"]

        self.assertEqual(len(edits), 26)
        self.assertEqual(
            [
                (
                    item.destination_offset,
                    item.length,
                    item.source_target_id,
                    item.source_offset,
                )
                for item in donors
            ],
            [
                (0x4B1208, 84, "nun5_elf", 0x4B86F8),
                (0x4B12A4, 24, "nun5_elf", 0x4B8794),
                (0x1E4C90, 24, "nun5_btl", 0x1ED870),
            ],
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

    def test_numeric_item_status_layout_uses_shared_helper_and_nun5_records(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-010"]
        patch = package.patches["UI-BTL-010"]
        donors = [item for item in edits if item.operation == "copy"]

        self.assertEqual(len(edits), 16)
        self.assertEqual(
            [
                (
                    item.destination_offset,
                    item.length,
                    item.source_target_id,
                    item.source_offset,
                    item.source_expected_hex,
                )
                for item in donors
            ],
            [
                (
                    0x4B116C,
                    12,
                    "nun5_elf",
                    0x4B865C,
                    "01003100610046000E000000",
                ),
                (
                    0x4B1178,
                    12,
                    "nun5_elf",
                    0x4B8668,
                    "0100F10055000E002A000000",
                ),
                (
                    0x4B11FC,
                    12,
                    "nun5_elf",
                    0x4B86EC,
                    "0100A100D10032000A000200",
                ),
            ],
        )
        self.assertEqual(
            [
                (item.destination_offset, item.replacement_hex)
                for item in edits[-6:]
            ],
            [
                (0x5A8C0, "10C2023C"),
                (0x5A910, "D8C1023C"),
                (0x5A95C, "90C1023C"),
                (0x5A9BC, "00C2023C"),
                (0x5AA0C, "B0C1023C"),
                (0x5AA60, "D0C1023C"),
            ],
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

    def test_single_item_status_layout_uses_nun5_records_and_bounded_rotation(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-011"]
        patch = package.patches["UI-BTL-011"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [f"UI-BTL-011-{index:02d}" for index in range(1, 7)],
        )
        records = edits[0]
        self.assertEqual(records.operation, "copy")
        self.assertEqual(records.destination_offset, 0x4B1268)
        self.assertEqual(records.length, 5 * 12)
        self.assertEqual(records.source_target_id, "nun5_elf")
        self.assertEqual(records.source_offset, 0x4B8758)
        self.assertEqual(
            records.source_expected_hex,
            "01001B00010024004E000100"
            "0100E100C1001E000E000200"
            "0100B10071003E000E000000"
            "0100AD0021000E002A000000"
            "0100410001007A000E000000",
        )
        self.assertEqual(
            [
                (item.destination_offset, item.expected_hex, item.replacement_hex)
                for item in edits[1:5]
            ],
            [
                (0x5AC10, "0442023C", "0000023C"),
                (0x5AC28, "2842023C", "0442023C"),
                (0x5ACAC, "00708044", "C816230C"),
                (0x5ACB0, "2D204000", "00708044"),
            ],
        )
        helper = edits[5]
        self.assertEqual(helper.destination_offset, 0x211C20)
        self.assertEqual(helper.length, 32)
        self.assertEqual(helper.expected_hex, "00" * 32)
        self.assertEqual(
            helper.replacement_hex,
            "82000824020008129900082402000816"
            "8A00083C30250EC50800E0032D204000",
        )

        scale = next(
            item for item in package.edits if item.edit_id == "UI-BTL-009-12"
        )
        scale_code = bytes.fromhex(scale.replacement_hex)
        self.assertEqual(len(scale_code), 168)
        self.assertEqual(
            scale_code[0x2C:0x34],
            bytes.fromhex("0C008A9012004B2D"),
        )
        self.assertEqual(
            scale_code[0x88:],
            bytes.fromhex(
                "8C000C3C405B80E528420A3C00088A44"
                "00000000020001460800E003C6000046"
            ),
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "high")

    def test_fixed_item_status_layout_reuses_shared_donor_width_helper(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-012"]
        patch = package.patches["UI-BTL-012"]

        self.assertEqual(
            [item.edit_id for item in edits],
            ["UI-BTL-012-01", "UI-BTL-012-02"],
        )
        self.assertEqual(
            [item.destination_offset for item in edits],
            [0x5B128, 0x5B1F0],
        )
        self.assertEqual([item.length for item in edits], [48, 48])
        for edit in edits:
            replacement = bytes.fromhex(edit.replacement_hex)
            self.assertEqual(len(replacement), 48)
            helper_call = int.from_bytes(replacement[24:28], "little")
            self.assertEqual(helper_call, 0x0C231695)
            self.assertEqual(
                ((helper_call & 0x03FFFFFF) << 2),
                0x008C5A54,
            )
        self.assertEqual(
            bytes.fromhex(edits[0].replacement_hex)[8:24],
            bytes.fromhex("000006242D4000000800A92702000724"),
        )
        self.assertEqual(
            bytes.fromhex(edits[1].replacement_hex)[8:24],
            bytes.fromhex("010006242D4000000800A92711000724"),
        )
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "high")

    def test_controls_vibration_rectangle_is_an_exact_nun5_copy(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        rectangle = next(
            item for item in package.edits if item.edit_id == "UI-ELF-006-01"
        )

        self.assertEqual(rectangle.destination_offset, 0x4D53C0)
        self.assertEqual(rectangle.expected_hex, "010045002A001600")
        self.assertEqual(rectangle.source_target_id, "nun5_elf")
        self.assertEqual(rectangle.source_offset, 0x4DEA28)
        self.assertEqual(rectangle.source_expected_hex, "4000580040001400")
        self.assertEqual(
            struct.unpack("<hhhh", bytes.fromhex(rectangle.source_expected_hex)),
            (64, 88, 64, 20),
        )

    def test_character_select_footer_anchors_are_exact_nun5_copies(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ELF-007"]

        self.assertEqual(
            [item.edit_id for item in edits],
            ["UI-ELF-007-01", "UI-ELF-007-02"],
        )
        self.assertTrue(all(item.operation == "copy" for item in edits))
        self.assertEqual(
            [item.destination_offset for item in edits],
            [0x2BC600, 0x2BC624],
        )
        self.assertEqual(
            [item.expected_hex for item in edits],
            ["9643023C", "2043023C"],
        )
        self.assertEqual(
            [item.source_target_id for item in edits],
            ["nun5_elf", "nun5_elf"],
        )
        self.assertEqual(
            [item.source_offset for item in edits],
            [0x2CF300, 0x2CF324],
        )
        self.assertEqual(
            [item.source_expected_hex for item in edits],
            ["8243023C", "C842023C"],
        )

    def test_common_prompt_records_are_exact_nun5_copies(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ELF-008"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [
                "UI-ELF-008-01",
                "UI-ELF-008-02",
                "UI-ELF-008-03",
                "UI-ELF-008-04",
            ],
        )
        self.assertTrue(all(item.operation == "copy" for item in edits))
        self.assertEqual(
            [item.destination_offset for item in edits],
            [0x4D47C0, 0x4D47B0, 0x4D47B8, 0x4D47A0],
        )
        self.assertEqual(
            [item.expected_hex for item in edits],
            [
                "030019001A001600",
                "0100310072001600",
                "010049002A001600",
                "2D00490046001600",
            ],
        )
        self.assertEqual(
            [item.source_target_id for item in edits],
            ["nun5_elf", "nun5_elf", "nun5_elf", "nun5_elf"],
        )
        self.assertEqual(
            [item.source_offset for item in edits],
            [0x4DEA20, 0x4DEA10, 0x4DEA18, 0x4DEA00],
        )
        self.assertEqual(
            [item.source_expected_hex for item in edits],
            [
                "0200180018001800",
                "0100310038001600",
                "0000000000000000",
                "2D00490042001600",
            ],
        )

    def test_shared_options_select_anchors_are_exact_nun5_copies(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ELF-009"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [
                "UI-ELF-009-01",
                "UI-ELF-009-02",
                "UI-ELF-009-03",
                "UI-ELF-009-04",
            ],
        )
        self.assertTrue(all(item.operation == "copy" for item in edits))
        self.assertEqual(
            [item.destination_offset for item in edits],
            [0x288DA4, 0x288DC8, 0x28A5B8, 0x28A5DC],
        )
        self.assertEqual(
            [item.expected_hex for item in edits],
            ["6643023C", "6643023C", "6643023C", "6643023C"],
        )
        self.assertEqual(
            [item.source_target_id for item in edits],
            ["nun5_elf", "nun5_elf", "nun5_elf", "nun5_elf"],
        )
        self.assertEqual(
            [item.source_offset for item in edits],
            [0x29A704, 0x29A72C, 0x29BF68, 0x29BF90],
        )
        self.assertEqual(
            [item.source_expected_hex for item in edits],
            ["4843023C", "4843023C", "4843023C", "4843023C"],
        )

    def test_collection_submenu_patch_uses_only_exact_nun5_records(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ETC-002"]

        self.assertEqual(
            [item.edit_id for item in edits],
            [
                "UI-ETC-002-01",
                "UI-ETC-002-02",
                "UI-ETC-002-03",
                "UI-ETC-002-04",
                "UI-ETC-002-05",
                "UI-ETC-002-06",
                "UI-ETC-002-07",
                "UI-ETC-002-08",
            ],
        )
        self.assertTrue(all(item.operation == "copy" for item in edits))
        self.assertEqual(
            [
                (
                    item.destination_offset,
                    item.length,
                    item.source_target_id,
                    item.source_offset,
                )
                for item in edits
            ],
            [
                (0x2E930, 32, "nun5_etc", 0x281C0),
                (0x30A80, 16, "nun5_etc", 0x29A60),
                (0x30490, 8, "nun5_elf", 0x4DDC50),
                (0x30498, 8, "nun5_elf", 0x4DDC58),
                (0x304A0, 8, "nun5_elf", 0x4DDC60),
                (0x2E790, 8, "nun5_elf", 0x4DDC70),
                (0x2EB40, 64, "nun5_etc", 0x283D0),
                (0x30AB0, 32, "nun5_etc", 0x29A90),
            ],
        )
        self.assertEqual(
            [
                struct.unpack("<hhhh", bytes.fromhex(item.source_expected_hex))
                for item in edits[2:6]
            ],
            [
                (0, 0, 192, 28),
                (0, 28, 96, 28),
                (0, 56, 96, 28),
                (144, 24, 72, 24),
            ],
        )
        self.assertEqual(
            struct.unpack("<16f", bytes.fromhex(edits[6].source_expected_hex)),
            (
                206.0,
                364.0,
                0.0,
                0.0,
                99.0,
                364.0,
                0.0,
                0.0,
                97.0,
                339.0,
                0.0,
                0.0,
                207.0,
                339.0,
                0.0,
                0.0,
            ),
        )
        self.assertEqual(
            [
                struct.unpack(
                    "<HHHH",
                    bytes.fromhex(edits[7].source_expected_hex)[index : index + 8],
                )
                for index in range(0, 32, 8)
            ],
            [
                (1, 72, 108, 24),
                (1, 48, 108, 24),
                (1, 96, 112, 24),
                (144, 1, 112, 23),
            ],
        )
        self.assertNotIn(0x2E798, {item.destination_offset for item in edits})

    def test_binary_patch_provenance_is_donor_first(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        ui_edits = [edit for edit in package.edits if edit.patch_id.startswith("UI-")]
        operations = Counter(edit.operation for edit in ui_edits)
        copy_sources = Counter(
            edit.source_target_id
            for edit in ui_edits
            if edit.operation == "copy"
        )
        stage_scales = [
            edit
            for edit in ui_edits
            if edit.edit_id.startswith("UI-BTL-002-S")
        ]
        adaptations = [
            edit
            for edit in ui_edits
            if edit.operation == "replace" and edit not in stage_scales
        ]

        self.assertEqual(len(ui_edits), 277)
        self.assertEqual(operations, {"copy": 99, "replace": 178})
        self.assertEqual(
            copy_sources,
            {"nun5_elf": 64, "nun5_btl": 26, "nun5_etc": 9},
        )
        self.assertEqual(len(stage_scales), 24)
        self.assertEqual(len(adaptations), 154)

    def test_plan_applies_only_inside_the_selected_cvm_member(self) -> None:
        result = self.result("battlegauge")
        end = result.outer_cvm_offset + len(result.original)
        cvm = bytearray(b"\xA5" * (end + 32))
        cvm[: len(self.plan.target_header)] = self.plan.target_header
        cvm[result.outer_cvm_offset:end] = result.original
        before = bytes(cvm)

        selected_plan = engine.TexturePatchPlan(
            self.plan.package,
            (result,),
            self.plan.target_header,
        )
        selected_plan.apply_to_cvm(cvm)

        self.assertEqual(len(cvm), len(before))
        self.assertEqual(
            bytes(cvm[: result.outer_cvm_offset]),
            before[: result.outer_cvm_offset],
        )
        self.assertEqual(bytes(cvm[result.outer_cvm_offset:end]), result.replacement)
        self.assertEqual(bytes(cvm[end:]), before[end:])

    def test_profile_log_records_every_container_patch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "texture_patcher"
            write_texture_patch_log(self.plan, output)
            with (output / "patch_log.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                patches = list(csv.DictReader(handle, delimiter="\t"))
            with (output / "run_summary.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                summary = list(csv.DictReader(handle, delimiter="\t"))

            self.assertEqual(len(patches), 96)
            self.assertTrue(all(row["file"] == "DATA/DATA.CVM" for row in patches))
            self.assertTrue(all(row["original_sha256"] for row in patches))
            self.assertTrue(all(row["new_sha256"] for row in patches))
            self.assertTrue(
                all(row["derivation"].startswith("canonical_nun5_") for row in patches)
            )
            self.assertEqual(summary[0]["container_count"], "96")
            self.assertEqual(summary[0]["mapping_count"], "210")
            self.assertEqual(summary[0]["worker_count"], str(self.plan.worker_count))


if __name__ == "__main__":
    unittest.main()
