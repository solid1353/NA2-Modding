from __future__ import annotations

import csv
import gzip
import tempfile
import unittest
from pathlib import Path

from na2_patcher.build_profile import write_ui_texture_log
from na2_patcher.modules.ui_textures import engine


class UiTextureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        na2_root, nun5_root, data_root = engine.default_roots()
        required = (
            na2_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.iso",
            na2_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.hdr",
            nun5_root / "DATA" / "DATA.CVM.files" / "DATA.CVM.iso",
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest(
                "UI texture verification requires extracted NA2 and NUN5 sources"
            )
        cls.plan = engine.build_ui_texture_plan(
            na2_root=na2_root,
            nun5_root=nun5_root,
            data_root=data_root,
        )

    def result(self, container_id: str) -> engine.ContainerResult:
        return next(
            result
            for result in self.plan.containers
            if result.spec.container_id == container_id
        )

    def test_complete_package_is_pinned_and_fixed_size(self) -> None:
        self.assertEqual(len(self.plan.containers), 34)
        self.assertEqual(self.plan.mapping_count, 76)
        for result in self.plan.containers:
            self.assertEqual(
                len(result.replacement), len(result.original), result.spec.path
            )
            self.assertEqual(
                engine.sha256(result.replacement), result.strategy.blob_sha256
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

    def test_plan_applies_only_inside_the_selected_cvm_member(self) -> None:
        result = self.result("battlegauge")
        end = result.outer_cvm_offset + len(result.original)
        cvm = bytearray(b"\xA5" * (end + 32))
        cvm[: len(self.plan.target_header)] = self.plan.target_header
        cvm[result.outer_cvm_offset:end] = result.original
        before = bytes(cvm)

        selected_plan = engine.UiTexturePlan(
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
            output = Path(directory) / "ui_textures"
            write_ui_texture_log(self.plan, output)
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
            self.assertEqual(summary[0]["container_count"], "34")
            self.assertEqual(summary[0]["mapping_count"], "76")


if __name__ == "__main__":
    unittest.main()
