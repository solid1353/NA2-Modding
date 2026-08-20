from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[4]
MODULE_PATH = REPOSITORY / "scripts" / "research" / "substitution" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("na2_substitution_catalog", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load {MODULE_PATH}")
CATALOG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CATALOG
SPEC.loader.exec_module(CATALOG)


class SubstitutionCatalogTests(unittest.TestCase):
    def test_scan_uses_exact_reference_before_shared_source(self) -> None:
        elf = bytearray(0x500)
        metadata_address = 0x00100000
        metadata_offset = metadata_address - CATALOG.VIRTUAL_TO_FILE_DELTA
        action_base = 0x00100100
        action_offset = action_base - CATALOG.VIRTUAL_TO_FILE_DELTA
        name_pointer = 0x00100300
        name_source_offset = name_pointer - CATALOG.VIRTUAL_TO_FILE_DELTA

        struct.pack_into("<H", elf, metadata_offset + 0x28, 2)
        struct.pack_into("<I", elf, metadata_offset + 0x2C, action_base)
        for index in range(2):
            offset = action_offset + index * CATALOG.ACTION_RECORD_SIZE
            struct.pack_into("<I", elf, offset + 0x08, name_pointer)
        struct.pack_into("<I", elf, action_offset + 0x10, 0x00040000)
        struct.pack_into("<I", elf, action_offset + 0x14, 0x02008000)
        struct.pack_into("<B", elf, action_offset + 0x2C, 0x1F)
        struct.pack_into(
            "<b",
            elf,
            action_offset + CATALOG.ACTION_RECORD_SIZE + 0x1A,
            -2,
        )

        second_name_field = action_offset + CATALOG.ACTION_RECORD_SIZE + 0x08
        character_rows = [
            {
                "character": "Test Fighter",
                "id": "7",
                "record_address": f"0x{metadata_address:08X}",
            }
        ]
        mapping_rows = [
            {
                "id": "T1",
                "display_context": CATALOG.COMMAND_CONTEXT,
                "source_ref": f"NA2_SLPS@0x{name_source_offset:X}",
                "reference_refs": "",
                "donor": "Shared Name",
            },
            {
                "id": "T2",
                "display_context": CATALOG.COMMAND_CONTEXT,
                "source_ref": f"NA2_SLPS@0x{name_source_offset:X}",
                "reference_refs": f"NA2_SLPS@0x{second_name_field:X}",
                "donor": "Exact Alias",
            },
        ]

        records, summary = CATALOG.scan_action_catalog(
            bytes(elf), character_rows, mapping_rows
        )

        self.assertEqual(records[0]["command_name"], "Shared Name")
        self.assertEqual(records[0]["mapping_join"], "source")
        self.assertEqual(records[0]["catalog_scope"], "primary")
        self.assertEqual(records[0]["metadata_address"], "0x00100000")
        self.assertEqual(records[0]["raw_timing"], 0)
        self.assertEqual(records[0]["effective_timing"], -1)
        self.assertEqual(records[0]["negative_rng_modulus"], 3)
        self.assertEqual(records[0]["negative_rng_passing_u32_words"], 1431655765)
        self.assertEqual(records[0]["negative_rng_total_u32_words"], 1 << 32)
        self.assertEqual(records[0]["response_selector_2c"], "0x1F")
        self.assertFalse(records[0]["runtime_timing_mutated"])
        self.assertEqual(records[0]["runtime_timing_writers"], "")
        self.assertFalse(records[0]["runtime_substitution_block_mutated"])
        self.assertEqual(
            records[0]["substitution_block_flags"], "0x02008000"
        )
        self.assertEqual(records[1]["command_name"], "Exact Alias")
        self.assertEqual(records[1]["mapping_join"], "reference")
        self.assertEqual(records[1]["policy"], "mt_modulo_1_of_5_current_record")
        self.assertEqual(summary["records"], 2)
        self.assertEqual(
            summary["scope_counts"],
            {
                "primary": {"characters": 1, "records": 2},
                "auxiliary": {"characters": 0, "records": 0},
            },
        )
        self.assertEqual(summary["flagged_zero_to_negative_one"], 1)
        self.assertEqual(summary["exceptional_records"], 2)
        self.assertEqual(summary["substitution_block_flagged_records"], 1)
        self.assertEqual(summary["substitution_block_flagged_named"], 1)
        self.assertEqual(summary["substitution_block_flagged_exceptional"], 1)
        self.assertEqual(
            summary["substitution_block_flag_counts"], {"0x02008000": 1}
        )
        self.assertEqual(
            summary["response_selector_counts"], {"0x00": 1, "0x1F": 1}
        )
        self.assertEqual(summary["runtime_timing_mutated_records"], 0)
        self.assertEqual(summary["runtime_timing_mutated_named"], 0)
        self.assertEqual(
            summary["runtime_substitution_block_mutated_records"], 0
        )
        self.assertEqual(summary["runtime_timing_mutations"], [])
        self.assertEqual(summary["mapping_ids_in_primary_tables"], 2)
        self.assertEqual(summary["mapping_ids_in_auxiliary_tables"], 0)
        self.assertEqual(summary["mapping_ids_in_all_tables"], 2)
        self.assertEqual(summary["command_mapping_rows_unmatched"], 0)
        self.assertEqual(
            summary["command_mapping_instance_count_distribution"], {"1": 2}
        )
        self.assertEqual(summary["command_mapping_ids_with_multiple_instances"], 0)
        self.assertEqual(
            summary["command_mapping_ids_with_mixed_reliability"], 0
        )
        self.assertEqual(records[0]["command_mapping_instances"], 1)
        self.assertEqual(records[0]["command_mapping_policy_variants"], 1)

    def test_scan_separates_auxiliary_scope(self) -> None:
        elf = bytearray(0x700)
        primary_metadata = 0x00100000
        auxiliary_metadata = 0x00100080
        primary_action = 0x00100200
        auxiliary_action = 0x00100300
        primary_name = 0x00100400
        auxiliary_name = 0x00100420

        for metadata, action in (
            (primary_metadata, primary_action),
            (auxiliary_metadata, auxiliary_action),
        ):
            offset = metadata - CATALOG.VIRTUAL_TO_FILE_DELTA
            struct.pack_into("<H", elf, offset + 0x28, 1)
            struct.pack_into("<I", elf, offset + 0x2C, action)
        struct.pack_into(
            "<I",
            elf,
            primary_action - CATALOG.VIRTUAL_TO_FILE_DELTA + 0x08,
            primary_name,
        )
        struct.pack_into(
            "<I",
            elf,
            auxiliary_action - CATALOG.VIRTUAL_TO_FILE_DELTA + 0x08,
            auxiliary_name,
        )
        rows = [
            {
                "character": "Primary",
                "id": "1",
                "record_address": f"0x{primary_metadata:08X}",
            },
            {
                "character": "Auxiliary",
                "id": "0x1A",
                "record_address": f"0x{auxiliary_metadata:08X}",
                "catalog_scope": "auxiliary",
            },
        ]
        mappings = [
            {
                "id": "T1",
                "display_context": CATALOG.COMMAND_CONTEXT,
                "source_ref": (
                    f"NA2_SLPS@0x{primary_name - CATALOG.VIRTUAL_TO_FILE_DELTA:X}"
                ),
                "reference_refs": "",
                "donor": "Primary Move",
            },
            {
                "id": "T2",
                "display_context": CATALOG.COMMAND_CONTEXT,
                "source_ref": (
                    f"NA2_SLPS@0x{auxiliary_name - CATALOG.VIRTUAL_TO_FILE_DELTA:X}"
                ),
                "reference_refs": "",
                "donor": "Auxiliary Move",
            },
        ]

        records, summary = CATALOG.scan_action_catalog(bytes(elf), rows, mappings)

        self.assertEqual(
            [record["catalog_scope"] for record in records],
            ["primary", "auxiliary"],
        )
        self.assertEqual(
            summary["scope_counts"],
            {
                "primary": {"characters": 1, "records": 1},
                "auxiliary": {"characters": 1, "records": 1},
            },
        )
        self.assertEqual(summary["mapping_ids_in_primary_tables"], 1)
        self.assertEqual(summary["mapping_ids_in_auxiliary_tables"], 1)
        self.assertEqual(summary["mapping_ids_in_all_tables"], 2)

    def test_shared_mapping_reports_distinct_record_policies(self) -> None:
        elf = bytearray(0x500)
        metadata_address = 0x00100000
        metadata_offset = metadata_address - CATALOG.VIRTUAL_TO_FILE_DELTA
        action_base = 0x00100100
        action_offset = action_base - CATALOG.VIRTUAL_TO_FILE_DELTA
        name_pointer = 0x00100300

        struct.pack_into("<H", elf, metadata_offset + 0x28, 2)
        struct.pack_into("<I", elf, metadata_offset + 0x2C, action_base)
        for index in range(2):
            offset = action_offset + index * CATALOG.ACTION_RECORD_SIZE
            struct.pack_into("<I", elf, offset + 0x08, name_pointer)
        struct.pack_into("<I", elf, action_offset + 0x10, 0x00040000)
        second = action_offset + CATALOG.ACTION_RECORD_SIZE
        struct.pack_into("<b", elf, second + 0x1A, 1)
        rows = [
            {
                "character": "Shared Fighter",
                "id": "3",
                "record_address": f"0x{metadata_address:08X}",
            }
        ]
        mappings = [
            {
                "id": "T9",
                "display_context": CATALOG.COMMAND_CONTEXT,
                "source_ref": (
                    f"NA2_SLPS@0x{name_pointer - CATALOG.VIRTUAL_TO_FILE_DELTA:X}"
                ),
                "reference_refs": "",
                "donor": "Shared Attack",
            }
        ]

        records, summary = CATALOG.scan_action_catalog(bytes(elf), rows, mappings)

        self.assertEqual(records[0]["command_mapping_instances"], 2)
        self.assertEqual(records[0]["command_mapping_policy_variants"], 2)
        self.assertEqual(summary["command_mapping_ids_with_multiple_instances"], 1)
        self.assertEqual(
            summary["command_mapping_ids_with_mixed_reliability"], 1
        )
        self.assertEqual(summary["command_mapping_ids_with_mixed_timing"], 1)
        self.assertEqual(
            summary["command_mapping_ids_with_mixed_block_flags"], 0
        )
        self.assertEqual(
            summary["mixed_command_mapping_reliability"][0][
                "command_mapping_id"
            ],
            "T9",
        )

    def test_mapping_filter_accepts_id_or_exact_title(self) -> None:
        records = [
            {
                "command_mapping_id": "T1",
                "command_name": "First Attack",
            },
            {
                "command_mapping_id": "T2",
                "command_name": "Second Attack",
            },
        ]
        self.assertEqual(CATALOG._mapping_filter("t1", records), {"T1"})
        self.assertEqual(
            CATALOG._mapping_filter("SECOND ATTACK", records), {"T2"}
        )
        with self.assertRaisesRegex(ValueError, "unknown Command Chart"):
            CATALOG._mapping_filter("Missing", records)

    def test_known_runtime_mutation_inventory(self) -> None:
        mutations = CATALOG.RUNTIME_TIMING_MUTATIONS
        self.assertEqual(
            set(mutations),
            {
                (0x40, 0x2B),
                (0x40, 0x2C),
                (0x40, 0x2D),
                (0x43, 0x27),
                (0x45, 0x2A),
                (0x4C, 0x1E),
            },
        )
        self.assertEqual(
            sum(bool(item["block_mutated"]) for item in mutations.values()),
            4,
        )

    def test_timing_policy_clamps_only_positive_history_distance(self) -> None:
        self.assertEqual(
            CATALOG._timing_policy(7, 0),
            (7, "deterministic_current_plus_3_earlier"),
        )
        self.assertEqual(
            CATALOG._timing_policy(-3, 0),
            (-3, "mt_modulo_1_of_7_current_record"),
        )
        self.assertEqual(CATALOG._negative_rng_policy(0), (None, None))
        self.assertEqual(CATALOG._negative_rng_policy(-128), (257, 16711935))


if __name__ == "__main__":
    unittest.main()
