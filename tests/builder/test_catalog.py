from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.scripts import catalog


class CatalogTests(unittest.TestCase):
    def write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def write_catalog(self, path: Path, value: object) -> None:
        if not isinstance(value, dict) or set(value) != {"features"}:
            raise ValueError("Test catalog must contain only features")
        features = value["features"]
        if not isinstance(features, dict):
            raise ValueError("Test catalog features must be an object")
        path.mkdir(parents=True, exist_ok=True)
        for feature_id, feature in features.items():
            self.write_json(path / f"{feature_id}.json", feature)
        implementation = path / "implementation"
        implementation.mkdir(exist_ok=True)
        for name in ("edits.json", "injections.json"):
            definition_path = implementation / name
            if not definition_path.exists():
                definition_path.write_text("{}\n", encoding="utf-8")
        self.write_json(
            path.parent / "configurations" / "base.json",
            {"features": True, "overrides": {}},
        )

    def test_configuration_must_match_catalog_at_every_descended_level(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(
                catalog_path,
                {
                    "features": {
                        "feature": {
                        "description": "ignored",
                        "nested": {
                            "first_leaf": {"proven": False},
                            "second_leaf": {},
                        },
                        }
                    },
                },
            )
            self.write_json(
                root / "configurations" / "base.json",
                {
                    "features": {"feature": {"nested": {"first_leaf": True}}},
                    "overrides": {},
                },
            )
            self.write_json(configuration_path, {"overrides": {}})
            with self.assertRaisesRegex(ValueError, "children differ"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_configuration_leaf_cannot_be_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(catalog_path, {"features": {"feature": {"leaf": {}}}})
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"leaf": {}}}},
            )
            with self.assertRaisesRegex(ValueError, "must be true or false"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_proven_can_only_be_false(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(
                catalog_path,
                {"features": {"feature": {"leaf": {"proven": True}}}},
            )
            self.write_json(configuration_path, {"overrides": {}})
            with self.assertRaisesRegex(ValueError, "proven must be false"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(catalog_path, {"features": {"feature": {}}})
            (catalog_path / "feature.json").write_text(
                '{"leaf":{},"leaf":{}}\n', encoding="utf-8"
            )
            self.write_json(configuration_path, {"overrides": {}})
            with self.assertRaisesRegex(ValueError, "duplicate key"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_all_enabled_configuration_mirrors_every_selectable_leaf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(
                catalog_path,
                {
                    "features": {
                        "feature": {
                        "description": "ignored",
                        "first": {},
                        "nested": {
                            "description": "ignored",
                            "second": {"proven": False},
                        },
                        }
                    },
                },
            )

            configuration = catalog.all_enabled_configuration(catalog_path)
            self.assertEqual(
                configuration,
                {"features": True, "overrides": {}},
            )
            self.write_json(configuration_path, configuration)
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertTrue(all(node.enabled for node in selection.nodes))

    def test_partial_overrides_merge_over_compact_features_setting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(
                catalog_path,
                {
                    "features": {
                        "feature": {
                            "first": {},
                            "nested": {"second": {}, "third": {}},
                        }
                    }
                },
            )
            self.write_json(
                configuration_path,
                {
                    "overrides": {"feature": {"nested": {"second": False}}},
                },
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertTrue(selection.node_enabled("features", "feature", "first"))
            self.assertFalse(
                selection.node_enabled("features", "feature", "nested", "second")
            )
            self.assertTrue(
                selection.node_enabled("features", "feature", "nested", "third")
            )
            third = next(
                node
                for node in selection.nodes
                if node.path == ("features", "feature", "nested", "third")
            )
            self.assertEqual(third.node_id, "feature.nested.third")

    def test_base_then_base_overrides_then_configuration_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(
                catalog_path,
                {
                    "features": {
                        "feature": {
                            "first": {},
                            "second": {},
                            "third": {},
                        }
                    }
                },
            )
            self.write_json(
                root / "configurations" / "base.json",
                {
                    "features": True,
                    "overrides": {"feature": {"second": False}},
                },
            )
            self.write_json(
                configuration_path,
                {"overrides": {"feature": {"second": True, "third": False}}},
            )

            selection = catalog.load_selection(catalog_path, configuration_path)

            self.assertTrue(selection.node_enabled("features", "feature", "first"))
            self.assertTrue(selection.node_enabled("features", "feature", "second"))
            self.assertFalse(selection.node_enabled("features", "feature", "third"))

            materialized = catalog.materialized_configuration(
                catalog_path, configuration_path
            )
            self.assertEqual(
                materialized,
                {
                    "features": {
                        "feature": {
                            "first": True,
                            "second": False,
                            "third": True,
                        }
                    },
                    "overrides": {
                        "feature": {"second": True, "third": False}
                    },
                },
            )
            bundled_path = root / "bundled.json"
            self.write_json(bundled_path, materialized)
            bundled = catalog.load_selection(catalog_path, bundled_path)
            self.assertIsNone(bundled.base_configuration_path)
            self.assertEqual(
                [node.enabled for node in selection.nodes],
                [node.enabled for node in bundled.nodes],
            )

    def test_self_contained_configuration_does_not_load_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            configuration_path = root / "configuration.json"
            self.write_catalog(catalog_path, {"features": {"feature": {}}})
            (root / "configurations" / "base.json").write_text(
                "not json\n", encoding="utf-8"
            )
            self.write_json(
                configuration_path,
                {"features": True, "overrides": {}},
            )
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertIsNone(selection.base_configuration_path)
            self.assertTrue(selection.node_enabled("features", "feature"))

    def test_repository_configuration_rejects_self_contained_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog"
            self.write_catalog(catalog_path, {"features": {"feature": {}}})
            configuration_path = root / "configurations" / "release.json"
            self.write_json(
                configuration_path,
                {"features": True, "overrides": {}},
            )
            with self.assertRaisesRegex(
                ValueError, "Repository configurations must contain only"
            ):
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
                    "runtime_code": {
                        "object": "runtime.text",
                        "order": 1,
                    }
                },
            }
            with mock.patch.object(
                catalog.ee_c_fragments,
                "extract_ee_object",
                return_value=extracted,
            ) as extract, mock.patch.object(
                catalog.ee_c_fragments,
                "compile_and_extract",
            ) as compile_source, mock.patch.object(
                catalog.ee_c_fragments,
                "default_toolchain_bin",
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

    def test_live_catalog_and_configurations_reconstruct_migrated_data(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        catalog_path = repository / "na228_builder" / "catalog"
        configuration_root = repository / "na228_builder" / "configurations"
        implementation_root = catalog_path / "implementation"
        targets = implementation_root / "targets.tsv"
        operations = (
            repository
            / "na228_builder"
            / "modules"
            / "binary_patcher"
            / "operations"
        )
        selections = [
            catalog.load_selection(catalog_path, configuration_root / f"{name}.json")
            for name in ("test", "release", "development")
        ]
        self.assertEqual(
            [selection.feature_ids for selection in selections],
            [
                ("localization", "qol", "battle_logic", "rendering"),
                ("localization", "qol", "battle_logic", "rendering"),
                ("localization", "qol", "battle_logic", "rendering"),
            ],
        )
        release = selections[1]
        binary_count = sum(
            len(
                catalog.load_binary_package(
                    release,
                    feature_id,
                    targets,
                    repository,
                    operations,
                ).edits
            )
            for feature_id in release.feature_ids
            if catalog.feature_has(release, feature_id, "edits")
        )
        self.assertEqual(binary_count, 491)
        runtime = [
            catalog.load_runtime_package(
                release,
                feature_id,
                targets,
                repository,
                f"{feature_id}.runtime_injector",
            )
            for feature_id in release.feature_ids
            if catalog.feature_has(release, feature_id, "injections")
        ]
        self.assertEqual(sum(len(package.fragments) for package in runtime), 118)
        self.assertEqual(sum(len(package.edits) for package in runtime), 68)
        raw_catalog = {
            "features": {
                path.stem: json.loads(path.read_text(encoding="utf-8"))
                for path in selections[0].catalog_files
            }
        }
        raw_edits = json.loads(
            (implementation_root / "edits.json").read_text(encoding="utf-8")
        )
        raw_injections = json.loads(
            (implementation_root / "injections.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            json.loads((configuration_root / "base.json").read_text(encoding="utf-8")),
            {"features": True, "overrides": {}},
        )
        for name in ("test", "release", "development"):
            self.assertEqual(
                json.loads(
                    (configuration_root / f"{name}.json").read_text(encoding="utf-8")
                ),
                {"overrides": {}},
            )
        self.assertEqual(len(raw_edits), 491)
        self.assertEqual(len(raw_injections), 24)
        localization = raw_catalog["features"]["localization"]
        self.assertNotIn("translated_text", localization)
        self.assertNotIn("translated_textures", localization)
        forbidden = {
            "features",
            "modules",
            "groups",
            "patches",
            "children",
            "enabled",
            "status",
            "confidence",
            "evidence_id",
            "review_notes",
            "reason",
            "group_id",
            "patch_id",
            "edit_id",
        }

        def inspect(value: object, path: tuple[str, ...] = ()) -> None:
            if isinstance(value, list):
                for index, item in enumerate(value):
                    inspect(item, (*path, str(index)))
                return
            if not isinstance(value, dict):
                return
            disallowed = forbidden - ({"features"} if not path else set())
            self.assertFalse(
                disallowed & value.keys(),
                ".".join(path) or "catalog",
            )
            self.assertNotIn("hooks", value, ".".join(path))
            self.assertNotIn("payload", value, ".".join(path))
            if "edits" in value:
                self.assertIsInstance(value["edits"], list)
                self.assertTrue(set(value["edits"]) <= set(raw_edits))
            if "injections" in value:
                self.assertIsInstance(value["injections"], list)
                self.assertTrue(set(value["injections"]) <= set(raw_injections))
            for key, item in value.items():
                inspect(item, (*path, key))

        inspect(raw_catalog)
        for injection_id, injection in raw_injections.items():
            self.assertTrue(set(injection) <= {"hooks", "payload"}, injection_id)
            self.assertTrue(injection, injection_id)
            for hook_id, hook in injection.get("hooks", {}).items():
                self.assertNotIn("operation", hook, hook_id)
        for path in [
            *selections[0].catalog_files,
            implementation_root / "edits.json",
            implementation_root / "injections.json",
            *configuration_root.glob("*.json"),
        ]:
            self.assertNotIn("\n\n", path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
