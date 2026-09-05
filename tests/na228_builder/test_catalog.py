from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.modules.binary_patcher import adapters
from na228_builder.scripts import catalog, catalog_format, jsonc
from scripts.lib.paths import load_local_paths


PATCH_ID = re.compile(r'patch:\s*"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)"')


class CatalogTests(unittest.TestCase):
    def write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def write_project(
        self,
        root: Path,
        sources: dict[str, str],
        features: dict[str, object],
        *,
        edits: dict[str, object] | None = None,
        injections: dict[str, object] | None = None,
        string_patches: dict[str, object] | None = None,
        patch_definitions: dict[str, object] | None = None,
    ) -> tuple[Path, Path]:
        catalog_path = root / "catalog.modcat"
        patches_path = root / "patches"
        patches_path.mkdir(parents=True)
        (root / "modules").mkdir()
        referenced = {
            patch for source in sources.values() for patch in PATCH_ID.findall(source)
        }
        patches: dict[str, dict[str, object]] = {
            patch: {"modules": ["binary_patcher"]}
            for patch in sorted(referenced)
        }
        for patch_id, definition in (edits or {}).items():
            assert isinstance(definition, dict)
            target = patches.setdefault(patch_id, {})
            description = definition.get("description")
            if description:
                target["description"] = description
            if "edits" in definition:
                target.update(
                    {
                        key: value
                        for key, value in definition.items()
                        if key != "description"
                    }
                )
            else:
                target["edit"] = {
                    key: value
                    for key, value in definition.items()
                    if key != "description"
                }
        for patch_id, definition in (injections or {}).items():
            assert isinstance(definition, dict)
            target = patches.setdefault(patch_id, {})
            for key in ("description", "hooks", "payload"):
                if key in definition:
                    target[key] = definition[key]
        for patch_id, definition in (string_patches or {}).items():
            assert isinstance(definition, dict)
            target = patches.setdefault(patch_id, {})
            target["string_patch"] = definition
        for patch_id, definition in (patch_definitions or {}).items():
            assert isinstance(definition, dict)
            patches.setdefault(patch_id, {}).update(definition)
        parsed_features: dict[str, catalog_format.ContainerNode] = {}
        for feature_id, source in sources.items():
            temporary = root / f".{feature_id}.modcat"
            temporary.write_text(source, encoding="utf-8")
            parsed_features[feature_id] = catalog_format.parse_catalog(temporary)
            temporary.unlink()
        catalog_path.write_text(
            catalog_format.serialize_catalog(parsed_features, include_patches=True),
            encoding="utf-8",
        )
        by_file: dict[str, dict[str, object]] = {}
        for patch_id, definition in patches.items():
            by_file.setdefault(patch_id.split(".", 1)[0], {})[patch_id] = definition
        for stem, definitions in by_file.items():
            self.write_json(patches_path / f"{stem}.json", definitions)
        self.write_json(
            root / "configurations" / "base.jsonc",
            {"features": features},
        )
        configuration_path = root / "configuration.jsonc"
        self.write_json(configuration_path, {"overrides": {}})
        return catalog_path, configuration_path

    def test_complete_minimal_grammar_and_type_matching(self) -> None:
        source = r'''
        {
          // Plain switch.
          plain: setting {
            description: "Plain setting.",
            patch: "feature.plain",
          },
          supplied_bool: setting<{ value: bool, label?: string, }> {
            description: "Boolean data wrapped in an object.",
            patch: "feature.supplied_bool",
          },
          patch_and_module: setting {
            description: "Patch-backed internal module.",
            patch: "feature.patch_and_module",
          },
          numeric: setting<(int & 1..15) | (decimal & >0 & <1)> {
            description: "Disjoint numeric union.",
            patch: "feature.numeric",
          },
          alternative:
            setting<int> {
              description: "Direct integer.",
              patch: "feature.direct",
            }
            |
            {
              ratio: setting<{ numerator: int & >0, denominator: int & >0 }> {
                description: "Named ratio.",
                patch: "feature.ratio",
              },
            },
        }
        '''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(source, encoding="utf-8")
            parsed = catalog_format.parse_catalog(path)

        fields = {field.name: field.node for field in parsed.fields}
        self.assertEqual(fields["plain"].patch, "feature.plain")
        self.assertEqual(fields["patch_and_module"].patch, "feature.patch_and_module")
        self.assertTrue(catalog_format.matches_type(fields["numeric"].value_type, 5))
        self.assertTrue(catalog_format.matches_type(fields["numeric"].value_type, 0.5))
        self.assertFalse(catalog_format.matches_type(fields["numeric"].value_type, 16))
        supplied = fields["supplied_bool"]
        self.assertTrue(catalog_format.matches_type(supplied.value_type, {"value": False}))
        self.assertFalse(
            catalog_format.matches_type(
                supplied.value_type, {"value": False, "extra": True}
            )
        )
        rendered = catalog_format.serialize_catalog(
            {"feature": parsed}, include_patches=False
        )
        embedded = catalog_format.serialize_catalog(
            {"feature": parsed}, include_patches=True
        )
        self.assertIn("\n      |\n      {\n", rendered)
        self.assertNotIn("patch:", rendered)
        self.assertIn('patch: "feature.patch_and_module"', embedded)

    def test_startup_fast_forward_frames_combine_one_override_and_additives(
        self,
    ) -> None:
        source = '''{
          baseline: setting {
            description: "Baseline.",
            patch: "feature.baseline",
          },
          extra: setting {
            description: "Extra.",
            patch: "feature.extra",
          },
          disabled_override: setting {
            description: "Disabled override.",
            patch: "feature.disabled_override",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {
                    "feature": {
                        "baseline": True,
                        "extra": True,
                        "disabled_override": False,
                    }
                },
                patch_definitions={
                    "feature.baseline": {
                        "startup_fast_forward_frames": {
                            "override": 100,
                            "additive": 5,
                        }
                    },
                    "feature.extra": {
                        "startup_fast_forward_frames": {"additive": -20}
                    },
                    "feature.disabled_override": {
                        "startup_fast_forward_frames": {"override": 999}
                    },
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertEqual(
                catalog.startup_fast_forward_frames(selection, 40),
                85,
            )
            self.assertEqual(
                catalog.load_startup_fast_forward_frames(
                    catalog_path, configuration_path, 40
                ),
                85,
            )

            self.write_json(
                root / "configurations" / "base.jsonc",
                {
                    "features": {
                        "feature": {
                            "baseline": False,
                            "extra": True,
                            "disabled_override": False,
                        }
                    }
                },
            )
            negative = catalog.load_selection(catalog_path, configuration_path)
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                "Resolved startup_fast_forward_frames must be a UInt64 integer; "
                "got -10",
            ):
                catalog.startup_fast_forward_frames(negative, 10)

            self.write_json(
                root / "configurations" / "base.jsonc",
                {
                    "features": {
                        "feature": {
                            "baseline": True,
                            "extra": True,
                            "disabled_override": True,
                        }
                    }
                },
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                "Multiple enabled startup_fast_forward_frames overrides: "
                "feature.baseline, feature.disabled_override",
            ):
                catalog.load_selection(catalog_path, configuration_path)

    def test_startup_fast_forward_override_is_a_positive_uint64_integer(
        self,
    ) -> None:
        invalid_values = ("0", "-1", "1.5", str(1 << 64))
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                catalog_path, configuration_path = self.write_project(
                    root,
                    {"feature": '{ leaf: setting { patch: "feature.leaf" } }'},
                    {"feature": {"leaf": True}},
                )
                self.write_json(
                    root / "patches" / "feature.json",
                    {
                        "feature.leaf": {
                            "startup_fast_forward_frames": {
                                "override": json.loads(value)
                            }
                        }
                    },
                )
                with self.assertRaisesRegex(ValueError, "integer"):
                    catalog.load_selection(catalog_path, configuration_path)

    def test_object_intersection_shares_fields_across_union_branches(self) -> None:
        source = '''{
          startup:
            {
              faster_loading: setting {
                description: "Load faster.",
                patch: "feature.faster_loading",
              },
            }
            &
            (
              {
                skip_opening: setting {
                  description: "Skip opening.",
                  patch: "feature.skip_opening",
                },
              }
              |
              {
                savedata_loading: setting<"automatic"> {
                  description: "Load save automatically.",
                  patch: "feature.savedata_loading",
                },
              }
            ),
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {
                    "feature": {
                        "startup": {
                            "faster_loading": True,
                            "skip_opening": True,
                        }
                    }
                },
            )
            title = catalog.load_selection(catalog_path, configuration_path)
            self.assertTrue(
                title.node_enabled(
                    "features", "feature", "startup", "faster_loading"
                )
            )
            self.assertTrue(
                title.node_enabled(
                    "features", "feature", "startup", "skip_opening"
                )
            )

            self.write_json(
                root / "configurations" / "base.jsonc",
                {
                    "features": {
                        "feature": {
                            "startup": {
                                "faster_loading": True,
                                "savedata_loading": "automatic",
                            }
                        }
                    }
                },
            )
            direct = catalog.load_selection(catalog_path, configuration_path)
            self.assertTrue(
                direct.node_enabled(
                    "features", "feature", "startup", "faster_loading"
                )
            )
            self.assertTrue(
                direct.node_enabled(
                    "features", "feature", "startup", "savedata_loading"
                )
            )

            public = catalog.public_catalog(catalog_path)
            self.assertIn("\n      &\n", public)
            self.assertEqual(public.count("faster_loading:"), 1)

    def test_intersection_shared_overrides_merge_but_branch_overrides_are_atomic(
        self,
    ) -> None:
        source = '''{
          startup:
            {
              faster_loading: setting {
                description: "Load faster.",
                patch: "feature.faster_loading",
              },
            }
            &
            (
              {
                skip_intro: setting {
                  description: "Skip intro.",
                  patch: "feature.skip_intro",
                },
                skip_opening: setting {
                  description: "Skip opening.",
                  patch: "feature.skip_opening",
                },
              }
              |
              {
                savedata_loading: setting<"automatic"> {
                  description: "Load save automatically.",
                  patch: "feature.savedata_loading",
                },
                loading_screen: setting {
                  description: "Show loading screen.",
                  patch: "feature.loading_screen",
                },
              }
            ),
        }'''
        base = {
            "feature": {
                "startup": {
                    "faster_loading": True,
                    "savedata_loading": "automatic",
                    "loading_screen": True,
                }
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root, {"feature": source}, base
            )

            self.write_json(
                configuration_path,
                {
                    "overrides": {
                        "feature": {"startup": {"faster_loading": False}}
                    }
                },
            )
            shared_override = catalog.load_selection(
                catalog_path, configuration_path
            )
            self.assertFalse(
                shared_override.node_enabled(
                    "features", "feature", "startup", "faster_loading"
                )
            )
            self.assertTrue(
                shared_override.node_enabled(
                    "features", "feature", "startup", "savedata_loading"
                )
            )
            self.assertTrue(
                shared_override.node_enabled(
                    "features", "feature", "startup", "loading_screen"
                )
            )

            self.write_json(
                configuration_path,
                {
                    "overrides": {
                        "feature": {
                            "startup": {"savedata_loading": "automatic"}
                        }
                    }
                },
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError, "expected exactly one of"
            ):
                catalog.load_selection(catalog_path, configuration_path)

            self.write_json(
                configuration_path,
                {
                    "overrides": {
                        "feature": {
                            "startup": {
                                "skip_intro": False,
                                "skip_opening": True,
                            }
                        }
                    }
                },
            )
            branch_override = catalog.load_selection(
                catalog_path, configuration_path
            )
            self.assertTrue(
                branch_override.node_enabled(
                    "features", "feature", "startup", "faster_loading"
                )
            )
            self.assertFalse(
                branch_override.node_enabled(
                    "features", "feature", "startup", "skip_intro"
                )
            )
            self.assertTrue(
                branch_override.node_enabled(
                    "features", "feature", "startup", "skip_opening"
                )
            )

    def test_repository_configurations_select_startup_behavior(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        catalog_path = paths.path("builder", "catalog.modcat")
        configurations = paths.path("builder", "configurations")

        selections = {
            name: catalog.load_selection(
                catalog_path, configurations / f"{name}.jsonc"
            )
            for name in ("base", "test", "release")
        }
        test = selections["test"]
        self.assertTrue(
            test.node_enabled("features", "startup", "auto_loading")
        )
        self.assertTrue(
            test.node_enabled("features", "startup", "loading_screen")
        )
        for name in ("base", "release"):
            with self.subTest(configuration=name):
                self.assertTrue(
                    selections[name].node_enabled(
                        "features", "startup", "faster_loading"
                    )
                )
        self.assertTrue(
            test.node_enabled("features", "startup", "faster_loading")
        )
        expected_frames = {"base": 1160, "test": 1160, "release": 1160}
        for name, selection in selections.items():
            with self.subTest(configuration=name):
                self.assertEqual(
                    catalog.startup_fast_forward_frames(selection, 1760),
                    expected_frames[name],
                )

    def test_repository_practice_defaults_are_owned_by_settings(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        builder = paths.path("builder")
        catalog_path = builder / "catalog.modcat"
        base = jsonc.loads(
            (builder / "configurations" / "base.jsonc").read_text(encoding="utf-8")
        )
        self.assertEqual(
            base["features"]["settings"]["ingame"]["practice_mode"]
            ["opponent_settings"]["linked_attack"],
            "dont_use",
        )
        selection = catalog.load_selection(
            catalog_path, builder / "configurations" / "base.jsonc"
        )
        package = catalog.load_binary_package(
            selection,
            "practice",
            builder / "modules" / "targets.tsv",
            paths.repository,
            builder / "modules" / "binary_patcher" / "operations",
        )
        self.assertEqual(package.edits, [])
        self.assertIn("settings.ingame", selection.injections)

    def test_repository_simple_display_is_a_standalone_setting(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        builder = paths.path("builder")
        catalog_path = builder / "catalog.modcat"
        base = jsonc.loads(
            (builder / "configurations" / "base.jsonc").read_text(encoding="utf-8")
        )
        self.assertEqual(
            base["features"]["settings"]["simple_display"],
            "off",
        )

        for value, replacement_hex in (("off", "00000000"), ("on", "25186600")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                configuration = Path(directory) / "configuration.jsonc"
                configured = json.loads(json.dumps(base))
                configured["features"]["settings"]["simple_display"] = value
                configuration.write_text(json.dumps(configured), encoding="utf-8")
                selection = catalog.load_selection(catalog_path, configuration)
                package = catalog.load_binary_package(
                    selection,
                    "settings",
                    builder / "modules" / "targets.tsv",
                    paths.repository,
                    builder / "modules" / "binary_patcher" / "operations",
                )
                edit = next(
                    edit
                    for edit in package.edits
                    if edit.edit_id.endswith(".settings.simple_display")
                )
                self.assertEqual(edit.destination_offset, 0xE7BAC)
                self.assertEqual(edit.expected_hex, "25186600")
                self.assertEqual(edit.replacement_hex, replacement_hex)

    def test_object_intersection_rejects_duplicate_fields(self) -> None:
        source = '''{
          value:
            { duplicate: setting {
              description: "First.", patch: "feature.first",
            } }
            &
            { duplicate: setting {
              description: "Second.", patch: "feature.second",
            } },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(source, encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "intersected catalog objects repeat fields: duplicate",
            ):
                catalog_format.parse_catalog(path)

    def test_decimal_includes_integers_and_step_is_zero_anchored(self) -> None:
        source = '''{
          value: setting<decimal & 0..15 & step 0.25> {
            description: "Quarter-step value.",
            patch: "feature.value",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(source, encoding="utf-8")
            parsed = catalog_format.parse_catalog(path)

        value_type = parsed.fields[0].node.value_type
        for value in (0, 1, 1.25, 15):
            with self.subTest(accepted=value):
                self.assertTrue(catalog_format.matches_type(value_type, value))
        for value in (-0.25, 0.1, 1.1, 15.25):
            with self.subTest(rejected=value):
                self.assertFalse(catalog_format.matches_type(value_type, value))
        rendered = catalog_format.serialize_feature(parsed)
        self.assertIn("setting<decimal & 0..15 & step 0.25>", rendered)

        for invalid_type in (
            "decimal & step 0",
            "decimal & step -0.25",
            "decimal & 0.1..0.2 & step 1",
            "int | decimal",
        ):
            with (
                self.subTest(invalid_type=invalid_type),
                tempfile.TemporaryDirectory() as directory,
            ):
                invalid = Path(directory) / "invalid.modcat"
                invalid.write_text(
                    "{ value: setting<"
                    + invalid_type
                    + '> { description: "Invalid.", patch: "x.y" } }',
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    catalog_format.parse_catalog(invalid)

    def test_direct_boolean_setting_types_are_supported(self) -> None:
        for value_type in ("bool", "true", "false", 'string | false'):
            with self.subTest(value_type=value_type), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "feature.modcat"
                path.write_text(
                    "{ value: setting<"
                    + value_type
                    + '> { patch: "x.y" } }',
                    encoding="utf-8",
                )
                parsed = catalog_format.parse_catalog(path)
                self.assertEqual(parsed.fields[0].node.patch, "x.y")

    def test_overlapping_unions_are_rejected_at_catalog_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(
                '''{
                  value:
                    setting<int> {
                      description: "Any integer.", patch: "x.any",
                    }
                    |
                    setting<int & 1..3> {
                      description: "Small integer.", patch: "x.small",
                    },
                }''',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "branches 1 and 2 overlap"):
                catalog_format.parse_catalog(path)

    def test_false_disables_every_node_and_bool_remains_object_data(self) -> None:
        source = '''{
          plain: setting {
            description: "Plain.", patch: "feature.plain",
          },
          integer: setting<int> {
            description: "Integer.", patch: "feature.integer",
          },
          supplied_bool: setting<{ value: bool }> {
            description: "Supplied bool.", patch: "feature.bool",
          },
          alternative:
            setting<int> {
              description: "Direct.", patch: "feature.direct",
            }
            |
            { fixed: setting<int> {
              description: "Fixed.", patch: "feature.fixed",
            } },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {
                    "feature": {
                        "plain": True,
                        "integer": False,
                        "supplied_bool": {"value": False},
                        "alternative": False,
                    }
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)

        self.assertTrue(selection.node_enabled("features", "feature", "plain"))
        self.assertFalse(selection.node_enabled("features", "feature", "integer"))
        boolean_node = next(
            node for node in selection.nodes if node.node_id == "feature.supplied_bool"
        )
        self.assertTrue(boolean_node.enabled)
        self.assertEqual(boolean_node.configured_value, {"value": False})
        self.assertFalse(selection.node_enabled("features", "feature", "alternative"))

    def test_true_normalizes_to_empty_object_only_when_the_type_accepts_it(
        self,
    ) -> None:
        source = '''{
          optional: setting<{ count?: int }> {
            description: "Optional object.", patch: "f.optional",
          },
          required: setting<{ count: int }> {
            description: "Required object.", patch: "f.required",
          },
          alternative:
            setting<{ count?: int }> {
              description: "Optional branch.", patch: "f.branch_object",
            }
            |
            setting<"named"> {
              description: "Named branch.", patch: "f.branch_named",
            },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {
                    "feature": {
                        "optional": True,
                        "required": {"count": 1},
                        "alternative": True,
                    }
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            selected = {
                node.node_id: node
                for node in selection.nodes
                if node.node_id in {"feature.optional", "feature.alternative"}
            }
            self.assertEqual(selected["feature.optional"].configured_value, {})
            self.assertEqual(selected["feature.alternative"].configured_value, {})

            self.write_json(
                root / "configurations" / "base.jsonc",
                {
                    "features": {
                        "feature": {
                            "optional": True,
                            "required": True,
                            "alternative": True,
                        }
                    }
                },
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                r"feature\.required: got true",
            ):
                catalog.load_selection(catalog_path, configuration_path)

    def test_containers_merge_recursively_but_settings_and_unions_are_atomic(self) -> None:
        source = '''{
          nested: {
            first: setting { description: "First.", patch: "f.first" },
            second: setting { description: "Second.", patch: "f.second" },
          },
          scalar: setting<int> {
            description: "Scalar.", patch: "f.scalar",
          },
          named:
            { pair: {
              left: setting<int> {
                description: "Left.", patch: "f.left",
              },
              right: setting<int> {
                description: "Right.", patch: "f.right",
              },
            } }
            |
            setting<string> {
              description: "Text.", patch: "f.text",
            },
        }'''
        base = {
            "feature": {
                "nested": {"first": True, "second": True},
                "scalar": 3,
                "named": {"pair": {"left": 1, "right": 2}},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root, {"feature": source}, base
            )
            self.write_json(
                configuration_path,
                {
                    "overrides": {
                        "feature": {
                            "nested": {"first": False},
                            "scalar": 7,
                            "named": "custom",
                        }
                    }
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            scalar = next(node for node in selection.nodes if node.node_id == "feature.scalar")
            text = next(node for node in selection.nodes if node.node_id == "feature.named")
            self.assertEqual(scalar.configured_value, 7)
            self.assertEqual(text.configured_value, "custom")
            self.assertFalse(
                selection.node_enabled("features", "feature", "nested", "first")
            )
            self.assertTrue(
                selection.node_enabled("features", "feature", "nested", "second")
            )

            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"named": {"pair": {"left": 9}}}}},
            )
            with self.assertRaisesRegex(ValueError, "does not match its setting type|exactly one"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_parent_true_and_invalid_typed_values_are_rejected(self) -> None:
        source = '''{
          nested: {
            leaf: setting { description: "Leaf.", patch: "f.leaf" },
          },
          integer: setting<int> {
            description: "Integer.", patch: "f.integer",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"nested": {"leaf": True}, "integer": 2}},
            )
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"nested": True}}},
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                "Invalid config value at features.feature.nested: "
                "got true; expected an object override, or false to disable it",
            ):
                catalog.load_selection(catalog_path, configuration_path)
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"integer": True}}},
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                "Invalid config value at features.feature.integer: "
                "got true; expected int, or false to disable it",
            ):
                catalog.load_selection(catalog_path, configuration_path)

            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"unknown": True}}},
            )
            with self.assertRaisesRegex(
                catalog.ConfigurationError,
                "Invalid config override at features.feature: unknown keys: unknown",
            ):
                catalog.load_selection(catalog_path, configuration_path)

            self.write_json(
                root / "configurations" / "base.jsonc",
                {"features": False},
            )
            self.write_json(configuration_path, {"overrides": {}})
            disabled = catalog.load_selection(catalog_path, configuration_path)
            self.assertFalse(disabled.node_enabled("features", "feature"))
            self.assertFalse(
                disabled.node_enabled("features", "feature", "nested", "leaf")
            )
            self.assertFalse(
                disabled.node_enabled("features", "feature", "integer")
            )

    def test_materialized_configuration_applies_repository_override(self) -> None:
        source = '''{
          first: setting { description: "First.", patch: "f.first" },
          second: setting { description: "Second.", patch: "f.second" },
          third: setting { description: "Third.", patch: "f.third" },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"first": True, "second": True, "third": True}},
            )
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"third": False}}},
            )
            materialized = catalog.materialized_configuration(
                catalog_path, configuration_path
            )
            self.assertEqual(
                materialized,
                {
                    "features": {
                        "feature": {
                            "first": True,
                            "second": True,
                            "third": False,
                        }
                    }
                },
            )
            bundled = root / "config.json"
            self.write_json(bundled, materialized)
            self.assertIsNone(
                catalog.load_selection(catalog_path, bundled).base_configuration_path
            )

    def test_descriptions_and_patch_references_are_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(
                '{ plain: setting {}, patched: setting { patch: "f.leaf" } }',
                encoding="utf-8",
            )
            parsed = catalog_format.parse_catalog(path)
            self.assertEqual(parsed.fields[0].node.description, "")
            self.assertIsNone(parsed.fields[0].node.patch)
            self.assertEqual(parsed.fields[1].node.patch, "f.leaf")

            path.write_text(
                '{ leaf: setting { description: "" } }',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "description must be nonempty"):
                catalog_format.parse_catalog(path)

    def test_unknown_and_orphaned_implementation_ids_are_rejected(self) -> None:
        source = '''{
          leaf: setting {
            description: "Leaf.", patch: "f.missing",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"leaf": True}},
            )
            patches_path = root / "patches" / "f.json"
            values = json.loads(patches_path.read_text(encoding="utf-8"))
            values.pop("f.missing")
            values["f.orphan"] = {"modules": ["binary_patcher"]}
            self.write_json(patches_path, values)
            with self.assertRaisesRegex(ValueError, "unknown patch"):
                catalog.load_selection(catalog_path, configuration_path)

            values["f.missing"] = {"modules": ["binary_patcher"]}
            self.write_json(patches_path, values)
            with self.assertRaisesRegex(ValueError, "not catalog-referenced"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_public_catalog_keeps_contract_and_strips_implementation(self) -> None:
        source = '''{
          value: setting<decimal & 0..15 & step 0.25> {
            description: "Bounded value.",
            patch: "f.value",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, _ = self.write_project(
                root,
                {"feature": source},
                {"feature": {"value": 5}},
                patch_definitions={
                    "f.value": {
                        "startup_fast_forward_frames": {"additive": 12}
                    }
                },
            )
            public = catalog.public_catalog(catalog_path)
        self.assertIn("features:", public)
        self.assertIn("setting<decimal & 0..15 & step 0.25>", public)
        self.assertIn('description: "Bounded value."', public)
        self.assertNotIn("patches", public)
        self.assertNotIn("startup_fast_forward_frames", public)
        self.assertNotIn("f.value", public)

    def test_mips_lui_float32_adapter_preserves_instruction_and_rejects_bad_guards(self) -> None:
        replacements = {
            quarter / 4: adapters.apply_adapter(
                "mips_lui_float32", "803F023C", quarter / 4
            )
            for quarter in range(61)
        }
        self.assertEqual(replacements[1], "803F023C")
        self.assertEqual(replacements[1.25], "A03F023C")
        self.assertEqual(replacements[3], "4040023C")
        self.assertEqual(replacements[15], "7041023C")
        self.assertTrue(all(value.endswith("023C") for value in replacements.values()))
        with self.assertRaisesRegex(ValueError, "cannot encode"):
            adapters.apply_adapter("mips_lui_float32", "803F023C", 0.1)
        with self.assertRaisesRegex(ValueError, "four-byte"):
            adapters.apply_adapter("mips_lui_float32", "803F", 3)
        with self.assertRaisesRegex(ValueError, "not a MIPS LUI"):
            adapters.apply_adapter("mips_lui_float32", "00000000", 3)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            adapters.apply_adapter("unknown", "803F023C", 3)

    def test_ascii_fixed_adapter_encodes_equal_length_values(self) -> None:
        expected, replacement = adapters.apply_fixed_adapter(
            "ascii_fixed",
            "BISLPS-25837NARUTO5",
            "BASLOP-NA228NARUTO6",
        )
        self.assertEqual(bytes.fromhex(expected), b"BISLPS-25837NARUTO5")
        self.assertEqual(bytes.fromhex(replacement), b"BASLOP-NA228NARUTO6")
        with self.assertRaisesRegex(ValueError, "equal encoded lengths"):
            adapters.apply_fixed_adapter("ascii_fixed", "short", "longer")
        with self.assertRaisesRegex(ValueError, "must be ASCII"):
            adapters.apply_fixed_adapter("ascii_fixed", "clean", "not ASCII: 日")

    def test_nul_padded_text_adapter_encodes_fixed_length_text(self) -> None:
        expected, replacement = adapters.apply_fixed_adapter(
            "nul_padded_text",
            "original",
            "ＮＡ",
            encoding="cp932",
            length=16,
        )
        self.assertEqual(len(bytes.fromhex(expected)), 16)
        self.assertEqual(len(bytes.fromhex(replacement)), 16)
        self.assertTrue(bytes.fromhex(expected).startswith(b"original\0"))
        self.assertTrue(bytes.fromhex(replacement).startswith("ＮＡ".encode("cp932") + b"\0"))
        with self.assertRaisesRegex(ValueError, "does not fit"):
            adapters.apply_fixed_adapter(
                "nul_padded_text",
                "exactly16bytes!!",
                "short",
                encoding="ascii",
                length=16,
            )
        with self.assertRaisesRegex(ValueError, "unknown"):
            adapters.apply_fixed_adapter(
                "nul_padded_text",
                "original",
                "replacement",
                encoding="not-a-codec",
                length=32,
            )
        with self.assertRaisesRegex(ValueError, "without a NUL"):
            adapters.apply_fixed_adapter(
                "nul_padded_text",
                "bad\0value",
                "replacement",
                encoding="ascii",
                length=32,
            )
        with self.assertRaisesRegex(ValueError, "not encodable"):
            adapters.apply_fixed_adapter(
                "nul_padded_text",
                "original",
                "🙂",
                encoding="cp932",
                length=32,
            )

    def test_string_patch_selection_is_explicit_and_disableable(self) -> None:
        source = '''{
          replace_title: setting {
            description: "Replace title.",
            patch: "feature.replace_title",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"replace_title": True}},
                string_patches={
                    "feature.replace_title": {
                        "description": "Replace imported title.",
                        "operation": "replace_imported_game_title",
                        "expected_value": "Imported Game",
                        "expected_mapping_count": 1,
                        "expected_occurrence_count": 1,
                    }
                },
            )
            enabled = catalog.load_selection(catalog_path, configuration_path)
            self.assertEqual(
                [item[1] for item in catalog.selected_string_patches(
                    enabled, "replace_imported_game_title"
                )],
                ["feature.replace_title"],
            )
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"replace_title": False}}},
            )
            disabled = catalog.load_selection(catalog_path, configuration_path)
            self.assertEqual(
                catalog.selected_string_patches(
                    disabled, "replace_imported_game_title"
                ),
                (),
            )

    def test_destination_offsets_require_nonempty_unique_values(self) -> None:
        self.assertEqual(
            catalog._parse_int_list(["0x10", "0x20"], "offsets"),
            (0x10, 0x20),
        )
        with self.assertRaisesRegex(ValueError, "non-empty integer list"):
            catalog._parse_int_list([], "offsets")
        with self.assertRaisesRegex(ValueError, "unique offsets"):
            catalog._parse_int_list(["0x10", "0x10"], "offsets")

    def test_destination_offset_forms_normalize_to_internal_lists(self) -> None:
        singular = {
            "operation": "replace",
            "destination_target_id": "test_target",
            "destination_offset": "0x10",
            "expected_hex": "00",
            "replacement_hex": "01",
        }
        plural = {
            **singular,
            "destination_offsets": ["0x10", "0x20"],
        }
        del plural["destination_offset"]

        singular_member = catalog._edit_members(
            "feature.singular", singular
        )[0][1]
        plural_member = catalog._edit_members(
            "feature.plural", plural
        )[0][1]

        self.assertNotIn("destination_offset", singular_member)
        self.assertEqual(singular_member["destination_offsets"], [0x10])
        self.assertEqual(plural_member["destination_offsets"], [0x10, 0x20])

    def test_destination_offset_forms_reject_ambiguous_or_redundant_input(
        self,
    ) -> None:
        definition = {
            "operation": "replace",
            "destination_target_id": "test_target",
            "destination_offset": "0x10",
            "expected_hex": "00",
            "replacement_hex": "01",
        }
        with self.assertRaisesRegex(
            ValueError,
            "exactly one of destination_offset or destination_offsets",
        ):
            catalog._edit_members(
                "feature.ambiguous",
                {**definition, "destination_offsets": ["0x10", "0x20"]},
            )
        with self.assertRaisesRegex(
            ValueError,
            "exactly one of destination_offset or destination_offsets",
        ):
            missing = dict(definition)
            del missing["destination_offset"]
            catalog._edit_members("feature.missing", missing)
        with self.assertRaisesRegex(ValueError, "must contain at least two"):
            redundant = dict(definition)
            del redundant["destination_offset"]
            redundant["destination_offsets"] = ["0x10"]
            catalog._edit_members("feature.redundant", redundant)

    def test_grouped_edit_expands_named_primitive_edits(self) -> None:
        source = '''{
          grouped: setting {
            description: "Grouped edits.",
            patch: "feature.grouped",
          },
        }'''
        grouped = {
            "description": "Three independently guarded operations.",
            "edits": {
                "set_values": {
                    "description": "Set two matching values.",
                    "operation": "replace",
                    "destination_target_id": "test_target",
                    "destination_offsets": ["0x0", "0x4"],
                    "expected_hex": "0000",
                    "replacement_hex": "3412",
                },
                "install_blob": {
                    "description": "Install one binary asset.",
                    "operation": "blob",
                    "destination_target_id": "test_target",
                    "destination_offset": "0xC",
                    "expected_sha256": "0" * 64,
                    "blob_path": "asset.bin",
                    "blob_sha256": hashlib.sha256(b"\xAA\xBB").hexdigest(),
                },
                "clear_flag": {
                    "description": "Clear one flag.",
                    "operation": "replace",
                    "destination_target_id": "test_target",
                    "destination_offset": "0x8",
                    "expected_hex": "01",
                    "replacement_hex": "00",
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"grouped": True}},
                edits={"feature.grouped": grouped},
            )
            (root / "asset.bin").write_bytes(b"\xAA\xBB")
            (catalog_path.parent / "modules" / "targets.tsv").write_text(
                "target_id\troot_id\trole\tpath\texpected_size\t"
                "expected_sha256\n"
                "test_target\ttest\tdestination\tdata.bin\t16\t"
                + "0" * 64
                + "\n",
                encoding="utf-8",
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
            package = catalog.load_binary_package(
                selection,
                "feature",
                catalog_path.parent / "modules" / "targets.tsv",
                root,
                paths.path("builder", "modules", "binary_patcher", "operations"),
            )
            referenced = catalog.referenced_files(selection, root, "feature")

        self.assertEqual(
            [edit.destination_offset for edit in package.edits],
            [0x8, 0xC, 0x0, 0x4],
        )
        self.assertEqual(
            [edit.operation for edit in package.edits],
            ["replace", "blob", "replace", "replace"],
        )
        self.assertTrue(all("feature.grouped" in edit.edit_id for edit in package.edits))
        self.assertIn(".clear_flag", package.edits[0].edit_id)
        self.assertIn(".install_blob", package.edits[1].edit_id)
        self.assertIn(".set_values", package.edits[2].edit_id)
        self.assertEqual(
            referenced,
            ((root / "asset.bin").resolve(),),
        )

    def test_replace_table_expands_fixed_stride_record_patches(self) -> None:
        source = '''{
          table: setting {
            description: "Table edit.",
            patch: "feature.table",
          },
        }'''
        table = {
            "description": "Patch synthetic table fields.",
            "operation": "replace_table",
            "destination_target_id": "test_target",
            "table_offset": "0x10",
            "record_stride": 8,
            "field_offset": 2,
            "record_patches": {
                "first": {
                    "record_index": 0,
                    "expected_hex": "0001",
                    "replacement_hex": "1001",
                },
                "shared": {
                    "record_indices": [2, 4],
                    "expected_hex": "0203",
                    "replacement_hex": "1203",
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"table": True}},
                edits={"feature.table": table},
            )
            (catalog_path.parent / "modules" / "targets.tsv").write_text(
                "target_id\troot_id\trole\tpath\texpected_size\t"
                "expected_sha256\n"
                "test_target\ttest\tdestination\tdata.bin\t64\t"
                + "0" * 64
                + "\n",
                encoding="utf-8",
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
            package = catalog.load_binary_package(
                selection,
                "feature",
                catalog_path.parent / "modules" / "targets.tsv",
                root,
                paths.path("builder", "modules", "binary_patcher", "operations"),
            )

        self.assertEqual(
            [edit.destination_offset for edit in package.edits],
            [0x12, 0x22, 0x32],
        )
        self.assertEqual(
            [edit.expected_hex for edit in package.edits],
            ["0001", "0203", "0203"],
        )
        self.assertEqual(
            [edit.replacement_hex for edit in package.edits],
            ["1001", "1203", "1203"],
        )
        self.assertTrue(all(edit.operation == "replace" for edit in package.edits))
        self.assertIn(".first", package.edits[0].edit_id)
        self.assertIn(".shared.at_00000022", package.edits[1].edit_id)

    def test_replace_table_rejects_invalid_record_contracts(self) -> None:
        valid = {
            "operation": "replace_table",
            "destination_target_id": "test_target",
            "table_offset": "0x10",
            "record_stride": 4,
            "field_offset": 0,
            "record_patches": {
                "first": {
                    "record_index": 0,
                    "expected_hex": "0000",
                    "replacement_hex": "1111",
                },
            },
        }
        invalid = (
            (
                {
                    **valid,
                    "record_patches": {
                        "first": {
                            "expected_hex": "0000",
                            "replacement_hex": "1111",
                        }
                    },
                },
                "requires exactly one of record_index or record_indices",
            ),
            (
                {
                    **valid,
                    "record_patches": {
                        "first": valid["record_patches"]["first"],
                        "second": {
                            "record_index": 0,
                            "expected_hex": "2222",
                            "replacement_hex": "3333",
                        },
                    },
                },
                "reuses table record indices",
            ),
            (
                {
                    **valid,
                    "record_patches": {
                        "first": {
                            "record_index": 0,
                            "expected_hex": "00",
                            "replacement_hex": "1111",
                        }
                    },
                },
                "expected/replacement length mismatch",
            ),
            (
                {**valid, "field_offset": 3},
                "field exceeds the 4-byte record stride",
            ),
        )
        for definition, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    catalog._edit_members("feature.table", definition)

    def test_grouped_edit_rejects_overlapping_child_destinations(self) -> None:
        source = '''{
          grouped: setting {
            description: "Grouped edits.",
            patch: "feature.grouped",
          },
        }'''
        grouped = {
            "description": "Invalid overlapping edits.",
            "edits": {
                "first": {
                    "operation": "replace",
                    "destination_target_id": "test_target",
                    "destination_offset": "0x0",
                    "expected_hex": "0000",
                    "replacement_hex": "1111",
                },
                "second": {
                    "operation": "replace",
                    "destination_target_id": "test_target",
                    "destination_offset": "0x1",
                    "expected_hex": "00",
                    "replacement_hex": "22",
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"grouped": True}},
                edits={"feature.grouped": grouped},
            )
            (catalog_path.parent / "modules" / "targets.tsv").write_text(
                "target_id\troot_id\trole\tpath\texpected_size\t"
                "expected_sha256\n"
                "test_target\ttest\tdestination\tdata.bin\t16\t"
                + "0" * 64
                + "\n",
                encoding="utf-8",
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
            with self.assertRaisesRegex(ValueError, "overlapping destination ranges"):
                catalog.load_binary_package(
                    selection,
                    "feature",
                    catalog_path.parent / "modules" / "targets.tsv",
                    root,
                    paths.path("builder", "modules", "binary_patcher", "operations"),
                )

    def test_repository_grouped_edit_maps_are_alphabetical(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        patch_files = sorted(paths.path("builder", "patches").glob("*.json"))
        self.assertTrue(patch_files)
        for patch_file in patch_files:
            definitions = json.loads(patch_file.read_text(encoding="utf-8"))
            for patch_id, definition in definitions.items():
                if "edits" not in definition and "edit" not in definition:
                    continue
                with self.subTest(patch_id=patch_id):
                    if "edits" in definition:
                        self.assertEqual(
                            list(definition["edits"]),
                            sorted(definition["edits"]),
                        )
                    members = (
                        definition["edits"].values()
                        if "edits" in definition
                        else (definition["edit"],)
                    )
                    for member in members:
                        if member.get("operation") == "replace_table":
                            self.assertEqual(
                                list(member["record_patches"]),
                                sorted(member["record_patches"]),
                            )

    def test_grouped_edit_structure_fails_closed(self) -> None:
        source = '''{
          grouped: setting {
            description: "Grouped edits.",
            patch: "feature.grouped",
          },
        }'''
        invalid_groups = (
            (
                {"description": "Null group.", "edits": None},
                "must be a non-empty object",
            ),
            (
                {"description": "Empty group.", "edits": {}},
                "must be a non-empty object",
            ),
            (
                {
                    "description": "Mixed group.",
                    "operation": "replace",
                    "edits": {"member": {"description": "Member."}},
                },
                "unknown fields",
            ),
            (
                {
                    "description": "Nested group.",
                    "edits": {
                        "member": {
                            "description": "Member.",
                            "edits": {"nested": {}},
                        }
                    },
                },
                "must be a primitive edit",
            ),
            (
                {
                    "description": "Invalid member ID.",
                    "edits": {"not-semantic": {"description": "Member."}},
                },
                "meaningful snake_case key",
            ),
            (
                {
                    "description": "Invalid member value.",
                    "edits": {"member": "not an object"},
                },
                "must be an object",
            ),
        )
        for grouped, message in invalid_groups:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                catalog_path, configuration_path = self.write_project(
                    root,
                    {"feature": source},
                    {"feature": {"grouped": True}},
                    edits={"feature.grouped": grouped},
                )
                with self.assertRaisesRegex(ValueError, message):
                    catalog.load_selection(catalog_path, configuration_path)

    def test_runtime_source_uses_packaged_object_without_toolchain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            source = repository / "runtime.c"
            source.write_text("void runtime(void) {}\n", encoding="utf-8")
            packaged_object = repository / "runtime.c.o"
            packaged_object.write_bytes(b"packaged object")
            extracted = catalog.ee_c_fragments.ExtractedEeObject(
                fragments=(
                    catalog.PayloadFragment(
                        owner="feature.runtime_injector",
                        symbol="runtime.text.second",
                        kind="code",
                        alignment=4,
                        payload=b"\0\0\0\0",
                    ),
                    catalog.PayloadFragment(
                        owner="feature.runtime_injector",
                        symbol="runtime.text.first",
                        kind="code",
                        alignment=4,
                        payload=b"\1\0\0\0",
                    ),
                ),
                symbols={},
            )
            value = {
                "kind": "c",
                "path": "runtime.c",
                "namespace": "runtime",
                "imports": {},
                "fragments": {
                    "runtime_first": {"object": "runtime.text.first"},
                    "runtime_second": {"object": "runtime.text.second"},
                },
            }
            with mock.patch.object(
                catalog.ee_c_fragments, "extract_ee_object", return_value=extracted
            ) as extract, mock.patch.object(
                catalog.ee_c_fragments, "compile_and_extract"
            ) as compile_source, mock.patch.object(
                catalog.ee_c_fragments, "default_toolchain_bin"
            ) as toolchain:
                fragments = catalog._compile_source(
                    repository,
                    "feature.runtime_injector",
                    "runtime_source",
                    value,
                    "feature.payload.runtime_source",
                )
            self.assertEqual(
                [fragment.symbol for fragment in fragments],
                ["runtime_first", "runtime_second"],
            )
            extract.assert_called_once_with(
                packaged_object.resolve(),
                namespace="runtime",
                owner="feature.runtime_injector",
                external_symbols={},
            )
            compile_source.assert_not_called()
            toolchain.assert_not_called()

    def test_runtime_assembly_uses_packaged_object_without_toolchain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            source = repository / "runtime.S"
            source.write_text("nop\n", encoding="ascii")
            packaged_object = repository / "runtime.S.o"
            packaged_object.write_bytes(b"packaged object")
            extracted = catalog.ee_c_fragments.ExtractedEeObject(
                fragments=(
                    catalog.PayloadFragment(
                        owner="feature.runtime_injector",
                        symbol="runtime.text.entry",
                        kind="code",
                        alignment=4,
                        payload=bytes(4),
                    ),
                ),
                symbols={},
            )
            value = {
                "kind": "asm",
                "path": "runtime.S",
                "namespace": "runtime",
                "imports": {},
                "fragments": {
                    "runtime_code": {
                        "object": "runtime.text.entry",
                    }
                },
            }
            with mock.patch.object(
                catalog.ee_c_fragments, "extract_ee_object", return_value=extracted
            ) as extract, mock.patch.object(
                catalog.ee_c_fragments, "compile_and_extract"
            ) as compile_source, mock.patch.object(
                catalog.ee_c_fragments, "default_toolchain_bin"
            ) as toolchain:
                fragments = catalog._compile_source(
                    repository,
                    "feature.runtime_injector",
                    "runtime_source",
                    value,
                    "feature.payload.runtime_source",
                )
            self.assertEqual(fragments[0].symbol, "runtime_code")
            extract.assert_called_once_with(
                packaged_object.resolve(),
                namespace="runtime",
                owner="feature.runtime_injector",
                external_symbols={},
            )
            compile_source.assert_not_called()
            toolchain.assert_not_called()

    def test_runtime_source_kind_and_suffix_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "runtime.c").write_text("nop\n", encoding="ascii")
            base = {
                "path": "runtime.c",
                "namespace": "runtime",
                "imports": {},
                "fragments": {
                    "runtime_code": {"object": "runtime.text"}
                },
            }
            with self.assertRaisesRegex(ValueError, "supported EE source language"):
                catalog._compile_source(
                    repository,
                    "feature.runtime_injector",
                    "runtime_source",
                    {**base, "kind": "code"},
                    "feature.payload.runtime_source",
                )
            with self.assertRaisesRegex(ValueError, "exact .S suffix"):
                catalog._compile_source(
                    repository,
                    "feature.runtime_injector",
                    "runtime_source",
                    {**base, "kind": "asm"},
                    "feature.payload.runtime_source",
                )

    def test_referenced_files_includes_selected_assembly_source(self) -> None:
        source = '''{
          runtime: setting {
            description: "Assembly runtime.",
            patch: "feature.runtime",
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assembly = root / "src" / "runtime.S"
            assembly.parent.mkdir()
            assembly.write_text("nop\n", encoding="ascii")
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"runtime": True}},
                injections={
                    "feature.runtime": {
                        "description": "Assembly runtime.",
                        "payload": {
                            "runtime_source": {
                                "kind": "asm",
                                "path": "src/runtime.S",
                                "namespace": "runtime",
                                "imports": {},
                                "fragments": {
                                    "runtime_code": {
                                        "object": "runtime.text",
                                    }
                                },
                            }
                        },
                    }
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertEqual(
                (assembly.resolve(),),
                catalog.referenced_files(selection, root, "feature"),
            )

    def test_runtime_payload_and_fragment_fields_fail_closed(self) -> None:
        source = '''{
          runtime: setting {
            description: "Runtime payload.",
            patch: "feature.runtime",
          },
        }'''
        invalid_fields = (
            ("source", "payload.runtime_source"),
            ("label", "fragments.runtime_code"),
        )
        for field, location in invalid_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fragment = {"object": "runtime.text.entry"}
                payload = {
                    "kind": "c",
                    "path": "runtime.c",
                    "namespace": "runtime",
                    "imports": {},
                    "fragments": {"runtime_code": fragment},
                }
                if field == "source":
                    payload[field] = "retired metadata"
                else:
                    fragment[field] = "retired metadata"
                catalog_path, configuration_path = self.write_project(
                    root,
                    {"feature": source},
                    {"feature": {"runtime": True}},
                    injections={
                        "feature.runtime": {
                            "payload": {"runtime_source": payload},
                        }
                    },
                )
                with self.assertRaisesRegex(
                    ValueError,
                    rf"{re.escape(location)}.*unknown fields.*{field}",
                ):
                    catalog.load_selection(catalog_path, configuration_path)

if __name__ == "__main__":
    unittest.main()
