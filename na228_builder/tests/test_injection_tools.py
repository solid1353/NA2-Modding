from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


apply_injection = importlib.import_module("scripts.injection.apply")
build_injection = importlib.import_module("scripts.injection.build")


class FakePineClient:
    instances: list["FakePineClient"] = []
    guard = bytes.fromhex("11111111")

    def __init__(self, _port: int) -> None:
        self.state = "running"
        self.events: list[str] = []
        self.memory: dict[int, int] = {
            0x3000 + index: value for index, value in enumerate(self.guard)
        }
        self.instances.append(self)

    def __enter__(self) -> "FakePineClient":
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def status(self) -> str:
        return self.state

    def pause(self) -> None:
        self.events.append("pause")
        self.state = "paused"

    def resume(self) -> None:
        self.events.append("resume")
        self.state = "running"

    def clear_execution_caches(self) -> None:
        self.events.append("refresh")

    def read(self, address: int, length: int) -> bytes:
        return bytes(self.memory.get(address + index, 0) for index in range(length))

    def write(self, address: int, value: bytes) -> None:
        self.events.append(f"write:{address:08X}")
        for index, byte in enumerate(value):
            self.memory[address + index] = byte


def write_candidate(directory: Path) -> None:
    fragment = bytes.fromhex("0102030405060708")
    (directory / "fragment.bin").write_bytes(fragment)
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "fragment_file": "fragment.bin",
                "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
                "segments": [
                    {
                        "file_offset": 0,
                        "runtime_address": "0x1000",
                        "size": 8,
                    }
                ],
                "zero_fill": [
                    {
                        "runtime_address": "0x2000",
                        "size": 4,
                    }
                ],
                "writes": [
                    {
                        "id": "caller",
                        "runtime_address": "0x3000",
                        "expected_hex": "11111111",
                        "replacement_hex": "22222222",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


class InjectionApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        FakePineClient.instances.clear()
        FakePineClient.guard = bytes.fromhex("11111111")

    def run_apply(self, directory: Path) -> FakePineClient:
        arguments = argparse.Namespace(input=directory, port=28100)
        with (
            mock.patch.object(apply_injection, "parse_args", return_value=arguments),
            mock.patch.object(apply_injection, "PineClient", FakePineClient),
        ):
            self.assertEqual(apply_injection.main(), 0)
        return FakePineClient.instances[-1]

    def test_applies_one_paused_transaction_and_restores_running_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_candidate(directory)
            client = self.run_apply(directory)

        self.assertEqual(client.read(0x1000, 8), bytes.fromhex("0102030405060708"))
        self.assertEqual(client.read(0x2000, 4), bytes(4))
        self.assertEqual(client.read(0x3000, 4), bytes.fromhex("22222222"))
        self.assertEqual(client.state, "running")
        self.assertEqual(client.events[0], "pause")
        self.assertEqual(client.events[-2:], ["refresh", "resume"])

    def test_guard_failure_resumes_without_writing_candidate(self) -> None:
        FakePineClient.guard = bytes.fromhex("33333333")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_candidate(directory)
            arguments = argparse.Namespace(input=directory, port=28100)
            with (
                mock.patch.object(
                    apply_injection, "parse_args", return_value=arguments
                ),
                mock.patch.object(
                    apply_injection, "PineClient", FakePineClient
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "live guard mismatch"):
                    apply_injection.main()

        client = FakePineClient.instances[-1]
        self.assertEqual(client.state, "running")
        self.assertEqual(client.events, ["pause", "resume"])
        self.assertEqual(client.read(0x1000, 8), bytes(8))

    def test_rejects_fragment_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_candidate(directory)
            (directory / "fragment.bin").write_bytes(bytes(8))
            with self.assertRaisesRegex(ValueError, "does not match"):
                apply_injection.load_candidate(directory)


class InjectionBuildTests(unittest.TestCase):
    def test_overlay_plan_accepts_resident_symbol_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            plan_path = repository / "work" / "Font" / "overlay.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source_id": "font_v2_core",
                        "entry_symbol": "localization.font.v2.entry",
                        "abi": "arg0_text_arg2",
                        "purpose": "Exercise an older resident layout.",
                        "writes": [
                            {
                                "id": "caller",
                                "runtime_address": "0x003BCA54",
                                "expected_hex": "C4080E0C00000000",
                                "replacement": {"kind": "entry_call"},
                                "reason": "Route the selected caller.",
                            }
                        ],
                        "resident_symbol_overrides": {
                            "localization.font.v2.title_callback": "0x008F5500",
                            "localization.font.v2.wrap_native": "0x008F5510",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                build_injection, "REPOSITORY", repository
            ):
                (
                    _path,
                    _raw,
                    _entries,
                    _writes,
                    overrides,
                ) = build_injection.load_overlay_plan(
                    str(plan_path),
                    source_id="font_v2_core",
                    entry_symbol="localization.font.v2.entry",
                )

        self.assertEqual(
            overrides,
            {
                "localization.font.v2.title_callback": 0x008F5500,
                "localization.font.v2.wrap_native": 0x008F5510,
            },
        )

    def test_resident_symbol_overrides_replace_selected_imports(self) -> None:
        addresses = build_injection.resolve_external_addresses(
            {
                "localization.font.v2.title_callback",
                "localization.font.v2.wrap_native",
            },
            {
                "localization.font.v2.title_callback": {
                    "address": 0x008F56E8,
                },
                "localization.font.v2.wrap_native": {
                    "address": 0x008F56F8,
                },
            },
            {
                "localization.font.v2.title_callback": 0x008F5500,
            },
        )

        self.assertEqual(
            addresses,
            {
                "localization.font.v2.title_callback": 0x008F5500,
                "localization.font.v2.wrap_native": 0x008F56F8,
            },
        )

    def test_rejects_override_for_unselected_import(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "not selected imports.*unused"
        ):
            build_injection.resolve_external_addresses(
                {"selected"},
                {"selected": {"address": 0x008F4000}},
                {"unused": 0x008F5000},
            )


if __name__ == "__main__":
    unittest.main()
