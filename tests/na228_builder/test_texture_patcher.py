from __future__ import annotations

import gzip
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.modules.texture_patcher import engine


class ExternalTexturePackTests(unittest.TestCase):
    def write_package(self, root: Path, payload: bytes) -> bytes:
        replacement = gzip.compress(payload, mtime=0) + b"\0" * 7
        assets = root / "assets"
        assets.mkdir()
        (assets / "example.ccs.gz").write_bytes(replacement)
        (root / "assets.tsv").write_text(
            "container_id\tpath\tasset_sha256\tpayload_sha256\n"
            f"example\tUI/EXAMPLE.CCS\t{engine.sha256(replacement)}\t"
            f"{engine.sha256(payload)}\n",
            encoding="utf-8",
        )
        return replacement

    def test_builds_sector_aligned_pack_with_runtime_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = b"localized texture payload"
            replacement = self.write_package(root, payload)

            plan = engine.build_external_texture_pack(root)

            self.assertEqual(1, len(plan.containers))
            self.assertEqual(0, len(plan.payload) % engine.EXTERNAL_PACK_SECTOR_SIZE)
            path_hash, sector, sector_count, decompressed_size = struct.unpack_from(
                "<IIII", plan.payload, 16
            )
            self.assertEqual(engine.runtime_path_hash("UI/EXAMPLE.CCS"), path_hash)
            self.assertEqual(1, sector)
            self.assertEqual(
                (len(replacement) + engine.EXTERNAL_PACK_SECTOR_SIZE - 1)
                // engine.EXTERNAL_PACK_SECTOR_SIZE,
                sector_count,
            )
            self.assertEqual(len(payload), decompressed_size)
            self.assertEqual(
                replacement,
                plan.payload[
                    sector * engine.EXTERNAL_PACK_SECTOR_SIZE :
                    sector * engine.EXTERNAL_PACK_SECTOR_SIZE + len(replacement)
                ],
            )

    def test_rejects_unlisted_asset_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_package(root, b"payload")
            (root / "assets" / "unlisted.ccs.gz").write_bytes(b"extra")

            with self.assertRaisesRegex(ValueError, "unlisted unlisted.ccs.gz"):
                engine.build_external_texture_pack(root)


if __name__ == "__main__":
    unittest.main()
