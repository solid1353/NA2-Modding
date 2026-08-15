from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.modules.binary_patcher import adapters
from na228_builder.scripts import catalog, catalog_format


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
        implementation = catalog_path / "implementation"
        implementation.mkdir(parents=True)
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
        for feature_id, source in sources.items():
            (catalog_path / f"{feature_id}.modcat").write_text(
                source, encoding="utf-8"
            )
        self.write_json(implementation / "edits.json", generated_edits)
        self.write_json(implementation / "injections.json", generated_injections)
        self.write_json(
            implementation / "string_patches.json", generated_string_patches
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
        self.assertIn("\n      |\n      {\n", rendered)
        self.assertNotIn("startup_fast_forward_frames", rendered)

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

    def test_repository_configurations_inherit_base_startup_flow(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        catalog_path = repository / "na228_builder" / "catalog"
        configurations = repository / "na228_builder" / "configurations"

        selections = {
            name: catalog.load_selection(
                catalog_path, configurations / f"{name}.json"
            )
            for name in ("dev", "test", "release")
        }
        test = selections["test"]
        self.assertTrue(
            test.node_enabled(
                "features", "qol", "startup", "flow", "savedata_loading"
            )
        )
        self.assertTrue(
            test.node_enabled(
                "features", "qol", "startup", "flow", "loading_screen"
            )
        )
        for name in ("dev", "test", "release"):
            with self.subTest(configuration=name):
                self.assertTrue(
                    selections[name].node_enabled(
                        "features", "qol", "startup", "faster_loading"
                    )
                )
        expected_frames = {"dev": 1160, "test": 1160, "release": 1160}
        for name, selection in selections.items():
            with self.subTest(configuration=name):
                self.assertEqual(
                    catalog.startup_fast_forward_frames(selection, 1760),
                    expected_frames[name],
                )

    def test_repository_practice_starting_hp_variants_select_exact_guarded_edits(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        builder = repository / "na228_builder"
        catalog_path = builder / "catalog"
        base = json.loads(
            (builder / "configurations" / "base.json").read_text(encoding="utf-8")
        )
        expected_replacements = {
            "full": "010080A002000924",
            "half": "010085A002000924",
            "critical": "02000924010089A0",
        }

        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "configuration.json"
            for value, expected_replacement in expected_replacements.items():
                with self.subTest(value=value):
                    base["features"]["qol"]["practice"]["starting_hp"] = value
                    self.write_json(configuration_path, base)
                    selection = catalog.load_selection(
                        catalog_path, configuration_path
                    )
                    package = catalog.load_binary_package(
                        selection,
                        "qol",
                        catalog_path / "implementation" / "targets.tsv",
                        repository,
                        builder / "modules" / "binary_patcher" / "operations",
                    )
                    edits = [
                        edit
                        for edit in package.edits
                        if "e__qol__practice__starting_hp__" in edit.edit_id
                    ]
                    self.assertEqual(len(edits), 1)
                    self.assertEqual(edits[0].destination_offset, 0xE7BE8)
                    self.assertEqual(edits[0].expected_hex, "010080A002000924")
                    self.assertEqual(edits[0].replacement_hex, expected_replacement)

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
            edits_path = catalog_path / "implementation" / "edits.json"
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
                        symbol="runtime.text",
                        kind="code",
                        alignment=4,
                        payload=b"\0\0\0\0",
                    ),
                ),
                symbols={},
            )
            value = {
                "path": "runtime.c",
                "namespace": "runtime",
                "imports": {},
                "fragments": {
                    "runtime_code": {"object": "runtime.text", "order": 1}
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
            self.assertEqual(fragments[0][1].symbol, "runtime_code")
            extract.assert_called_once_with(
                packaged_object.resolve(),
                namespace="runtime",
                owner="feature.runtime_injector",
                external_symbols={},
            )
            compile_source.assert_not_called()
            toolchain.assert_not_called()

if __name__ == "__main__":
    unittest.main()
