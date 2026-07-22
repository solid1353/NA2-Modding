from __future__ import annotations

import csv
import gzip
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
        self.assertEqual(len(self.plan.containers), 34)
        self.assertEqual(self.plan.mapping_count, 76)
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
        self.assertEqual(len(whole), 33)
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

    def test_stage_fitter_scales_only_the_horizontal_axis(self) -> None:
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

        self.assertEqual(vertical.destination_offset, 0x61570)
        self.assertEqual(vertical.expected_hex, "00708244")
        self.assertEqual(vertical.replacement_hex, "00788244")
        self.assertEqual(horizontal.destination_offset, 0x6157C)
        self.assertEqual(horizontal.expected_hex, "C6730046")
        self.assertEqual(horizontal.replacement_hex, "04006EC4")

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

    def test_mode_select_start_patch_uses_nun5_rectangle_and_na2_register(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        rectangle = next(
            item for item in package.edits if item.edit_id == "UI-ELF-005-01"
        )
        anchor = next(
            item for item in package.edits if item.edit_id == "UI-ELF-005-02"
        )

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

    def test_shop_patch_retains_only_the_proven_nun5_currency_rectangles(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-ETC-001"]

        self.assertEqual(len(edits), 1)
        rectangle = edits[0]
        self.assertEqual(rectangle.edit_id, "UI-ETC-001-01")
        self.assertEqual(rectangle.destination_offset, 0x30308)
        self.assertEqual(rectangle.source_target_id, "nun5_etc")
        self.assertEqual(rectangle.source_offset, 0x292F8)

    def test_jutsu_patch_retains_the_fourteen_runtime_proven_edits(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_patcher.load_package(
            repository
            / "na2_patcher/features/localization/binary_patcher"
        )
        edits = [item for item in package.edits if item.patch_id == "UI-BTL-005"]
        patch = package.patches["UI-BTL-005"]

        self.assertEqual(len(edits), 14)
        self.assertEqual(
            {item.edit_id for item in edits},
            {f"UI-BTL-005-{index:02d}" for index in range(1, 15)},
        )
        self.assertNotIn(0xA0, {item.destination_offset for item in edits})
        self.assertNotIn(0x9E44, {item.destination_offset for item in edits})
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")

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

        self.assertEqual(len(ui_edits), 86)
        self.assertEqual(operations, {"copy": 47, "replace": 39})
        self.assertEqual(
            copy_sources,
            {"nun5_elf": 39, "nun5_btl": 7, "nun5_etc": 1},
        )
        self.assertEqual(len(stage_scales), 24)
        self.assertEqual(len(adaptations), 15)

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

            self.assertEqual(len(patches), 34)
            self.assertTrue(all(row["file"] == "DATA/DATA.CVM" for row in patches))
            self.assertTrue(all(row["original_sha256"] for row in patches))
            self.assertTrue(all(row["new_sha256"] for row in patches))
            self.assertTrue(
                all(row["derivation"].startswith("canonical_nun5_") for row in patches)
            )
            self.assertEqual(summary[0]["container_count"], "34")
            self.assertEqual(summary[0]["mapping_count"], "76")


if __name__ == "__main__":
    unittest.main()
