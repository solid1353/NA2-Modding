from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder import catalog


class CatalogTests(unittest.TestCase):
    def write_json(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_configuration_must_match_catalog_at_every_descended_level(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            configuration_path = root / "configuration.json"
            self.write_json(
                catalog_path,
                {
                    "feature": {
                        "description": "ignored",
                        "nested": {
                            "first_leaf": {"proven": False},
                            "second_leaf": {},
                        },
                    }
                },
            )
            self.write_json(
                configuration_path,
                {"feature": {"nested": {"first_leaf": True}}},
            )
            with self.assertRaisesRegex(ValueError, "children differ"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_configuration_leaf_cannot_be_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            configuration_path = root / "configuration.json"
            self.write_json(catalog_path, {"feature": {"leaf": {}}})
            self.write_json(configuration_path, {"feature": {"leaf": {}}})
            with self.assertRaisesRegex(ValueError, "must be true or false"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_proven_can_only_be_false(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            configuration_path = root / "configuration.json"
            self.write_json(
                catalog_path,
                {"feature": {"leaf": {"proven": True}}},
            )
            self.write_json(configuration_path, {"feature": {"leaf": True}})
            with self.assertRaisesRegex(ValueError, "proven must be false"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            configuration_path = root / "configuration.json"
            catalog_path.write_text(
                '{"feature":{"leaf":{},"leaf":{}}}\n', encoding="utf-8"
            )
            self.write_json(configuration_path, {"feature": {"leaf": True}})
            with self.assertRaisesRegex(ValueError, "duplicate key"):
                catalog.load_selection(catalog_path, configuration_path)

    def test_all_enabled_configuration_mirrors_every_selectable_leaf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            configuration_path = root / "configuration.json"
            self.write_json(
                catalog_path,
                {
                    "feature": {
                        "description": "ignored",
                        "first": {},
                        "nested": {
                            "description": "ignored",
                            "second": {"proven": False},
                        },
                    }
                },
            )

            configuration = catalog.all_enabled_configuration(catalog_path)
            self.assertEqual(
                configuration,
                {"feature": {"first": True, "nested": {"second": True}}},
            )
            self.write_json(configuration_path, configuration)
            selection = catalog.load_selection(catalog_path, configuration_path)
            self.assertTrue(all(node.enabled for node in selection.nodes))

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
        catalog_path = repository / "na228_builder" / "catalog.json"
        configuration_root = repository / "na228_builder" / "configurations"
        targets = repository / "na228_builder" / "features" / "targets.tsv"
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
            if catalog.feature_has(release, feature_id, "hooks")
        ]
        self.assertEqual(sum(len(package.fragments) for package in runtime), 118)
        self.assertEqual(sum(len(package.edits) for package in runtime), 68)
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
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
            self.assertFalse(
                forbidden & value.keys(),
                ".".join(path) or "catalog",
            )
            if "hooks" in value:
                for hook_id, hook in value["hooks"].items():
                    self.assertNotIn("operation", hook, ".".join((*path, hook_id)))
            keys = list(value)
            if "edits" in value:
                for later in ("hooks", "payload"):
                    if later in value:
                        self.assertLess(keys.index("edits"), keys.index(later))
            for key, item in value.items():
                inspect(item, (*path, key))

        inspect(raw_catalog)
        for path in [catalog_path, *configuration_root.glob("*.json")]:
            self.assertNotIn("\n\n", path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
