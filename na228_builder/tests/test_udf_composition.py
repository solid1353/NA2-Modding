from __future__ import annotations

import binascii
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.image_assembler.iso9660 import Iso9660, SECTOR, compose_filesystems
from na228_builder.image_assembler.udf import Udf


SECTORS = 400
PARTITION_START = 266
PARTITION_LENGTH = SECTORS - PARTITION_START - 1
RECORDED_AT = bytes((126, 7, 20, 12, 0, 0, 12))


def set_u16(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", raw, offset, value)


def set_u32(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", raw, offset, value)


def set_u64(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<Q", raw, offset, value)


def set_both_u32(raw: bytearray, offset: int, value: int) -> None:
    raw[offset:offset + 4] = value.to_bytes(4, "little")
    raw[offset + 4:offset + 8] = value.to_bytes(4, "big")


def set_both_u16(raw: bytearray, offset: int, value: int) -> None:
    raw[offset:offset + 2] = value.to_bytes(2, "little")
    raw[offset + 2:offset + 4] = value.to_bytes(2, "big")


def finish_udf_tag(
    raw: bytearray,
    identifier: int,
    location: int,
    *,
    crc_length: int | None = None,
) -> bytes:
    set_u16(raw, 0, identifier)
    set_u16(raw, 2, 2)
    raw[4] = 0
    raw[5] = 0
    set_u16(raw, 6, 0)
    length = len(raw) - 16 if crc_length is None else crc_length
    set_u16(raw, 10, length)
    set_u32(raw, 12, location)
    set_u16(raw, 8, binascii.crc_hqx(bytes(raw[16:16 + length]), 0))
    raw[4] = (sum(raw[:4]) + sum(raw[5:16])) & 0xFF
    return bytes(raw)


def iso_record(
    identifier: bytes,
    *,
    extent: int,
    size: int,
    is_dir: bool,
    length: int | None = None,
) -> bytes:
    minimum = 33 + len(identifier) + (1 if len(identifier) % 2 == 0 else 0)
    record_length = minimum if length is None else length
    raw = bytearray(record_length)
    raw[0] = record_length
    set_both_u32(raw, 2, extent)
    set_both_u32(raw, 10, size)
    raw[18:25] = RECORDED_AT
    raw[25] = 2 if is_dir else 0
    raw[28:30] = (1).to_bytes(2, "little")
    raw[30:32] = (1).to_bytes(2, "big")
    raw[32] = len(identifier)
    raw[33:33 + len(identifier)] = identifier
    return bytes(raw)


def cs0(name: str) -> bytes:
    return b"\x10" + name.encode("utf-16-be")


def path_table_record(
    identifier: bytes,
    *,
    extent: int,
    parent_number: int,
    byteorder: str,
) -> bytes:
    length = 8 + len(identifier) + (len(identifier) & 1)
    raw = bytearray(length)
    raw[0] = len(identifier)
    raw[1] = 0
    raw[2:6] = extent.to_bytes(4, byteorder)
    raw[6:8] = parent_number.to_bytes(2, byteorder)
    raw[8:8 + len(identifier)] = identifier
    return bytes(raw)


def udf_fid(
    name: str | None,
    *,
    icb_lbn: int,
    icb_length: int,
    directory: bool,
    location: int,
    parent: bool = False,
) -> bytes:
    identifier = b"" if name is None else cs0(name)
    length = (38 + len(identifier) + 3) & ~3
    raw = bytearray(length)
    set_u16(raw, 16, 1)
    raw[18] = (2 if directory else 0) | (8 if parent else 0)
    raw[19] = len(identifier)
    set_u32(raw, 20, icb_length)
    set_u32(raw, 24, icb_lbn)
    set_u16(raw, 28, 0)
    set_u16(raw, 36, 0)
    raw[38:38 + len(identifier)] = identifier
    return finish_udf_tag(raw, 257, location)


def udf_file_entry(
    *,
    icb_lbn: int,
    file_type: int,
    information_length: int,
    data_lbn: int,
    unique_id: int,
) -> bytes:
    raw = bytearray(184)
    set_u16(raw, 20, 4)
    raw[27] = file_type
    set_u16(raw, 34, 0)
    set_u32(raw, 36, 0xFFFFFFFF)
    set_u32(raw, 40, 0xFFFFFFFF)
    set_u32(raw, 44, 0x14A5)
    set_u16(raw, 48, 1)
    set_u64(raw, 56, information_length)
    set_u64(raw, 64, (information_length + SECTOR - 1) // SECTOR)
    timestamp = struct.pack(
        "<BBHBBBBBBBB", 0, 0, 2026, 7, 20, 12, 0, 0, 0, 0, 0
    )
    raw[72:84] = timestamp
    raw[84:96] = timestamp
    raw[96:108] = timestamp
    set_u32(raw, 108, 1)
    set_u64(raw, 160, unique_id)
    set_u32(raw, 168, 0)
    set_u32(raw, 172, 8)
    set_u32(raw, 176, information_length)
    set_u32(raw, 180, data_lbn)
    return finish_udf_tag(raw, 261, icb_lbn)


def udf_sector_descriptor(identifier: int, location: int) -> bytearray:
    raw = bytearray(SECTOR)
    set_u16(raw, 0, identifier)
    set_u16(raw, 2, 2)
    set_u16(raw, 10, SECTOR - 16)
    set_u32(raw, 12, location)
    return raw


def udf_primary_descriptor(location: int) -> bytes:
    raw = udf_sector_descriptor(1, location)
    set_u32(raw, 16, 1)
    set_u32(raw, 20, 0)
    raw[24:56] = b"\x08SYNTHETIC UDF BRIDGE".ljust(31, b"\0") + b"\x15"
    set_u16(raw, 56, 1)
    set_u16(raw, 58, 1)
    set_u16(raw, 60, 2)
    set_u16(raw, 62, 3)
    set_u32(raw, 64, 1)
    set_u32(raw, 68, 1)
    raw[72:200] = b"\x08SYNTHETIC".ljust(127, b"\0") + b"\x0A"
    chars = b"\0OSTA Compressed Unicode".ljust(64, b"\0")
    raw[200:264] = chars
    raw[264:328] = chars
    struct.pack_into("<BBHBBBBBBBB", raw, 376, 0, 0, 2026, 7, 20, 12, 0, 0, 0, 0, 0)
    return finish_udf_tag(raw, 1, location)


def make_bridge_iso(path: Path) -> bytes:
    image = bytearray(SECTORS * SECTOR)

    root_extent = 80
    prg_extent = 81
    flist_extent = 310
    boot_extent = 311
    etc_extent = 312
    flist = b"prg\\ETC.bin\r\n"
    boot = b"BOOT"
    etc = b"ETC!"

    root_records = b"".join(
        (
            iso_record(b"\x00", extent=root_extent, size=0, is_dir=True, length=48),
            iso_record(b"\x01", extent=root_extent, size=0, is_dir=True, length=48),
            iso_record(b"PRG;1", extent=prg_extent, size=0, is_dir=True, length=56),
            iso_record(b"FLIST.DIR;1", extent=flist_extent, size=len(flist), is_dir=False),
            iso_record(b"SLPS_258.37;1", extent=boot_extent, size=len(boot), is_dir=False),
        )
    )
    root_size = len(root_records)
    root_records = bytearray(root_records)
    for offset in (10, 58):
        set_both_u32(root_records, offset, root_size)
    set_both_u32(root_records, 48 + 48 + 10, 0)

    prg_records = b"".join(
        (
            iso_record(b"\x00", extent=prg_extent, size=0, is_dir=True, length=48),
            iso_record(b"\x01", extent=root_extent, size=root_size, is_dir=True, length=48),
            iso_record(b"ETC.BIN;1", extent=etc_extent, size=len(etc), is_dir=False),
        )
    )
    prg_size = len(prg_records)
    prg_records = bytearray(prg_records)
    set_both_u32(prg_records, 10, prg_size)
    set_both_u32(root_records, 48 + 48 + 10, prg_size)

    pvd = bytearray(SECTOR)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[8:40] = b" " * 32
    pvd[40:72] = b"SYNTHETIC UDF BRIDGE".ljust(32, b" ")
    set_both_u32(pvd, 80, SECTORS)
    set_both_u16(pvd, 120, 1)
    set_both_u16(pvd, 124, 1)
    set_both_u16(pvd, 128, SECTOR)
    little_path_table = b"".join(
        (
            path_table_record(
                b"\x00", extent=root_extent, parent_number=1, byteorder="little"
            ),
            path_table_record(
                b"PRG", extent=prg_extent, parent_number=1, byteorder="little"
            ),
        )
    )
    big_path_table = b"".join(
        (
            path_table_record(
                b"\x00", extent=root_extent, parent_number=1, byteorder="big"
            ),
            path_table_record(
                b"PRG", extent=prg_extent, parent_number=1, byteorder="big"
            ),
        )
    )
    set_both_u32(pvd, 132, len(little_path_table))
    set_u32(pvd, 140, 70)
    pvd[148:152] = (71).to_bytes(4, "big")
    root_pvd = iso_record(
        b"\x00", extent=root_extent, size=root_size, is_dir=True
    )
    pvd[156:156 + len(root_pvd)] = root_pvd
    pvd[881] = 1
    image[16 * SECTOR:17 * SECTOR] = pvd
    image[70 * SECTOR:70 * SECTOR + len(little_path_table)] = little_path_table
    image[71 * SECTOR:71 * SECTOR + len(big_path_table)] = big_path_table

    terminator = bytearray(SECTOR)
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1
    image[17 * SECTOR:18 * SECTOR] = terminator
    for sector, signature in ((18, b"BEA01"), (19, b"NSR02"), (20, b"TEA01")):
        vrs = bytearray(SECTOR)
        vrs[0] = 0
        vrs[1:6] = signature
        vrs[6] = 1
        image[sector * SECTOR:(sector + 1) * SECTOR] = vrs

    image[root_extent * SECTOR:root_extent * SECTOR + root_size] = root_records
    image[prg_extent * SECTOR:prg_extent * SECTOR + prg_size] = prg_records
    image[flist_extent * SECTOR:flist_extent * SECTOR + len(flist)] = flist
    image[boot_extent * SECTOR:boot_extent * SECTOR + len(boot)] = boot
    image[etc_extent * SECTOR:etc_extent * SECTOR + len(etc)] = etc

    for sector in (256, SECTORS - 1):
        anchor = udf_sector_descriptor(2, sector)
        set_u32(anchor, 16, 16 * SECTOR)
        set_u32(anchor, 20, 32)
        set_u32(anchor, 24, 16 * SECTOR)
        set_u32(anchor, 28, 48)
        image[sector * SECTOR:(sector + 1) * SECTOR] = finish_udf_tag(
            anchor, 2, sector
        )

    for sector in (32, 48):
        image[sector * SECTOR:(sector + 1) * SECTOR] = udf_primary_descriptor(
            sector
        )

    for sector in (33, 49):
        partition = udf_sector_descriptor(5, sector)
        set_u32(partition, 16, 2)
        set_u16(partition, 20, 1)
        set_u16(partition, 22, 0)
        partition[24:31] = b"\x02+NSR02"
        set_u32(partition, 184, 1)
        set_u32(partition, 188, PARTITION_START)
        set_u32(partition, 192, PARTITION_LENGTH)
        image[sector * SECTOR:(sector + 1) * SECTOR] = finish_udf_tag(
            partition, 5, sector
        )

    for sector in (34, 50):
        logical = udf_sector_descriptor(6, sector)
        set_u32(logical, 16, 3)
        set_u32(logical, 212, SECTOR)
        logical[216:248] = b"\0*OSTA UDF Compliant".ljust(32, b"\0")
        set_u32(logical, 248, SECTOR)
        set_u32(logical, 252, 0)
        set_u16(logical, 256, 0)
        set_u32(logical, 264, 6)
        set_u32(logical, 268, 1)
        set_u32(logical, 432, 2 * SECTOR)
        set_u32(logical, 436, 64)
        logical[440:446] = b"\x01\x06\x01\x00\x00\x00"
        image[sector * SECTOR:(sector + 1) * SECTOR] = finish_udf_tag(
            logical, 6, sector
        )

    for sector in (35, 51):
        descriptor = udf_sector_descriptor(8, sector)
        image[sector * SECTOR:(sector + 1) * SECTOR] = finish_udf_tag(
            descriptor, 8, sector
        )

    integrity = udf_sector_descriptor(9, 64)
    struct.pack_into(
        "<BBHBBBBBBBB", integrity, 16, 0, 0, 2026, 7, 20, 12, 0, 0, 0, 0, 0
    )
    set_u32(integrity, 28, 1)
    set_u32(integrity, 72, 1)
    set_u32(integrity, 76, 48)
    set_u32(integrity, 80, 0)
    set_u32(integrity, 84, PARTITION_LENGTH)
    integrity[88:120] = b"\0TEST" + b"\0" * 27
    set_u32(integrity, 120, 3)
    set_u32(integrity, 124, 2)
    image[64 * SECTOR:65 * SECTOR] = finish_udf_tag(integrity, 9, 64)
    integrity_terminator = udf_sector_descriptor(8, 65)
    image[65 * SECTOR:66 * SECTOR] = finish_udf_tag(
        integrity_terminator, 8, 65
    )

    file_set = udf_sector_descriptor(256, 0)
    struct.pack_into(
        "<BBHBBBBBBBB", file_set, 16, 0, 0, 2026, 7, 20, 12, 0, 0, 0, 0, 0
    )
    set_u16(file_set, 28, 3)
    set_u16(file_set, 30, 3)
    set_u32(file_set, 32, 1)
    set_u32(file_set, 36, 1)
    set_u32(file_set, 400, 184)
    set_u32(file_set, 404, 4)
    set_u16(file_set, 408, 0)
    file_set[416:448] = b"\0*OSTA UDF Compliant".ljust(32, b"\0")
    image[PARTITION_START * SECTOR:(PARTITION_START + 1) * SECTOR] = finish_udf_tag(
        file_set, 256, 0
    )

    file_set_terminator = udf_sector_descriptor(8, PARTITION_START + 1)
    image[(PARTITION_START + 1) * SECTOR:(PARTITION_START + 2) * SECTOR] = (
        finish_udf_tag(file_set_terminator, 8, PARTITION_START + 1)
    )

    root_fids = b"".join(
        (
            udf_fid(None, icb_lbn=4, icb_length=184, directory=True, location=2, parent=True),
            udf_fid("PRG", icb_lbn=5, icb_length=184, directory=True, location=2),
            udf_fid("FLIST.DIR", icb_lbn=6, icb_length=184, directory=False, location=2),
            udf_fid("SLPS_258.37", icb_lbn=7, icb_length=184, directory=False, location=2),
        )
    )
    prg_fids = b"".join(
        (
            udf_fid(None, icb_lbn=5, icb_length=184, directory=True, location=3, parent=True),
            udf_fid("ETC.BIN", icb_lbn=8, icb_length=184, directory=False, location=3),
        )
    )
    image[(PARTITION_START + 2) * SECTOR:(PARTITION_START + 2) * SECTOR + len(root_fids)] = root_fids
    image[(PARTITION_START + 3) * SECTOR:(PARTITION_START + 3) * SECTOR + len(prg_fids)] = prg_fids

    entries = (
        (4, 4, len(root_fids), 2, 0),
        (5, 4, len(prg_fids), 3, 16),
        (6, 5, len(flist), flist_extent - PARTITION_START, 17),
        (7, 5, len(boot), boot_extent - PARTITION_START, 18),
        (8, 5, len(etc), etc_extent - PARTITION_START, 19),
    )
    for icb, file_type, size, data_lbn, unique_id in entries:
        entry = udf_file_entry(
            icb_lbn=icb,
            file_type=file_type,
            information_length=size,
            data_lbn=data_lbn,
            unique_id=unique_id,
        )
        offset = (PARTITION_START + icb) * SECTOR
        image[offset:offset + len(entry)] = entry

    data = bytes(image)
    path.write_bytes(data)
    return data


def rename_iso_boot(path: Path) -> None:
    iso = Iso9660(path)
    record = iso.by_path["SLPS_258.37"]
    assert record.directory_record_offset is not None
    old_identifier = b"SLPS_258.37;1"
    new_identifier = b"SLOP_NA2.28;1"
    with path.open("r+b") as handle:
        handle.seek(record.directory_record_offset + 33)
        if handle.read(len(old_identifier)) != old_identifier:
            raise AssertionError("unexpected synthetic boot identifier")
        handle.seek(record.directory_record_offset + 33)
        handle.write(new_identifier)


class UdfCompositionTests(unittest.TestCase):
    def test_mirrors_insertions_and_existing_rename_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            first = root / "first.iso"
            second = root / "second.iso"
            source_data = make_bridge_iso(source)
            shutil.copyfile(source, first)
            shutil.copyfile(source, second)
            rename_iso_boot(first)
            rename_iso_boot(second)

            payloads = {
                "PRG/MOD.BIN": b"M" * 3000,
                "PRG/TEXTENG.BIN": b"T" * 100,
            }
            first_result = compose_filesystems(
                first,
                payloads,
                udf_renames={"SLPS_258.37": "SLOP_NA2.28"},
            )
            second_result = compose_filesystems(
                second,
                payloads,
                udf_renames={"SLPS_258.37": "SLOP_NA2.28"},
            )

            self.assertEqual(source.read_bytes(), source_data)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual([item.extent for item in first_result.insertions], [313, 315])
            self.assertTrue(
                all(item.udf_file_entry_offset is not None for item in first_result.insertions)
            )
            self.assertEqual(len(first_result.udf_renames), 1)

            iso = Iso9660(first)
            udf = Udf(first)
            self.assertEqual(
                {(record.path, record.is_dir) for record in iso.records},
                {(record.path, record.is_dir) for record in udf.records},
            )
            self.assertNotIn("SLPS_258.37", udf.by_path)
            self.assertIn("SLOP_NA2.28", udf.by_path)
            self.assertEqual(udf.recorded_file_count, 5)
            for path, payload in payloads.items():
                record = udf.by_path[path]
                self.assertEqual(udf.read_file(record), payload)
                self.assertEqual(udf.absolute_extent(record), iso.by_path[path].extent)

    def test_rejects_stale_udf_tree_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            original = make_bridge_iso(image)
            rename_iso_boot(image)
            with self.assertRaisesRegex(RuntimeError, "bridge tree mismatch"):
                compose_filesystems(image, {"PRG/MOD.BIN": b"mod"})
            self.assertNotEqual(image.read_bytes(), original)
            self.assertNotIn("PRG/MOD.BIN", Iso9660(image).by_path)

    def test_rejects_corrupt_udf_descriptor_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_bridge_iso(image)
            raw = bytearray(image.read_bytes())
            raw[33 * SECTOR + 188] ^= 1
            image.write_bytes(raw)
            before = image.read_bytes()
            with self.assertRaisesRegex(RuntimeError, "descriptor CRC"):
                compose_filesystems(image, {"PRG/MOD.BIN": b"mod"})
            self.assertEqual(image.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
