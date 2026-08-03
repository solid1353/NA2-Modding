from __future__ import annotations

import struct
import unittest

from na228_builder.elf_identity import apply_elf_crc_discriminator


def make_elf() -> bytes:
    data = bytearray(0x300)
    struct.pack_into(
        "<16sHHIIIIIHHHHHH",
        data,
        0,
        b"\x7fELF\x01\x01\x01" + bytes(9),
        2,
        8,
        1,
        0x100000,
        0x34,
        0x200,
        0,
        52,
        32,
        1,
        40,
        1,
        0,
    )
    struct.pack_into("<IIIIIIII", data, 0x34, 1, 0x100, 0x100000, 0x100000, 0x80, 0x80, 5, 0x100)
    struct.pack_into("<IIIIIIIIII", data, 0x200, 0, 1, 0, 0, 0x180, 0x20, 0, 0, 1, 0)
    data[0x100:0x180] = b"L" * 0x80
    data[0x180:0x1A0] = b"S" * 0x20
    return bytes(data)


class ElfIdentityTests(unittest.TestCase):
    def test_zero_discriminator_preserves_the_elf(self) -> None:
        source = make_elf()
        result, edit = apply_elf_crc_discriminator(source, 0)
        self.assertEqual(bytes(result), source)
        self.assertIsNone(edit)

    def test_discriminator_uses_only_runtime_unloaded_padding(self) -> None:
        source = make_elf()
        result, edit = apply_elf_crc_discriminator(source, 0x45324501)
        self.assertIsNotNone(edit)
        assert edit is not None
        self.assertEqual(edit.offset, 0x2FC)
        self.assertEqual(edit.original, bytes(4))
        self.assertEqual(edit.replacement, bytes.fromhex("01453245"))
        self.assertEqual(result[:0x2FC], source[:0x2FC])

    def test_discriminator_rejects_an_elf_without_safe_padding(self) -> None:
        source = bytearray(make_elf())
        source[0x54:0x100] = b"X" * 0xAC
        source[0x1A0:0x200] = b"X" * 0x60
        source[0x228:0x300] = b"X" * 0xD8
        with self.assertRaisesRegex(ValueError, "no aligned runtime-unloaded zero word"):
            apply_elf_crc_discriminator(source, 1)


if __name__ == "__main__":
    unittest.main()
