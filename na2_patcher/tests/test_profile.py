from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.profile import (
    FEATURE_FIELDS,
    FEATURE_SELECTION_FIELDS,
    MODULE_FIELDS,
    content_sha256,
    load_profile,
    module_content_sha256,
)


def write_tsv(path: Path, fields: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


class ProfileTests(unittest.TestCase):
    def create_profile(
        self,
        workspace: Path,
        expected_hash: str,
        *,
        enabled: str = "1",
    ) -> Path:
        source = workspace / "source" / "input.bin"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"profile input")
        profile = workspace / "profiles" / "test"
        write_tsv(
            profile / "manifest.tsv",
            ["key", "value"],
            [["schema_version", "2"], ["profile_id", "test"]],
        )
        write_tsv(
            profile / "roots.tsv",
            ["root_id", "path"],
            [["na2", "source"]],
        )
        write_tsv(
            profile / "features.tsv",
            FEATURE_FIELDS,
            [["feature", enabled, "Feature", "Test feature.", "test"]],
        )
        write_tsv(
            profile / "modules.tsv",
            MODULE_FIELDS,
            [
                [
                    "one",
                    "10",
                    "translation",
                    "source/input.bin",
                    expected_hash,
                    "test",
                ]
            ],
        )
        write_tsv(
            profile / "feature_selections.tsv",
            FEATURE_SELECTION_FIELDS,
            [["feature", "one", "all", "", "test"]],
        )
        return profile

    def test_loads_hash_pinned_relative_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile = load_profile(self.create_profile(workspace, expected), workspace)
            self.assertEqual(profile.manifest["profile_id"], "test")
            self.assertEqual(profile.modules[0].module_id, "one")

    def test_rejects_enabled_input_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            profile_path = self.create_profile(workspace, "0" * 64)
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_profile(profile_path, workspace)

    def test_preserves_duplicate_feature_selection_occurrences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            with (profile_path / "feature_selections.tsv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write("feature\tone\tall\t\tsecond occurrence\n")

            profile = load_profile(profile_path, workspace)
            self.assertEqual(len(profile.selections), 2)
            self.assertEqual(len(profile.modules[0].selections), 2)
            self.assertEqual(
                [selection.occurrence for selection in profile.modules[0].selections],
                [0, 1],
            )

    def test_rejects_enabled_feature_without_selections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            write_tsv(
                profile_path / "feature_selections.tsv",
                FEATURE_SELECTION_FIELDS,
                [],
            )

            with self.assertRaisesRegex(ValueError, "Feature feature has no selections"):
                load_profile(profile_path, workspace)

    def test_disabled_input_hash_mismatch_does_not_block_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            disabled = self.create_profile(workspace, "0" * 64, enabled="0")
            features = disabled / "features.tsv"
            with features.open(encoding="utf-8", newline="") as handle:
                feature_rows = list(csv.DictReader(handle, delimiter="\t"))
            feature_rows.append(
                {
                    "feature_id": "active",
                    "enabled": "1",
                    "name": "Active",
                    "description": "",
                    "reason": "active",
                }
            )
            with features.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=FEATURE_FIELDS, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(feature_rows)
            modules = disabled / "modules.tsv"
            with modules.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows.append(
                {
                    "module_id": "enabled",
                    "order": "20",
                    "module": "translation",
                    "input": "source/input.bin",
                    "expected_sha256": hashlib.sha256(b"profile input")
                    .hexdigest()
                    .upper(),
                    "reason": "active",
                }
            )
            with modules.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=MODULE_FIELDS, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(rows)
            selections = disabled / "feature_selections.tsv"
            with selections.open("a", encoding="utf-8", newline="") as handle:
                handle.write("active\tenabled\tall\t\tactive\n")
            profile = load_profile(disabled, workspace)
            self.assertFalse(profile.modules[0].enabled)
            self.assertTrue(profile.modules[1].enabled)

    def test_rejects_retired_zip_overlay_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            modules = profile_path / "modules.tsv"
            text = modules.read_text(encoding="utf-8")
            modules.write_text(
                text.replace("\ttranslation\t", "\tzip_overlay\t"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsupported module 'zip_overlay'"):
                load_profile(profile_path, workspace)

    def test_directory_hash_is_path_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a").mkdir()
            (root / "a" / "one.txt").write_text("one", encoding="utf-8")
            first = content_sha256(root / "a")
            (root / "a" / "one.txt").write_text("two", encoding="utf-8")
            second = content_sha256(root / "a")
            self.assertNotEqual(first, second)

    def test_raw_binary_hash_excludes_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            for name in (
                "manifest.tsv",
                "targets.tsv",
                "groups.tsv",
                "patches.tsv",
            ):
                (package / name).write_text(f"{name}\n", encoding="utf-8")
            (package / "edits.tsv").write_text("blob_path\n", encoding="utf-8")
            (package / "README.md").write_text("first\n", encoding="utf-8")

            first = module_content_sha256(package, "raw_binary")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            second = module_content_sha256(package, "raw_binary")
            self.assertEqual(first, second)

            (package / "patches.tsv").write_text("changed\n", encoding="utf-8")
            third = module_content_sha256(package, "raw_binary")
            self.assertNotEqual(second, third)

    def test_raw_binary_hash_includes_referenced_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            for name in (
                "manifest.tsv",
                "targets.tsv",
                "groups.tsv",
                "patches.tsv",
            ):
                (package / name).write_text(f"{name}\n", encoding="utf-8")
            (package / "payload.bin").write_bytes(b"one")
            (package / "edits.tsv").write_text(
                "blob_path\npayload.bin\n", encoding="utf-8"
            )

            first = module_content_sha256(package, "raw_binary")
            (package / "groups.tsv").write_text("changed\n", encoding="utf-8")
            groups_changed = module_content_sha256(package, "raw_binary")
            self.assertNotEqual(first, groups_changed)
            (package / "groups.tsv").write_text("groups.tsv\n", encoding="utf-8")
            (package / "payload.bin").write_bytes(b"two")
            second = module_content_sha256(package, "raw_binary")
            self.assertNotEqual(first, second)

    def test_ui_texture_hash_includes_only_declarative_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            (package / "containers.tsv").write_text(
                "container_id\nexample\n", encoding="utf-8"
            )
            (package / "mappings.tsv").write_text("mapping_id\none\n", encoding="utf-8")
            (package / "strategies.tsv").write_text(
                "container_id\tstrategy\nexample\twhole\n",
                encoding="utf-8",
            )
            (package / "generated.ccs").write_bytes(b"one")
            (package / "README.md").write_text("first\n", encoding="utf-8")
            (package / "engine.py").write_text("first\n", encoding="utf-8")

            first = module_content_sha256(package, "ui_textures")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            (package / "engine.py").write_text("second\n", encoding="utf-8")
            (package / "generated.ccs").write_bytes(b"two")
            self.assertEqual(first, module_content_sha256(package, "ui_textures"))

            (package / "mappings.tsv").write_text(
                "mapping_id\ntwo\n", encoding="utf-8"
            )
            second = module_content_sha256(package, "ui_textures")
            self.assertNotEqual(first, second)

            (package / "strategies.tsv").write_text(
                "container_id\tstrategy\nexample\tmapped\n", encoding="utf-8"
            )
            third = module_content_sha256(package, "ui_textures")
            self.assertNotEqual(second, third)

    def test_external_translation_hash_includes_only_control_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "external_translation"
            package.mkdir()
            (package / "manifest.tsv").write_text(
                "key\tvalue\nschema_version\t1\n", encoding="utf-8"
            )
            (package / "pointer_refs.tsv").write_text(
                "mapping_id\toffset\none\t0x10\n", encoding="utf-8"
            )
            (package / "README.md").write_text("first\n", encoding="utf-8")
            (package / "engine.py").write_text("first\n", encoding="utf-8")

            first = module_content_sha256(package, "external_translation")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            (package / "engine.py").write_text("second\n", encoding="utf-8")
            self.assertEqual(
                first, module_content_sha256(package, "external_translation")
            )

            (package / "pointer_refs.tsv").write_text(
                "mapping_id\toffset\none\t0x20\n", encoding="utf-8"
            )
            self.assertNotEqual(
                first, module_content_sha256(package, "external_translation")
            )

    def test_current_enabled_module_hashes_match(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        profile = load_profile(
            repository / "na2_patcher" / "profiles" / "current",
            repository,
        )
        for module in profile.modules:
            if not module.enabled:
                continue
            self.assertEqual(
                module_content_sha256(module.input_path, module.module),
                module.expected_sha256,
                module.module_id,
            )

    def test_current_raw_binary_selections_are_group_only(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        profile = load_profile(
            repository / "na2_patcher" / "profiles" / "current",
            repository,
        )
        module_types = {module.module_id: module.module for module in profile.modules}
        raw_selections = [
            selection
            for selection in profile.selections
            if module_types[selection.module_id] == "raw_binary"
        ]
        self.assertTrue(raw_selections)
        self.assertEqual(
            {selection.selection_kind for selection in raw_selections},
            {"group"},
        )


if __name__ == "__main__":
    unittest.main()
