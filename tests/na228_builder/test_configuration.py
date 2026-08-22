from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.modules.binary_patcher import engine as binary_patcher
from na228_builder.scripts import catalog as catalog_module
from na228_builder.scripts import catalog_format
from na228_builder.scripts.composer import resolve_module_order
from na228_builder.scripts.configuration import (
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
        write_tsv(
            root / "catalog" / "targets.tsv",
            binary_patcher.TARGET_FIELDS,
            [],
        )
        self.create_module(localization, "translation_importer")
        self.create_module(localization, "texture_patcher")
        source.mkdir()
        (source / "NA2.iso.files").mkdir()
        (source / "NUN5.iso.files").mkdir()
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
                        "pcsx2_files": "pcsx2",
                        "pcsx2_cheats": "pcsx2/cheats",
                        "pcsx2_game_settings": "pcsx2/game_settings",
                        "pcsx2_input_profiles": "pcsx2/input_profiles",
                        "pcsx2_memory_cards": "pcsx2/memory_cards",
                    },
                    "files": {
                        "placeholder": "placeholder",
                        "game_catalog": "games.json",
                        "settings": "game.json",
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
                        },
                        "NUN5": {
                            "serial": "SLES-55605",
                            "crc": "C071D4C1",
                        },
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
            targets = feature.parent / "catalog" / "targets.tsv"
            if not targets.is_file():
                write_tsv(targets, binary_patcher.TARGET_FIELDS, [])
            write_tsv(module / "groups.tsv", binary_patcher.GROUP_FIELDS, [])
            write_tsv(module / "patches.tsv", binary_patcher.PATCH_FIELDS, [])
            write_tsv(module / "edits.tsv", binary_patcher.EDIT_FIELDS, [])
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
        catalog_root = root / "catalog"
        catalog_root.mkdir(parents=True, exist_ok=True)
        injections: dict[str, object] = {}
        parsed_features: dict[str, catalog_format.ContainerNode] = {}
        for feature_id, feature in catalog.items():
            if not isinstance(feature, dict):
                raise ValueError("Test catalog feature must be an object")
            description = feature.get("description", f"{feature_id} feature")
            injection_id = f"i__{feature_id}__enabled"
            temporary = catalog_root / f".{feature_id}.modcat"
            temporary.write_text(
                "{\n"
                f"  description: {json.dumps(description)},\n"
                "  enabled: setting {\n"
                f"    description: {json.dumps(description)},\n"
                f"    patches: [{json.dumps(injection_id)}],\n"
                "  },\n"
                "}\n",
                encoding="utf-8",
            )
            parsed_features[feature_id] = catalog_format.parse_catalog(temporary)
            temporary.unlink()
            injections[injection_id] = {"description": str(description)}
        (catalog_root / "catalog.modcat").write_text(
            catalog_format.serialize_catalog(parsed_features, include_patches=True),
            encoding="utf-8",
        )
        (catalog_root / "edits.json").write_text("{}\n", encoding="utf-8")
        (catalog_root / "injections.json").write_text(
            json.dumps(injections, indent=2) + "\n", encoding="utf-8"
        )
        (catalog_root / "string_patches.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (configurations / "base.json").write_text(
            json.dumps(
                {
                    "features": {
                        feature_id: {"enabled": True}
                        for feature_id in catalog
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        normalized_selection = {
            feature_id: {"enabled": value}
            if isinstance(value, bool)
            else value
            for feature_id, value in selection.items()
        }
        configuration.write_text(
            json.dumps({"overrides": normalized_selection}, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "game.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "output_boot_path": "SLOP_NA2.28",
                    "launch_settings": {
                        "startup_fast_forward_frames": 321,
                        "practice": {"startup_fast_forward_frames": 654},
                    },
                    "builds": {
                        "latest": {
                            "configuration": configuration_id,
                            "rotate_to": "previous",
                        },
                        "previous": {},
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return configuration

    def test_configuration_derives_modules_and_order(self) -> None:
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
            catalog_only = next(
                feature
                for feature in loaded.features
                if feature.feature_id == "catalog_only"
            )
            self.assertEqual(catalog_only.module_ids, ())

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
            self.assertIn((root / "game.json").resolve(), resources)
            self.assertIn((root / "catalog" / "catalog.modcat").resolve(), resources)
            self.assertIn(
                (root / "catalog" / "edits.json").resolve(),
                resources,
            )
            self.assertIn(
                (root / "catalog" / "injections.json").resolve(),
                resources,
            )
            self.assertIn(
                (root / "catalog" / "string_patches.json").resolve(),
                resources,
            )
            self.assertIn(
                (root / "configurations" / "base.json").resolve(), resources
            )
            self.assertIn(configuration.resolve(), resources)
            self.assertIn((feature / "translation_importer" / "mappings.tsv").resolve(), resources)
            self.assertIn(
                (builder / "catalog" / "targets.tsv").resolve(),
                resources,
            )
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

    def test_output_boot_path_must_preserve_source_length(self) -> None:
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
            settings_path = root / "game.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["output_boot_path"] = "BOOT.ELF"
            settings_path.write_text(
                json.dumps(settings, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "byte length"):
                load_configuration(configuration, root, root)

    def test_launch_settings_accept_open_direct_profile_overrides(self) -> None:
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
            settings_path = root / "game.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["launch_settings"] = {
                "startup_fast_forward_frames": 321,
                "tool_assisted": {},
            }
            settings_path.write_text(
                json.dumps(settings, indent=2) + "\n", encoding="utf-8"
            )
            loaded = load_configuration(configuration, root, root)
            self.assertEqual(loaded.configuration_id, configuration.stem)

    def test_build_targets_require_composition_and_valid_rotation(self) -> None:
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
            settings_path = root / "game.json"
            original = json.loads(settings_path.read_text(encoding="utf-8"))

            missing_composition = json.loads(json.dumps(original))
            del missing_composition["builds"]["latest"]["configuration"]
            settings_path.write_text(
                json.dumps(missing_composition, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "requires a configuration"):
                load_configuration(configuration, root, root)

            unknown_rotation = json.loads(json.dumps(original))
            unknown_rotation["builds"]["latest"]["rotate_to"] = "missing"
            settings_path.write_text(
                json.dumps(unknown_rotation, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "rotates to unknown target"):
                load_configuration(configuration, root, root)

            unconfigured_rotation = json.loads(json.dumps(original))
            del unconfigured_rotation["builds"]["latest"]["configuration"]
            unconfigured_rotation["builds"]["previous"]["rotate_to"] = "latest"
            settings_path.write_text(
                json.dumps(unconfigured_rotation, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "requires a configuration"):
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
            targets = (
                feature.parent
                / "catalog"
                / "targets.tsv"
            )
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

    def test_complete_resources_include_disabled_feature_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            configuration_path = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Optional localization"}},
                {"localization": False},
            )
            loaded = load_configuration(
                configuration_path,
                root,
                builder,
            )
            selected = set(configuration_resource_files(loaded))
            complete = set(
                configuration_resource_files(loaded, include_disabled=True)
            )
            optional_inputs = {
                (builder / "localization" / "texture_patcher" / name).resolve()
                for name in ("containers.tsv", "mappings.tsv", "strategies.tsv")
            }
            self.assertTrue(optional_inputs.isdisjoint(selected))
            self.assertTrue(optional_inputs <= complete)

    def test_assembly_source_selection_and_hash_follow_catalog_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            configuration_path = self.create_configuration(
                configurations,
                source,
                {"localization": {"description": "Optional localization"}},
                {"localization": False},
            )
            assembly = root / "src" / "runtime.S"
            assembly.parent.mkdir()
            assembly.write_text("nop\n", encoding="ascii")
            injections_path = root / "catalog" / "injections.json"
            injections = json.loads(injections_path.read_text(encoding="utf-8"))
            injections["i__localization__enabled"]["hooks"] = {"runtime": {}}
            injections["i__localization__enabled"]["payload"] = {
                "runtime_asm": {
                    "kind": "asm",
                    "path": "src/runtime.S",
                    "namespace": "runtime.asm",
                    "imports": {},
                    "fragments": {
                        "runtime_code": {
                            "order": 1,
                            "object": "runtime.asm.text",
                        }
                    },
                }
            }
            injections_path.write_text(
                json.dumps(injections, indent=2) + "\n", encoding="utf-8"
            )

            disabled = load_configuration(configuration_path, root, builder)
            self.assertFalse(
                any(
                    module.module_id == "localization.runtime_injector"
                    for module in disabled.modules
                )
            )

            configuration_path.write_text(
                json.dumps(
                    {"overrides": {"localization": {"enabled": True}}},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            first = load_configuration(configuration_path, root, builder)
            runtime = next(
                module
                for module in first.modules
                if module.module_id == "localization.runtime_injector"
            )
            self.assertIn(
                assembly.resolve(),
                set(
                    catalog_module.referenced_files(
                        first.selection, root, "localization"
                    )
                ),
            )
            assembly.write_text("nop\nnop\n", encoding="ascii")
            second = load_configuration(configuration_path, root, builder)
            changed = next(
                module
                for module in second.modules
                if module.module_id == "localization.runtime_injector"
            )
            self.assertNotEqual(runtime.input_sha256, changed.input_sha256)

if __name__ == "__main__":
    unittest.main()
