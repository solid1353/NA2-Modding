from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.modules.binary_patcher import engine as binary_patcher
from na228_builder.scripts import catalog as catalog_module
from na228_builder.scripts import catalog_format
from na228_builder.scripts.configuration import (
    load_configuration,
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
        source = root / "source"
        configurations = root / "configurations"
        build = root / "build"
        pcsx2 = root / "pcsx2"
        write_tsv(
            root / "modules" / "targets.tsv",
            binary_patcher.TARGET_FIELDS,
            [],
        )
        localization = root / "patches" / "localization" / "enabled"
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
                    "roots": {
                        "source": "source",
                        "build": "build",
                        "pcsx2_files": "pcsx2",
                        "pcsx2_input_profiles": "pcsx2/input_profiles",
                        "pcsx2_memory_cards": "pcsx2/memory_cards",
                    },
                    "files": {
                        "placeholder": "placeholder",
                        "source_catalog": "games.json",
                        "project_settings": "game.json",
                    },
                }
            ),
            encoding="utf-8",
        )
        (root / "games.json").write_text(
            json.dumps(
                {
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
        module = feature
        module.mkdir(parents=True, exist_ok=True)
        if module_type == "translation_importer":
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
        feature = builder / "patches" / feature_id / "enabled"
        feature.mkdir(parents=True, exist_ok=True)
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
        configuration = configurations / f"{configuration_id}.jsonc"
        patches_root = root / "patches"
        patches_root.mkdir(parents=True, exist_ok=True)
        patches: dict[str, dict[str, object]] = {}
        parsed_features: dict[str, catalog_format.ContainerNode] = {}
        for feature_id, feature in catalog.items():
            if not isinstance(feature, dict):
                raise ValueError("Test catalog feature must be an object")
            description = feature.get("description", f"{feature_id} feature")
            module_settings = feature.get("module_settings", {})
            if not isinstance(module_settings, dict):
                raise ValueError("Test module settings must be an object")
            enabled_patch_id = f"{feature_id}.enabled"
            temporary = root / f".{feature_id}.modcat"
            module_source_parts: list[str] = []
            for setting_id, module_type in module_settings.items():
                module_patch_id = f"{feature_id}.{setting_id}"
                module_source_parts.append(
                    f"  {setting_id}: setting {{\n"
                    f"    description: {json.dumps(f'Select {module_type}.')},\n"
                    f"    patch: {json.dumps(module_patch_id)},\n"
                    "  },\n"
                )
                self.create_module(
                    patches_root / feature_id / setting_id,
                    str(module_type),
                )
                patches[module_patch_id] = {
                    "description": f"Synthetic {setting_id}.",
                    "modules": [module_type],
                }
            module_source = "".join(module_source_parts)
            temporary.write_text(
                "{\n"
                f"  description: {json.dumps(description)},\n"
                "  enabled: setting {\n"
                f"    description: {json.dumps(description)},\n"
                f"    patch: {json.dumps(enabled_patch_id)},\n"
                "  },\n"
                f"{module_source}"
                "}\n",
                encoding="utf-8",
            )
            parsed_features[feature_id] = catalog_format.parse_catalog(temporary)
            temporary.unlink()
            enabled_inputs = patches_root / feature_id / "enabled"
            enabled_modules: list[str] = []
            if (enabled_inputs / "mappings.tsv").is_file():
                enabled_modules.append("translation_importer")
            if (enabled_inputs / "containers.tsv").is_file():
                enabled_modules.append("texture_patcher")
            enabled_modules = [
                module
                for module in enabled_modules
                if module not in module_settings.values()
            ]
            patches[enabled_patch_id] = (
                {"description": str(description), "modules": enabled_modules}
                if enabled_modules
                else {
                    "description": str(description),
                    "startup_fast_forward_frames": {"additive": 0},
                }
            )
        (root / "catalog.modcat").write_text(
            catalog_format.serialize_catalog(parsed_features, include_patches=True),
            encoding="utf-8",
        )
        by_file: dict[str, dict[str, object]] = {}
        for patch_id, definition in patches.items():
            by_file.setdefault(patch_id.split(".", 1)[0], {})[patch_id] = definition
        for stem, definitions in by_file.items():
            (patches_root / f"{stem}.json").write_text(
                json.dumps(definitions, indent=2) + "\n",
                encoding="utf-8",
            )
        (configurations / "base.jsonc").write_text(
            json.dumps(
                {
                    "features": {
                        feature_id: {
                            "enabled": True,
                            **{
                                setting_id: True
                                for setting_id in feature.get(
                                    "module_settings", {}
                                )
                            },
                        }
                        for feature_id, feature in catalog.items()
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
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "output_boot_path": "SLOP_NA2.28",
                    "launch_settings": {
                        "default": {
                            "startup_fast_forward_frames": 321,
                            "speed_after_startup": "turbo",
                        },
                        "practice": {
                            "startup_fast_forward_frames": 654,
                            "speed_after_startup": "normal",
                        },
                    },
                    "configurations": {configuration_id: "t"},
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

    def test_ui_setting_controls_texture_module(self) -> None:
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
                {
                    "localization": {
                        "description": "Localization",
                        "module_settings": {
                            "ui": "texture_patcher",
                        },
                    }
                },
                {"localization": {"ui": False}},
            )

            configuration = load_configuration(configuration_path, root, root)

            self.assertEqual(
                [item.module_id for item in configuration.modules],
                ["localization.translation_importer"],
            )

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
            helper = feature / "helper.py"
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
            self.assertIn((root / "catalog.modcat").resolve(), resources)
            self.assertIn(
                (root / "patches" / "localization.json").resolve(),
                resources,
            )
            self.assertIn(
                (root / "configurations" / "base.jsonc").resolve(), resources
            )
            self.assertIn(configuration.resolve(), resources)
            self.assertIn((feature / "mappings.tsv").resolve(), resources)
            self.assertIn(
                (builder / "modules" / "targets.tsv").resolve(),
                resources,
            )
            self.assertNotIn(helper.resolve(), resources)

    def test_loader_does_not_discover_modules_from_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, source, configurations = self.create_workspace(root)
            feature = builder / "patches" / "localization" / "enabled"
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
                "default": {
                    "startup_fast_forward_frames": 321,
                    "speed_after_startup": "turbo",
                },
                "tool_assisted": {"speed_after_startup": "normal"},
            }
            settings_path.write_text(
                json.dumps(settings, indent=2) + "\n", encoding="utf-8"
            )
            loaded = load_configuration(configuration, root, root)
            self.assertEqual(loaded.configuration_id, configuration.stem)

    def test_configuration_aliases_are_optional_unique_selectors(self) -> None:
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

            no_aliases = json.loads(json.dumps(original))
            no_aliases["configurations"] = {}
            settings_path.write_text(
                json.dumps(no_aliases, indent=2) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_configuration(configuration, root, root).configuration_id,
                "test",
            )

            duplicate_alias = json.loads(json.dumps(original))
            duplicate_alias["configurations"] = {"base": "x", "test": "x"}
            settings_path.write_text(
                json.dumps(duplicate_alias, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate configuration alias"):
                load_configuration(configuration, root, root)

            invalid_alias = json.loads(json.dumps(original))
            invalid_alias["configurations"] = {"test": "not valid"}
            settings_path.write_text(
                json.dumps(invalid_alias, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid alias"):
                load_configuration(configuration, root, root)

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
                (builder / "patches" / "localization" / "enabled" / name).resolve()
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
            patches_path = root / "patches" / "localization.json"
            patches = json.loads(patches_path.read_text(encoding="utf-8"))
            patches["localization.enabled"]["hooks"] = {"runtime": {}}
            patches["localization.enabled"]["payload"] = {
                "runtime_asm": {
                    "kind": "asm",
                    "path": "src/runtime.S",
                    "namespace": "runtime.asm",
                    "imports": {},
                    "fragments": {
                        "runtime_code": {
                            "object": "runtime.asm.text",
                        }
                    },
                }
            }
            patches_path.write_text(
                json.dumps(patches, indent=2) + "\n", encoding="utf-8"
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
