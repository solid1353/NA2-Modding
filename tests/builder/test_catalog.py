from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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

    def test_live_pin_values_remain_untouched(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        pins = catalog.read_pins(
            repository / "na228_builder" / "profiles" / "default.tsv"
        )
        self.assertEqual(
            [(pin.feature_id, pin.expected_sha256, pin.bypass_check) for pin in pins],
            [
                (
                    "localization",
                    "AFB13606235CC157C3C44CB9FF9D43AFB008EB7FA4F910BA01E6103A0F6BAF30",
                    True,
                ),
                (
                    "qol",
                    "6360CB031D2CA1A74CA849C37E3EB8FF2D9A7986BCBE275FC4B2C0D86B19A1B4",
                    True,
                ),
                (
                    "battle_logic",
                    "BF8F2AD32E428B605F043AFF849177D3547268E8CD8E6AD40CB32495F96B6878",
                    True,
                ),
                (
                    "rendering",
                    "E88CC91E85BBF60DB6D8E3759947475EC68FE7A4DC2D0FC432884EE82B23A491",
                    True,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
