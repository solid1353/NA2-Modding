from __future__ import annotations

import csv
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts.character_overrides import (
    OVERRIDE_FIELDS,
    REFERENCE_FIELDS,
    SUBSTITUTION_COST_DELTA_FLAG,
    TABLE_VERSION,
    TIER_WIDTH,
    character_override_fragment,
    load_character_overrides as _load_character_overrides,
    render_character_overrides,
)


def load_character_overrides(
    definition_path: Path,
    builder_root: Path,
):
    return _load_character_overrides(
        definition_path,
        builder_root,
        builder_root.parent / "resources" / "character_data.tsv",
    )


class CharacterOverrideTests(unittest.TestCase):
    def write_tsv(
        self,
        path: Path,
        fields: tuple[str, ...],
        rows: list[dict[str, object]],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    def create_builder(self, root: Path) -> Path:
        builder = root / "na228_builder"
        self.write_tsv(
            builder.parent / "resources" / "character_data.tsv",
            REFERENCE_FIELDS,
            [
                {
                    "character": "Alpha",
                    "id": 1,
                    "support_id": "0x01",
                    "awakening_ids": "0x10,0x11",
                    "linked_uj": "0x01,0x02",
                    "linked_jutsu": "0x20",
                },
                {"character": "Gamma", "id": 3, "awakening_ids": "32"},
            ],
        )
        return builder

    def test_layered_values_merge_by_character_and_generate_dense_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "dev.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "Base", "substitution_cost": "2.5"},
                    {
                        "id": 3,
                        "base_id": 1,
                        "character": "Gamma",
                        "tier": "S+++",
                        "substitution_cost": "3",
                    },
                    {
                        "id": 1,
                        "character": "Alpha",
                        "tier": "A",
                        "substitution_cost": "+0.5",
                    },
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "dev.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "Base", "hp": 100},
                    {"id": 1, "character": "Alpha", "hp": 80},
                ],
            )

            configuration = load_character_overrides(definition, builder)

            self.assertEqual(configuration.character_count, 4)
            self.assertEqual(
                configuration.support_id_by_character(),
                {1: 0x01, 3: None},
            )
            self.assertEqual(
                configuration.awakening_ids_by_character(),
                {1: (0x10, 0x11), 3: (0x20,)},
            )
            self.assertEqual(
                configuration.linked_uj_by_character(),
                {1: (0x01, 0x02), 3: ()},
            )
            self.assertEqual(
                configuration.linked_jutsu_by_character(),
                {1: (0x20,), 3: ()},
            )
            self.assertEqual(configuration.base.values[:2], (2.5, 100.0))
            self.assertEqual(configuration.row_by_id()[1].values[:2], (0.5, 80.0))
            self.assertTrue(configuration.row_by_id()[1].substitution_cost_is_delta)
            self.assertEqual(configuration.row_by_id()[3].values[0], 3.0)
            self.assertFalse(configuration.row_by_id()[3].substitution_cost_is_delta)
            self.assertEqual(
                [row.character_id for row in configuration.characters],
                [3, 1],
            )
            materialized = render_character_overrides(configuration)
            self.assertIn("base\t\tBase\t\t2.5\t100.0", materialized)
            self.assertIn("3\t1\tGamma\tS+++\t3.0", materialized)
            self.assertIn("1\t\tAlpha\tA\t+0.5\t80.0", materialized)
            self.assertEqual(len(materialized.splitlines()), 4)

            fragment = character_override_fragment(configuration, owner="battle_logic")
            self.assertEqual(fragment.symbol, "character_overrides")
            self.assertEqual(
                struct.unpack_from("<4I", fragment.payload),
                (TABLE_VERSION, 4, 5, 0),
            )
            self.assertEqual(struct.unpack_from("<I", fragment.payload, 16)[0], 0b00011)
            row_size = struct.calcsize("<I4s5f")
            self.assertEqual(row_size, 28)
            alpha_offset = 16 + row_size + row_size
            self.assertEqual(
                struct.unpack_from("<I", fragment.payload, alpha_offset)[0],
                0b00011 | SUBSTITUTION_COST_DELTA_FLAG,
            )
            self.assertEqual(
                struct.unpack_from(
                    f"<{TIER_WIDTH}s", fragment.payload, alpha_offset + 4
                )[0],
                b"A\0\0\0",
            )
            gamma_offset = 16 + row_size + row_size * 3
            self.assertEqual(
                struct.unpack_from("<I", fragment.payload, gamma_offset)[0],
                0b00001,
            )
            self.assertEqual(
                struct.unpack_from(
                    f"<{TIER_WIDTH}s", fragment.payload, gamma_offset + 4
                )[0],
                b"S+++",
            )

    def test_rejects_invalid_character_awakening_ids(self) -> None:
        cases = (
            ("0x10,0x10", "duplicate awakening ID 16"),
            ("0x8A", "awakening ID must be from 0 through 137"),
            ("0x10,", "must be comma-separated IDs"),
            ("invalid", "invalid awakening ID 'invalid'"),
        )
        for awakening_ids, expected in cases:
            with (
                self.subTest(awakening_ids=awakening_ids),
                tempfile.TemporaryDirectory() as directory,
            ):
                builder = Path(directory) / "na228_builder"
                self.write_tsv(
                    builder.parent / "resources" / "character_data.tsv",
                    REFERENCE_FIELDS,
                    [
                        {
                            "character": "Alpha",
                            "id": 1,
                            "awakening_ids": awakening_ids,
                        }
                    ],
                )
                configurations = builder / "configurations"
                definition = configurations / "dev.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [{"id": "base", "character": "Base"}],
                )
                self.write_tsv(
                    configurations / "overrides" / "dev.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_rejects_invalid_character_support_ids(self) -> None:
        cases = (
            ("0x22", "support ID must be from 0 through 33"),
            ("0x01,0x02", "invalid support ID '0x01,0x02'"),
            ("invalid", "invalid support ID 'invalid'"),
        )
        for support_id, expected in cases:
            with (
                self.subTest(support_id=support_id),
                tempfile.TemporaryDirectory() as directory,
            ):
                builder = Path(directory) / "na228_builder"
                self.write_tsv(
                    builder.parent / "resources" / "character_data.tsv",
                    REFERENCE_FIELDS,
                    [
                        {
                            "character": "Alpha",
                            "id": 1,
                            "support_id": support_id,
                        }
                    ],
                )
                configurations = builder / "configurations"
                definition = configurations / "dev.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [{"id": "base", "character": "Base"}],
                )
                self.write_tsv(
                    configurations / "overrides" / "dev.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_rejects_duplicate_character_support_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = Path(directory) / "na228_builder"
            self.write_tsv(
                builder.parent / "resources" / "character_data.tsv",
                REFERENCE_FIELDS,
                [
                    {"character": "Alpha", "id": 1, "support_id": "0x01"},
                    {"character": "Gamma", "id": 3, "support_id": "0x01"},
                ],
            )
            configurations = builder / "configurations"
            definition = configurations / "dev.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [{"id": "base", "character": "Base"}],
            )
            self.write_tsv(
                configurations / "overrides" / "dev.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [],
            )

            with self.assertRaisesRegex(
                ValueError,
                "duplicate support ID 1; already assigned to character ID 1",
            ):
                load_character_overrides(definition, builder)

    def test_rejects_invalid_character_linked_support_ids(self) -> None:
        cases = (
            ("linked_uj", "0x01,0x01", "duplicate support ID 1"),
            ("linked_jutsu", "0x22", "support ID must be from 0 through 33"),
            ("linked_uj", "0x01,", "linked_uj must be comma-separated IDs"),
            ("linked_jutsu", "invalid", "invalid support ID 'invalid'"),
        )
        for field, value, expected in cases:
            with (
                self.subTest(field=field, value=value),
                tempfile.TemporaryDirectory() as directory,
            ):
                builder = Path(directory) / "na228_builder"
                self.write_tsv(
                    builder.parent / "resources" / "character_data.tsv",
                    REFERENCE_FIELDS,
                    [{"character": "Alpha", "id": 1, field: value}],
                )
                configurations = builder / "configurations"
                definition = configurations / "dev.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [{"id": "base", "character": "Base"}],
                )
                self.write_tsv(
                    configurations / "overrides" / "dev.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_profile_can_replace_delta_with_literal_and_accept_negative_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "dev.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "Base", "substitution_cost": "2.5"},
                    {"id": 1, "character": "Alpha", "substitution_cost": "+0.5"},
                    {"id": 3, "character": "Gamma", "substitution_cost": "-0.5"},
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "dev.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [{"id": 1, "character": "Alpha", "substitution_cost": "3"}],
            )

            configuration = load_character_overrides(definition, builder)

            alpha = configuration.row_by_id()[1]
            gamma = configuration.row_by_id()[3]
            self.assertEqual(alpha.values[0], 3.0)
            self.assertFalse(alpha.substitution_cost_is_delta)
            self.assertEqual(gamma.values[0], -0.5)
            self.assertTrue(gamma.substitution_cost_is_delta)
            materialized = render_character_overrides(configuration)
            self.assertIn("1\t\tAlpha\t\t3.0", materialized)
            self.assertIn("3\t\tGamma\t\t-0.5", materialized)

    def test_external_configuration_reads_adjacent_materialized_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            builder = self.create_builder(root)
            release = root / "release"
            definition = release / "config.json"
            definition.parent.mkdir(parents=True)
            definition.write_text("{}\n", encoding="utf-8")
            table = release / "character_overrides.tsv"
            self.write_tsv(
                table,
                OVERRIDE_FIELDS,
                [{"id": "base", "character": "Base", "substitution_cost": 1}],
            )

            configuration = load_character_overrides(definition, builder)

            self.assertEqual(configuration.base.values[0], 1.0)
            self.assertEqual(
                configuration.resource_files,
                ((builder.parent / "resources" / "character_data.tsv").resolve(), table.resolve()),
            )

    def test_rejects_identity_mismatch_and_invalid_numbers(self) -> None:
        cases = (
            ({"id": 1, "character": "Gamma", "substitution_cost": 1}, "must be named 'Alpha'"),
            ({"id": 1, "character": "Alpha", "hp": -1}, "must be nonnegative"),
            ({"id": 1, "character": "Alpha", "hp": "nan"}, "must be finite"),
            ({"id": 1, "base_id": 2, "character": "Alpha"}, "unknown base character ID 2"),
            ({"id": 1, "base_id": 1, "character": "Alpha"}, "cannot be its own base form"),
        )
        for row, expected in cases:
            with self.subTest(row=row), tempfile.TemporaryDirectory() as directory:
                builder = self.create_builder(Path(directory))
                configurations = builder / "configurations"
                definition = configurations / "dev.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [{"id": "base", "character": "Base", "substitution_cost": 0.5}],
                )
                self.write_tsv(
                    configurations / "overrides" / "dev.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [row],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_rejects_delta_on_base_substitution_cost(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "dev.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [{"id": "base", "character": "Base", "substitution_cost": "+2.5"}],
            )
            self.write_tsv(
                configurations / "overrides" / "dev.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [],
            )

            with self.assertRaisesRegex(
                ValueError,
                "base substitution_cost must be a literal value",
            ):
                load_character_overrides(definition, builder)

    def test_requires_base_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "dev.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [{"id": 1, "character": "Alpha", "substitution_cost": 2}],
            )
            self.write_tsv(
                configurations / "overrides" / "dev.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [],
            )

            with self.assertRaisesRegex(ValueError, "missing required base row"):
                load_character_overrides(definition, builder)

if __name__ == "__main__":
    unittest.main()
