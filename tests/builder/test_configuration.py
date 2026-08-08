from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.modules.binary_patcher import engine as binary_patcher
from na228_builder.modules.runtime_injector import engine as runtime_injector
from na228_builder.scripts.composer import resolve_module_order
from na228_builder.scripts.configuration import (
    MODULE_TYPE_ORDER,
    load_configuration,
    module_content_sha256,
    configuration_resource_files,
)


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class ConfigurationTests(unittest.TestCase):
    def create_workspace(self, root: Path) -> tuple[Path, Path, Path]:
        localization = root / "localization"
        source = root / "source"
        configurations = root / "configurations"
        build = root / "build"
        pcsx2 = root / "pcsx2"
        localization.mkdir()
        write_tsv(root / "targets.tsv", binary_patcher.TARGET_FIELDS, [])
        self.create_module(localization, "translation_importer")
        self.create_module(localization, "texture_patcher")
        source.mkdir()
        configurations.mkdir()
        build.mkdir()
        for directory in (
            "cheats",
            "game_settings",
            "input_profiles",
            "memory_cards",
        ):
            (pcsx2 / directory).mkdir(parents=True)
        (root / "paths.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "roots": {
                        "repository": ".",
                        "source": "source",
                        "build": "build",
                        "pcsx2_cheats": "pcsx2/cheats",
                        "pcsx2_game_settings": "pcsx2/game_settings",
                        "pcsx2_input_profiles": "pcsx2/input_profiles",
                        "pcsx2_memory_cards": "pcsx2/memory_cards",
                    },
                    "files": {
                        "placeholder": "placeholder",
                        "game_catalog": "games.json",
                        "product_config": "product.json",
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "games.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "sources": {
                        "NA2": {
                            "serial": "SLPS-25837",
                            "crc": "C0659AD1",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        return root, source, configurations

    def create_module(self, feature: Path, module_type: str) -> Path:
        module = feature / module_type
        module.mkdir(parents=True, exist_ok=True)
        if module_type == "binary_patcher":
            targets = feature.parent / "targets.tsv"
            if not targets.is_file():
                write_tsv(targets, binary_patcher.TARGET_FIELDS, [])
            write_tsv(module / "groups.tsv", binary_patcher.GROUP_FIELDS, [])
            write_tsv(module / "patches.tsv", binary_patcher.PATCH_FIELDS, [])
            write_tsv(module / "edits.tsv", binary_patcher.EDIT_FIELDS, [])
        elif module_type == "runtime_injector":
            targets = feature.parent / "targets.tsv"
            if not targets.is_file():
                write_tsv(targets, runtime_injector.TARGET_FIELDS, [])
            for name, fields in (
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

    def create_feature_inputs(
        self, builder: Path, feature_id: str, *module_types: str
    ) -> Path:
        feature = builder / feature_id
        feature.mkdir(exist_ok=True)
        for module_type in module_types:
            self.create_module(feature, module_type)
        return feature

    def create_configuration(
        self,
        configurations: Path,
        source: Path,
        catalog: dict[str, object],
        selection: dict[str, object],
        *,
        configuration_id: str = "test",
    ) -> Path:
        root = configurations.parent
        configuration = configurations / f"{configuration_id}.json"
        (root / "catalog.json").write_text(
            json.dumps({"features": catalog}, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in ("edits.json", "injections.json"):
            (root / name).write_text("{}\n", encoding="utf-8")
        configuration.write_text(
            json.dumps({"features": selection, "overrides": {}}, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "inputs": {"na2": "source"},
                    "identity": {
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
                    "builds": {"latest": {"postfix": "Latest"}},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return configuration

    def test_configuration_derives_identity_modules_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            self.create_feature_inputs(
                builder,
                "localization",
                "translation_importer",
                "texture_patcher",
            )
            configuration_path = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            configuration = load_configuration(configuration_path, root, root)
            self.assertEqual(configuration.configuration_id, "test")
            self.assertEqual(
                [item.feature_id for item in configuration.features], ["localization"]
            )
            self.assertEqual(
                [item.module_id for item in configuration.modules],
                [
                    "localization.translation_importer",
                    "localization.texture_patcher",
                ],
            )
            self.assertEqual([item.order for item in configuration.modules], [1, 2])

    def test_configuration_definition_must_be_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, configurations = self.create_workspace(root)
            definition = configurations / "legacy.tsv"
            definition.write_text("feature_id\tenabled\n", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "not a JSON file"):
                load_configuration(definition, root, root)

    def test_disabled_catalog_only_feature_requires_no_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            self.create_feature_inputs(builder, "localization", "translation_importer")
            configuration = self.create_configuration(
                configurations,
                source,
                {
                    "localization": {"description": "Localization"},
                    "catalog_only": {"description": "Catalog-only leaf"},
                },
                {
                    "localization": True,
                    "catalog_only": False,
                },
            )
            loaded = load_configuration(configuration, root, root)
            self.assertFalse((builder / "catalog_only").exists())
            self.assertEqual(loaded.features[1].module_ids, ())

    def test_resources_include_only_canonical_configuration_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            feature = self.create_feature_inputs(
                builder, "localization", "translation_importer"
            )
            helper = feature / "translation_importer" / "helper.py"
            helper.write_text("raise SystemExit\n", encoding="utf-8")
            configuration = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            loaded = load_configuration(configuration, root, root)
            resources = set(configuration_resource_files(loaded))
            self.assertIn((root / "product.json").resolve(), resources)
            self.assertIn((root / "catalog.json").resolve(), resources)
            self.assertIn((root / "edits.json").resolve(), resources)
            self.assertIn((root / "injections.json").resolve(), resources)
            self.assertIn(configuration.resolve(), resources)
            self.assertIn((feature / "translation_importer" / "mappings.tsv").resolve(), resources)
            self.assertIn((builder / "targets.tsv").resolve(), resources)
            self.assertNotIn(helper.resolve(), resources)

    def test_loader_does_not_discover_modules_from_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            feature = builder / "localization"
            (feature / "unknown").mkdir()
            self.create_module(feature, "translation_importer")
            configuration = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            loaded = load_configuration(configuration, root, root)
            self.assertEqual(
                [module.module_id for module in loaded.modules],
                [
                    "localization.translation_importer",
                    "localization.texture_patcher",
                ],
            )

    def test_loader_does_not_enumerate_builder_metadata_as_feature_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            feature = self.create_feature_inputs(
                builder, "localization", "translation_importer"
            )
            (feature / "manifest.tsv").write_text("key\tvalue\n", encoding="utf-8")
            configuration = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            loaded = load_configuration(configuration, root, root)
            resources = set(configuration_resource_files(loaded))
            self.assertNotIn((feature / "manifest.tsv").resolve(), resources)

    def test_importer_uses_derived_string_consumer_without_string_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            self.create_feature_inputs(builder, "localization", "translation_importer")
            configuration = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            loaded = load_configuration(configuration, root, root)
            self.assertEqual(resolve_module_order(loaded.modules), loaded.modules)

    def test_configuration_identity_requires_equal_length_boot_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            self.create_feature_inputs(builder, "localization", "translation_importer")
            configuration = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Localization"}},
                {"localization": True},
            )
            product_path = root / "product.json"
            product = json.loads(product_path.read_text(encoding="utf-8"))
            product["identity"]["image"]["output_boot_path"] = "BOOT.ELF"
            product_path.write_text(json.dumps(product, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "equal byte lengths"):
                load_configuration(configuration, root, root)

    def test_binary_hash_ignores_helpers_but_includes_referenced_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "feature"
            feature.mkdir()
            module = self.create_module(feature, "binary_patcher")
            first = module_content_sha256(module, "binary_patcher")
            (module / "helper.py").write_text("print('one')\n", encoding="utf-8")
            self.assertEqual(first, module_content_sha256(module, "binary_patcher"))
            targets = feature.parent / "targets.tsv"
            targets.write_text(
                targets.read_text(encoding="utf-8")
                + "boot\tna2\tdestination\tSLPS_258.37\t16\t"
                + "0" * 64
                + "\n",
                encoding="utf-8",
            )
            self.assertNotEqual(
                first, module_content_sha256(module, "binary_patcher")
            )
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

    def test_release_configuration_loads(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        configuration_path = (
            repository / "na228_builder" / "configurations" / "release.json"
        )
        marker = repository / "na228_builder" / "release_manifest.json"
        loaded = load_configuration(
            configuration_path,
            repository,
            repository / "na228_builder",
            root_overrides={"na2": marker, "nun5": marker},
        )
        self.assertEqual(
            [module.module_id for module in loaded.modules],
            [
                "localization.translation_importer",
                "localization.runtime_injector",
                "localization.texture_patcher",
                "localization.binary_patcher",
                "qol.runtime_injector",
                "qol.binary_patcher",
                "battle_logic.binary_patcher",
                "rendering.binary_patcher",
            ],
        )
        features_root = repository / "na228_builder" / "features"
        self.assertFalse(features_root.exists())

    def test_complete_release_resources_include_disabled_feature_inputs(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        builder_root = repository / "na228_builder"
        default_path = builder_root / "configurations" / "release.json"
        configuration = json.loads(default_path.read_text(encoding="utf-8"))
        configuration["overrides"] = {
            "features": {"localization": False}
        }
        marker = builder_root / "release_manifest.json"
        texture_root = builder_root / "localization" / "texture_patcher"
        texture_files = {
            (texture_root / name).resolve()
            for name in ("containers.tsv", "mappings.tsv", "strategies.tsv")
        }

        with tempfile.TemporaryDirectory() as directory:
            configuration_path = (
                Path(directory) / "Narutimate Accel v2.28.json"
            )
            configuration_path.write_text(
                json.dumps(configuration, indent=2) + "\n",
                encoding="utf-8",
            )
            loaded = load_configuration(
                configuration_path,
                repository,
                builder_root,
                root_overrides={"na2": marker, "nun5": marker},
            )
            self.assertEqual(loaded.configuration_id, "Narutimate Accel v2.28")
            selected = set(configuration_resource_files(loaded))
            complete = set(
                configuration_resource_files(loaded, include_disabled=True)
            )

        self.assertTrue(texture_files.isdisjoint(selected))
        self.assertTrue(texture_files <= complete)
        operations_root = builder_root / "modules" / "binary_patcher" / "operations"
        self.assertEqual(
            {path.resolve() for path in operations_root.glob("*.tsv")},
            {path for path in complete if path.parent == operations_root.resolve()},
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
