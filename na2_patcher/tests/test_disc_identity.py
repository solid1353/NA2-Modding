from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na2_patcher.iso9660 import IsoRecord
from na2_patcher.modules.disc_identity.engine import (
    DiscIdentity,
    apply_iso_directory_identifier,
    apply_system_cnf,
    serial_from_boot_path,
)


class DiscIdentityTests(unittest.TestCase):
    def identity(self) -> DiscIdentity:
        return DiscIdentity(
            source_boot_path="SLPS_258.37",
            replacement_boot_path="SLPS_222.28",
            reason="test",
        )

    def test_serial_from_boot_path(self) -> None:
        self.assertEqual(serial_from_boot_path("SLPS_222.28"), "SLPS-22228")

    def test_system_cnf_replacement_preserves_size(self) -> None:
        original = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\nVER = 1.00\r\n"
        updated, edit = apply_system_cnf(self.identity(), original)
        self.assertEqual(len(updated), len(original))
        self.assertIn(b"SLPS_222.28", updated)
        self.assertNotIn(b"SLPS_258.37", updated)
        self.assertEqual(edit["target"], "SYSTEM.CNF")

    def test_iso_directory_identifier_replacement_preserves_record(self) -> None:
        identity = self.identity()
        source = b"SLPS_258.37;1"
        replacement = b"SLPS_222.28;1"
        record_offset = 64
        record = bytearray(33 + len(source) + 1)
        record[0] = len(record)
        record[32] = len(source)
        record[33:33 + len(source)] = source

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.iso"
            image = bytearray(256)
            image[record_offset:record_offset + len(record)] = record
            path.write_bytes(image)
            iso = SimpleNamespace(
                path=path,
                by_path={
                    identity.source_boot_path: IsoRecord(
                        path=identity.source_boot_path,
                        is_dir=False,
                        extent=1,
                        size=1,
                        recorded_at=None,
                        directory_record_offset=record_offset,
                    )
                },
            )

            edit = apply_iso_directory_identifier(identity, iso)
            result = path.read_bytes()

        self.assertEqual(len(result), len(image))
        self.assertEqual(
            result[record_offset + 33:record_offset + 33 + len(source)],
            replacement,
        )
        self.assertEqual(edit["target"], "<ISO9660 root directory>")


if __name__ == "__main__":
    unittest.main()
