from __future__ import annotations

import hashlib
import struct
import unittest
from pathlib import Path


from scripts.research.ee_memory_map.analyze_savestates import (
    MemoryMapError,
    _variant_for,
    observe_region,
    parse_allocator,
    parse_overlay,
    parse_state_identity,
)


DOCUMENTED_HEAP_GLOBALS = {
    "user_base": 0x00607380,
    "heap_end": 0x00607384,
    "tracked_bytes": 0x00607388,
    "peak_tracked_bytes": 0x0060738C,
    "allocation_count": 0x00607390,
    "unresolved_607394": 0x00607394,
    "base_sentinel": 0x00607398,
    "end_sentinel": 0x0060739C,
    "cached_largest_predecessor": 0x006073A0,
    "cached_largest_gap": 0x006073A4,
}
DOCUMENTED_OVERLAY_BASE = 0x006B3F00
DOCUMENTED_MWO3_MAGIC = 0x336F574D


class IdentityTests(unittest.TestCase):
    def test_parses_pcsx2_state_name(self) -> None:
        identity = parse_state_identity(Path("SLPS-25837 (c0659ad1).03.p2s"))
        self.assertEqual(identity.serial, "SLPS-25837")
        self.assertEqual(identity.crc, "C0659AD1")
        self.assertEqual(identity.slot, 3)

    def test_parses_project_state_name(self) -> None:
        identity = parse_state_identity(Path("SLOP-NA228 (7db97f53).06.p2s"))
        self.assertEqual(identity.serial, "SLOP-NA228")
        self.assertEqual(identity.crc, "7DB97F53")
        self.assertEqual(identity.slot, 6)

    def test_rejects_unrecognized_name(self) -> None:
        with self.assertRaises(MemoryMapError):
            parse_state_identity(Path("state.p2s"))

    def test_parses_e2e_transaction_state(self) -> None:
        path = Path(
            "e2e/.transactions/run-example/jobs/padded/suites/collection/"
            "capture/sstates/0039.p2s"
        )
        identity = parse_state_identity(path)
        self.assertEqual(identity.serial, "SLOP-NA228")
        self.assertEqual(identity.crc, "")
        self.assertEqual(identity.slot, 39)
        self.assertEqual(_variant_for(path, identity), "padded")

    def test_rejects_numeric_name_outside_e2e_transaction(self) -> None:
        with self.assertRaises(MemoryMapError):
            parse_state_identity(Path("0039.p2s"))


class AllocatorTests(unittest.TestCase):
    def _memory(self) -> bytearray:
        memory = bytearray(0x00900000)
        base = 0x008DD090
        first = 0x008DD0C0
        end = 0x008DD200

        values = {
            "user_base": base + 0x10,
            "heap_end": end,
            "tracked_bytes": 0x30,
            "peak_tracked_bytes": 0x50,
            "allocation_count": 1,
            "unresolved_607394": 0,
            "base_sentinel": base,
            "end_sentinel": end,
            "cached_largest_predecessor": first,
            "cached_largest_gap": end - (first + 0x30),
        }
        for name, address in DOCUMENTED_HEAP_GLOBALS.items():
            struct.pack_into("<I", memory, address, values[name])

        struct.pack_into("<IIII", memory, base, 0, first, 0x10, 0)
        # Only the low byte is the allocator flag; the upper bytes may retain
        # unrelated/stale data in real captures.
        struct.pack_into("<IIII", memory, first, base, end, 0x30, 0xAABBCC01)
        struct.pack_into("<IIII", memory, end, first, 0, 0x10, 0)
        return memory

    def test_walks_and_validates_allocator(self) -> None:
        observation = parse_allocator(self._memory())
        self.assertEqual(observation.walked_allocation_count, 1)
        self.assertEqual(observation.computed_total_free, 0x20 + 0x110)
        self.assertEqual(observation.computed_largest_gap, 0x110)
        self.assertEqual(observation.fragmentation_bytes, 0x20)
        self.assertEqual(observation.computed_tracked_bytes, 0x30)
        self.assertEqual(observation.computed_untracked_bytes, 0)
        self.assertEqual(observation.flag_counts, {1: 1})

    def test_rejects_broken_back_link(self) -> None:
        memory = self._memory()
        struct.pack_into("<I", memory, 0x008DD0C0, 0)
        with self.assertRaises(MemoryMapError):
            parse_allocator(memory)


class OverlayTests(unittest.TestCase):
    def test_parses_adv_overlay(self) -> None:
        memory = bytearray(0x00900000)
        struct.pack_into(
            "<8I",
            memory,
            DOCUMENTED_OVERLAY_BASE,
            DOCUMENTED_MWO3_MAGIC,
            2,
            DOCUMENTED_OVERLAY_BASE,
            0x0014E0C0,
            0x000C4E00,
            0x00000400,
            0x008C6DB0,
            0x008C6DE4,
        )
        observation = parse_overlay(memory)
        self.assertEqual(observation.name, "ADV.BIN")
        self.assertEqual(observation.effective_end, 0x008C7200)
        self.assertEqual(observation.phase_slack, 0x15E80)

    def test_parses_no_overlay(self) -> None:
        observation = parse_overlay(bytearray(0x00900000))
        self.assertEqual(observation.name, "none")
        self.assertEqual(observation.phase_slack, 0x229180)


class RegionTests(unittest.TestCase):
    def test_reports_region_content(self) -> None:
        memory = b"\x00\x01\x00\x02"
        observation = observe_region(memory, "sample", 0, len(memory))
        self.assertEqual(observation.nonzero_bytes, 2)
        self.assertEqual(
            observation.sha256, hashlib.sha256(memory).hexdigest().upper()
        )


if __name__ == "__main__":
    unittest.main()
