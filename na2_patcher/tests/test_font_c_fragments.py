from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na2_patcher.modules.runtime_injector import engine as runtime_injector
from na2_patcher.payload_builder import build_resident_payload
from na2_patcher.payload_builder import mips
from na2_patcher.payload_builder.operations import PayloadFragment
from na2_patcher.payload_builder import ee_c_fragments
from scripts.localization import generate_font_renderer


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

    def test_compiled_core_is_deterministic_and_relocatable(self) -> None:
        first = generate_font_renderer.build_v2_c_core()
        second = generate_font_renderer.build_v2_c_core()
        self.assertEqual(first, second)

        fragments = {fragment.symbol: fragment for fragment in first}
        self.assertTrue(
            {
                "localization.font.v2.measure",
                "localization.font.v2.prepare",
                "localization.font.v2.adapter_call",
                "localization.font.v2.pause_list_adapter",
                "localization.font.v2.quit_unselected_adapter",
                "localization.font.v2.wrap_native",
                "localization.font.v2.c.practice_adapter_impl",
            }.issubset(fragments)
        )
        for fragment in first:
            self.assertEqual(fragment.kind, "code")
            self.assertGreater(len(fragment.payload), 0)
            self.assertEqual(len(fragment.payload) % 4, 0)
            self.assertTrue(
                all(
                    relocation.kind in {"abs32", "j26", "jal26", "hi16", "lo16"}
                    for relocation in fragment.relocations
                )
            )

    def test_native_entry_shims_preserve_ee_eabi_register_contract(
        self,
    ) -> None:
        pause = generate_font_renderer.build_v2_pause_list_selected_entry()
        pause_words = [
            int.from_bytes(pause.payload[offset:offset + 4], "little")
            for offset in range(0, len(pause.payload), 4)
        ]
        self.assertEqual(
            pause.relocations,
            (
                mips.Relocation(
                    offset=0x8,
                    kind="jal26",
                    symbol=generate_font_renderer.V2_PAUSE_LIST_SELECTED_IMPL,
                ),
            ),
        )
        self.assertNotIn(mips.i_type(0x2B, 29, 8, 0x10), pause_words)

        practice = generate_font_renderer.build_v2_practice_adapter_entry()
        practice_words = [
            int.from_bytes(practice.payload[offset:offset + 4], "little")
            for offset in range(0, len(practice.payload), 4)
        ]
        self.assertEqual(
            practice_words[2:5],
            [
                mips.r_type(19, 0, 7, 0x21),
                mips.r_type(18, 0, 8, 0x21),
                mips.mfc1(9, 12),
            ],
        )
        self.assertEqual(
            practice.relocations,
            (
                mips.Relocation(
                    offset=0x14,
                    kind="jal26",
                    symbol=generate_font_renderer.V2_PRACTICE_ADAPTER_IMPL,
                ),
            ),
        )

    def test_normal_build_compiles_canonical_font_fragments(self) -> None:
        directory = (
            REPOSITORY_ROOT
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector"
        )
        declaration = runtime_injector.load_package(
            directory, owner="localization.runtime_injector"
        )
        v2 = generate_font_renderer.v2_fragments()
        expected = (*v2[:-2], *generate_font_renderer.numeric_fragments(), *v2[-2:])
        self.assertEqual(
            [fragment.symbol for fragment in expected],
            [fragment.symbol for fragment in declaration.fragments],
        )
        for generated, actual in zip(
            expected, declaration.fragments, strict=True
        ):
            self.assertEqual(generated.payload, actual.payload)
            self.assertEqual(generated.kind, actual.kind)
            self.assertEqual(generated.alignment, actual.alignment)
            self.assertEqual(
                [
                    (
                        relocation.offset,
                        relocation.kind,
                        relocation.symbol,
                        relocation.addend,
                    )
                    for relocation in generated.relocations
                ],
                [
                    (
                        relocation.offset,
                        relocation.kind,
                        relocation.symbol,
                        relocation.addend,
                    )
                    for relocation in actual.relocations
                ],
            )


if __name__ == "__main__":
    unittest.main()
