from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from na2_patcher.iso9660 import Iso9660


def directory_record(recorded_at: bytes) -> bytes:
    raw = bytearray(34)
    raw[0] = len(raw)
    raw[2:6] = (1).to_bytes(4, "little")
    raw[6:10] = (1).to_bytes(4, "big")
    raw[10:14] = (0).to_bytes(4, "little")
    raw[14:18] = (0).to_bytes(4, "big")
    raw[18:25] = recorded_at
    raw[25] = 0x02
    raw[32] = 1
    return bytes(raw)


class Iso9660TimestampTests(unittest.TestCase):
    def parser(self) -> Iso9660:
        parser = Iso9660.__new__(Iso9660)
        parser.file_size = 4096
        return parser

    def test_parses_recording_time_and_timezone(self) -> None:
        record = self.parser()._parse_record(
            directory_record(bytes((126, 7, 18, 12, 34, 56, 12))), "TEST"
        )
        self.assertEqual(
            record.recorded_at,
            datetime(2026, 7, 18, 12, 34, 56, tzinfo=timezone(timedelta(hours=3))),
        )

    def test_zero_recording_time_is_unspecified(self) -> None:
        record = self.parser()._parse_record(directory_record(b"\0" * 7), "TEST")
        self.assertIsNone(record.recorded_at)

    def test_preserves_directory_record_offset(self) -> None:
        record = self.parser()._parse_record(
            directory_record(b"\0" * 7),
            "TEST",
            0x1234,
        )
        self.assertEqual(record.directory_record_offset, 0x1234)


if __name__ == "__main__":
    unittest.main()
