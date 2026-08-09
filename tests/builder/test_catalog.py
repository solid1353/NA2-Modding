from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.modules.binary_patcher import adapters
from na228_builder.scripts import catalog, catalog_format


PATCH_ID = re.compile(r'"((?:e|i)__[a-z0-9_]+)"')


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
        overrides: dict[str, object] | None = None,
        edits: dict[str, object] | None = None,
        injections: dict[str, object] | None = None,
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
        generated_edits.update(edits or {})
        generated_injections.update(injections or {})
        for feature_id, source in sources.items():
            (catalog_path / f"{feature_id}.modcat").write_text(
                source, encoding="utf-8"
            )
        self.write_json(implementation / "edits.json", generated_edits)
        self.write_json(implementation / "injections.json", generated_injections)
        self.write_json(
            root / "configurations" / "base.json",
            {"features": features, "overrides": overrides or {}},
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
            patches: ["e__feature__plain",],
          },
          supplied_bool: setting<{ value: bool, label?: string, }> {
            description: "Boolean data wrapped in an object.",
            patches: ["e__feature__supplied_bool"],
          },
          numeric: setting<(int & 1..15) | (decimal & >0 & <=1)> {
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
            with self.assertRaisesRegex(ValueError, "must be false or an object"):
                catalog.load_selection(catalog_path, configuration_path)
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"integer": True}}},
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                catalog.load_selection(catalog_path, configuration_path)

            self.write_json(
                root / "configurations" / "base.json",
                {"features": False, "overrides": {}},
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

    def test_materialized_configuration_applies_both_override_layers(self) -> None:
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
                overrides={"feature": {"second": False}},
            )
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"second": True, "third": False}}},
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
                    },
                    "overrides": {},
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
          value: setting<int & 1..15> {
            description: "Bounded value.", patches: ["e__f__value"],
          },
        }'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path, _ = self.write_project(
                root, {"feature": source}, {"feature": {"value": 5}}
            )
            public = catalog.public_catalog(catalog_path)
        self.assertIn("features:", public)
        self.assertIn("setting<int & 1..15>", public)
        self.assertIn('description: "Bounded value."', public)
        self.assertNotIn("patches", public)
        self.assertNotIn("e__f__value", public)

    def test_mips_lui_float32_adapter_preserves_instruction_and_rejects_bad_guards(self) -> None:
        replacements = {
            value: adapters.apply_adapter("mips_lui_float32", "803F023C", value)
            for value in range(1, 16)
        }
        self.assertEqual(replacements[1], "803F023C")
        self.assertEqual(replacements[3], "4040023C")
        self.assertEqual(replacements[15], "7041023C")
        self.assertTrue(all(value.endswith("023C") for value in replacements.values()))
        with self.assertRaisesRegex(ValueError, "four-byte"):
            adapters.apply_adapter("mips_lui_float32", "803F", 3)
        with self.assertRaisesRegex(ValueError, "not a MIPS LUI"):
            adapters.apply_adapter("mips_lui_float32", "00000000", 3)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            adapters.apply_adapter("unknown", "803F023C", 3)

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

    def test_live_catalog_configurations_and_value_adapter(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        builder = repository / "na228_builder"
        catalog_path = builder / "catalog"
        configurations = builder / "configurations"
        release = catalog.load_selection(catalog_path, configurations / "release.json")
        self.assertEqual(
            release.feature_ids,
            ("battle_logic", "localization", "qol", "rendering"),
        )
        self.assertEqual(len(release.edits), 493)
        self.assertEqual(len(release.injections), 24)
        self.assertTrue(
            release.node_enabled("features", "qol", "startup", "save_loading")
        )
        self.assertFalse(
            release.node_enabled("features", "battle_logic", "substitution_cost")
        )
        self.assertTrue(all(key.startswith("e__") for key in release.edits))
        self.assertTrue(all(key.startswith("i__") for key in release.injections))
        self.assertFalse((catalog_path / "__reference.json").exists())
        self.assertEqual(
            {path.suffix for path in release.catalog_files}, {".modcat"}
        )
        release_binary_count = sum(
            len(
                catalog.load_binary_package(
                    release,
                    feature_id,
                    catalog_path / "implementation" / "targets.tsv",
                    repository,
                    builder / "modules" / "binary_patcher" / "operations",
                ).edits
            )
            for feature_id in release.feature_ids
            if catalog.feature_has(release, feature_id, "edits", enabled_only=True)
        )
        self.assertEqual(release_binary_count, 491)

        configured = catalog.materialized_configuration(
            catalog_path, configurations / "release.json"
        )
        configured["features"]["battle_logic"]["substitution_cost"] = 3
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "config.json"
            self.write_json(configuration_path, configured)
            selection = catalog.load_selection(catalog_path, configuration_path)
            package = catalog.load_binary_package(
                selection,
                "battle_logic",
                catalog_path / "implementation" / "targets.tsv",
                repository,
                builder / "modules" / "binary_patcher" / "operations",
            )
        edit = next(
            item
            for item in package.edits
            if item.edit_id.endswith("e__battle_logic__substitution_cost")
        )
        self.assertEqual(edit.expected_hex, "803F023C")
        self.assertEqual(edit.replacement_hex, "4040023C")
        self.assertEqual(edit.length, 4)


if __name__ == "__main__":
    unittest.main()
