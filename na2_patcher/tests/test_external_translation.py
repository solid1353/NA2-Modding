from __future__ import annotations

import struct
import unittest
from pathlib import Path

from na2_patcher.modules.external_translation import engine
from na2_patcher.modules.translation_importer import engine as translation_importer
from na2_patcher.project_paths import load_project_paths


class ExternalTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        paths = load_project_paths(cls.repository)
        cls.roots = {
            "na2": paths.path("source_na2"),
            "nun5": paths.path("source_nun5"),
        }
        cls.package = (
            cls.repository / "na2_patcher" / "modules" / "external_translation"
        )
        cls.plan = engine.build_external_translation_plan(
            package_directory=cls.package,
            roots=cls.roots,
        )

    def test_generates_exact_two_pinned_payloads(self) -> None:
        self.assertEqual(
            list(self.plan.insertions),
            ["PRG/MOD.BIN", "PRG/TEXTENG.BIN"],
        )
        expected = {
            "PRG/MOD.BIN": (
                0x100,
                "C00D69E124E425741745B7B61A2FE07B48AFD729806F96113C6FF81D957706DA",
            ),
            "PRG/TEXTENG.BIN": (
                0x30E00,
                "AA5E7C6ADCDFDC3A7695AF295DD488EA91D926B01ED9DDD191550C98E3F4EAB9",
            ),
        }
        for path, payload in self.plan.insertions.items():
            with self.subTest(path=path):
                size, digest = expected[path]
                self.assertEqual(len(payload), size)
                self.assertEqual(engine.sha256(payload), digest)

    def test_texteng_preserves_donor_and_appends_only_four_derived_strings(self) -> None:
        donor = (self.roots["nun5"] / "PRG" / "TEXTENG.BIN").read_bytes()
        generated = self.plan.insertions["PRG/TEXTENG.BIN"]
        self.assertEqual(generated[0x20:0x30D00], donor[0x20:])
        self.assertEqual(
            struct.unpack_from("<4s7I", generated, 0),
            (
                b"MWo3",
                4,
                0x008F3D00,
                0xC0,
                0x30D00,
                0,
                0x00924B00,
                0x00924B00,
            ),
        )
        expected = {
            0x30D00: "Are you sure you want to quit Free Battle and return to ",
            0x30D3C: "Are you sure you want to quit Practice and return to ",
            0x30D74: "Do you want to quit Free Battle?",
            0x30D98: (
                "No Naruto Shippuden: Ultimate Ninja 5 data found <br>"
                "on memory card (PS2) in MEMORY CARD slot 1. "
            ),
        }
        for offset, text in expected.items():
            with self.subTest(offset=hex(offset)):
                end = generated.index(0, offset)
                self.assertEqual(generated[offset:end].decode("cp1252"), text)

    def test_mod_has_fixed_mwo3_header_and_loader_call(self) -> None:
        mod = self.plan.insertions["PRG/MOD.BIN"]
        self.assertEqual(
            struct.unpack_from("<4s7I", mod, 0),
            (
                b"MWo3",
                8,
                0x00940000,
                0x40,
                0xB0,
                0,
                0x00940100,
                0x00940100,
            ),
        )
        self.assertEqual(mod[0x20:0x28], b"Mod.bin\0")
        self.assertEqual(mod[0x70:0x7C], b"TEXTENG.BIN\0")
        self.assertEqual(
            struct.unpack_from("<11I", mod, 0x40),
            (
                0x27BDFFE0,
                0xFFBF0010,
                0x24040003,
                0x3C050094,
                0x24A50070,
                0x0C06F9FC,
                0,
                0xDFBF0010,
                0x27BD0020,
                0x03E00008,
                0,
            ),
        )

    def test_plan_has_complete_guarded_edit_inventory(self) -> None:
        counts = self.plan.summary["edits_by_kind"]
        self.assertEqual(
            counts,
            {
                "loader": 3,
                "memory_layout": 12,
                "redirect_pointer": 35,
                "restore_inline": 35,
            },
        )
        self.assertEqual(len(self.plan.edits), 85)
        self.assertNotIn("PRG/ADV.BIN", {edit.path for edit in self.plan.edits})
        for edit in self.plan.edits:
            self.assertTrue(edit.expected)
            self.assertEqual(len(edit.expected), len(edit.replacement))

    def test_external_edits_reverse_every_inline_shortening_after_translation(self) -> None:
        na2 = translation_importer.FolderSource(self.roots["na2"])
        clean = {
            target: na2.read(spec[1], f"NA2 {target}")
            for target, spec in translation_importer.TARGET_SPECS.items()
        }
        composed = {
            translation_importer.TARGET_SPECS[target][0]: bytearray(payload)
            for target, payload in clean.items()
        }
        translation = translation_importer.build_translation_import_plan(
            na2_folder=self.roots["na2"],
            nun5_folder=self.roots["nun5"],
            data_root=(
                self.repository
                / "na2_patcher"
                / "modules"
                / "translation_importer"
            ),
            apply="BTL,ETC,SLPS",
        )
        for row in translation.import_rows:
            path = row["path"]
            offset = int(row["offset"], 0)
            expected = bytes.fromhex(row["expected_hex"])
            replacement = bytes.fromhex(row["replacement_hex"])
            self.assertEqual(bytes(composed[path][offset : offset + len(expected)]), expected)
            composed[path][offset : offset + len(expected)] = replacement

        for edit in self.plan.edits:
            data = composed[edit.path]
            actual = bytes(data[edit.offset : edit.offset + len(edit.expected)])
            self.assertEqual(actual, edit.expected, edit.mapping_id)
            data[edit.offset : edit.offset + len(edit.expected)] = edit.replacement

        parsed = translation_importer.parse_mappings(
            translation_importer.read_rows(
                self.repository
                / "na2_patcher"
                / "modules"
                / "translation_importer"
                / "mappings.tsv"
            )
        )
        for mapping in parsed["text"]:
            if mapping["mode"] != "shorten":
                continue
            target = str(mapping["target"])
            path = translation_importer.TARGET_SPECS[target][0]
            offset = int(mapping["target_offset"])
            capacity = int(mapping["capacity"])
            self.assertEqual(
                bytes(composed[path][offset : offset + capacity]),
                clean[target][offset : offset + capacity],
                mapping["id"],
            )

    def test_elf_bootstrap_preserves_original_constructor_call(self) -> None:
        by_id = {edit.mapping_id: edit for edit in self.plan.edits}
        hook = by_id["ELF-XT-HOOK"]
        self.assertEqual(struct.unpack("<I", hook.expected)[0], 0x0C06F694)
        self.assertEqual(struct.unpack("<I", hook.replacement)[0], 0x0C181CC5)

        cave = by_id["ELF-XT-BOOTSTRAP"].replacement
        self.assertEqual(cave[-8:], b"MOD.BIN\0")
        words = struct.unpack_from("<17I", cave, 0)
        self.assertEqual(words[6], 0x0C06F9FC)
        self.assertEqual(words[8], 0x0C250010)
        self.assertEqual(words[11], 0x0C06F694)
        self.assertEqual(words[15], 0x03E00008)


if __name__ == "__main__":
    unittest.main()
