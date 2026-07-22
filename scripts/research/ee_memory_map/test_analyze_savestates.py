from __future__ import annotations

import hashlib
import struct
import unittest
from pathlib import Path


from analyze_savestates import (
    HEAP_GLOBALS,
    MWO3_MAGIC,
    OVERLAY_BASE,
    MemoryMapError,
    observe_region,
    parse_allocator,
    parse_overlay,
    parse_state_identity,
)


class IdentityTests(unittest.TestCase):
    def test_parses_pcsx2_state_name(self) -> None:
        identity = parse_state_identity(Path("SLPS-25837 (c0659ad1).03.p2s"))
        self.assertEqual(identity.serial, "SLPS-25837")
        self.assertEqual(identity.crc, "C0659AD1")
        self.assertEqual(identity.slot, 3)

    def test_rejects_unrecognized_name(self) -> None:
        with self.assertRaises(MemoryMapError):
            parse_state_identity(Path("state.p2s"))


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
        for name, address in HEAP_GLOBALS.items():
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
            OVERLAY_BASE,
            MWO3_MAGIC,
            2,
            OVERLAY_BASE,
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
