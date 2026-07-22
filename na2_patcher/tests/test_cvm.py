from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na2_patcher.cvm import CvmError, CvmIso, _crypt_sector, _rofs_key
from na2_patcher.image_assembler.iso9660 import Iso9660, IsoRecord, SECTOR
from na2_patcher.project_paths import load_project_paths


PASSWORD = "cc2fuku"


def iso_record(extent: int, size: int, identifier: bytes, *, directory: bool) -> bytes:
    length = 33 + len(identifier)
    if len(identifier) % 2 == 0:
        length += 1
    raw = bytearray(length)
    raw[0] = length
    raw[2:6] = extent.to_bytes(4, "little")
    raw[6:10] = extent.to_bytes(4, "big")
    raw[10:14] = size.to_bytes(4, "little")
    raw[14:18] = size.to_bytes(4, "big")
    raw[25] = 0x02 if directory else 0
    raw[28:30] = (1).to_bytes(2, "little")
    raw[30:32] = (1).to_bytes(2, "big")
    raw[32] = len(identifier)
    raw[33 : 33 + len(identifier)] = identifier
    return bytes(raw)


def synthetic_cvm(*, encrypted: bool = True) -> tuple[bytes, bytes, bytes]:
    file_payload = b"read-only CVM payload"
    inner = bytearray(22 * SECTOR)
    root_record = iso_record(20, SECTOR, b"\0", directory=True)

    pvd = bytearray(SECTOR)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[156 : 156 + len(root_record)] = root_record
    inner[16 * SECTOR : 17 * SECTOR] = pvd

    terminator = bytearray(SECTOR)
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1
    inner[17 * SECTOR : 18 * SECTOR] = terminator

    directory = bytearray(SECTOR)
    records = (
        root_record,
        iso_record(20, SECTOR, b"\x01", directory=True),
        iso_record(21, len(file_payload), b"HELLO.BIN;1", directory=False),
    )
    offset = 0
    for record in records:
        directory[offset : offset + len(record)] = record
        offset += len(record)
    inner[20 * SECTOR : 21 * SECTOR] = directory
    inner[21 * SECTOR : 21 * SECTOR + len(file_payload)] = file_payload

    iso_start_sector = 3
    cvm = bytearray(iso_start_sector * SECTOR + len(inner))
    cvmh = bytearray(SECTOR - 12)
    cvmh[0x24:0x28] = (0x10 if encrypted else 0).to_bytes(4, "big")
    cvmh[0x7C:0x80] = iso_start_sector.to_bytes(4, "big")
    cvm[0:4] = b"CVMH"
    cvm[4:12] = len(cvmh).to_bytes(8, "big")
    cvm[12:SECTOR] = cvmh

    zone_payload_offset = SECTOR + 12
    zone_length = len(cvm) - zone_payload_offset
    cvm[SECTOR : SECTOR + 4] = b"ZONE"
    cvm[SECTOR + 4 : SECTOR + 12] = zone_length.to_bytes(8, "big")
    cvm[zone_payload_offset + 0x20 : zone_payload_offset + 0x24] = (
        iso_start_sector.to_bytes(4, "big")
    )
    cvm[zone_payload_offset + 0x24 : zone_payload_offset + 0x2C] = len(inner).to_bytes(
        8, "big"
    )

    inner_on_disc = bytearray(inner)
    if encrypted:
        key = _rofs_key(PASSWORD)
        for sector in range(16, 21):
            start = sector * SECTOR
            inner_on_disc[start : start + SECTOR] = _crypt_sector(
                bytes(inner_on_disc[start : start + SECTOR]),
                sector,
                key,
            )
    cvm[iso_start_sector * SECTOR :] = inner_on_disc
    return bytes(cvm), bytes(inner), file_payload


class CvmTests(unittest.TestCase):
    def open_synthetic(self, *, encrypted: bool = True) -> tuple[CvmIso, Path, bytes, bytes]:
        cvm, inner, payload = synthetic_cvm(encrypted=encrypted)
        self.temporary = tempfile.TemporaryDirectory()
        path = Path(self.temporary.name) / "outer.iso"
        prefix = b"P" * (2 * SECTOR)
        path.write_bytes(prefix + cvm + b"trailing data")
        outer = SimpleNamespace(
            path=path,
            by_path={
                "DATA/DATA.CVM": IsoRecord(
                    path="DATA/DATA.CVM",
                    is_dir=False,
                    extent=2,
                    size=len(cvm),
                    recorded_at=None,
                )
            },
        )
        reader = CvmIso.from_iso(outer)
        return reader, path, inner, payload

    def tearDown(self) -> None:
        temporary = getattr(self, "temporary", None)
        if temporary is not None:
            temporary.cleanup()

    def test_rofs_password_key_matches_supported_games(self) -> None:
        self.assertEqual(_rofs_key(PASSWORD).hex().upper(), "5BD558AB553D41BD")

    def test_reads_encrypted_inner_iso_without_extracting_it(self) -> None:
        reader, path, inner, payload = self.open_synthetic()
        before = path.read_bytes()

        self.assertTrue(reader.toc_encrypted)
        self.assertEqual(reader.header_size, 3 * SECTOR)
        self.assertEqual(reader.iso_length, len(inner))
        self.assertEqual(reader.end_toc_sector, 21)
        self.assertEqual(
            reader.read_iso_bytes(16 * SECTOR, 5 * SECTOR),
            inner[16 * SECTOR : 21 * SECTOR],
        )
        self.assertEqual(reader.read_file("hello.bin"), payload)
        self.assertEqual(reader.by_path.keys(), {"", "HELLO.BIN"})

        record = reader.record("HELLO.BIN")
        expected_cvm_offset = 3 * SECTOR + 21 * SECTOR
        self.assertEqual(reader.member_cvm_offset(record), expected_cvm_offset)
        self.assertEqual(reader.member_image_offset(record), 2 * SECTOR + expected_cvm_offset)
        self.assertEqual(path.read_bytes(), before)

    def test_reads_unencrypted_toc(self) -> None:
        reader, _, inner, payload = self.open_synthetic(encrypted=False)
        self.assertFalse(reader.toc_encrypted)
        self.assertEqual(reader.read_iso_bytes(0, len(inner)), inner)
        self.assertEqual(reader.read_file("HELLO.BIN"), payload)

    def test_rejects_wrong_password(self) -> None:
        cvm, _, _ = synthetic_cvm()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "DATA.CVM"
            path.write_bytes(cvm)
            with self.assertRaisesRegex(CvmError, "password may be wrong"):
                CvmIso(path, password="incorrect")

    def test_rejects_cvm_range_outside_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.bin"
            path.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "outside the image"):
                CvmIso(path, cvm_offset=4, cvm_size=2)


class CvmExtractedReferenceTests(unittest.TestCase):
    def test_supported_sources_match_existing_extractions_when_available(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        paths = load_project_paths(repository, allow_missing=True)
        source = paths.roots["source"]
        cases = ("NA2.iso", "NUN5.iso")
        required = [
            source / name
            for name in cases
        ] + [
            source / (name + ".files") / "DATA" / "DATA.CVM.files" / "DATA.CVM.iso"
            for name in cases
        ]
        if not all(path.is_file() for path in required):
            self.skipTest("Original and extracted NA2/NUN5 references are unavailable")

        sample = "MODENAME/MODE2KDV.CCS"
        for name in cases:
            with self.subTest(image=name):
                outer = Iso9660(source / name)
                direct = CvmIso.from_iso(outer)
                extracted_root = source / (name + ".files") / "DATA" / "DATA.CVM.files"
                extracted = Iso9660(extracted_root / "DATA.CVM.iso")
                self.assertEqual(
                    direct.header,
                    (extracted_root / "DATA.CVM.hdr").read_bytes(),
                )
                toc_size = direct.end_toc_sector * SECTOR
                with (extracted_root / "DATA.CVM.iso").open("rb") as handle:
                    self.assertEqual(
                        direct.read_iso_bytes(0, toc_size),
                        handle.read(toc_size),
                    )
                self.assertEqual(
                    [
                        (record.path, record.is_dir, record.extent, record.size)
                        for record in direct.records
                    ],
                    [
                        (record.path, record.is_dir, record.extent, record.size)
                        for record in extracted.records
                    ],
                )
                self.assertEqual(
                    direct.read_file(sample),
                    extracted.read_file(extracted.by_path[sample]),
                )


if __name__ == "__main__":
    unittest.main()
