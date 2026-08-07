from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from na228_builder.build_profile import apply_binary_patch_set
from na228_builder.composer import resolve_symbolic_patches
from na228_builder.modules.binary_patcher import engine as binary_engine
from na228_builder.modules.runtime_injector import engine
from na228_builder.payload_builder.builder import build_resident_payload


def write_tsv(
    path: Path, fields: list[str], rows: list[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


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
                groups={
                    "layout": binary_engine.Group(
                        group_id="layout",
                        enabled=True,
                        name="Layout",
                        description="Retained disabled layout.",
                        review_notes="",
                    )
                },
                patches={
                    "layout_hook": binary_engine.Patch(
                        patch_id="layout_hook",
                        group_id="layout",
                        enabled=False,
                        status="runtime_proven",
                        confidence="high",
                        name="Layout hook",
                        description="Retained disabled hook.",
                        evidence_id="TEST-LAYOUT",
                        review_notes="Runtime: resident",
                    )
                },
                edits=[],
            )
            payloads: dict[str, bytearray] = {}
            owners: dict[str, str] = {}

            result = apply_binary_patch_set(
                directory,
                package=package,
                roots={"na2": root},
                feature_id="feature",
                source=object(),
                payloads=payloads,
                owners=owners,
                allow_empty_enabled=True,
            )

            self.assertEqual(result["selected"], [])
            self.assertEqual(result["edits"], [])
            self.assertEqual(result["patched_paths"], [])
            self.assertEqual(payloads, {})
            self.assertEqual(owners, {})

    def test_loads_fragments_and_compiles_symbolic_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            blob = b"\0" * 8 + b"\x00\x00\x80\x3F"
            blob_path = directory / "assets" / "resident.bin"
            blob_path.parent.mkdir()
            blob_path.write_bytes(blob)
            digest = hashlib.sha256(blob).hexdigest().upper()
            write_tsv(
                directory / "targets.tsv",
                engine.TARGET_FIELDS,
                [
                    {
                        "target_id": "boot",
                        "root_id": "na2",
                        "role": "destination",
                        "path": "SLPS_258.37",
                        "expected_size": 64,
                        "expected_sha256": "1" * 64,
                    },
                    {
                        "target_id": "unused_source",
                        "root_id": "nun5",
                        "role": "source",
                        "path": "SLES_556.05",
                        "expected_size": 64,
                        "expected_sha256": "2" * 64,
                    },
                ],
            )
            write_tsv(
                directory / "groups.tsv",
                engine.GROUP_FIELDS,
                [{
                    "group_id": "layout",
                    "enabled": 1,
                    "name": "Layout",
                    "description": "Resident layout test.",
                    "review_notes": "",
                }],
            )
            write_tsv(
                directory / "patches.tsv",
                engine.PATCH_FIELDS,
                [{
                    "patch_id": "layout_hook",
                    "group_id": "layout",
                    "enabled": 1,
                    "status": "approved_for_test",
                    "confidence": "high",
                    "name": "Layout hook",
                    "description": "Route one hook.",
                    "evidence_id": "TEST-LAYOUT",
                    "review_notes": "Runtime: resident",
                }],
            )
            write_tsv(
                directory / "fragments.tsv",
                engine.FRAGMENT_FIELDS,
                [
                    {
                        "fragment_id": "test.code",
                        "order": 1,
                        "kind": "code",
                        "alignment": 4,
                        "payload_hex": "",
                        "blob_path": "assets/resident.bin",
                        "blob_offset": 0,
                        "length": 8,
                        "blob_sha256": digest,
                        "init": 0,
                    },
                    {
                        "fragment_id": "test.scale",
                        "order": 2,
                        "kind": "data",
                        "alignment": 4,
                        "payload_hex": "",
                        "blob_path": "assets/resident.bin",
                        "blob_offset": 8,
                        "length": 4,
                        "blob_sha256": digest,
                        "init": 0,
                    },
                ],
            )
            write_tsv(directory / "c_sources.tsv", engine.C_SOURCE_FIELDS, [])
            write_tsv(directory / "c_imports.tsv", engine.C_IMPORT_FIELDS, [])
            write_tsv(directory / "c_fragments.tsv", engine.C_FRAGMENT_FIELDS, [])
            write_tsv(
                directory / "relocations.tsv",
                engine.RELOCATION_FIELDS,
                [{
                    "relocation_id": "test.code.scale",
                    "fragment_id": "test.code",
                    "order": 10,
                    "offset": 0,
                    "kind": "abs32",
                    "symbol": "test.scale",
                    "addend": 0,
                }],
            )
            write_tsv(
                directory / "edits.tsv",
                engine.EDIT_FIELDS,
                [{
                    "edit_id": "layout_hook_jump",
                    "patch_id": "layout_hook",
                    "order": 10,
                    "target_id": "boot",
                    "offset": 16,
                    "expected_hex": "1122334455667788",
                    "replacement_hex": "0000000000000000",
                    "relocation_offset": 0,
                    "symbol": "test.code",
                    "encoding": "j26",
                    "addend": 0,
                    "reason": "Route the test hook.",
                }],
            )

            declaration = engine.load_package(
                directory, owner="feature.runtime_injector"
            )
            self.assertEqual(set(declaration.targets), {"boot"})
            build = build_resident_payload(declaration.fragments)
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
            self.assertEqual(package.edits[0].replacement_hex[-8:], "00000000")
            self.assertEqual(package.edits[0].patch_id, "layout_hook")


if __name__ == "__main__":
    unittest.main()
