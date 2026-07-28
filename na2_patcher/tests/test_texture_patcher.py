from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from na2_patcher.build_profile import write_texture_patch_log
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
            repository
            / "na2_patcher"
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

    def result(self, container_id: str) -> engine.ContainerResult:
        return next(
            result
            for result in self.plan.containers
            if result.spec.container_id == container_id
        )

    def test_every_container_replacement_preserves_file_size(self) -> None:
        self.assertTrue(self.plan.containers)
        for result in self.plan.containers:
            self.assertEqual(
                len(result.replacement),
                len(result.original),
                result.spec.path,
            )

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

            self.assertEqual(
                {row["member"] for row in patches},
                {result.spec.path for result in self.plan.containers},
            )
            self.assertTrue(all(row["file"] == "DATA/DATA.CVM" for row in patches))
            self.assertTrue(all(row["original_sha256"] for row in patches))
            self.assertTrue(all(row["new_sha256"] for row in patches))
            self.assertEqual(
                summary[0]["container_count"],
                str(len(self.plan.containers)),
            )
            self.assertEqual(
                summary[0]["mapping_count"],
                str(self.plan.mapping_count),
            )
            self.assertEqual(
                summary[0]["worker_count"],
                str(self.plan.worker_count),
            )


if __name__ == "__main__":
    unittest.main()
