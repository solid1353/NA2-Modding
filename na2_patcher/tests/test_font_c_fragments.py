from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.payload_builder import build_resident_payload
from na2_patcher.payload_builder.operations import PayloadFragment
from scripts.research.localization import ee_c_fragments
from scripts.research.localization import generate_font_renderer


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY_ROOT)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"


class FontCFragmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not COMPILER.is_file():
            raise unittest.SkipTest(f"local EE compiler is unavailable: {COMPILER}")

    def compile_probe(self, root: Path, name: str):
        source = root / f"{name}.c"
        source.write_text(
            "\n".join(
                (
                    "extern unsigned int font_native(unsigned int value);",
                    "static const unsigned char widths[4] = {3, 5, 7, 9};",
                    "static volatile unsigned int state;",
                    "unsigned int font_measure(unsigned int index) {",
                    "    state += widths[index & 3u];",
                    "    return font_native(state);",
                    "}",
                    "",
                )
            ),
            encoding="ascii",
        )
        return ee_c_fragments.compile_and_extract(
            source,
            root / f"{name}.o",
            namespace="localization.font.c.probe",
            toolchain_bin=TOOLCHAIN_BIN,
            external_symbols={
                "font_native": ee_c_fragments.SymbolReference(
                    "localization.font.c.native"
                )
            },
        )

    def test_real_ee_object_exports_relocatable_payload_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            extracted = self.compile_probe(Path(temporary), "probe")

        fragments = {fragment.symbol: fragment for fragment in extracted.fragments}
        self.assertEqual(
            {
                "localization.font.c.probe.text",
                "localization.font.c.probe.rodata",
                "localization.font.c.probe.bss",
            },
            set(fragments),
        )
        self.assertEqual("code", fragments["localization.font.c.probe.text"].kind)
        self.assertEqual(
            "rodata", fragments["localization.font.c.probe.rodata"].kind
        )
        self.assertEqual("data", fragments["localization.font.c.probe.bss"].kind)
        self.assertEqual(
            ee_c_fragments.SymbolReference(
                "localization.font.c.probe.text", 0
            ),
            extracted.symbols["font_measure"],
        )
        relocations = fragments[
            "localization.font.c.probe.text"
        ].relocations
        self.assertIn(
            ("jal26", "localization.font.c.native"),
            {(item.kind, item.symbol) for item in relocations},
        )
        self.assertIn(
            ("hi16", "localization.font.c.probe.rodata"),
            {(item.kind, item.symbol) for item in relocations},
        )
        self.assertIn(
            ("lo16", "localization.font.c.probe.bss"),
            {(item.kind, item.symbol) for item in relocations},
        )

        native_stub = PayloadFragment(
            owner="localization.runtime_injector",
            symbol="localization.font.c.native",
            kind="code",
            alignment=4,
            payload=bytes.fromhex("0800E00300000000"),
        )
        linked = build_resident_payload((*extracted.fragments, native_stub))
        self.assertIn("localization.font.c.probe.text", linked.symbols)
        self.assertIn("localization.font.c.native", linked.symbols)

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
                "void font_entry(void) { missing(); }\n",
                encoding="ascii",
            )
            ee_c_fragments.compile_ee_c(
                source,
                object_path,
                toolchain_bin=TOOLCHAIN_BIN,
            )
            with self.assertRaisesRegex(
                ValueError, "unresolved external C symbol 'missing'"
            ):
                ee_c_fragments.extract_ee_object(
                    object_path,
                    namespace="localization.font.c.probe",
                )


class FontCSharedCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not COMPILER.is_file():
            raise unittest.SkipTest(f"local EE compiler is unavailable: {COMPILER}")

    def test_compiled_core_is_deterministic(self) -> None:
        compiled = {
            fragment.symbol: (
                len(fragment.payload),
                hashlib.sha256(fragment.payload).hexdigest().upper(),
            )
            for fragment in generate_font_renderer.build_v2_c_core()
        }
        self.assertEqual(
            {
                "localization.font.v2.c.is_br": (
                    72,
                    "8D237660C7EAFF9CC326A0E61BB7A56E2EB67FF6B8627B1EECCBFFE62225DF1B",
                ),
                "localization.font.v2.measure": (
                    312,
                    "3556D787360097C7BD0901101068AE640168533B041B11866F3FE8A91533C7A7",
                ),
                "localization.font.v2.prepare": (
                    584,
                    "7B0E8737D296AD767CDC377730EC990B727E9A43ADA6A05142482AAE67E30B14",
                ),
                "localization.font.v2.adapter_call": (
                    216,
                    "1763CE7B8E15393AE9FC25C8F15E3E53DEE796C806B2D764A8BB889B6247B595",
                ),
                "localization.font.v2.controls_adapter": (
                    136,
                    "5F9F94ED1AB2248C2F4BAECE1AFD905C39704AC019B8F060D6C3E6CEE268773F",
                ),
                "localization.font.v2.title_adapter": (
                    120,
                    "AE60BAD491CDC7542FDB08C0B161AD8CD49A0CC01930B2DC3600549618C25C02",
                ),
                "localization.font.v2.command_title_entry": (
                    56,
                    "4EF411D3F32815A14E4EC8C8EB5765766DEB1F4B046F6BFE4333A67B39B86E25",
                ),
                "localization.font.v2.practice_title_entry": (
                    56,
                    "157653A9FB727D469438BB99D055D0F99A3A15D3ACF8C39A07B4FA25E89F0056",
                ),
            },
            compiled,
        )

    def test_c_core_reproduces_canonical_generated_outputs(self) -> None:
        v2_blob, numeric_blob, fragments, relocations = (
            generate_font_renderer.generated_outputs()
        )
        self.assertEqual(
            generate_font_renderer.V2_BLOB_OUTPUT.read_bytes(), v2_blob
        )
        self.assertEqual(
            generate_font_renderer.NUMERIC_BLOB_OUTPUT.read_bytes(),
            numeric_blob,
        )
        self.assertEqual(
            generate_font_renderer.FRAGMENTS_OUTPUT.read_bytes(), fragments
        )
        self.assertEqual(
            generate_font_renderer.RELOCATIONS_OUTPUT.read_bytes(),
            relocations,
        )


if __name__ == "__main__":
    unittest.main()
