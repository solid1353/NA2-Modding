from __future__ import annotations

import dataclasses
import unittest

from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.payload_builder.builder import build_resident_payload, load_config
from na2_patcher.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
)


class PayloadBuilderTests(unittest.TestCase):
    def test_links_fragments_deterministically_and_resolves_relocations(self) -> None:
        fragments = (
            PayloadFragment("feature.data", "shared.data", "data", 16, b"DATA"),
            PayloadFragment(
                "feature.code",
                "shared.code",
                "code",
                4,
                b"\0" * 4,
                (PayloadRelocation(0, "abs32", "shared.data"),),
            ),
        )
        first = build_resident_payload(fragments)
        second = build_resident_payload(tuple(reversed(fragments)))
        self.assertEqual(first.payload, second.payload)
        code = first.symbols["shared.code"]
        data = first.symbols["shared.data"]
        self.assertEqual(data.file_offset, 0x100)
        self.assertEqual(
            first.payload[code.file_offset:code.file_offset + 4],
            data.runtime_address.to_bytes(4, "little"),
        )

    def test_composer_resolves_external_symbolic_patch(self) -> None:
        build = build_resident_payload(
            (PayloadFragment("feature.data", "shared.text", "rodata", 4, b"Text\0"),)
        )
        patch = SymbolicPatch(
            owner="feature.data",
            path="SLPS_258.37",
            offset=0x20,
            expected=b"\0" * 4,
            symbol="shared.text",
            encoding="abs32",
            mapping_id="TEST-PTR",
            kind="redirect_pointer",
            reason="Test symbolic resolution.",
        )
        resolved = resolve_symbolic_patches(build, (patch,))[0]
        self.assertEqual(
            resolved.replacement,
            build.symbols["shared.text"].runtime_address.to_bytes(4, "little"),
        )

    def test_rejects_duplicate_and_unresolved_symbols(self) -> None:
        duplicate = PayloadFragment("a", "same", "data", 4, b"a")
        with self.assertRaisesRegex(ValueError, "duplicate symbols"):
            build_resident_payload((duplicate, dataclasses.replace(duplicate, owner="b")))
        unresolved = PayloadFragment(
            "a",
            "code",
            "code",
            4,
            b"\0" * 4,
            (PayloadRelocation(0, "abs32", "missing"),),
        )
        with self.assertRaisesRegex(ValueError, "unresolved symbol"):
            build_resident_payload((unresolved,))

    def test_rejects_payload_beyond_the_proven_envelope(self) -> None:
        config = load_config()
        constrained = dataclasses.replace(
            config, maximum_end=config.load_base + config.minimum_data_offset + 8
        )
        with self.assertRaisesRegex(ValueError, "reservation envelope"):
            build_resident_payload(
                (PayloadFragment("a", "large", "data", 4, b"x" * 32),),
                config=constrained,
            )


if __name__ == "__main__":
    unittest.main()
