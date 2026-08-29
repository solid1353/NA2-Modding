from __future__ import annotations

import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.character_overrides import (
    OVERRIDE_FIELDS,
    REFERENCE_FIELDS,
    SUBSTITUTION_COST_DELTA_FLAG,
    TABLE_VERSION,
    TIER_WIDTH,
    character_override_fragment,
    character_override_fragment_feature,
    character_overrides_enabled_fragment,
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

    def required_override_rows(
        self,
        base_cost: object = 20,
    ) -> list[dict[str, object]]:
        return [
            {"id": "base", "character": "", "substitution_cost": base_cost},
            {"id": "step", "character": "", "substitution_cost": "+5"},
        ]

    def test_table_routing_covers_all_override_and_overlay_combinations(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        builder = repository / "na228_builder"
        catalog_path = builder / "catalog"
        base = json.loads(
            (builder / "configurations" / "base.json").read_text(
                encoding="utf-8"
            )
        )
        cases = (
            (False, False, None),
            (False, True, "character_select"),
            (True, False, "general"),
            (True, True, "general"),
        )
        for overrides_enabled, overlay_enabled, expected_feature in cases:
            with (
                self.subTest(
                    overrides=overrides_enabled,
                    overlay=overlay_enabled,
                ),
                tempfile.TemporaryDirectory() as directory,
            ):
                features = json.loads(json.dumps(base["features"]))
                features["general"]["character_overrides"] = overrides_enabled
                features["character_select"]["balance_overlay"] = overlay_enabled
                configuration_path = Path(directory) / "configuration.json"
                configuration_path.write_text(
                    json.dumps({"features": features}, indent=2) + "\n",
                    encoding="utf-8",
                )
                selection = catalog.load_selection(
                    catalog_path,
                    configuration_path,
                )

                self.assertEqual(
                    character_override_fragment_feature(selection),
                    expected_feature,
                )
                self.assertEqual(
                    selection.node_enabled(
                        "features", "general", "character_overrides"
                    ),
                    overrides_enabled,
                )
                self.assertEqual(
                    selection.node_enabled(
                        "features", "character_select", "balance_overlay"
                    ),
                    overlay_enabled,
                )
                if overlay_enabled:
                    enabled_fragment = character_overrides_enabled_fragment(
                        overrides_enabled,
                        owner="character_select.runtime_injector",
                    )
                    self.assertEqual(
                        struct.unpack("<I", enabled_fragment.payload),
                        (int(overrides_enabled),),
                    )

    def test_canonical_tiers_preserve_native_costs_through_x_over_100(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        builder = repository / "na228_builder"
        configuration = load_character_overrides(
            builder / "configurations" / "base.json",
            builder,
        )
        base_table = (
            builder
            / "configurations"
            / "overrides"
            / "base.character_overrides.tsv"
        ).resolve()
        self.assertEqual(configuration.resource_files.count(base_table), 1)
        base_cost = configuration.base.values[0]
        assert base_cost is not None
        expected_native_costs = {
            "D": 3.0,
            "C": 3.75,
            "B": 4.5,
            "A": 5.25,
            "S": 6.0,
            "S+": 6.75,
            "S+++": 8.25,
        }
        def f32(value: float) -> float:
            return struct.unpack("<f", struct.pack("<f", value))[0]

        fragment = character_override_fragment(configuration, owner="battle_logic")
        row_size = struct.calcsize("<I4s5f")
        observed: dict[str, float] = {}
        for row in configuration.characters:
            assert row.character_id is not None
            offset = 16 + row_size + row.character_id * row_size
            flags = struct.unpack_from("<I", fragment.payload, offset)[0]
            encoded_cost = struct.unpack_from("<f", fragment.payload, offset + 8)[0]
            if flags & SUBSTITUTION_COST_DELTA_FLAG:
                resolved = f32(base_cost + encoded_cost)
            else:
                resolved = encoded_cost
            native_cost = f32(f32(resolved * 15.0) / 100.0)
            if row.tier in observed:
                self.assertEqual(observed[row.tier], native_cost)
            else:
                observed[row.tier] = native_cost

        self.assertEqual(set(observed), set(expected_native_costs))
        for tier, expected in expected_native_costs.items():
            self.assertEqual(observed[tier], expected)

    def test_layered_values_merge_by_character_and_generate_dense_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "profile.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "", "substitution_cost": "20"},
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                    {
                        "id": 3,
                        "base_id": 1,
                        "character": "Gamma",
                        "tier": "S+++",
                        "substitution_cost": "30",
                    },
                    {
                        "id": 1,
                        "character": "Alpha",
                        "tier": "A",
                        "substitution_cost": "+10",
                    },
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "profile.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "", "hp": 100},
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
            self.assertEqual(configuration.base.values[:2], (20.0, 100.0))
            self.assertEqual(configuration.step.values[0], 5.0)
            self.assertEqual(configuration.row_by_id()[1].values[:2], (10.0, 80.0))
            self.assertTrue(configuration.row_by_id()[1].substitution_cost_is_delta)
            self.assertEqual(configuration.row_by_id()[3].values[0], 30.0)
            self.assertFalse(configuration.row_by_id()[3].substitution_cost_is_delta)
            self.assertEqual(
                [row.character_id for row in configuration.characters],
                [3, 1],
            )
            materialized = render_character_overrides(configuration)
            self.assertIn("base\t\t\t\t20.0\t100.0", materialized)
            self.assertIn("step\t\t\t\t+5.0", materialized)
            self.assertIn("3\t1\tGamma\tS+++\t30.0", materialized)
            self.assertIn("1\t\tAlpha\tA\t+10.0\t80.0", materialized)
            self.assertEqual(len(materialized.splitlines()), 5)

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
                struct.unpack_from("<f", fragment.payload, alpha_offset + 8)[0],
                25.0,
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
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    self.required_override_rows(),
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
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
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    self.required_override_rows(),
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
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
            definition = configurations / "profile.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                self.required_override_rows(),
            )
            self.write_tsv(
                configurations / "overrides" / "profile.character_overrides.tsv",
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
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    self.required_override_rows(),
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_profile_can_replace_delta_with_literal_and_accept_negative_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "profile.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "", "substitution_cost": "20"},
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                    {"id": 1, "character": "Alpha", "substitution_cost": "+5"},
                    {"id": 3, "character": "Gamma", "substitution_cost": "-5"},
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "profile.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [{"id": 1, "character": "Alpha", "substitution_cost": "30"}],
            )

            configuration = load_character_overrides(definition, builder)

            alpha = configuration.row_by_id()[1]
            gamma = configuration.row_by_id()[3]
            self.assertEqual(alpha.values[0], 30.0)
            self.assertFalse(alpha.substitution_cost_is_delta)
            self.assertEqual(gamma.values[0], -5.0)
            self.assertTrue(gamma.substitution_cost_is_delta)
            materialized = render_character_overrides(configuration)
            self.assertIn("1\t\tAlpha\t\t30.0", materialized)
            self.assertIn("3\t\tGamma\t\t-5.0", materialized)

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
                self.required_override_rows(base_cost=1),
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
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    self.required_override_rows(base_cost=0.5),
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [row],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_rejects_delta_on_base_substitution_cost(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "profile.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "base", "character": "", "substitution_cost": "+20"},
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "profile.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [],
            )

            with self.assertRaisesRegex(
                ValueError,
                "base substitution_cost must be a literal value",
            ):
                load_character_overrides(definition, builder)

    def test_rejects_substitution_cost_outside_normalized_range(self) -> None:
        cases = (
            (
                [{"id": "base", "character": "", "substitution_cost": 101}],
                "substitution_cost must be from 0 through 100",
            ),
            (
                [
                    {"id": "base", "character": "", "substitution_cost": 60},
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                    {"id": 1, "character": "Alpha", "substitution_cost": "+50"},
                ],
                "resolved substitution_cost for character ID 1 must be from 0 through 100",
            ),
            (
                [
                    {"id": "base", "character": ""},
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                    {"id": 1, "character": "Alpha", "substitution_cost": "+10"},
                ],
                "base substitution_cost is required for tier-derived costs",
            ),
        )
        for rows, expected in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as directory:
                builder = self.create_builder(Path(directory))
                configurations = builder / "configurations"
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    rows,
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_requires_valid_step_row(self) -> None:
        cases = (
            (
                [{"id": "base", "character": "", "substitution_cost": 20}],
                "missing required step row",
            ),
            (
                [
                    {"id": "base", "character": "", "substitution_cost": 20},
                    {"id": "step", "character": "", "substitution_cost": 5},
                ],
                "step substitution_cost must be an explicitly signed positive value",
            ),
            (
                [
                    {"id": "base", "character": "", "substitution_cost": 20},
                    {"id": "step", "character": "", "substitution_cost": "+0"},
                ],
                "step substitution_cost must be an explicitly signed positive value",
            ),
            (
                [
                    {"id": "base", "character": "", "substitution_cost": 20},
                    {
                        "id": "step",
                        "character": "",
                        "substitution_cost": "+5",
                        "hp": 1,
                    },
                ],
                "step row may only set substitution_cost",
            ),
        )
        for rows, expected in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as directory:
                builder = self.create_builder(Path(directory))
                configurations = builder / "configurations"
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    rows,
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_metadata_rows_require_empty_identity_cells(self) -> None:
        cases = (
            ("base", "character", "Base", "base row character must be empty"),
            ("base", "base_id", "1", "base row base_id must be empty"),
            ("base", "tier", "D", "base row tier must be empty"),
            ("step", "character", "Step", "step row character must be empty"),
            ("step", "base_id", "1", "step row base_id must be empty"),
            ("step", "tier", "D", "step row tier must be empty"),
        )
        for row_id, field, value, expected in cases:
            with (
                self.subTest(row=row_id, field=field),
                tempfile.TemporaryDirectory() as directory,
            ):
                builder = self.create_builder(Path(directory))
                configurations = builder / "configurations"
                definition = configurations / "profile.json"
                definition.parent.mkdir(parents=True, exist_ok=True)
                definition.write_text("{}\n", encoding="utf-8")
                rows = self.required_override_rows()
                metadata_row = next(row for row in rows if row["id"] == row_id)
                metadata_row[field] = value
                self.write_tsv(
                    configurations / "overrides" / "base.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    rows,
                )
                self.write_tsv(
                    configurations / "overrides" / "profile.character_overrides.tsv",
                    OVERRIDE_FIELDS,
                    [],
                )

                with self.assertRaisesRegex(ValueError, expected):
                    load_character_overrides(definition, builder)

    def test_requires_base_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            builder = self.create_builder(Path(directory))
            configurations = builder / "configurations"
            definition = configurations / "profile.json"
            definition.parent.mkdir(parents=True, exist_ok=True)
            definition.write_text("{}\n", encoding="utf-8")
            self.write_tsv(
                configurations / "overrides" / "base.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [
                    {"id": "step", "character": "", "substitution_cost": "+5"},
                    {"id": 1, "character": "Alpha", "substitution_cost": 2},
                ],
            )
            self.write_tsv(
                configurations / "overrides" / "profile.character_overrides.tsv",
                OVERRIDE_FIELDS,
                [],
            )

            with self.assertRaisesRegex(ValueError, "missing required base row"):
                load_character_overrides(definition, builder)

if __name__ == "__main__":
    unittest.main()
