from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.profile import (
    FEATURE_FIELDS,
    MODULE_FIELDS,
    content_sha256,
    feature_content_sha256,
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
    def create_feature(
        self,
        workspace: Path,
        feature_id: str,
    ) -> Path:
        package = workspace / "features" / feature_id
        write_tsv(
            package / "manifest.tsv",
            ["key", "value"],
            [
                ["schema_version", "1"],
                ["feature_id", feature_id],
                ["name", feature_id.title()],
                ["description", "Test feature."],
            ],
        )
        return package

    def create_profile(
        self,
        workspace: Path,
        expected_hash: str,
        *,
        enabled: str = "1",
    ) -> Path:
        source = workspace / "source"
        source.mkdir(parents=True)
        feature = self.create_feature(workspace, "feature")
        module_input = feature / "translation_importer" / "input.bin"
        module_input.parent.mkdir()
        module_input.write_bytes(b"profile input")
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
            [
                [
                    "feature",
                    enabled,
                    "features/feature",
                    feature_content_sha256(feature),
                    "test",
                ]
            ],
        )
        write_tsv(
            profile / "modules.tsv",
            MODULE_FIELDS,
            [
                [
                    "one",
                    "10",
                    "translation_importer",
                    "features/feature/translation_importer/input.bin",
                    expected_hash,
                    "test",
                ]
            ],
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

    def test_rejects_enabled_feature_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            with (workspace / "features" / "feature" / "manifest.tsv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write("changed\twithout repinning\n")

            with self.assertRaisesRegex(ValueError, "Feature feature: input SHA-256"):
                load_profile(profile_path, workspace)

    def test_rejects_module_outside_feature_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            outside = workspace / "outside" / "input.bin"
            outside.parent.mkdir()
            outside.write_bytes(b"profile input")
            modules = profile_path / "modules.tsv"
            with modules.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[0]["input"] = "outside/input.bin"
            with modules.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=MODULE_FIELDS, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "exactly one feature directory"):
                load_profile(profile_path, workspace)

    def test_rejects_module_subfolder_that_does_not_match_engine(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            wrong = workspace / "features" / "feature" / "wrong" / "input.bin"
            wrong.parent.mkdir()
            wrong.write_bytes(b"profile input")
            modules = profile_path / "modules.tsv"
            with modules.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[0]["input"] = "features/feature/wrong/input.bin"
            with modules.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=MODULE_FIELDS, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "first feature subfolder"):
                load_profile(profile_path, workspace)

    def test_disabled_input_hash_mismatch_does_not_block_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            disabled = self.create_profile(workspace, "0" * 64, enabled="0")
            active_feature = self.create_feature(workspace, "active")
            active_input = active_feature / "translation_importer" / "input.bin"
            active_input.parent.mkdir()
            active_input.write_bytes(b"profile input")
            features = disabled / "features.tsv"
            with features.open(encoding="utf-8", newline="") as handle:
                feature_rows = list(csv.DictReader(handle, delimiter="\t"))
            feature_rows.append(
                {
                    "feature_id": "active",
                    "enabled": "1",
                    "input": "features/active",
                    "expected_sha256": feature_content_sha256(active_feature),
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
                    "module": "translation_importer",
                    "input": "features/active/translation_importer/input.bin",
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
            with (workspace / "features" / "feature" / "manifest.tsv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write("changed\twithout repinning\n")
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
                text.replace("\ttranslation_importer\t", "\tzip_overlay\t"),
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

    def test_feature_hash_includes_only_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            package = self.create_feature(workspace, "feature")
            (package / "README.md").write_text("first\n", encoding="utf-8")
            module_input = package / "binary_patcher" / "data.tsv"
            module_input.parent.mkdir()
            module_input.write_text("first\n", encoding="utf-8")
            first = feature_content_sha256(package)
            (package / "README.md").write_text("second\n", encoding="utf-8")
            module_input.write_text("second\n", encoding="utf-8")
            self.assertEqual(first, feature_content_sha256(package))
            with (package / "manifest.tsv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                handle.write("changed\tvalue\n")
            self.assertNotEqual(first, feature_content_sha256(package))

    def test_binary_patcher_hash_excludes_documentation(self) -> None:
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

            first = module_content_sha256(package, "binary_patcher")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            second = module_content_sha256(package, "binary_patcher")
            self.assertEqual(first, second)

            (package / "patches.tsv").write_text("changed\n", encoding="utf-8")
            third = module_content_sha256(package, "binary_patcher")
            self.assertNotEqual(second, third)

    def test_binary_patcher_hash_includes_referenced_blobs(self) -> None:
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

            first = module_content_sha256(package, "binary_patcher")
            (package / "groups.tsv").write_text("changed\n", encoding="utf-8")
            groups_changed = module_content_sha256(package, "binary_patcher")
            self.assertNotEqual(first, groups_changed)
            (package / "groups.tsv").write_text("groups.tsv\n", encoding="utf-8")
            (package / "payload.bin").write_bytes(b"two")
            second = module_content_sha256(package, "binary_patcher")
            self.assertNotEqual(first, second)

    def test_string_patcher_hash_includes_only_string_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "string_patcher"
            package.mkdir()
            (package / "strings.tsv").write_text("string_id\none\n", encoding="utf-8")
            (package / "README.md").write_text("first\n", encoding="utf-8")
            (package / "engine.py").write_text("first\n", encoding="utf-8")

            first = module_content_sha256(package, "string_patcher")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            (package / "engine.py").write_text("second\n", encoding="utf-8")
            self.assertEqual(first, module_content_sha256(package, "string_patcher"))

            (package / "strings.tsv").write_text("string_id\ntwo\n", encoding="utf-8")
            self.assertNotEqual(
                first,
                module_content_sha256(package, "string_patcher"),
            )

    def test_translation_importer_hash_includes_only_declarative_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "translation_importer"
            package.mkdir()
            (package / "manifest.tsv").write_text(
                "key\tvalue\nschema_version\t1\nmapping_version\t1\n"
                f"mappings_sha256\t{'0' * 64}\n",
                encoding="utf-8",
            )
            (package / "mappings.tsv").write_text("mapping\n", encoding="utf-8")
            (package / "README.md").write_text("first\n", encoding="utf-8")
            first = module_content_sha256(package, "translation_importer")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            self.assertEqual(
                first,
                module_content_sha256(package, "translation_importer"),
            )
            (package / "manifest.tsv").write_text(
                "key\tvalue\nschema_version\t1\nmapping_version\t2\n"
                f"mappings_sha256\t{'0' * 64}\n",
                encoding="utf-8",
            )
            self.assertNotEqual(
                first,
                module_content_sha256(package, "translation_importer"),
            )

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

            first = module_content_sha256(package, "texture_patcher")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            (package / "engine.py").write_text("second\n", encoding="utf-8")
            (package / "generated.ccs").write_bytes(b"two")
            self.assertEqual(first, module_content_sha256(package, "texture_patcher"))

            (package / "mappings.tsv").write_text(
                "mapping_id\ntwo\n", encoding="utf-8"
            )
            second = module_content_sha256(package, "texture_patcher")
            self.assertNotEqual(first, second)

            (package / "strategies.tsv").write_text(
                "container_id\tstrategy\nexample\tmapped\n", encoding="utf-8"
            )
            third = module_content_sha256(package, "texture_patcher")
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

    def test_current_profile_contains_no_selection_tables(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        profile_directory = repository / "na2_patcher" / "profiles" / "current"
        self.assertFalse((profile_directory / "feature_selections.tsv").exists())
        features = repository / "na2_patcher" / "features"
        self.assertFalse(any(features.glob("*/selections.tsv")))
        self.assertFalse(
            (features / "schemas" / "v1" / "selections.schema.tsv").exists()
        )

    def test_each_feature_has_one_root_readme_and_no_nested_markdown(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        features = repository / "na2_patcher" / "features"
        for feature in sorted(features.iterdir()):
            if not feature.is_dir() or not (feature / "manifest.tsv").is_file():
                continue
            with self.subTest(feature=feature.name):
                markdown = sorted(feature.rglob("*.md"))
                self.assertEqual(markdown, [feature / "README.md"])

    def test_current_modules_are_owned_by_matching_feature_subfolders(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        profile = load_profile(
            repository / "na2_patcher" / "profiles" / "current",
            repository,
        )
        features = {feature.feature_id: feature for feature in profile.features}
        for module in profile.modules:
            relative = module.input_path.relative_to(
                features[module.feature_id].input_path
            )
            self.assertEqual(relative.parts[0], module.module)


if __name__ == "__main__":
    unittest.main()
