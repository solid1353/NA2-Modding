from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from na228_builder.image_assembler.assembler import (
    assemble_image,
    assemble_image_digest,
    building_image_path,
)
from na228_builder.image_assembler.iso9660 import SECTOR, Iso9660, insert_files
from na228_builder.image_assembler.operations import (
    AssemblyPlan,
    FileInsertion,
    FileReplacement,
)


RECORDED_AT = bytes((126, 7, 19, 12, 0, 0, 12))


def set_both_u32(raw: bytearray, offset: int, value: int) -> None:
    raw[offset:offset + 4] = value.to_bytes(4, "little")
    raw[offset + 4:offset + 8] = value.to_bytes(4, "big")


def directory_record(
    identifier: bytes,
    *,
    extent: int,
    size: int,
    is_dir: bool,
    length: int | None = None,
) -> bytes:
    minimum = 33 + len(identifier) + (1 if len(identifier) % 2 == 0 else 0)
    record_length = length if length is not None else minimum
    if record_length < minimum:
        raise ValueError("synthetic record is too short")
    raw = bytearray(record_length)
    raw[0] = record_length
    set_both_u32(raw, 2, extent)
    set_both_u32(raw, 10, size)
    raw[18:25] = RECORDED_AT
    raw[25] = 0x02 if is_dir else 0
    raw[28:30] = (1).to_bytes(2, "little")
    raw[30:32] = (1).to_bytes(2, "big")
    raw[32] = len(identifier)
    raw[33:33 + len(identifier)] = identifier
    return bytes(raw)


def make_iso(
    path: Path,
    *,
    sectors: int = 40,
    prg_size: int = 264,
    dirty_tail_sectors: tuple[int, ...] = (),
    dirty_append_area: bool = False,
) -> bytes:
    image = bytearray(sectors * SECTOR)
    root_extent = 20
    prg_extent = 21
    root_size = 152

    pvd = bytearray(SECTOR)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    set_both_u32(pvd, 80, sectors)
    root_pvd = directory_record(
        b"\x00", extent=root_extent, size=root_size, is_dir=True
    )
    pvd[156:156 + len(root_pvd)] = root_pvd
    image[16 * SECTOR:17 * SECTOR] = pvd

    terminator = bytearray(SECTOR)
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1
    image[17 * SECTOR:18 * SECTOR] = terminator

    root_records = b"".join(
        (
            directory_record(
                b"\x00", extent=root_extent, size=root_size, is_dir=True, length=48
            ),
            directory_record(
                b"\x01", extent=root_extent, size=root_size, is_dir=True, length=48
            ),
            directory_record(
                b"PRG;1", extent=prg_extent, size=prg_size, is_dir=True, length=56
            ),
        )
    )
    image[root_extent * SECTOR:root_extent * SECTOR + len(root_records)] = root_records

    prg_records = b"".join(
        (
            directory_record(
                b"\x00", extent=prg_extent, size=prg_size, is_dir=True, length=48
            ),
            directory_record(
                b"\x01", extent=root_extent, size=root_size, is_dir=True, length=48
            ),
            directory_record(
                b"ADV.BIN;1", extent=22, size=4, is_dir=False, length=56
            ),
            directory_record(
                b"BTL.BIN;1", extent=23, size=4, is_dir=False, length=56
            ),
            directory_record(
                b"ETC.BIN;1", extent=24, size=4, is_dir=False, length=56
            ),
        )
    )
    image[prg_extent * SECTOR:prg_extent * SECTOR + len(prg_records)] = prg_records
    image[22 * SECTOR:22 * SECTOR + 4] = b"ADV!"
    image[23 * SECTOR:23 * SECTOR + 4] = b"BTL!"
    image[24 * SECTOR:24 * SECTOR + 4] = b"ETC!"

    for sector in dirty_tail_sectors:
        image[sector * SECTOR] = 0xA5
    if dirty_append_area:
        image[prg_extent * SECTOR + prg_size] = 0xA5
    image[-14:] = b"TAIL-SENTINEL!"
    data = bytes(image)
    path.write_bytes(data)
    return data


class IsoInsertionTests(unittest.TestCase):
    def test_virtual_digest_matches_verified_staged_assembly_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.iso"
            output_path = root / "retained.iso"
            source_data = make_iso(source_path)
            plan = AssemblyPlan(
                replacements=(
                    FileReplacement(
                        "PRG/BTL.BIN",
                        b"BTL!",
                        b"NEW!",
                        "test",
                        "replace fixture file",
                    ),
                ),
                insertions=(
                    FileInsertion(
                        "PRG/MOD.BIN",
                        b"M" * 3000,
                        "test",
                        "insert fixture file",
                    ),
                ),
            )

            retained = assemble_image(source_path, output_path, plan)
            staged_path = building_image_path(output_path)
            expected_hash = hashlib.sha256(staged_path.read_bytes()).hexdigest().upper()
            virtual = assemble_image_digest(source_path, plan)

            self.assertEqual(virtual.assembly, retained)
            self.assertEqual(virtual.size_bytes, len(source_data))
            self.assertEqual(virtual.sha256, expected_hash)
            self.assertEqual(source_path.read_bytes(), source_data)
            self.assertFalse(output_path.exists())

    def test_inserts_deterministically_without_resizing_or_touching_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.iso"
            first_path = root / "first.iso"
            second_path = root / "second.iso"
            source_data = make_iso(source_path)
            shutil.copyfile(source_path, first_path)
            shutil.copyfile(source_path, second_path)

            mod = b"M" * 3000
            texteng = b"T" * 100
            first = insert_files(
                first_path,
                {"PRG/TEXTENG.BIN": texteng, "PRG/MOD.BIN": mod},
            )
            second = insert_files(
                second_path,
                {"prg/mod.bin": mod, "prg/texteng.bin": texteng},
            )

            self.assertEqual(source_path.read_bytes(), source_data)
            self.assertEqual(first_path.stat().st_size, len(source_data))
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())
            self.assertEqual(
                [item.path for item in first],
                ["PRG/MOD.BIN", "PRG/TEXTENG.BIN"],
            )
            self.assertEqual([item.extent for item in first], [25, 27])
            self.assertEqual(first[0].sha256, hashlib.sha256(mod).hexdigest().upper())

            result = Iso9660(first_path)
            self.assertEqual(result.by_path["PRG"].size, 352)
            self.assertEqual(result.by_path["PRG/MOD.BIN"].size, len(mod))
            self.assertEqual(result.by_path["PRG/TEXTENG.BIN"].size, len(texteng))
            self.assertEqual(result.read_file(result.by_path["PRG/MOD.BIN"]), mod)
            self.assertEqual(
                result.read_file(result.by_path["PRG/TEXTENG.BIN"]), texteng
            )
            self.assertEqual(
                result.by_path["PRG/MOD.BIN"].directory_record_offset,
                21 * SECTOR + 264,
            )
            self.assertEqual(
                result.by_path["PRG/TEXTENG.BIN"].directory_record_offset,
                21 * SECTOR + 306,
            )
            self.assertEqual(first_path.read_bytes()[-14:], b"TAIL-SENTINEL!")

    def test_skips_nonzero_tail_sectors_and_preserves_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_iso(image, dirty_tail_sectors=(25,))
            before = image.read_bytes()[25 * SECTOR:(25 + 1) * SECTOR]
            results = insert_files(
                image,
                {"PRG/MOD.BIN": b"M" * 3000, "PRG/TEXTENG.BIN": b"T"},
            )
            self.assertEqual([item.extent for item in results], [26, 28])
            self.assertEqual(
                image.read_bytes()[25 * SECTOR:(25 + 1) * SECTOR], before
            )

    def test_updates_child_parent_record_when_root_directory_grows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_iso(image)
            before = Iso9660(image)
            insert_files(image, {"ROOT.BIN": b"root"})
            after = Iso9660(image)
            expected_root_size = before.by_path[""].size + 44
            self.assertEqual(after.by_path[""].size, expected_root_size)
            raw = image.read_bytes()
            prg_parent_offset = after.by_path["PRG"].byte_offset + 48
            self.assertEqual(
                int.from_bytes(raw[prg_parent_offset + 10:prg_parent_offset + 14], "little"),
                expected_root_size,
            )
            self.assertEqual(
                int.from_bytes(raw[prg_parent_offset + 14:prg_parent_offset + 18], "big"),
                expected_root_size,
            )

    def test_rejects_existing_and_duplicate_normalized_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_iso(image)
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                insert_files(image, {"PRG/ETC.BIN": b"collision"})
            with self.assertRaisesRegex(ValueError, "Duplicate normalized"):
                insert_files(
                    image,
                    {"prg/mod.bin": b"one", "PRG/MOD.BIN": b"two"},
                )

    def test_rejects_missing_parent_and_invalid_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_iso(image)
            with self.assertRaisesRegex(RuntimeError, "parent directory"):
                insert_files(image, {"MISSING/MOD.BIN": b"data"})
            with self.assertRaisesRegex(ValueError, "Unsupported ISO9660"):
                insert_files(image, {"PRG/BAD-NAME.BIN": b"data"})

    def test_rejects_directory_capacity_and_nonzero_append_area(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full = root / "full.iso"
            dirty = root / "dirty.iso"
            make_iso(full, prg_size=2030)
            make_iso(dirty, dirty_append_area=True)
            with self.assertRaisesRegex(RuntimeError, "no record capacity"):
                insert_files(full, {"PRG/MOD.BIN": b"data"})
            with self.assertRaisesRegex(RuntimeError, "append area is not zero"):
                insert_files(dirty, {"PRG/MOD.BIN": b"data"})

    def test_insufficient_zero_tail_capacity_fails_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            original = make_iso(image, sectors=28)
            with self.assertRaisesRegex(RuntimeError, "No verified-zero tail extent"):
                insert_files(
                    image,
                    {"PRG/MOD.BIN": b"M" * 3000, "PRG/TEXTENG.BIN": b"T"},
                )
            self.assertEqual(image.read_bytes(), original)

    def test_rejects_malformed_both_endian_directory_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.iso"
            make_iso(image)
            raw = bytearray(image.read_bytes())
            raw[21 * SECTOR + 14:21 * SECTOR + 18] = (999).to_bytes(4, "big")
            image.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError, "both-endian"):
                insert_files(image, {"PRG/MOD.BIN": b"data"})


if __name__ == "__main__":
    unittest.main()
