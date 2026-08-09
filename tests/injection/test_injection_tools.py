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
pine = apply_injection.PINE_MODULE


class FakePineClient:
    instances: list["FakePineClient"] = []
    guard = bytes.fromhex("11111111")
    initial_state = "running"

    def __init__(self, _port: int) -> None:
        self.state = self.initial_state
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
        FakePineClient.initial_state = "running"

    def run_apply(
        self, directory: Path, *, resume: bool = False
    ) -> FakePineClient:
        arguments = argparse.Namespace(
            input=directory, port=28100, resume=resume
        )
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

    def test_explicit_resume_restarts_an_initially_paused_vm(self) -> None:
        FakePineClient.initial_state = "paused"
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_candidate(directory)
            client = self.run_apply(directory, resume=True)

        self.assertEqual(client.state, "running")
        self.assertNotIn("pause", client.events)
        self.assertEqual(client.events[-2:], ["refresh", "resume"])

    def test_guard_failure_resumes_without_writing_candidate(self) -> None:
        FakePineClient.guard = bytes.fromhex("33333333")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_candidate(directory)
            arguments = argparse.Namespace(
                input=directory, port=28100, resume=False
            )
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
    def test_direct_source_scope_selects_registered_root_and_file(self) -> None:
        root, root_sources = build_injection.source_ids_for_path(Path("src"))
        numeric, numeric_sources = build_injection.source_ids_for_path(
            Path("src/localization/font/font_numeric.c")
        )

        self.assertEqual(root, build_injection.REPOSITORY / "src")
        self.assertEqual(
            root_sources,
            [
                "hot_reload_message",
                "v2_core",
                "font_numeric",
                "glyph_metrics",
                "startup_loading",
            ],
        )
        self.assertEqual(
            numeric,
            build_injection.REPOSITORY
            / "src"
            / "localization"
            / "font"
            / "font_numeric.c",
        )
        self.assertEqual(numeric_sources, ["font_numeric"])

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
                            "v2_title_callback": "0x008F5500",
                            "v2_wrap_native": "0x008F5510",
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
                "v2_title_callback": 0x008F5500,
                "v2_wrap_native": 0x008F5510,
            },
        )

    def test_resident_symbol_overrides_replace_selected_imports(self) -> None:
        addresses = build_injection.resolve_external_addresses(
            {
                "v2_title_callback",
                "v2_wrap_native",
            },
            {
                "v2_title_callback": {
                    "address": 0x008F56E8,
                },
                "v2_wrap_native": {
                    "address": 0x008F56F8,
                },
            },
            {
                "v2_title_callback": 0x008F5500,
            },
        )

        self.assertEqual(
            addresses,
            {
                "v2_title_callback": 0x008F5500,
                "v2_wrap_native": 0x008F56F8,
            },
        )

    def test_resident_override_closes_fragment_without_build_record(self) -> None:
        entry = build_injection.PayloadFragment(
            owner="localization.runtime_injector",
            symbol="localization.font.v2.new_entry",
            kind="code",
            alignment=4,
            payload=bytes(8),
            relocations=(
                build_injection.PayloadRelocation(
                    offset=0,
                    kind="jal26",
                    symbol="localization.font.v2.resident_helper",
                ),
            ),
        )
        helper = build_injection.PayloadFragment(
            owner="localization.runtime_injector",
            symbol="localization.font.v2.resident_helper",
            kind="code",
            alignment=4,
            payload=bytes(4),
        )

        with mock.patch.object(
            build_injection,
            "_load_static_fragments",
            return_value=[],
        ):
            fragments, imports = build_injection.select_fragment_closure(
                ["localization.font.v2.new_entry"],
                [entry, helper],
                [
                    (1, "entry", "localization.font.v2.new_entry"),
                    (2, "helper", "localization.font.v2.resident_helper"),
                ],
                {},
                b"",
                {
                    "localization.font.v2.resident_helper": 0x008F5000,
                },
            )

        self.assertEqual(
            [fragment.symbol for fragment in fragments],
            ["localization.font.v2.new_entry"],
        )
        self.assertEqual(
            imports,
            {"localization.font.v2.resident_helper"},
        )

    def test_forced_source_fragment_is_linked_instead_of_resident_import(self) -> None:
        entry = build_injection.PayloadFragment(
            owner="localization.runtime_injector",
            symbol="localization.font.v2.entry",
            kind="code",
            alignment=4,
            payload=bytes(8),
            relocations=(
                build_injection.PayloadRelocation(
                    offset=0,
                    kind="jal26",
                    symbol="localization.font.v2.changed_impl",
                ),
            ),
        )
        changed_impl = build_injection.PayloadFragment(
            owner="localization.runtime_injector",
            symbol="localization.font.v2.changed_impl",
            kind="code",
            alignment=4,
            payload=bytes.fromhex("0800E00300000000"),
        )
        current_payload = bytes(16)
        symbol_map = {
            "localization.font.v2.changed_impl": {
                "kind": "code",
                "size": 8,
                "offset": 0,
                "address": 0x008F4000,
            }
        }

        with mock.patch.object(
            build_injection,
            "_load_static_fragments",
            return_value=[],
        ):
            fragments, imports = build_injection.select_fragment_closure(
                ["localization.font.v2.entry"],
                [entry, changed_impl],
                [
                    (1, "entry", "localization.font.v2.entry"),
                    (2, "impl", "localization.font.v2.changed_impl"),
                ],
                symbol_map,
                current_payload,
                {},
                forced_symbols={"localization.font.v2.changed_impl"},
            )

        self.assertEqual(
            [fragment.symbol for fragment in fragments],
            [
                "localization.font.v2.entry",
                "localization.font.v2.changed_impl",
            ],
        )
        self.assertNotIn("localization.font.v2.changed_impl", imports)

    def test_missing_build_record_is_optional_for_override_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(
                build_injection,
                "REPOSITORY",
                Path(temporary),
            ):
                self.assertIsNone(
                    build_injection.locate_build_record(
                        "AA" * 32,
                        required=False,
                    )
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


class PineInjectionTests(unittest.TestCase):
    def test_load_state_queues_slot_then_uses_pause_as_barrier(self) -> None:
        payloads: list[bytes] = []
        client = object.__new__(pine.PineClient)

        def exchange(payload: bytes) -> bytes:
            payloads.append(payload)
            return b""

        client.exchange = exchange
        client.load_state(7)

        self.assertEqual(
            payloads,
            [
                bytes([pine.LOAD_STATE, 7]),
                bytes([pine.PAUSE]),
            ],
        )


if __name__ == "__main__":
    unittest.main()
