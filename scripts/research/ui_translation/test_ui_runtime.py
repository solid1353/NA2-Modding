from __future__ import annotations

import argparse
import json
import struct
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import ui_runtime


def pine_reply(payload: bytes = b"", *, ok: bool = True) -> bytes:
    body = bytes([0 if ok else 0xFF]) + payload
    return struct.pack("<I", len(body) + 4) + body


def pine_string(value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    return struct.pack("<I", len(encoded)) + encoded


def minimal_png(width: int = 640, height: int = 480) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + bytes([8, 6, 0, 0, 0])
        + b"\0\0\0\0"
    )


class FakeSocket:
    def __init__(self, replies: bytes):
        self.replies = bytearray(replies)
        self.sent = bytearray()
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def recv(self, size: int) -> bytes:
        if not self.replies:
            return b""
        result = bytes(self.replies[:size])
        del self.replies[:size]
        return result

    def close(self) -> None:
        self.closed = True


class PineClientTests(unittest.TestCase):
    def test_status_packet_and_reply(self) -> None:
        sock = FakeSocket(pine_reply(struct.pack("<I", 1)))
        client = ui_runtime.PineClient(sock)  # type: ignore[arg-type]

        self.assertEqual(client.status(), "paused")
        self.assertEqual(bytes(sock.sent), struct.pack("<I", 5) + b"\x0f")

    def test_identity_queries(self) -> None:
        responses = b"".join(
            [
                pine_reply(struct.pack("<I", 1)),
                pine_reply(pine_string("PCSX2 v2.6.3")),
                pine_reply(pine_string("Naruto")),
                pine_reply(pine_string("SLPS-22228")),
                pine_reply(pine_string("71ade583")),
                pine_reply(pine_string("1.00")),
            ]
        )
        client = ui_runtime.PineClient(FakeSocket(responses))  # type: ignore[arg-type]

        identity = client.identity()

        self.assertEqual(identity.status, "paused")
        self.assertEqual(identity.serial, "SLPS-22228")
        self.assertEqual(identity.crc, "71ADE583")

    def test_read32(self) -> None:
        sock = FakeSocket(pine_reply(struct.pack("<I", 0x12345678)))
        client = ui_runtime.PineClient(sock)  # type: ignore[arg-type]

        self.assertEqual(client.read(0x00100000, 32), 0x12345678)
        self.assertEqual(
            bytes(sock.sent),
            struct.pack("<I", 9) + b"\x02" + struct.pack("<I", 0x00100000),
        )

    def test_write32(self) -> None:
        sock = FakeSocket(pine_reply())
        client = ui_runtime.PineClient(sock)  # type: ignore[arg-type]

        client.write(0x00100000, 32, 0x12345678)

        self.assertEqual(
            bytes(sock.sent),
            struct.pack("<I", 13)
            + b"\x06"
            + struct.pack("<I", 0x00100000)
            + struct.pack("<I", 0x12345678),
        )

    def test_rejected_request(self) -> None:
        client = ui_runtime.PineClient(  # type: ignore[arg-type]
            FakeSocket(pine_reply(ok=False))
        )
        with self.assertRaises(ui_runtime.PineProtocolError):
            client.status()


class GuardedPatchTests(unittest.TestCase):
    class MemoryClient:
        def __init__(self, data: bytes):
            self.data = bytearray(data)

        def read(self, address: int, width: int) -> int:
            size = width // 8
            return int.from_bytes(self.data[address : address + size], "little")

        def write(self, address: int, width: int, value: int) -> None:
            size = width // 8
            self.data[address : address + size] = value.to_bytes(size, "little")

    def test_exact_guard_and_readback(self) -> None:
        client = self.MemoryClient(bytes(range(32)))
        expected = bytes(range(3, 22))
        replacement = bytes(reversed(expected))

        result = ui_runtime.guarded_patch_memory(
            client, 3, expected, replacement  # type: ignore[arg-type]
        )

        self.assertEqual(client.data[3:22], replacement)
        self.assertTrue(result["readback_verified"])

    def test_mismatch_rejects_without_writing(self) -> None:
        original = bytes(range(16))
        client = self.MemoryClient(original)

        with self.assertRaisesRegex(ui_runtime.UiRuntimeError, "rejected"):
            ui_runtime.guarded_patch_memory(
                client, 4, b"wrong", b"RIGHT"  # type: ignore[arg-type]
            )

        self.assertEqual(bytes(client.data), original)


class RenderingTests(unittest.TestCase):
    GLOBAL = """\
[EmuCore]
EnablePINE = true
EnableWideScreenPatches = false
PINESlot = 28012

[EmuCore/GS]
AspectRatio = Auto 4:3/3:2
LoadTextureReplacements = false
DumpReplaceableTextures = false
SaveTexture = false
"""

    def inspect(self, game: str, *, global_ini: str | None = None):
        with tempfile.TemporaryDirectory() as raw_temp:
            temp = Path(raw_temp)
            global_path = temp / "PCSX2.ini"
            game_path = temp / "game.ini"
            global_path.write_text(global_ini or self.GLOBAL, encoding="utf-8")
            game_path.write_text(game, encoding="utf-8")
            return ui_runtime.inspect_rendering_settings(global_path, game_path)

    def test_neutral_settings_pass(self) -> None:
        settings = self.inspect("[MemoryCards]\nSlot1_Enable = true\n")
        self.assertEqual(settings.blockers, ())
        self.assertEqual(settings.effective_aspect_ratio, "Auto 4:3/3:2")

    def test_per_game_widescreen_is_blocked(self) -> None:
        settings = self.inspect(
            "[EmuCore/GS]\nAspectRatio = 16:9\n\n"
            "[Patches]\nEnable = Widescreen 16:9\n"
        )
        self.assertTrue(
            any("not neutral 4:3" in item for item in settings.blockers)
        )
        self.assertTrue(
            any("per-game patch" in item for item in settings.blockers)
        )

    def test_texture_replacements_are_blocked(self) -> None:
        changed = self.GLOBAL.replace(
            "LoadTextureReplacements = false",
            "LoadTextureReplacements = true",
        )
        settings = self.inspect("", global_ini=changed)
        self.assertIn("texture replacements are enabled", settings.blockers)


class StateArchiveTests(unittest.TestCase):
    def test_extract_embedded_screenshot(self) -> None:
        screenshot = minimal_png(512, 448)
        with tempfile.TemporaryDirectory() as raw_temp:
            state = Path(raw_temp) / "state.p2s"
            with zipfile.ZipFile(state, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("Screenshot.png", screenshot)

            extracted = ui_runtime.extract_embedded_screenshot(state)

        self.assertEqual(extracted, screenshot)
        self.assertEqual(ui_runtime.png_dimensions(extracted), (512, 448))

    def test_wait_for_expected_slot(self) -> None:
        screenshot = minimal_png()
        target = ui_runtime.Target(
            target_id="test",
            serial="SLPS-22228",
            crc="71ADE583",
            image_kind="project_file",
            image_value="current_iso",
            settings_file="unused.ini",
        )
        with tempfile.TemporaryDirectory() as raw_temp:
            root = Path(raw_temp)
            state = root / "SLPS-22228 (71ADE583).09.p2s"

            def create_state() -> None:
                time.sleep(0.05)
                with zipfile.ZipFile(state, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("Screenshot.png", screenshot)

            worker = threading.Thread(target=create_state)
            worker.start()
            found = ui_runtime.wait_for_saved_state(
                root, target, 9, {}, timeout=2.0
            )
            worker.join()

        self.assertEqual(found.name, state.name)

    def test_capture_archives_verified_state_and_consumes_slot(self) -> None:
        screenshot = minimal_png(640, 448)
        with tempfile.TemporaryDirectory() as raw_temp:
            root = Path(raw_temp)
            repository = root / "repository"
            source = root / "source"
            pcsx2 = root / "pcsx2"
            build = repository / "build"
            work = repository / "work"
            for directory in (
                repository,
                source,
                pcsx2 / "inis",
                pcsx2 / "gamesettings",
                pcsx2 / "sstates",
                build,
                work,
            ):
                directory.mkdir(parents=True, exist_ok=True)
            (pcsx2 / "inis" / "PCSX2.ini").write_text(
                RenderingTests.GLOBAL, encoding="utf-8"
            )
            (pcsx2 / "gamesettings" / "SLPS-22228_71ADE583.ini").write_text(
                "[MemoryCards]\nSlot1_Enable = true\n", encoding="utf-8"
            )
            image = build / "Current.iso"
            image.write_bytes(b"test image")

            paths = ui_runtime.ProjectPaths(
                manifest=repository / "project-paths.json",
                roots={
                    "repository": repository,
                    "source": source,
                    "pcsx2": pcsx2,
                    "build": build,
                    "work": work,
                },
                files={"current_iso": image},
            )
            target = ui_runtime.Target(
                target_id="current",
                serial="SLPS-22228",
                crc="71ADE583",
                image_kind="project_file",
                image_value="current_iso",
                settings_file="SLPS-22228_71ADE583.ini",
            )

            class FakeClient:
                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    return None

                def identity(self):
                    return ui_runtime.LiveIdentity(
                        emulator_version="PCSX2 v2.6.3",
                        title="NA2",
                        serial=target.serial,
                        crc=target.crc,
                        game_version="1.00",
                        status="paused",
                    )

                def save_state(self, slot: int) -> None:
                    state = (
                        pcsx2
                        / "sstates"
                        / f"{target.serial} ({target.crc}).{slot:02d}.p2s"
                    )
                    with zipfile.ZipFile(
                        state, "w", zipfile.ZIP_DEFLATED
                    ) as archive:
                        archive.writestr("Screenshot.png", screenshot)

            with mock.patch.object(
                ui_runtime.PineClient, "connect", return_value=FakeClient()
            ):
                result = ui_runtime.capture_state(
                    paths,
                    target,
                    "character_select",
                    slot=9,
                    timeout=2.0,
                    keep_slot_state=False,
                )

            captures = list(
                (work / "UI Translation" / "runtime_cases").rglob(
                    "manifest.json"
                )
            )
            self.assertEqual(len(captures), 1)
            manifest = json.loads(captures[0].read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_image"]["path"], "@build/Current.iso")
            self.assertEqual(manifest["screenshot"]["width"], 640)
            self.assertEqual(manifest["screenshot"]["height"], 448)
            self.assertTrue(result["slot_state_removed"])
            self.assertEqual(list((pcsx2 / "sstates").iterdir()), [])

    def test_manual_f1_import_preserves_source_state(self) -> None:
        screenshot = minimal_png(512, 448)
        with tempfile.TemporaryDirectory() as raw_temp:
            root = Path(raw_temp)
            repository = root / "repository"
            source = root / "source"
            pcsx2 = root / "pcsx2"
            build = repository / "build"
            work = repository / "work"
            for directory in (
                repository,
                source,
                pcsx2 / "inis",
                pcsx2 / "gamesettings",
                pcsx2 / "sstates",
                build,
                work,
            ):
                directory.mkdir(parents=True, exist_ok=True)
            (pcsx2 / "inis" / "PCSX2.ini").write_text(
                RenderingTests.GLOBAL, encoding="utf-8"
            )
            (pcsx2 / "gamesettings" / "SLES-55605_C071D4C1.ini").write_text(
                "[EmuCore/GS]\nAspectRatio = 4:3\n", encoding="utf-8"
            )
            image = source / "NUN5.iso"
            image.write_bytes(b"reference image")

            paths = ui_runtime.ProjectPaths(
                manifest=repository / "project-paths.json",
                roots={
                    "repository": repository,
                    "source": source,
                    "pcsx2": pcsx2,
                    "build": build,
                    "work": work,
                },
                files={"nun5_iso": image},
            )
            target = ui_runtime.Target(
                target_id="nun5",
                serial="SLES-55605",
                crc="C071D4C1",
                image_kind="project_file",
                image_value="nun5_iso",
                settings_file="SLES-55605_C071D4C1.ini",
            )
            state = pcsx2 / "sstates" / "SLES-55605 (C071D4C1).01.p2s"
            with zipfile.ZipFile(state, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("Screenshot.png", screenshot)

            result = ui_runtime.import_state(
                paths,
                target,
                "mode_select",
                slot=1,
            )

            captures = list(
                (work / "UI Translation" / "runtime_cases").rglob(
                    "manifest.json"
                )
            )
            self.assertEqual(len(captures), 1)
            manifest = json.loads(captures[0].read_text(encoding="utf-8"))
            self.assertEqual(manifest["capture_method"], "manual_f1_import")
            self.assertEqual(manifest["live"], None)
            self.assertEqual(
                manifest["expected_identity"],
                {"serial": "SLES-55605", "crc": "C071D4C1"},
            )
            self.assertEqual(
                manifest["state"]["source_path"],
                "@pcsx2/sstates/SLES-55605 (C071D4C1).01.p2s",
            )
            self.assertTrue(state.is_file())
            self.assertFalse(result["slot_state_removed"])


class PairSyntaxTests(unittest.TestCase):
    def test_pair_parser(self) -> None:
        self.assertEqual(
            ui_runtime._parse_pair("10:stage_select_sand"),
            (10, "stage_select_sand"),
        )

    def test_pair_parser_rejects_bad_syntax(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            ui_runtime._parse_pair("stage_select_sand")


class IdentityTests(unittest.TestCase):
    def test_mismatch_is_rejected(self) -> None:
        target = ui_runtime.Target(
            target_id="current",
            serial="SLPS-22228",
            crc="71ADE583",
            image_kind="project_file",
            image_value="current_iso",
            settings_file="unused.ini",
        )
        identity = ui_runtime.LiveIdentity(
            emulator_version="PCSX2 v2.6.3",
            title="Wrong",
            serial="SLES-55605",
            crc="C071D4C1",
            game_version="1.00",
            status="paused",
        )
        with self.assertRaises(ui_runtime.UiRuntimeError):
            ui_runtime.assert_live_target(target, identity)


if __name__ == "__main__":
    unittest.main()
