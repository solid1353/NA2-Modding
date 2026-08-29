from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.modules.binary_patcher import adapters
from na228_builder.scripts import catalog, catalog_format
from scripts.lib.paths import load_local_paths


PATCH_ID = re.compile(r'"((?:e|i|s)__[a-z0-9_]+)"')


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
    ) -> tuple[Path, Path]:
        catalog_path = root / "catalog"
        catalog_path.mkdir(parents=True)
        referenced = {
            patch for source in sources.values() for patch in PATCH_ID.findall(source)
        }
        generated_edits = {
            patch: {"description": f"Synthetic edit {patch}."}
            for patch in sorted(referenced)
            if patch.startswith("e__")
        }
        generated_injections = {
            patch: {"description": f"Synthetic injection {patch}."}
            for patch in sorted(referenced)
            if patch.startswith("i__")
        }
        generated_string_patches = {
            patch: {
                "description": f"Synthetic string patch {patch}.",
                "operation": "replace_imported_game_title",
                "expected_value": "Imported Game",
                "expected_mapping_count": 1,
                "expected_occurrence_count": 1,
            }
            for patch in sorted(referenced)
            if patch.startswith("s__")
        }
        generated_edits.update(edits or {})
        generated_injections.update(injections or {})
        generated_string_patches.update(string_patches or {})
        parsed_features: dict[str, catalog_format.ContainerNode] = {}
        for feature_id, source in sources.items():
            temporary = catalog_path / f".{feature_id}.modcat"
            temporary.write_text(source, encoding="utf-8")
            parsed_features[feature_id] = catalog_format.parse_catalog(temporary)
            temporary.unlink()
        (catalog_path / "catalog.modcat").write_text(
            catalog_format.serialize_catalog(parsed_features, include_patches=True),
            encoding="utf-8",
        )
        self.write_json(catalog_path / "edits.json", generated_edits)
        self.write_json(catalog_path / "injections.json", generated_injections)
        self.write_json(
            catalog_path / "string_patches.json", generated_string_patches
        )
        self.write_json(
            root / "configurations" / "base.json",
            {"features": features},
        )
        configuration_path = root / "configuration.json"
        self.write_json(configuration_path, {"overrides": {}})
        return catalog_path, configuration_path

    def test_complete_minimal_grammar_and_type_matching(self) -> None:
        source = r'''
        {
          // Plain switch.
          plain: setting {
            description: "Plain setting.",
            startup_fast_forward_frames: {
              additive: 25,
              override: 100,
            },
            patches: ["e__feature__plain",],
          },
          supplied_bool: setting<{ value: bool, label?: string, }> {
            description: "Boolean data wrapped in an object.",
            patches: ["e__feature__supplied_bool"],
          },
          patch_and_module: setting {
            description: "Patch-backed internal module.",
            modules: ["texture_patcher"],
            patches: ["e__feature__patch_and_module"],
          },
          numeric: setting<(int & 1..15) | (decimal & >0 & <1)> {
            description: "Disjoint numeric union.",
            patches: ["e__feature__numeric"],
          },
          alternative:
            setting<int> {
              description: "Direct integer.",
              patches: ["e__feature__direct"],
            }
            |
            {
              ratio: setting<{ numerator: int & >0, denominator: int & >0 }> {
                description: "Named ratio.",
                patches: ["e__feature__ratio"],
              },
            },
        }
        '''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(source, encoding="utf-8")
            parsed = catalog_format.parse_catalog(path)

        fields = {field.name: field.node for field in parsed.fields}
        self.assertEqual(fields["plain"].startup_fast_forward_frames.additive, 25)
        self.assertEqual(fields["plain"].startup_fast_forward_frames.override, 100)
        self.assertEqual(
            fields["patch_and_module"].patches,
            ("e__feature__patch_and_module",),
        )
        self.assertEqual(
            fields["patch_and_module"].modules,
            ("texture_patcher",),
        )
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
        self.assertNotIn("startup_fast_forward_frames", rendered)
        self.assertNotIn("modules:", rendered)
        self.assertIn('modules: [\n          "texture_patcher",', embedded)

    def test_startup_fast_forward_frames_combine_one_override_and_additives(
        self,
    ) -> None:
        source = '''{
          baseline: setting {
            description: "Baseline.",
            startup_fast_forward_frames: { override: 100, additive: 5 },
            patches: ["e__feature__baseline"],
          },
          extra: setting {
            description: "Extra.",
            startup_fast_forward_frames: { additive: -20 },
            patches: ["e__feature__extra"],
          },
          disabled_override: setting {
            description: "Disabled override.",
            startup_fast_forward_frames: { override: 999 },
            patches: ["e__feature__disabled_override"],
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
                root / "configurations" / "base.json",
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
                root / "configurations" / "base.json",
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
                path = Path(directory) / "feature.modcat"
                path.write_text(
                    '''{
                      leaf: setting {
                        description: "Leaf.",
                        startup_fast_forward_frames: { override: %s },
                        patches: ["e__feature__leaf"],
                      },
                    }'''
                    % value,
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "integer"):
                    catalog_format.parse_catalog(path)

    def test_object_intersection_shares_fields_across_union_branches(self) -> None:
        source = '''{
          startup:
            {
              faster_loading: setting {
                description: "Load faster.",
                patches: ["i__feature__faster_loading"],
              },
            }
            &
            (
              {
                skip_opening: setting {
                  description: "Skip opening.",
                  patches: ["e__feature__skip_opening"],
                },
              }
              |
              {
                savedata_loading: setting<"automatic"> {
                  description: "Load save automatically.",
                  patches: ["i__feature__savedata_loading"],
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
                root / "configurations" / "base.json",
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
                patches: ["e__feature__faster_loading"],
              },
            }
            &
            (
              {
                skip_intro: setting {
                  description: "Skip intro.",
                  patches: ["e__feature__skip_intro"],
                },
                skip_opening: setting {
                  description: "Skip opening.",
                  patches: ["e__feature__skip_opening"],
                },
              }
              |
              {
                savedata_loading: setting<"automatic"> {
                  description: "Load save automatically.",
                  patches: ["e__feature__savedata_loading"],
                },
                loading_screen: setting {
                  description: "Show loading screen.",
                  patches: ["e__feature__loading_screen"],
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
        catalog_path = paths.path("builder", "catalog")
        configurations = paths.path("builder", "configurations")

        selections = {
            name: catalog.load_selection(
                catalog_path, configurations / f"{name}.json"
            )
            for name in ("base", "test", "release")
        }
        test = selections["test"]
        self.assertTrue(
            test.node_enabled(
                "features", "startup", "flow", "savedata_loading"
            )
        )
        self.assertTrue(
            test.node_enabled(
                "features", "startup", "flow", "loading_screen"
            )
        )
        for name in ("base", "release"):
            with self.subTest(configuration=name):
                self.assertTrue(
                    selections[name].node_enabled(
                        "features", "startup", "faster_loading"
                    )
                )
        self.assertFalse(
            test.node_enabled("features", "startup", "faster_loading")
        )
        expected_frames = {"base": 1160, "test": 1760, "release": 1160}
        for name, selection in selections.items():
            with self.subTest(configuration=name):
                self.assertEqual(
                    catalog.startup_fast_forward_frames(selection, 1760),
                    expected_frames[name],
                )

    def test_repository_practice_defaults_are_owned_by_settings(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        builder = paths.path("builder")
        catalog_path = builder / "catalog"
        base = json.loads(
            (builder / "configurations" / "base.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            base["features"]["settings"]["practice"],
            {
                "health": "full",
                "commands": "off",
                "guide_ninja_sound": "off",
                "linked_attack": "off",
            },
        )
        selection = catalog.load_selection(
            catalog_path, builder / "configurations" / "base.json"
        )
        package = catalog.load_binary_package(
            selection,
            "practice",
            catalog_path / "targets.tsv",
            paths.repository,
            builder / "modules" / "binary_patcher" / "operations",
        )
        self.assertEqual(package.edits, [])
        self.assertIn("i__practice__settings_rework", selection.injections)

    def test_repository_simple_display_is_a_shared_setting(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        builder = paths.path("builder")
        catalog_path = builder / "catalog"
        base = json.loads(
            (builder / "configurations" / "base.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            base["features"]["settings"]["shared"]["simple_display"],
            "off",
        )

        for value, replacement_hex in (("off", "00000000"), ("on", "25186600")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                configuration = Path(directory) / "configuration.json"
                configured = json.loads(json.dumps(base))
                configured["features"]["settings"]["shared"][
                    "simple_display"
                ] = value
                configuration.write_text(json.dumps(configured), encoding="utf-8")
                selection = catalog.load_selection(catalog_path, configuration)
                package = catalog.load_binary_package(
                    selection,
                    "settings",
                    catalog_path / "targets.tsv",
                    paths.repository,
                    builder / "modules" / "binary_patcher" / "operations",
                )
                edit = next(
                    edit
                    for edit in package.edits
                    if edit.edit_id.endswith(".e__battle__simple_display")
                )
                self.assertEqual(edit.destination_offset, 0xE7BAC)
                self.assertEqual(edit.expected_hex, "25186600")
                self.assertEqual(edit.replacement_hex, replacement_hex)

    def test_object_intersection_rejects_duplicate_fields(self) -> None:
        source = '''{
          value:
            { duplicate: setting {
              description: "First.", patches: ["e__feature__first"],
            } }
            &
            { duplicate: setting {
              description: "Second.", patches: ["e__feature__second"],
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
            patches: ["e__feature__value"],
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
                    + '> { description: "Invalid.", patches: ["e__x__y"] } }',
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    catalog_format.parse_catalog(invalid)

    def test_direct_boolean_setting_types_are_forbidden(self) -> None:
        for value_type in ("bool", "true", "false", 'string | false'):
            with self.subTest(value_type=value_type), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "feature.modcat"
                path.write_text(
                    "{ value: setting<"
                    + value_type
                    + '> { description: "Invalid.", patches: ["e__x__y"] } }',
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "boolean setting types"):
                    catalog_format.parse_catalog(path)

    def test_overlapping_unions_are_rejected_at_catalog_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feature.modcat"
            path.write_text(
                '''{
                  value:
                    setting<int> {
                      description: "Any integer.", patches: ["e__x__any"],
                    }
                    |
                    setting<int & 1..3> {
                      description: "Small integer.", patches: ["e__x__small"],
                    },
                }''',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "branches 1 and 2 overlap"):
                catalog_format.parse_catalog(path)

    def test_false_disables_every_node_and_bool_remains_object_data(self) -> None:
        source = '''{
          plain: setting {
            description: "Plain.", patches: ["e__feature__plain"],
          },
          integer: setting<int> {
            description: "Integer.", patches: ["e__feature__integer"],
          },
          supplied_bool: setting<{ value: bool }> {
            description: "Supplied bool.", patches: ["e__feature__bool"],
          },
          alternative:
            setting<int> {
              description: "Direct.", patches: ["e__feature__direct"],
            }
            |
            { fixed: setting<int> {
              description: "Fixed.", patches: ["e__feature__fixed"],
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
            description: "Optional object.", patches: ["e__f__optional"],
          },
          required: setting<{ count: int }> {
            description: "Required object.", patches: ["e__f__required"],
          },
          alternative:
            setting<{ count?: int }> {
              description: "Optional branch.", patches: ["e__f__branch_object"],
            }
            |
            setting<"named"> {
              description: "Named branch.", patches: ["e__f__branch_named"],
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
                root / "configurations" / "base.json",
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
            first: setting { description: "First.", patches: ["e__f__first"] },
            second: setting { description: "Second.", patches: ["e__f__second"] },
          },
          scalar: setting<int> {
            description: "Scalar.", patches: ["e__f__scalar"],
          },
          named:
            { pair: {
              left: setting<int> {
                description: "Left.", patches: ["e__f__left"],
              },
              right: setting<int> {
                description: "Right.", patches: ["e__f__right"],
              },
            } }
            |
            setting<string> {
              description: "Text.", patches: ["e__f__text"],
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
            leaf: setting { description: "Leaf.", patches: ["e__f__leaf"] },
          },
          integer: setting<int> {
            description: "Integer.", patches: ["e__f__integer"],
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
                root / "configurations" / "base.json",
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
          first: setting { description: "First.", patches: ["e__f__first"] },
          second: setting { description: "Second.", patches: ["e__f__second"] },
          third: setting { description: "Third.", patches: ["e__f__third"] },
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

    def test_descriptions_and_patch_references_are_mandatory(self) -> None:
        invalid_sources = (
            '{ leaf: setting { patches: ["e__f__leaf"] } }',
            '{ leaf: setting { description: "", patches: ["e__f__leaf"] } }',
            '{ leaf: setting { description: "Leaf.", patches: [] } }',
        )
        for source in invalid_sources:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "feature.modcat"
                path.write_text(source, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "requires"):
                    catalog_format.parse_catalog(path)

    def test_unknown_and_orphaned_implementation_ids_are_rejected(self) -> None:
        source = '''{
          leaf: setting {
            description: "Leaf.", patches: ["e__f__missing"],
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"leaf": True}},
                edits={"e__f__orphan": {"description": "Orphan."}},
            )
            edits_path = catalog_path / "edits.json"
            values = json.loads(edits_path.read_text(encoding="utf-8"))
            values.pop("e__f__missing")
            self.write_json(edits_path, values)
            with self.assertRaisesRegex(ValueError, "unknown edit"):
                catalog.load_selection(catalog_path, configuration_path)

            values["e__f__missing"] = {"description": "Present."}
            self.write_json(edits_path, values)
            with self.assertRaisesRegex(ValueError, "not catalog-referenced"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_public_catalog_keeps_contract_and_strips_implementation(self) -> None:
        source = '''{
          value: setting<decimal & 0..15 & step 0.25> {
            description: "Bounded value.",
            startup_fast_forward_frames: { additive: 12 },
            patches: ["e__f__value"],
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, _ = self.write_project(
                root, {"feature": source}, {"feature": {"value": 5}}
            )
            public = catalog.public_catalog(catalog_path)
        self.assertIn("features:", public)
        self.assertIn("setting<decimal & 0..15 & step 0.25>", public)
        self.assertIn('description: "Bounded value."', public)
        self.assertNotIn("patches", public)
        self.assertNotIn("startup_fast_forward_frames", public)
        self.assertNotIn("e__f__value", public)

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
            patches: ["s__feature__replace_title"],
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, configuration_path = self.write_project(
                root,
                {"feature": source},
                {"feature": {"replace_title": True}},
            )
            enabled = catalog.load_selection(catalog_path, configuration_path)
            self.assertEqual(
                [item[1] for item in catalog.selected_string_patches(
                    enabled, "replace_imported_game_title"
                )],
                ["s__feature__replace_title"],
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
            "e__feature__singular", singular
        )[0][1]
        plural_member = catalog._edit_members(
            "e__feature__plural", plural
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
                "e__feature__ambiguous",
                {**definition, "destination_offsets": ["0x10", "0x20"]},
            )
        with self.assertRaisesRegex(
            ValueError,
            "exactly one of destination_offset or destination_offsets",
        ):
            missing = dict(definition)
            del missing["destination_offset"]
            catalog._edit_members("e__feature__missing", missing)
        with self.assertRaisesRegex(ValueError, "must contain at least two"):
            redundant = dict(definition)
            del redundant["destination_offset"]
            redundant["destination_offsets"] = ["0x10"]
            catalog._edit_members("e__feature__redundant", redundant)

    def test_grouped_edit_expands_named_primitive_edits(self) -> None:
        source = '''{
          grouped: setting {
            description: "Grouped edits.",
            patches: ["e__feature__grouped"],
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
                edits={"e__feature__grouped": grouped},
            )
            (root / "asset.bin").write_bytes(b"\xAA\xBB")
            (catalog_path / "targets.tsv").write_text(
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
                catalog_path / "targets.tsv",
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
        self.assertTrue(all("e__feature__grouped" in edit.edit_id for edit in package.edits))
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
            patches: ["e__feature__table"],
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
                edits={"e__feature__table": table},
            )
            (catalog_path / "targets.tsv").write_text(
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
                catalog_path / "targets.tsv",
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
                    catalog._edit_members("e__feature__table", definition)

    def test_grouped_edit_rejects_overlapping_child_destinations(self) -> None:
        source = '''{
          grouped: setting {
            description: "Grouped edits.",
            patches: ["e__feature__grouped"],
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
                edits={"e__feature__grouped": grouped},
            )
            (catalog_path / "targets.tsv").write_text(
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
                    catalog_path / "targets.tsv",
                    root,
                    paths.path("builder", "modules", "binary_patcher", "operations"),
                )

    def test_repository_grouped_edit_maps_are_alphabetical(self) -> None:
        paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        definitions = json.loads(
            paths.path("builder", "catalog", "edits.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(list(definitions), sorted(definitions))
        for edit_id, definition in definitions.items():
            with self.subTest(edit_id=edit_id):
                if "edits" in definition:
                    self.assertEqual(
                        list(definition["edits"]),
                        sorted(definition["edits"]),
                    )
                members = (
                    definition["edits"].values()
                    if "edits" in definition
                    else (definition,)
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
            patches: ["e__feature__grouped"],
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
                    edits={"e__feature__grouped": grouped},
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
            patches: ["i__feature__runtime"],
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
                    "i__feature__runtime": {
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

if __name__ == "__main__":
    unittest.main()
