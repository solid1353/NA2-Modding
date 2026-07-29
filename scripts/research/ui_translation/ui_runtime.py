#!/usr/bin/env python3
"""Controlled PCSX2 runtime capture for NUN5-to-NA2 UI comparison."""

from __future__ import annotations

import argparse
import configparser
import functools
import hashlib
import json
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from na228_builder.project_paths import (  # noqa: E402
    ProjectPaths,
    load_project_paths,
    resolve_alias,
)


TARGETS_PATH = SCRIPT_DIR / "targets.json"
CASE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SLOT_STATE_RE = re.compile(r"^.+ \([0-9A-Fa-f]{8}\)\.\d{2}\.p2s$")


class UiRuntimeError(RuntimeError):
    """Expected runtime-capture failure with a user-facing message."""


class PineProtocolError(UiRuntimeError):
    """Malformed or rejected PINE request/reply."""


@dataclass(frozen=True)
class Target:
    target_id: str
    serial: str
    crc: str
    image_kind: str
    image_value: str
    settings_file: str

    def image_path(self, paths: ProjectPaths) -> Path:
        if self.image_kind == "root_alias":
            return resolve_alias(self.image_value, paths)
        if self.image_kind == "project_file":
            return paths.file(self.image_value)
        raise UiRuntimeError(
            f"Target {self.target_id!r} has unsupported image kind "
            f"{self.image_kind!r}"
        )


@dataclass(frozen=True)
class RenderingSettings:
    global_aspect_ratio: str | None
    game_aspect_ratio: str | None
    effective_aspect_ratio: str | None
    global_widescreen_patches: bool
    game_patch_enable: str | None
    load_texture_replacements: bool
    dump_replaceable_textures: bool
    save_textures: bool
    pine_enabled: bool
    pine_port: int
    blockers: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        result = asdict(self)
        result["blockers"] = list(self.blockers)
        return result


@dataclass(frozen=True)
class LiveIdentity:
    emulator_version: str
    title: str
    serial: str
    crc: str
    game_version: str
    status: str


def load_targets(path: Path = TARGETS_PATH) -> dict[str, Target]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise UiRuntimeError(
            f"Unsupported target schema: {data.get('schema_version')!r}"
        )
    raw_targets = data.get("targets")
    if not isinstance(raw_targets, dict) or not raw_targets:
        raise UiRuntimeError("Target configuration has no targets")

    targets: dict[str, Target] = {}
    for target_id, raw in raw_targets.items():
        if not isinstance(raw, dict):
            raise UiRuntimeError(f"Target {target_id!r} is not an object")
        image = raw.get("image")
        if not isinstance(image, dict):
            raise UiRuntimeError(f"Target {target_id!r} has no image object")
        try:
            target = Target(
                target_id=target_id,
                serial=str(raw["serial"]),
                crc=str(raw["crc"]).upper(),
                image_kind=str(image["kind"]),
                image_value=str(image["value"]),
                settings_file=str(raw["settings_file"]),
            )
        except KeyError as exc:
            raise UiRuntimeError(
                f"Target {target_id!r} is missing {exc.args[0]!r}"
            ) from exc
        if not re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", target.serial):
            raise UiRuntimeError(
                f"Target {target_id!r} has invalid serial {target.serial!r}"
            )
        if not re.fullmatch(r"[0-9A-F]{8}", target.crc):
            raise UiRuntimeError(
                f"Target {target_id!r} has invalid CRC {target.crc!r}"
            )
        targets[target_id] = target
    return targets


def _read_ini(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    if path.is_file():
        with path.open("r", encoding="utf-8-sig") as handle:
            parser.read_file(handle)
    return parser


def _ini_value(
    parser: configparser.ConfigParser, section: str, key: str
) -> str | None:
    matched_section = next(
        (item for item in parser.sections() if item.casefold() == section.casefold()),
        None,
    )
    if matched_section is None:
        return None
    for option, value in parser.items(matched_section):
        if option.casefold() == key.casefold():
            stripped = value.strip()
            return stripped or None
    return None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().casefold()
    if normalized in {"true", "yes", "on", "1"}:
        return True
    if normalized in {"false", "no", "off", "0"}:
        return False
    raise UiRuntimeError(f"Invalid PCSX2 boolean value: {value!r}")


def inspect_rendering_settings(
    pcsx2_ini: Path, game_ini: Path
) -> RenderingSettings:
    global_ini = _read_ini(pcsx2_ini)
    per_game_ini = _read_ini(game_ini)

    global_aspect = _ini_value(global_ini, "EmuCore/GS", "AspectRatio")
    game_aspect = _ini_value(per_game_ini, "EmuCore/GS", "AspectRatio")
    effective_aspect = game_aspect or global_aspect
    global_widescreen = _parse_bool(
        _ini_value(global_ini, "EmuCore", "EnableWideScreenPatches")
    )
    game_patch_enable = _ini_value(per_game_ini, "Patches", "Enable")

    game_load_replacements = _ini_value(
        per_game_ini, "EmuCore/GS", "LoadTextureReplacements"
    )
    load_replacements = _parse_bool(
        game_load_replacements
        if game_load_replacements is not None
        else _ini_value(global_ini, "EmuCore/GS", "LoadTextureReplacements")
    )
    dump_replacements = _parse_bool(
        _ini_value(global_ini, "EmuCore/GS", "DumpReplaceableTextures")
    )
    save_textures = _parse_bool(
        _ini_value(global_ini, "EmuCore/GS", "SaveTexture")
    )
    pine_enabled = _parse_bool(_ini_value(global_ini, "EmuCore", "EnablePINE"))
    raw_port = _ini_value(global_ini, "EmuCore", "PINESlot") or "28011"
    try:
        pine_port = int(raw_port, 10)
    except ValueError as exc:
        raise UiRuntimeError(f"Invalid PINE port: {raw_port!r}") from exc
    if not 1 <= pine_port <= 65535:
        raise UiRuntimeError(f"PINE port is outside 1..65535: {pine_port}")

    blockers: list[str] = []
    if not pine_enabled:
        blockers.append("PINE is disabled in PCSX2.ini")
    if load_replacements:
        blockers.append("texture replacements are enabled")
    accepted_aspects = {"4:3", "auto 4:3/3:2"}
    if effective_aspect is None:
        blockers.append("effective aspect ratio is unknown")
    elif effective_aspect.casefold() not in accepted_aspects:
        blockers.append(
            f"effective aspect ratio is {effective_aspect!r}, not neutral 4:3"
        )
    if global_widescreen:
        blockers.append("global widescreen patches are enabled")
    if game_patch_enable and "widescreen" in game_patch_enable.casefold():
        blockers.append(
            f"per-game patch set enables {game_patch_enable!r}"
        )

    return RenderingSettings(
        global_aspect_ratio=global_aspect,
        game_aspect_ratio=game_aspect,
        effective_aspect_ratio=effective_aspect,
        global_widescreen_patches=global_widescreen,
        game_patch_enable=game_patch_enable,
        load_texture_replacements=load_replacements,
        dump_replaceable_textures=dump_replacements,
        save_textures=save_textures,
        pine_enabled=pine_enabled,
        pine_port=pine_port,
        blockers=tuple(blockers),
    )


def rendering_for_target(
    paths: ProjectPaths, target: Target
) -> RenderingSettings:
    return inspect_rendering_settings(
        paths.path("pcsx2_stable", "inis", "PCSX2.ini"),
        paths.path("pcsx2_game_settings", target.settings_file),
    )


class PineClient:
    READ_OPCODES = {8: 0x00, 16: 0x01, 32: 0x02, 64: 0x03}
    WRITE_OPCODES = {8: 0x04, 16: 0x05, 32: 0x06, 64: 0x07}
    VERSION = 0x08
    SAVE_STATE = 0x09
    TITLE = 0x0B
    SERIAL = 0x0C
    CRC = 0x0D
    GAME_VERSION = 0x0E
    STATUS = 0x0F
    STATUS_NAMES = {0: "running", 1: "paused", 2: "shutdown"}

    def __init__(self, sock: socket.socket):
        self._sock = sock

    @classmethod
    def connect(
        cls, port: int, *, host: str = "127.0.0.1", timeout: float = 3.0
    ) -> "PineClient":
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(timeout)
        except OSError as exc:
            raise UiRuntimeError(
                f"Could not connect to PCSX2 PINE at {host}:{port}: {exc}"
            ) from exc
        return cls(sock)

    def close(self) -> None:
        self._sock.close()

    def __enter__(self) -> "PineClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _recv_exact(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            try:
                chunk = self._sock.recv(size - len(result))
            except OSError as exc:
                raise PineProtocolError(f"PINE receive failed: {exc}") from exc
            if not chunk:
                raise PineProtocolError("PINE connection closed during reply")
            result.extend(chunk)
        return bytes(result)

    def _exchange(self, payload: bytes) -> bytes:
        packet = struct.pack("<I", len(payload) + 4) + payload
        try:
            self._sock.sendall(packet)
        except OSError as exc:
            raise PineProtocolError(f"PINE send failed: {exc}") from exc
        reply_size = struct.unpack("<I", self._recv_exact(4))[0]
        if not 5 <= reply_size <= 450000:
            raise PineProtocolError(f"Invalid PINE reply size: {reply_size}")
        reply = self._recv_exact(reply_size - 4)
        if reply[0] != 0:
            raise PineProtocolError("PCSX2 rejected the PINE request")
        return reply[1:]

    def _string_query(self, opcode: int) -> str:
        reply = self._exchange(bytes([opcode]))
        if len(reply) < 4:
            raise PineProtocolError("PINE string reply is missing its length")
        size = struct.unpack_from("<I", reply)[0]
        if size < 1 or len(reply) != size + 4:
            raise PineProtocolError(
                f"Malformed PINE string reply: declared {size}, got {len(reply) - 4}"
            )
        raw = reply[4:]
        if raw[-1] != 0:
            raise PineProtocolError("PINE string reply is not NUL-terminated")
        return raw[:-1].decode("utf-8", errors="replace")

    def status(self) -> str:
        reply = self._exchange(bytes([self.STATUS]))
        if len(reply) != 4:
            raise PineProtocolError("Malformed PINE status reply")
        raw = struct.unpack("<I", reply)[0]
        try:
            return self.STATUS_NAMES[raw]
        except KeyError as exc:
            raise PineProtocolError(f"Unknown PINE status value: {raw}") from exc

    def identity(self) -> LiveIdentity:
        status = self.status()
        if status == "shutdown":
            raise UiRuntimeError("PCSX2 has no running game")
        return LiveIdentity(
            emulator_version=self._string_query(self.VERSION),
            title=self._string_query(self.TITLE),
            serial=self._string_query(self.SERIAL),
            crc=self._string_query(self.CRC).upper(),
            game_version=self._string_query(self.GAME_VERSION),
            status=status,
        )

    def save_state(self, slot: int) -> None:
        if not 0 <= slot <= 255:
            raise UiRuntimeError(f"Savestate slot is outside 0..255: {slot}")
        reply = self._exchange(bytes([self.SAVE_STATE, slot]))
        if reply:
            raise PineProtocolError("Unexpected data in PINE save-state reply")

    def read(self, address: int, width: int) -> int:
        try:
            opcode = self.READ_OPCODES[width]
        except KeyError as exc:
            raise UiRuntimeError(f"Unsupported read width: {width}") from exc
        if not 0 <= address <= 0xFFFFFFFF:
            raise UiRuntimeError(f"Address is outside 32-bit range: {address:#x}")
        reply = self._exchange(bytes([opcode]) + struct.pack("<I", address))
        expected_size = width // 8
        if len(reply) != expected_size:
            raise PineProtocolError(
                f"Read{width} returned {len(reply)} bytes, expected {expected_size}"
            )
        return int.from_bytes(reply, "little")

    def write(self, address: int, width: int, value: int) -> None:
        try:
            opcode = self.WRITE_OPCODES[width]
        except KeyError as exc:
            raise UiRuntimeError(f"Unsupported write width: {width}") from exc
        if not 0 <= address <= 0xFFFFFFFF:
            raise UiRuntimeError(f"Address is outside 32-bit range: {address:#x}")
        if not 0 <= value < 1 << width:
            raise UiRuntimeError(
                f"Value is outside unsigned {width}-bit range: {value:#x}"
            )
        reply = self._exchange(
            bytes([opcode])
            + struct.pack("<I", address)
            + value.to_bytes(width // 8, "little")
        )
        if reply:
            raise PineProtocolError(f"Unexpected data in PINE Write{width} reply")


def assert_live_target(target: Target, identity: LiveIdentity) -> None:
    mismatches: list[str] = []
    if identity.serial.casefold() != target.serial.casefold():
        mismatches.append(
            f"serial {identity.serial!r} != expected {target.serial!r}"
        )
    if identity.crc.upper() != target.crc:
        mismatches.append(f"CRC {identity.crc!r} != expected {target.crc!r}")
    if mismatches:
        raise UiRuntimeError(
            f"Live game does not match target {target.target_id!r}: "
            + "; ".join(mismatches)
        )


@functools.lru_cache(maxsize=64)
def _hash_file_cached(path_text: str, size: int, mtime_ns: int) -> str:
    del size, mtime_ns
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def hash_file(path: Path) -> str:
    stat = path.stat()
    return _hash_file_cached(str(path.resolve()), stat.st_size, stat.st_mtime_ns)


def resolve_runtime_input(value: str, paths: ProjectPaths) -> Path:
    if value.startswith("@"):
        try:
            result = resolve_alias(value, paths)
        except (KeyError, ValueError) as exc:
            raise UiRuntimeError(f"Invalid project-root alias: {value!r}") from exc
    else:
        candidate = Path(value)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise UiRuntimeError(
                f"Runtime input must be repository-relative or an @root alias: {value!r}"
            )
        result = (REPOSITORY_ROOT / candidate).resolve()
        try:
            result.relative_to(REPOSITORY_ROOT)
        except ValueError as exc:
            raise UiRuntimeError(f"Runtime input escapes the repository: {value!r}") from exc
    if not result.is_file():
        raise UiRuntimeError(f"Runtime input is not a file: {value!r}")
    return result


def file_slice(path: Path, offset: int, length: int) -> bytes:
    if offset < 0:
        raise UiRuntimeError(f"File offset cannot be negative: {offset}")
    if length < 1 or length > 1024 * 1024:
        raise UiRuntimeError("Patch length must be between 1 and 1048576 bytes")
    size = path.stat().st_size
    if offset + length > size:
        raise UiRuntimeError(
            f"Requested range 0x{offset:X}..0x{offset + length:X} exceeds "
            f"{path.name} size 0x{size:X}"
        )
    with path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read(length)
    if len(data) != length:
        raise UiRuntimeError(f"Short read from runtime input: {path.name}")
    return data


def memory_chunks(address: int, length: int) -> Iterable[tuple[int, int, int]]:
    if address < 0 or length < 0 or address + length > 0x100000000:
        raise UiRuntimeError(
            f"Memory range is outside 32-bit address space: {address:#x}+{length:#x}"
        )
    cursor = 0
    while cursor < length:
        remaining = length - cursor
        width = 64 if remaining >= 8 else 32 if remaining >= 4 else 16 if remaining >= 2 else 8
        size = width // 8
        yield address + cursor, width, size
        cursor += size


def read_memory_range(client: PineClient, address: int, length: int) -> bytes:
    result = bytearray()
    for chunk_address, width, size in memory_chunks(address, length):
        result.extend(client.read(chunk_address, width).to_bytes(size, "little"))
    return bytes(result)


def write_memory_range(client: PineClient, address: int, data: bytes) -> None:
    cursor = 0
    for chunk_address, width, size in memory_chunks(address, len(data)):
        client.write(
            chunk_address,
            width,
            int.from_bytes(data[cursor : cursor + size], "little"),
        )
        cursor += size


def guarded_patch_memory(
    client: PineClient,
    address: int,
    expected: bytes,
    replacement: bytes,
) -> dict[str, object]:
    if not expected or len(expected) != len(replacement):
        raise UiRuntimeError(
            "Expected and replacement memory ranges must have the same non-zero length"
        )
    current = read_memory_range(client, address, len(expected))
    if current != expected:
        mismatch = next(
            index
            for index, (actual, wanted) in enumerate(zip(current, expected))
            if actual != wanted
        )
        raise UiRuntimeError(
            f"Guarded memory patch rejected at 0x{address + mismatch:08X}: "
            f"live {current[mismatch]:02X} != expected {expected[mismatch]:02X}; "
            f"live SHA-256 {hashlib.sha256(current).hexdigest().upper()}"
        )
    try:
        write_memory_range(client, address, replacement)
        verified = read_memory_range(client, address, len(replacement))
        if verified != replacement:
            raise UiRuntimeError(
                "Guarded memory patch readback mismatch: "
                f"got {hashlib.sha256(verified).hexdigest().upper()}"
            )
    except BaseException as exc:
        try:
            write_memory_range(client, address, expected)
            rolled_back = read_memory_range(client, address, len(expected)) == expected
        except BaseException:
            rolled_back = False
        suffix = "runtime bytes restored" if rolled_back else "runtime rollback failed"
        raise UiRuntimeError(f"Guarded memory patch failed; {suffix}: {exc}") from exc
    return {
        "address": f"0x{address:08X}",
        "length": len(replacement),
        "expected_sha256": hashlib.sha256(expected).hexdigest().upper(),
        "replacement_sha256": hashlib.sha256(replacement).hexdigest().upper(),
        "readback_verified": True,
    }


def logical_path(path: Path, paths: ProjectPaths) -> str:
    resolved = path.resolve()
    candidates: list[tuple[int, str, Path]] = []
    for root_name, root_path in paths.roots.items():
        try:
            relative = resolved.relative_to(root_path.resolve())
        except ValueError:
            continue
        candidates.append((len(root_path.parts), root_name, relative))
    if not candidates:
        raise UiRuntimeError(f"Path is outside configured project roots: {path}")
    _, root_name, relative = max(candidates, key=lambda item: item[0])
    suffix = relative.as_posix()
    return f"@{root_name}/{suffix}" if suffix != "." else f"@{root_name}"


def _slot_state_snapshot(state_root: Path) -> dict[Path, tuple[int, int]]:
    result: dict[Path, tuple[int, int]] = {}
    if not state_root.is_dir():
        return result
    for path in state_root.iterdir():
        if path.is_file() and SLOT_STATE_RE.fullmatch(path.name):
            stat = path.stat()
            result[path] = (stat.st_mtime_ns, stat.st_size)
    return result


def _state_has_screenshot(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            return "Screenshot.png" in archive.namelist()
    except (OSError, zipfile.BadZipFile):
        return False


def wait_for_saved_state(
    state_root: Path,
    target: Target,
    slot: int,
    before: dict[Path, tuple[int, int]],
    timeout: float,
) -> Path:
    expected_name = f"{target.serial} ({target.crc}).{slot:02d}.p2s"
    expected_name_folded = expected_name.casefold()
    deadline = time.monotonic() + timeout
    last_size: int | None = None
    stable_samples = 0

    while time.monotonic() < deadline:
        matches = [
            path
            for path in state_root.iterdir()
            if path.is_file() and path.name.casefold() == expected_name_folded
        ]
        if len(matches) > 1:
            raise UiRuntimeError(
                f"Multiple savestates match expected name {expected_name!r}"
            )
        if matches:
            candidate = matches[0]
            stat = candidate.stat()
            previous = before.get(candidate)
            changed = previous is None or previous != (stat.st_mtime_ns, stat.st_size)
            if changed and stat.st_size > 0:
                if stat.st_size == last_size:
                    stable_samples += 1
                else:
                    last_size = stat.st_size
                    stable_samples = 1
                if stable_samples >= 3 and _state_has_screenshot(candidate):
                    return candidate
        time.sleep(0.2)

    changed_names = sorted(
        path.name
        for path, signature in _slot_state_snapshot(state_root).items()
        if before.get(path) != signature
    )
    detail = f" Changed slot files: {changed_names}" if changed_names else ""
    raise UiRuntimeError(
        f"Timed out waiting for {expected_name!r} after {timeout:.1f}s.{detail}"
    )


def extract_embedded_screenshot(state_path: Path) -> bytes:
    try:
        with zipfile.ZipFile(state_path) as archive:
            if "Screenshot.png" not in archive.namelist():
                raise UiRuntimeError(
                    f"Savestate has no embedded Screenshot.png: {state_path.name}"
                )
            try:
                data = archive.read("Screenshot.png")
            except (NotImplementedError, RuntimeError):
                data = b""
    except zipfile.BadZipFile as exc:
        raise UiRuntimeError(f"Savestate is not a valid ZIP archive: {state_path}") from exc

    if not data:
        tar = shutil.which("tar")
        if tar is None:
            raise UiRuntimeError(
                "Savestate uses unsupported ZIP compression and tar is unavailable"
            )
        result = subprocess.run(
            [tar, "-xOf", str(state_path), "Screenshot.png"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise UiRuntimeError(
                f"Could not extract embedded screenshot with tar: {error}"
            )
        data = result.stdout
    png_dimensions(data)
    return data


def png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise UiRuntimeError("Embedded screenshot is not a PNG")
    if data[12:16] != b"IHDR":
        raise UiRuntimeError("Embedded PNG has no leading IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        raise UiRuntimeError(f"Embedded PNG has invalid dimensions {width}x{height}")
    return width, height


def _utc_capture_id() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    capture_id = now.strftime("%Y%m%dT%H%M%S_") + f"{now.microsecond // 1000:03d}Z"
    return capture_id, now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_case_and_slot(case_id: str, slot: int) -> None:
    if not CASE_RE.fullmatch(case_id):
        raise UiRuntimeError(
            "Case must match [a-z0-9][a-z0-9_-]{0,63}; "
            f"got {case_id!r}"
        )
    if not 0 <= slot <= 99:
        raise UiRuntimeError("Savestate slot must be between 0 and 99")


def _validated_target_context(
    paths: ProjectPaths, target: Target
) -> tuple[RenderingSettings, Path]:
    rendering = rendering_for_target(paths, target)
    if rendering.blockers:
        raise UiRuntimeError(
            f"Rendering preflight failed for {target.target_id!r}: "
            + "; ".join(rendering.blockers)
        )

    image_path = target.image_path(paths)
    if not image_path.is_file():
        raise UiRuntimeError(
            f"Configured image for {target.target_id!r} does not exist: "
            f"{logical_path(image_path, paths)}"
        )
    return rendering, image_path


def _archive_state(
    paths: ProjectPaths,
    target: Target,
    case_id: str,
    source_state: Path,
    *,
    slot: int,
    rendering: RenderingSettings,
    image_path: Path,
    identity: LiveIdentity | None,
    capture_method: str,
    consume_source: bool,
) -> dict[str, Any]:
    _validate_case_and_slot(case_id, slot)
    if not source_state.is_file():
        raise UiRuntimeError(
            f"Savestate does not exist: {logical_path(source_state, paths)}"
        )

    capture_id, captured_at = _utc_capture_id()
    parent = paths.path(
        "work", "UI translation", "runtime_cases", case_id, target.target_id
    )
    parent.mkdir(parents=True, exist_ok=True)
    final_dir = parent / capture_id
    if final_dir.exists():
        raise UiRuntimeError(
            f"Capture output already exists: {logical_path(final_dir, paths)}"
        )
    temp_dir = Path(tempfile.mkdtemp(prefix=".capture-", dir=parent))
    try:
        archived_state = temp_dir / "state.p2s"
        shutil.copy2(source_state, archived_state)
        screenshot = extract_embedded_screenshot(archived_state)
        screenshot_path = temp_dir / "screenshot.png"
        screenshot_path.write_bytes(screenshot)
        width, height = png_dimensions(screenshot)

        image_stat = image_path.stat()
        state_stat = archived_state.stat()
        manifest = {
            "schema_version": 1,
            "capture_id": capture_id,
            "captured_at_utc": captured_at,
            "capture_method": capture_method,
            "case": case_id,
            "target": target.target_id,
            "expected_identity": {
                "serial": target.serial,
                "crc": target.crc,
            },
            "source_image": {
                "path": logical_path(image_path, paths),
                "size": image_stat.st_size,
                "sha256": hash_file(image_path),
            },
            "live": asdict(identity) if identity is not None else None,
            "rendering": rendering.to_json(),
            "state": {
                "source_path": logical_path(source_state, paths),
                "path": "state.p2s",
                "slot": slot,
                "size": state_stat.st_size,
                "sha256": hash_file(archived_state),
            },
            "screenshot": {
                "path": "screenshot.png",
                "size": len(screenshot),
                "sha256": hashlib.sha256(screenshot).hexdigest().upper(),
                "width": width,
                "height": height,
            },
        }
        (temp_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temp_dir.rename(final_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    source_state_removed = False
    removal_warning: str | None = None
    if consume_source:
        try:
            source_state.unlink()
            source_state_removed = True
        except OSError as exc:
            removal_warning = str(exc)

    return {
        "capture": logical_path(final_dir, paths),
        "capture_method": capture_method,
        "case": case_id,
        "target": target.target_id,
        "state_sha256": manifest["state"]["sha256"],
        "screenshot": f"{logical_path(final_dir, paths)}/screenshot.png",
        "slot_state_removed": source_state_removed,
        "removal_warning": removal_warning,
    }


def capture_state(
    paths: ProjectPaths,
    target: Target,
    case_id: str,
    *,
    slot: int,
    timeout: float,
    keep_slot_state: bool,
) -> dict[str, Any]:
    _validate_case_and_slot(case_id, slot)
    if timeout <= 0:
        raise UiRuntimeError("Capture timeout must be positive")

    rendering, image_path = _validated_target_context(paths, target)
    state_root = paths.path("pcsx2_stable", "sstates")
    state_root.mkdir(parents=True, exist_ok=True)
    before = _slot_state_snapshot(state_root)

    with PineClient.connect(rendering.pine_port) as client:
        identity = client.identity()
        assert_live_target(target, identity)
        if identity.status != "paused":
            raise UiRuntimeError(
                f"PCSX2 is {identity.status}; pause it with Space before capture"
            )
        client.save_state(slot)
        source_state = wait_for_saved_state(
            state_root, target, slot, before, timeout
        )

    return _archive_state(
        paths,
        target,
        case_id,
        source_state,
        slot=slot,
        rendering=rendering,
        image_path=image_path,
        identity=identity,
        capture_method="pine_save",
        consume_source=not keep_slot_state,
    )


def _manual_state_path(paths: ProjectPaths, target: Target, slot: int) -> Path:
    _validate_case_and_slot("manual", slot)
    return paths.path(
        "pcsx2_stable", "sstates", f"{target.serial} ({target.crc}).{slot:02d}.p2s"
    )


def import_state(
    paths: ProjectPaths,
    target: Target,
    case_id: str,
    *,
    slot: int,
    consume_state: bool = False,
) -> dict[str, Any]:
    _validate_case_and_slot(case_id, slot)
    rendering, image_path = _validated_target_context(paths, target)
    source_state = _manual_state_path(paths, target, slot)
    return _archive_state(
        paths,
        target,
        case_id,
        source_state,
        slot=slot,
        rendering=rendering,
        image_path=image_path,
        identity=None,
        capture_method="manual_f1_import",
        consume_source=consume_state,
    )


def import_pairs(
    paths: ProjectPaths,
    targets: dict[str, Target],
    pairs: list[tuple[int, str]],
    *,
    consume_states: bool = False,
) -> list[dict[str, Any]]:
    required_targets = ("nun5", "current")
    missing_targets = [name for name in required_targets if name not in targets]
    if missing_targets:
        raise UiRuntimeError(
            "Pair import requires configured targets: " + ", ".join(missing_targets)
        )
    if not pairs:
        raise UiRuntimeError("Pair import requires at least one SLOT:CASE pair")

    slots = [slot for slot, _ in pairs]
    cases = [case_id for _, case_id in pairs]
    if len(slots) != len(set(slots)):
        raise UiRuntimeError("Pair import contains a duplicate savestate slot")
    if len(cases) != len(set(cases)):
        raise UiRuntimeError("Pair import contains a duplicate case name")

    for slot, case_id in pairs:
        _validate_case_and_slot(case_id, slot)
        for target_name in required_targets:
            target = targets[target_name]
            _validated_target_context(paths, target)
            source_state = _manual_state_path(paths, target, slot)
            if not source_state.is_file():
                raise UiRuntimeError(
                    f"Missing {target_name} slot {slot:02d}: "
                    f"{logical_path(source_state, paths)}"
                )
            if not _state_has_screenshot(source_state):
                raise UiRuntimeError(
                    f"Savestate has no readable embedded screenshot: "
                    f"{logical_path(source_state, paths)}"
                )

    results: list[dict[str, Any]] = []
    for slot, case_id in pairs:
        for target_name in required_targets:
            results.append(
                import_state(
                    paths,
                    targets[target_name],
                    case_id,
                    slot=slot,
                    consume_state=consume_states,
                )
            )
    return results


def _settings_payload(
    paths: ProjectPaths, targets: Iterable[Target]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for target in targets:
        image_path = target.image_path(paths)
        result[target.target_id] = {
            "serial": target.serial,
            "crc": target.crc,
            "image": logical_path(image_path, paths),
            "image_exists": image_path.is_file(),
            "rendering": rendering_for_target(paths, target).to_json(),
        }
    return result


def _parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from exc


def _parse_pair(value: str) -> tuple[int, str]:
    slot_text, separator, case_id = value.partition(":")
    if not separator or not slot_text or not case_id:
        raise argparse.ArgumentTypeError(
            f"pair must use SLOT:CASE syntax; got {value!r}"
        )
    try:
        slot = int(slot_text, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"pair slot is not a decimal integer: {slot_text!r}"
        ) from exc
    try:
        _validate_case_and_slot(case_id, slot)
    except UiRuntimeError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return slot, case_id


def build_parser(target_names: list[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    settings = commands.add_parser(
        "settings", help="inspect offline rendering preflight"
    )
    settings.add_argument("--target", choices=["all", *target_names], default="all")

    probe = commands.add_parser("probe", help="verify the live PINE target")
    probe.add_argument("--target", choices=target_names, required=True)

    capture = commands.add_parser(
        "capture", help="save and archive one paused runtime case"
    )
    capture.add_argument("--target", choices=target_names, required=True)
    capture.add_argument("--case", dest="case_id", required=True)
    capture.add_argument("--slot", type=int, default=9)
    capture.add_argument("--timeout", type=float, default=30.0)
    capture.add_argument("--keep-slot-state", action="store_true")

    import_pairs_parser = commands.add_parser(
        "import-pairs",
        help="archive matching manual F1 states for NUN5 and Current",
    )
    import_pairs_parser.add_argument(
        "--pair",
        action="append",
        type=_parse_pair,
        required=True,
        metavar="SLOT:CASE",
    )
    import_pairs_parser.add_argument("--consume-states", action="store_true")

    read = commands.add_parser("read", help="perform targeted read-only EE access")
    read.add_argument("--target", choices=target_names, required=True)
    read.add_argument("--address", type=_parse_int, required=True)
    read.add_argument("--width", type=int, choices=[8, 16, 32, 64], required=True)
    read.add_argument("--count", type=int, default=1)

    patch = commands.add_parser(
        "patch",
        help="apply a paused, identity-checked, exact-byte-guarded EE hypothesis",
    )
    patch.add_argument("--target", choices=target_names, required=True)
    patch.add_argument("--address", type=_parse_int, required=True)
    patch.add_argument("--expected-file", required=True)
    patch.add_argument("--expected-offset", type=_parse_int, required=True)
    patch.add_argument("--replacement-file", required=True)
    patch.add_argument("--replacement-offset", type=_parse_int, required=True)
    patch.add_argument("--length", type=_parse_int, required=True)

    return parser


def run(argv: list[str] | None = None) -> int:
    paths = load_project_paths(REPOSITORY_ROOT)
    targets = load_targets()
    parser = build_parser(sorted(targets))
    args = parser.parse_args(argv)

    if args.command == "settings":
        selected = targets.values() if args.target == "all" else [targets[args.target]]
        payload = _settings_payload(paths, selected)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2 if any(item["rendering"]["blockers"] for item in payload.values()) else 0

    if args.command == "import-pairs":
        results = import_pairs(
            paths,
            targets,
            args.pair,
            consume_states=args.consume_states,
        )
        print(
            json.dumps(
                {
                    "pair_count": len(args.pair),
                    "capture_count": len(results),
                    "source_states_preserved": not args.consume_states,
                    "captures": results,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    target = targets[args.target]
    rendering = rendering_for_target(paths, target)

    if args.command == "probe":
        with PineClient.connect(rendering.pine_port) as client:
            identity = client.identity()
        assert_live_target(target, identity)
        print(
            json.dumps(
                {
                    "target": target.target_id,
                    "identity": asdict(identity),
                    "rendering": rendering.to_json(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2 if rendering.blockers else 0

    if args.command == "capture":
        result = capture_state(
            paths,
            target,
            args.case_id,
            slot=args.slot,
            timeout=args.timeout,
            keep_slot_state=args.keep_slot_state,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "read":
        if args.count < 1 or args.count > 1024:
            raise UiRuntimeError("Read count must be between 1 and 1024")
        step = args.width // 8
        with PineClient.connect(rendering.pine_port) as client:
            identity = client.identity()
            assert_live_target(target, identity)
            values = [
                {
                    "address": f"0x{args.address + index * step:08X}",
                    "value": f"0x{client.read(args.address + index * step, args.width):0{args.width // 4}X}",
                }
                for index in range(args.count)
            ]
        print(
            json.dumps(
                {
                    "target": target.target_id,
                    "identity": asdict(identity),
                    "width": args.width,
                    "values": values,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "patch":
        if rendering.blockers:
            raise UiRuntimeError(
                "Runtime patch preflight failed: " + "; ".join(rendering.blockers)
            )
        expected_path = resolve_runtime_input(args.expected_file, paths)
        replacement_path = resolve_runtime_input(args.replacement_file, paths)
        expected = file_slice(expected_path, args.expected_offset, args.length)
        replacement = file_slice(
            replacement_path, args.replacement_offset, args.length
        )
        with PineClient.connect(rendering.pine_port) as client:
            identity = client.identity()
            assert_live_target(target, identity)
            if identity.status != "paused":
                raise UiRuntimeError(
                    f"Guarded memory patches require paused PCSX2; status is {identity.status}"
                )
            result = guarded_patch_memory(
                client, args.address, expected, replacement
            )
        print(
            json.dumps(
                {
                    "target": target.target_id,
                    "identity": asdict(identity),
                    "expected_source": {
                        "path": logical_path(expected_path, paths),
                        "offset": f"0x{args.expected_offset:X}",
                        "file_sha256": hash_file(expected_path),
                    },
                    "replacement_source": {
                        "path": logical_path(replacement_path, paths),
                        "offset": f"0x{args.replacement_offset:X}",
                        "file_sha256": hash_file(replacement_path),
                    },
                    "patch": result,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


def main() -> int:
    try:
        return run()
    except (UiRuntimeError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
