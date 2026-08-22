"""Generic real-toolchain contracts for EE C compilation and extraction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.payload_builder import build_resident_payload
from na228_builder.payload_builder import ee_c_fragments
from na228_builder.payload_builder.operations import PayloadFragment
from tests.na228_builder._fixtures import resident_payload_config


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY_ROOT)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"


class EeCFragmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not COMPILER.is_file():
            raise unittest.SkipTest(f"local EE compiler is unavailable: {COMPILER}")

    def compile_probe(self, root: Path, name: str):
        source = root / f"{name}.c"
        source.write_text(
            "\n".join(
                (
                    "extern unsigned int native_call(unsigned int value);",
                    "static const unsigned char widths[4] = {3, 5, 7, 9};",
                    "static volatile unsigned int state;",
                    "unsigned int measure(unsigned int index) {",
                    "    state += widths[index & 3u];",
                    "    return native_call(state);",
                    "}",
                    "",
                )
            ),
            encoding="ascii",
        )
        return ee_c_fragments.compile_and_extract(
            source,
            root / f"{name}.o",
            namespace="test.ee.probe",
            toolchain_bin=TOOLCHAIN_BIN,
            external_symbols={
                "native_call": ee_c_fragments.SymbolReference("test.ee.native")
            },
        )

    def test_real_ee_object_exports_relocatable_payload_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            extracted = self.compile_probe(Path(temporary), "probe")

        fragments = {fragment.symbol: fragment for fragment in extracted.fragments}
        self.assertEqual(
            {
                "test.ee.probe.text",
                "test.ee.probe.rodata",
                "test.ee.probe.bss",
            },
            set(fragments),
        )
        self.assertEqual("code", fragments["test.ee.probe.text"].kind)
        self.assertEqual("rodata", fragments["test.ee.probe.rodata"].kind)
        self.assertEqual("data", fragments["test.ee.probe.bss"].kind)
        self.assertEqual(
            ee_c_fragments.SymbolReference("test.ee.probe.text", 0),
            extracted.symbols["measure"],
        )
        relocations = fragments["test.ee.probe.text"].relocations
        self.assertIn(
            ("jal26", "test.ee.native"),
            {(item.kind, item.symbol) for item in relocations},
        )
        self.assertIn(
            ("hi16", "test.ee.probe.rodata"),
            {(item.kind, item.symbol) for item in relocations},
        )
        self.assertIn(
            ("lo16", "test.ee.probe.bss"),
            {(item.kind, item.symbol) for item in relocations},
        )

        native_stub = PayloadFragment(
            owner="test.ee",
            symbol="test.ee.native",
            kind="code",
            alignment=4,
            payload=bytes.fromhex("0800E00300000000"),
        )
        linked = build_resident_payload(
            (*extracted.fragments, native_stub),
            config=resident_payload_config(),
        )
        self.assertIn("test.ee.probe.text", linked.symbols)
        self.assertIn("test.ee.native", linked.symbols)

    def test_real_ee_compilation_extracts_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.compile_probe(root, "first")
            second = self.compile_probe(root, "second")

        self.assertEqual(first, second)
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(64, len(first.fingerprint))

    def test_unmapped_external_symbol_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "probe.c"
            object_path = root / "probe.o"
            source.write_text(
                "extern void missing(void);\n"
                "void entry(void) { missing(); }\n",
                encoding="ascii",
            )
            ee_c_fragments.compile_ee_source(
                source,
                object_path,
                language="c",
                toolchain_bin=TOOLCHAIN_BIN,
            )
            with self.assertRaisesRegex(
                ValueError, "unresolved external C symbol 'missing'"
            ):
                ee_c_fragments.extract_ee_object(
                    object_path,
                    namespace="test.ee.probe",
                )

    def test_real_ee_assembly_preserves_bytes_relocations_and_determinism(self) -> None:
        source_text = """\
    .set noreorder
    .set noat
    .section .text.entry,"ax",@progbits
    .balign 4
    .globl entry
entry:
    addiu $sp, $sp, -16
    sw $ra, 0($sp)
    jal native_call
    nop
    lw $ra, 0($sp)
    jr $ra
    addiu $sp, $sp, 16
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "probe.S"
            source.write_text(source_text, encoding="ascii")
            arguments = {
                "namespace": "test.ee.asm",
                "language": "asm",
                "toolchain_bin": TOOLCHAIN_BIN,
                "external_symbols": {
                    "native_call": ee_c_fragments.SymbolReference(
                        "test.ee.native"
                    )
                },
            }
            first = ee_c_fragments.compile_and_extract(
                source, root / "first.o", **arguments
            )
            second = ee_c_fragments.compile_and_extract(
                source, root / "second.o", **arguments
            )

        self.assertEqual(first, second)
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(1, len(first.fragments))
        fragment = first.fragments[0]
        self.assertEqual("code", fragment.kind)
        self.assertEqual(4, fragment.alignment)
        self.assertEqual(
            bytes.fromhex(
                "F0FFBD270000BFAF0000000C00000000"
                "0000BF8F0800E0031000BD27"
            ),
            fragment.payload,
        )
        self.assertEqual(
            [(8, "jal26", "test.ee.native", 0)],
            [
                (item.offset, item.kind, item.symbol, item.addend)
                for item in fragment.relocations
            ],
        )

    def test_ee_source_kind_requires_its_canonical_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wrong_assembly = root / "probe.s"
            wrong_assembly.write_text("nop\n", encoding="ascii")
            wrong_c = root / "probe.S"
            wrong_c.write_text("nop\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "exact .S suffix"):
                ee_c_fragments.compile_ee_source(
                    wrong_assembly,
                    root / "assembly.o",
                    language="asm",
                    toolchain_bin=TOOLCHAIN_BIN,
                )
            with self.assertRaisesRegex(ValueError, "exact .c suffix"):
                ee_c_fragments.compile_ee_source(
                    wrong_c,
                    root / "c.o",
                    language="c",
                    toolchain_bin=TOOLCHAIN_BIN,
                )


if __name__ == "__main__":
    unittest.main()
