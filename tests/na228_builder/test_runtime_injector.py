from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from na228_builder.modules.binary_patcher import engine as binary_engine
from na228_builder.modules.runtime_injector import engine
from na228_builder.payload_builder.builder import build_resident_payload
from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
    encode_symbol_reference,
)
from na228_builder.scripts.build_configuration import apply_binary_patch_set
from na228_builder.scripts.composer import resolve_symbolic_patches
from tests.na228_builder._fixtures import resident_payload_config


class RuntimeInjectorTests(unittest.TestCase):
    def test_all_disabled_resident_package_composes_as_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root = directory / "na2"
            root.mkdir()
            target_data = bytes(range(16))
            (root / "SLPS_258.37").write_bytes(target_data)
            package = binary_engine.Package(
                directory=directory,
                package_id="feature.runtime_injector",
                targets={
                    "boot": binary_engine.Target(
                        target_id="boot",
                        root_id="na2",
                        role="destination",
                        path=PurePosixPath("SLPS_258.37"),
                        expected_size=len(target_data),
                        expected_sha256=hashlib.sha256(
                            target_data
                        ).hexdigest().upper(),
                    )
                },
                patches={},
                edits=[],
            )
            payloads: dict[str, bytearray] = {}
            owners: dict[str, str] = {}

            result = apply_binary_patch_set(
                package=package,
                roots={"na2": root},
                feature_id="feature",
                source=object(),
                payloads=payloads,
                owners=owners,
                allow_empty=True,
            )

            self.assertEqual(result["edits"], [])
            self.assertEqual(result["patched_paths"], [])
            self.assertEqual(payloads, {})
            self.assertEqual(owners, {})

    def test_finalizes_symbolic_hooks_into_binary_package(self) -> None:
        owner = "feature.runtime_injector"
        target = binary_engine.Target(
            target_id="boot",
            root_id="na2",
            role="destination",
            path=PurePosixPath("SLPS_258.37"),
            expected_size=64,
            expected_sha256="1" * 64,
        )
        patch = binary_engine.Patch(
            patch_id="layout_hook",
            group_id="layout",
            evidence_id="TEST-LAYOUT",
        )
        fragments = (
            PayloadFragment(
                owner=owner,
                symbol="test.code",
                kind="code",
                alignment=4,
                payload=b"\0" * 8,
                relocations=(
                    PayloadRelocation(
                        offset=0,
                        kind="abs32",
                        symbol="test.scale",
                    ),
                ),
            ),
            PayloadFragment(
                owner=owner,
                symbol="test.scale",
                kind="data",
                alignment=4,
                payload=b"\x00\x00\x80\x3F",
            ),
        )
        symbolic_patch = SymbolicPatch(
            owner=owner,
            path=target.path.as_posix(),
            offset=16,
            expected=bytes.fromhex("1122334455667788"),
            symbol="test.code",
            encoding="j26",
            mapping_id="layout_hook_jump",
            kind="layout",
            reason="Route the test hook.",
            replacement_template=b"\0" * 8,
        )
        declaration = engine.RuntimeInjectionPackage(
            directory=Path.cwd(),
            owner=owner,
            targets={target.target_id: target},
            patches={patch.patch_id: patch},
            fragments=fragments,
            edits=(
                engine.RuntimeSymbolicEdit(
                    edit_id=symbolic_patch.mapping_id,
                    patch_id=patch.patch_id,
                    order=10,
                    target_id=target.target_id,
                    symbolic_patch=symbolic_patch,
                ),
            ),
        )

        build = build_resident_payload(
            declaration.fragments,
            config=resident_payload_config(),
        )
        resolved = resolve_symbolic_patches(
            build, declaration.symbolic_patches
        )
        package = engine.build_binary_package(declaration, resolved)

        code = build.symbols["test.code"]
        scale = build.symbols["test.scale"]
        self.assertEqual(
            build.payload[code.file_offset:code.file_offset + 4],
            scale.runtime_address.to_bytes(4, "little"),
        )
        self.assertEqual(
            package.edits[0].replacement_hex,
            encode_symbol_reference(
                "j26", code.runtime_address
            ).hex().upper() + "00000000",
        )
        self.assertEqual(package.edits[0].patch_id, "layout_hook")


if __name__ == "__main__":
    unittest.main()
