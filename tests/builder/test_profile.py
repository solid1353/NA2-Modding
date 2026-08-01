from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.modules.binary_patcher import engine as binary_patcher
from na228_builder.modules.runtime_injector import engine as runtime_injector
from na228_builder.composer import resolve_module_order
from na228_builder.profile import (
    FEATURE_FIELDS,
    MODULE_TYPE_ORDER,
    feature_content_sha256,
    load_profile,
    module_content_sha256,
    profile_resource_files,
)


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class ProfileTests(unittest.TestCase):
    def create_workspace(self, root: Path) -> tuple[Path, Path, Path]:
        features = root / "features"
        source = root / "source"
        profiles = root / "profiles"
        features.mkdir()
        source.mkdir()
        profiles.mkdir()
        (root / "paths.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "roots": {
                        "repository": ".",
                        "features": "features",
                        "source": "source",
                    },
                    "files": {"placeholder": "placeholder"},
                }
            ),
            encoding="utf-8",
        )
        return features, source, profiles

    def create_module(self, feature: Path, module_type: str) -> Path:
        module = feature / module_type
        module.mkdir(parents=True)
        if module_type == "binary_patcher":
            write_tsv(module / "targets.tsv", binary_patcher.TARGET_FIELDS, [])
            write_tsv(module / "groups.tsv", binary_patcher.GROUP_FIELDS, [])
            write_tsv(module / "patches.tsv", binary_patcher.PATCH_FIELDS, [])
            write_tsv(module / "edits.tsv", binary_patcher.EDIT_FIELDS, [])
        elif module_type == "runtime_injector":
            for name, fields in (
                ("targets.tsv", runtime_injector.TARGET_FIELDS),
                ("groups.tsv", runtime_injector.GROUP_FIELDS),
                ("patches.tsv", runtime_injector.PATCH_FIELDS),
                ("fragments.tsv", runtime_injector.FRAGMENT_FIELDS),
                ("c_sources.tsv", runtime_injector.C_SOURCE_FIELDS),
                ("c_imports.tsv", runtime_injector.C_IMPORT_FIELDS),
                ("c_fragments.tsv", runtime_injector.C_FRAGMENT_FIELDS),
                ("relocations.tsv", runtime_injector.RELOCATION_FIELDS),
                ("edits.tsv", runtime_injector.EDIT_FIELDS),
            ):
                write_tsv(module / name, fields, [])
        elif module_type == "string_patcher":
            (module / "strings.tsv").write_text("string_id\n", encoding="utf-8")
        elif module_type == "translation_importer":
            (module / "mappings.tsv").write_text("id\n", encoding="utf-8")
        elif module_type == "texture_patcher":
            for name in ("containers.tsv", "mappings.tsv", "strategies.tsv"):
                (module / name).write_text("id\n", encoding="utf-8")
        else:
            self.fail(f"unsupported test module {module_type}")
        return module

    def create_feature(self, features: Path, feature_id: str, *module_types: str) -> Path:
        feature = features / feature_id
        feature.mkdir()
        (feature / "README.md").write_text(f"# {feature_id}\n", encoding="utf-8")
        for module_type in module_types:
            self.create_module(feature, module_type)
        return feature

    def create_profile(
        self,
        profiles: Path,
        source: Path,
        rows: list[dict[str, object]],
        *,
        profile_id: str = "test",
    ) -> Path:
        profile = profiles / profile_id
        profile.mkdir()
        write_tsv(profile / "roots.tsv", ["root_id", "path"], [{"root_id": "na2", "path": "source"}])
        write_tsv(
            profile / "features.tsv",
            FEATURE_FIELDS,
            [{"bypass_check": "0", **row} for row in rows],
        )
        (profile / "identity.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "image": {
                        "source_boot_path": "SLPS_258.37",
                        "output_boot_path": "SLOP_NA2.28",
                        "system_cnf_path": "SYSTEM.CNF",
                    },
                    "memory_card": {
                        "title_offset": 4,
                        "title_capacity": 16,
                        "title_encoding": "ascii",
                        "source_title": "Original",
                        "output_title": "NA 2.28",
                    },
                    "game_title": {
                        "imported": "Imported Game",
                        "output": "Output Game",
                        "expected_mapping_count": 1,
                        "expected_occurrence_count": 1,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return profile

    def test_profile_derives_identity_modules_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            alpha = self.create_feature(features, "alpha", "binary_patcher")
            localization = self.create_feature(
                features,
                "localization",
                "translation_importer",
                "string_patcher",
                "binary_patcher",
            )
            profile_path = self.create_profile(
                profiles,
                source,
                [
                    {"feature_id": "alpha", "expected_sha256": feature_content_sha256(alpha)},
                    {"feature_id": "localization", "expected_sha256": feature_content_sha256(localization)},
                ],
            )
            profile = load_profile(profile_path, root)
            self.assertEqual(profile.profile_id, "test")
            self.assertEqual([item.feature_id for item in profile.features], ["alpha", "localization"])
            self.assertEqual(
                [item.module_id for item in profile.modules],
                [
                    "alpha.binary_patcher",
                    "localization.translation_importer",
                    "localization.string_patcher",
                    "localization.binary_patcher",
                ],
            )
            self.assertEqual([item.order for item in profile.modules], [1, 2, 3, 4])

    def test_rejects_feature_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            self.create_feature(features, "alpha", "binary_patcher")
            profile = self.create_profile(
                profiles,
                source,
                [{"feature_id": "alpha", "expected_sha256": "0" * 64}],
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_profile(profile, root)

    def test_allows_explicit_feature_hash_bypass_and_records_actual_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            alpha = self.create_feature(features, "alpha", "binary_patcher")
            profile = self.create_profile(
                profiles,
                source,
                [
                    {
                        "feature_id": "alpha",
                        "expected_sha256": "0" * 64,
                        "bypass_check": "1",
                    }
                ],
            )

            loaded = load_profile(profile, root)

            feature = loaded.features[0]
            self.assertTrue(feature.hash_check_bypassed)
            self.assertEqual(feature.expected_sha256, "0" * 64)
            self.assertEqual(feature.actual_sha256, feature_content_sha256(alpha))

    def test_rejects_unknown_feature_hash_bypass_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            self.create_feature(features, "alpha", "binary_patcher")
            profile = self.create_profile(
                profiles,
                source,
                [
                    {
                        "feature_id": "alpha",
                        "expected_sha256": "0" * 64,
                        "bypass_check": "x",
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "bypass_check must be 0 or 1"):
                load_profile(profile, root)

    def test_rejects_duplicate_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            alpha = self.create_feature(features, "alpha", "binary_patcher")
            row = {"feature_id": "alpha", "expected_sha256": feature_content_sha256(alpha)}
            profile = self.create_profile(profiles, source, [row, row])
            with self.assertRaisesRegex(ValueError, "Duplicate or invalid feature_id"):
                load_profile(profile, root)

    def test_omitted_feature_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            active = self.create_feature(features, "active", "binary_patcher")
            self.create_feature(features, "inactive", "binary_patcher")
            profile = self.create_profile(
                profiles,
                source,
                [{"feature_id": "active", "expected_sha256": feature_content_sha256(active)}],
            )
            loaded = load_profile(profile, root)
            self.assertEqual([item.feature_id for item in loaded.features], ["active"])

    def test_release_resources_include_structure_and_only_canonical_module_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            feature = self.create_feature(features, "alpha", "binary_patcher")
            helper = feature / "binary_patcher" / "helper.py"
            helper.write_text("raise SystemExit\n", encoding="utf-8")
            profile_path = self.create_profile(
                profiles,
                source,
                [{"feature_id": "alpha", "expected_sha256": feature_content_sha256(feature)}],
            )
            loaded = load_profile(profile_path, root)
            resources = set(profile_resource_files(loaded))
            self.assertIn((profile_path / "identity.json").resolve(), resources)
            self.assertIn((feature / "README.md").resolve(), resources)
            self.assertIn(
                (feature / "binary_patcher" / "edits.tsv").resolve(), resources
            )
            self.assertNotIn(helper.resolve(), resources)

    def test_rejects_unknown_module_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, _, _ = self.create_workspace(root)
            feature = features / "alpha"
            feature.mkdir()
            (feature / "README.md").write_text("# alpha\n", encoding="utf-8")
            (feature / "unknown").mkdir()
            with self.assertRaisesRegex(ValueError, "unknown module"):
                feature_content_sha256(feature)

    def test_rejects_feature_root_metadata_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, _, _ = self.create_workspace(root)
            feature = self.create_feature(features, "alpha", "binary_patcher")
            (feature / "manifest.tsv").write_text("key\tvalue\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported files"):
                feature_content_sha256(feature)

    def test_importer_uses_derived_string_consumer_without_feature_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            feature = self.create_feature(features, "localization", "translation_importer")
            profile = self.create_profile(
                profiles,
                source,
                [{"feature_id": "localization", "expected_sha256": feature_content_sha256(feature)}],
            )
            loaded = load_profile(profile, root)
            self.assertEqual(resolve_module_order(loaded.modules), loaded.modules)

    def test_profile_identity_requires_equal_length_boot_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            features, source, profiles = self.create_workspace(root)
            alpha = self.create_feature(features, "alpha", "binary_patcher")
            profile = self.create_profile(
                profiles,
                source,
                [
                    {"feature_id": "alpha", "expected_sha256": feature_content_sha256(alpha)},
                ],
            )
            identity_path = profile / "identity.json"
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            identity["image"]["output_boot_path"] = "BOOT.ELF"
            identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "equal byte lengths"):
                load_profile(profile, root)

    def test_binary_hash_ignores_helpers_but_includes_referenced_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "feature"
            feature.mkdir()
            module = self.create_module(feature, "binary_patcher")
            first = module_content_sha256(module, "binary_patcher")
            (module / "helper.py").write_text("print('one')\n", encoding="utf-8")
            self.assertEqual(first, module_content_sha256(module, "binary_patcher"))
            (module / "groups.tsv").write_text(
                "group_id\tname\tdescription\treview_notes\n"
                "g\tGroup\tChanged canonical input.\t\n",
                encoding="utf-8",
            )
            self.assertNotEqual(first, module_content_sha256(module, "binary_patcher"))

    def test_resident_hash_ignores_helpers_but_includes_fragment_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "feature"
            feature.mkdir()
            module = self.create_module(feature, "runtime_injector")
            blob = module / "assets" / "resident.bin"
            blob.parent.mkdir()
            blob.write_bytes(b"\0\0\0\0")
            write_tsv(
                module / "fragments.tsv",
                runtime_injector.FRAGMENT_FIELDS,
                [{
                    "fragment_id": "test.code",
                    "order": 1,
                    "kind": "code",
                    "alignment": 4,
                    "payload_hex": "",
                    "blob_path": "assets/resident.bin",
                    "blob_offset": 0,
                    "length": 4,
                    "blob_sha256": hashlib.sha256(
                        blob.read_bytes()
                    ).hexdigest().upper(),
                    "init": 0,
                }],
            )
            first = module_content_sha256(module, "runtime_injector")
            (module / "helper.py").write_text(
                "print('one')\n", encoding="utf-8"
            )
            self.assertEqual(
                first, module_content_sha256(module, "runtime_injector")
            )
            blob.write_bytes(b"\1\0\0\0")
            self.assertNotEqual(
                first, module_content_sha256(module, "runtime_injector")
            )

    def test_resident_hash_includes_declared_c_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "feature"
            feature.mkdir()
            module = self.create_module(feature, "runtime_injector")
            source = module / "sources" / "resident.c"
            source.parent.mkdir()
            source.write_text("int resident(void) { return 1; }\n", encoding="utf-8")
            write_tsv(
                module / "c_sources.tsv",
                runtime_injector.C_SOURCE_FIELDS,
                [{
                    "source_id": "resident",
                    "language": "c",
                    "path": "sources/resident.c",
                    "namespace": "test.resident",
                }],
            )
            first = module_content_sha256(module, "runtime_injector")
            source.write_text("int resident(void) { return 2; }\n", encoding="utf-8")
            self.assertNotEqual(
                first, module_content_sha256(module, "runtime_injector")
            )

    def test_current_profile_loads(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        profile_directory = repository / "na228_builder" / "profiles" / "current"
        marker = repository / "na228_builder" / "release_manifest.json"
        load_profile(
            profile_directory,
            repository,
            root_overrides={"na2": marker, "nun5": marker},
        )

    def test_registered_module_readmes_declare_downstream_invocations(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        modules_root = repository / "na228_builder" / "modules"
        for module_type in MODULE_TYPE_ORDER:
            readme = modules_root / module_type / "README.md"
            text = readme.read_text(encoding="utf-8")
            self.assertIn("## Invokes\n", text, module_type)
            declaration = text.split("## Invokes\n", 1)[1].split("\n## ", 1)[0].strip()
            self.assertTrue(declaration, module_type)


if __name__ == "__main__":
    unittest.main()
