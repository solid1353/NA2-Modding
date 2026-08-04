from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.lib.paths import (  # noqa: E402
    Paths,
    load_paths,
    resolve_alias,
)


EE_MEMORY_SIZE = 0x02000000
MAIN_IMAGE_BASE = 0x00100000
OVERLAY_BASE = 0x006B3F00
OVERLAY_RESERVATION_END = 0x008DD080
MWO3_MAGIC = 0x336F574D

BASE_REGIONS = {
    "low_system_region": (0x00000000, MAIN_IMAGE_BASE),
    "resident_main_image": (MAIN_IMAGE_BASE, OVERLAY_BASE),
    "resident_bootstrap_cave": (0x00607314, 0x00607380),
    "overlay_reservation": (OVERLAY_BASE, OVERLAY_RESERVATION_END),
}

HEAP_GLOBALS = {
    "user_base": 0x00607380,
    "heap_end": 0x00607384,
    "tracked_bytes": 0x00607388,
    "peak_tracked_bytes": 0x0060738C,
    "allocation_count": 0x00607390,
    "unresolved_607394": 0x00607394,
    "base_sentinel": 0x00607398,
    "end_sentinel": 0x0060739C,
    "cached_largest_predecessor": 0x006073A0,
    "cached_largest_gap": 0x006073A4,
}

OVERLAY_LAYOUTS = {
    1: ("BTL.BIN", 0x008DD080),
    2: ("ADV.BIN", 0x008C7200),
    3: ("ETC.BIN", 0x006E4E00),
}

CURRENT_FIXED_REGIONS = {
    "pre_texteng_gap": (0x008DD080, 0x008F3D00),
    "texteng": (0x008F3D00, 0x00924B00),
    "post_texteng_slack": (0x00924B00, 0x00940000),
    "mod_bin": (0x00940000, 0x00940100),
}

SLOT_LABELS = {
    1: "title",
    2: "mode_select",
    3: "active_adv",
    4: "character_select",
    5: "active_battle",
    6: "shop",
    7: "collection",
    8: "options",
}

STATE_NAME_RE = re.compile(
    r"^(?P<serial>[A-Z]{4}-\d{5}) \((?P<crc>[0-9A-Fa-f]{8})\)\."
    r"(?P<slot>\d{2})\.p2s$"
)
E2E_STATE_NAME_RE = re.compile(r"^(?P<slot>\d+)\.p2s$")


class MemoryMapError(RuntimeError):
    pass


@dataclass(frozen=True)
class StateIdentity:
    serial: str
    crc: str
    slot: int


@dataclass(frozen=True)
class AllocatorBlock:
    address: int
    previous: int
    next: int
    size: int
    flags: int
    gap_after: int


@dataclass(frozen=True)
class AllocatorObservation:
    user_base: int
    heap_end: int
    tracked_bytes: int
    peak_tracked_bytes: int
    allocation_count: int
    unresolved_607394: int
    base_sentinel: int
    end_sentinel: int
    cached_largest_predecessor: int
    cached_largest_gap: int
    computed_total_free: int
    computed_largest_gap: int
    computed_largest_predecessor: int
    fragmentation_bytes: int
    walked_allocation_count: int
    computed_tracked_bytes: int
    computed_untracked_bytes: int
    flag_counts: dict[int, int]
    blocks: tuple[AllocatorBlock, ...]


@dataclass(frozen=True)
class OverlayObservation:
    kind: int
    name: str
    base: int
    effective_end: int
    phase_slack: int
    header_words: tuple[int, ...]


@dataclass(frozen=True)
class RegionObservation:
    name: str
    start: int
    end: int
    size: int
    nonzero_bytes: int
    sha256: str


@dataclass(frozen=True)
class StateObservation:
    variant: str
    identity: StateIdentity
    screen: str
    source_name: str
    source_size: int
    source_sha256: str
    allocator: AllocatorObservation
    overlay: OverlayObservation
    regions: tuple[RegionObservation, ...]


def read_u32(memory: bytes | bytearray | memoryview, address: int) -> int:
    if address < 0 or address + 4 > len(memory):
        raise MemoryMapError(f"u32 address is outside EE memory: 0x{address:08X}")
    return struct.unpack_from("<I", memory, address)[0]


def parse_state_identity(path: Path) -> StateIdentity:
    match = STATE_NAME_RE.fullmatch(path.name)
    if match is not None:
        return StateIdentity(
            serial=match.group("serial"),
            crc=match.group("crc").upper(),
            slot=int(match.group("slot")),
        )

    e2e_match = E2E_STATE_NAME_RE.fullmatch(path.name)
    if e2e_match is not None and _e2e_variant_for(path) is not None:
        return StateIdentity(
            serial="SLOP-NA228",
            crc="",
            slot=int(e2e_match.group("slot")),
        )

    raise MemoryMapError(f"Unrecognized PCSX2 savestate name: {path.name}")


def _e2e_variant_for(path: Path) -> str | None:
    state_directory = path.parent
    capture_directory = state_directory.parent
    suite_directory = capture_directory.parent
    suites_directory = suite_directory.parent
    variant_directory = suites_directory.parent
    jobs_directory = variant_directory.parent
    if (
        state_directory.name.casefold() != "sstates"
        or capture_directory.name.casefold() != "capture"
        or suites_directory.name.casefold() != "suites"
        or jobs_directory.name.casefold() != "jobs"
        or not suite_directory.name
        or not variant_directory.name
    ):
        return None
    return variant_directory.name


def _extract_with_zipfile(path: Path, member: str) -> bytes | None:
    try:
        with zipfile.ZipFile(path) as archive:
            try:
                return archive.read(member)
            except (NotImplementedError, RuntimeError):
                return None
    except (OSError, zipfile.BadZipFile) as exc:
        raise MemoryMapError(f"Savestate is not a readable ZIP archive: {path}") from exc


def extract_member(path: Path, member: str, *, expected_size: int | None = None) -> bytes:
    data = _extract_with_zipfile(path, member)
    if data is None:
        tar = shutil.which("tar")
        if tar is None:
            raise MemoryMapError(
                "Savestate compression is unsupported by Python and tar is unavailable"
            )
        result = subprocess.run(
            [tar, "-xOf", str(path), member],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data = result.stdout
        # Windows tar 3.7.7 can return a nonzero status and a harmless
        # "Truncated zstd file body" warning after emitting the complete member.
        if result.returncode != 0 and (
            expected_size is None or len(data) != expected_size
        ):
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise MemoryMapError(f"Could not extract {member!r}: {detail}")

    if expected_size is not None and len(data) != expected_size:
        raise MemoryMapError(
            f"{member!r} has size 0x{len(data):X}; expected 0x{expected_size:X}"
        )
    return data


def extract_ee_memory(path: Path) -> bytes:
    return extract_member(path, "eeMemory.bin", expected_size=EE_MEMORY_SIZE)


def parse_allocator(memory: bytes | bytearray | memoryview) -> AllocatorObservation:
    values = {name: read_u32(memory, address) for name, address in HEAP_GLOBALS.items()}
    base = values["base_sentinel"]
    end = values["end_sentinel"]
    heap_end = values["heap_end"]

    if values["user_base"] != base + 0x10:
        raise MemoryMapError(
            "Heap user base does not immediately follow the base sentinel: "
            f"0x{values['user_base']:08X} vs 0x{base + 0x10:08X}"
        )
    if end != heap_end:
        raise MemoryMapError(
            f"Heap end and end sentinel differ: 0x{heap_end:08X} vs 0x{end:08X}"
        )
    if not 0 <= base < end <= len(memory) - 0x10:
        raise MemoryMapError(
            f"Invalid heap sentinel range: 0x{base:08X}-0x{end:08X}"
        )

    blocks: list[AllocatorBlock] = []
    visited: set[int] = set()
    current = base
    expected_previous = 0
    total_free = 0
    largest_gap = -1
    largest_predecessor = 0

    while True:
        if current in visited:
            raise MemoryMapError(f"Allocator chain contains a cycle at 0x{current:08X}")
        if current < base or current > end or current + 0x10 > len(memory):
            raise MemoryMapError(
                f"Allocator node is outside the sentinel range: 0x{current:08X}"
            )
        visited.add(current)

        previous, following, size, raw_flags = struct.unpack_from(
            "<IIII", memory, current
        )
        flags = raw_flags & 0xF
        if current != base and previous != expected_previous:
            raise MemoryMapError(
                f"Allocator back-link mismatch at 0x{current:08X}: "
                f"0x{previous:08X} != 0x{expected_previous:08X}"
            )
        if size < 0x10 or size & 0xF:
            raise MemoryMapError(
                f"Allocator node has invalid size 0x{size:X} at 0x{current:08X}"
            )

        if current == end:
            blocks.append(
                AllocatorBlock(current, previous, following, size, flags, 0)
            )
            break
        if following <= current or following > end:
            raise MemoryMapError(
                f"Allocator next-link is invalid at 0x{current:08X}: 0x{following:08X}"
            )
        used_end = current + size
        if used_end > following:
            raise MemoryMapError(
                f"Allocator blocks overlap after 0x{current:08X}: "
                f"0x{used_end:08X} > 0x{following:08X}"
            )
        gap = following - used_end
        total_free += gap
        if gap > largest_gap:
            largest_gap = gap
            largest_predecessor = current
        blocks.append(
            AllocatorBlock(current, previous, following, size, flags, gap)
        )
        expected_previous = current
        current = following

        if len(blocks) > values["allocation_count"] + 2:
            raise MemoryMapError("Allocator chain exceeds the recorded allocation count")

    walked_count = len(blocks) - 2
    if walked_count != values["allocation_count"]:
        raise MemoryMapError(
            f"Allocator count mismatch: walked {walked_count}, "
            f"global reports {values['allocation_count']}"
        )
    if largest_gap < 0:
        raise MemoryMapError("Allocator chain has no gap-bearing predecessor")
    if values["cached_largest_gap"] != largest_gap:
        raise MemoryMapError(
            f"Cached largest gap 0x{values['cached_largest_gap']:X} "
            f"does not match walked value 0x{largest_gap:X}"
        )
    cached_predecessor = values["cached_largest_predecessor"]
    cached_block = next(
        (block for block in blocks if block.address == cached_predecessor), None
    )
    if cached_block is None or cached_block.gap_after != largest_gap:
        raise MemoryMapError(
            "Cached largest-gap predecessor does not identify a maximum gap: "
            f"0x{cached_predecessor:08X}"
        )

    active_blocks = blocks[1:-1]
    computed_tracked = sum(
        block.size for block in active_blocks if block.flags & 4 == 0
    )
    computed_untracked = sum(
        block.size for block in active_blocks if block.flags & 4 != 0
    )
    if computed_tracked != values["tracked_bytes"]:
        raise MemoryMapError(
            f"Tracked-byte mismatch: walked 0x{computed_tracked:X}, "
            f"global reports 0x{values['tracked_bytes']:X}"
        )
    flag_counts: dict[int, int] = {}
    for block in active_blocks:
        flag_counts[block.flags] = flag_counts.get(block.flags, 0) + 1

    return AllocatorObservation(
        **values,
        computed_total_free=total_free,
        computed_largest_gap=largest_gap,
        computed_largest_predecessor=largest_predecessor,
        fragmentation_bytes=total_free - largest_gap,
        walked_allocation_count=walked_count,
        computed_tracked_bytes=computed_tracked,
        computed_untracked_bytes=computed_untracked,
        flag_counts=flag_counts,
        blocks=tuple(blocks),
    )


def parse_overlay(memory: bytes | bytearray | memoryview) -> OverlayObservation:
    words = struct.unpack_from("<8I", memory, OVERLAY_BASE)
    if words[0] == 0:
        return OverlayObservation(
            0,
            "none",
            OVERLAY_BASE,
            OVERLAY_BASE,
            OVERLAY_RESERVATION_END - OVERLAY_BASE,
            words,
        )
    if words[0] != MWO3_MAGIC:
        raise MemoryMapError(
            f"Unexpected overlay magic at 0x{OVERLAY_BASE:08X}: 0x{words[0]:08X}"
        )
    try:
        name, effective_end = OVERLAY_LAYOUTS[words[1]]
    except KeyError as exc:
        raise MemoryMapError(f"Unknown MWo3 overlay kind: {words[1]}") from exc
    if words[2] != OVERLAY_BASE:
        raise MemoryMapError(
            f"Overlay header reports base 0x{words[2]:08X}, expected 0x{OVERLAY_BASE:08X}"
        )
    return OverlayObservation(
        words[1],
        name,
        words[2],
        effective_end,
        OVERLAY_RESERVATION_END - effective_end,
        words,
    )


def observe_region(
    memory: bytes | bytearray | memoryview, name: str, start: int, end: int
) -> RegionObservation:
    if not 0 <= start <= end <= len(memory):
        raise MemoryMapError(
            f"Region {name!r} is outside EE memory: 0x{start:08X}-0x{end:08X}"
        )
    data = bytes(memory[start:end])
    return RegionObservation(
        name=name,
        start=start,
        end=end,
        size=end - start,
        nonzero_bytes=sum(value != 0 for value in data),
        sha256=hashlib.sha256(data).hexdigest().upper(),
    )


def _variant_for(path: Path, identity: StateIdentity) -> str:
    e2e_variant = _e2e_variant_for(path)
    if e2e_variant is not None:
        return e2e_variant
    parent = path.parent.name.casefold()
    if parent in {"vanilla", "current"}:
        return parent
    if identity.serial == "SLPS-25837" and identity.crc == "C0659AD1":
        return "vanilla"
    if identity.serial in {"SLOP-NA228", "SLPS-22228"}:
        return "current"
    return "unknown"


def analyze_state(path: Path) -> StateObservation:
    identity = parse_state_identity(path)
    variant = _variant_for(path, identity)
    memory = extract_ee_memory(path)
    regions = [
        observe_region(memory, name, start, end)
        for name, (start, end) in BASE_REGIONS.items()
    ]
    if variant == "current" or _e2e_variant_for(path) is not None:
        regions.extend(
            observe_region(memory, name, start, end)
            for name, (start, end) in CURRENT_FIXED_REGIONS.items()
        )
    allocator = parse_allocator(memory)
    regions.append(
        observe_region(
            memory, "heap_end_sentinel", allocator.heap_end, allocator.heap_end + 0x10
        )
    )
    regions.append(
        observe_region(memory, "system_stack_tail", allocator.heap_end + 0x10, EE_MEMORY_SIZE)
    )
    stat = path.stat()
    return StateObservation(
        variant=variant,
        identity=identity,
        screen=SLOT_LABELS.get(identity.slot, f"slot_{identity.slot:02d}"),
        source_name=path.name,
        source_size=stat.st_size,
        source_sha256=_hash_file(path),
        allocator=allocator,
        overlay=parse_overlay(memory),
        regions=tuple(regions),
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def analyze_states(paths: Iterable[Path]) -> list[StateObservation]:
    observations = [analyze_state(path) for path in paths]
    observations.sort(key=lambda item: (item.variant, item.identity.slot, item.source_name))
    return observations


def _hex(value: int) -> str:
    return f"0x{value:08X}"


def _write_tsv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_reports(output_dir: Path, observations: Sequence[StateObservation]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory_fields = [
        "variant",
        "slot",
        "screen",
        "serial",
        "crc",
        "source_name",
        "source_size",
        "source_sha256",
    ]
    inventory_rows = [
        {
            "variant": item.variant,
            "slot": f"{item.identity.slot:02d}",
            "screen": item.screen,
            "serial": item.identity.serial,
            "crc": item.identity.crc,
            "source_name": item.source_name,
            "source_size": item.source_size,
            "source_sha256": item.source_sha256,
        }
        for item in observations
    ]
    _write_tsv(output_dir / "capture_inventory.tsv", inventory_fields, inventory_rows)

    runtime_fields = [
        "variant",
        "slot",
        "screen",
        "overlay",
        "overlay_kind",
        "overlay_effective_end",
        "phase_slack",
        "heap_user_base",
        "heap_end",
        "tracked_bytes",
        "peak_tracked_bytes",
        "allocation_count",
        "total_free",
        "largest_free",
        "fragmentation_bytes",
        "tracked_bytes_walked",
        "untracked_bytes_walked",
        "flag_counts",
        "cached_largest_predecessor",
    ]
    runtime_rows = []
    for item in observations:
        heap = item.allocator
        overlay = item.overlay
        runtime_rows.append(
            {
                "variant": item.variant,
                "slot": f"{item.identity.slot:02d}",
                "screen": item.screen,
                "overlay": overlay.name,
                "overlay_kind": overlay.kind,
                "overlay_effective_end": _hex(overlay.effective_end),
                "phase_slack": _hex(overlay.phase_slack),
                "heap_user_base": _hex(heap.user_base),
                "heap_end": _hex(heap.heap_end),
                "tracked_bytes": _hex(heap.tracked_bytes),
                "peak_tracked_bytes": _hex(heap.peak_tracked_bytes),
                "allocation_count": heap.allocation_count,
                "total_free": _hex(heap.computed_total_free),
                "largest_free": _hex(heap.computed_largest_gap),
                "fragmentation_bytes": _hex(heap.fragmentation_bytes),
                "tracked_bytes_walked": _hex(heap.computed_tracked_bytes),
                "untracked_bytes_walked": _hex(heap.computed_untracked_bytes),
                "flag_counts": ",".join(
                    f"{flag}:{count}" for flag, count in sorted(heap.flag_counts.items())
                ),
                "cached_largest_predecessor": _hex(
                    heap.cached_largest_predecessor
                ),
            }
        )
    _write_tsv(output_dir / "runtime_observations.tsv", runtime_fields, runtime_rows)

    region_fields = [
        "variant",
        "slot",
        "screen",
        "region",
        "start",
        "end",
        "size",
        "nonzero_bytes",
        "sha256",
    ]
    region_rows = []
    for item in observations:
        for region in item.regions:
            region_rows.append(
                {
                    "variant": item.variant,
                    "slot": f"{item.identity.slot:02d}",
                    "screen": item.screen,
                    "region": region.name,
                    "start": _hex(region.start),
                    "end": _hex(region.end),
                    "size": _hex(region.size),
                    "nonzero_bytes": region.nonzero_bytes,
                    "sha256": region.sha256,
                }
            )
    _write_tsv(output_dir / "region_observations.tsv", region_fields, region_rows)

    summary_observations = []
    for item in observations:
        allocator = asdict(item.allocator)
        allocator.pop("blocks")
        summary_observations.append(
            {
                "variant": item.variant,
                "identity": asdict(item.identity),
                "screen": item.screen,
                "source_name": item.source_name,
                "source_size": item.source_size,
                "source_sha256": item.source_sha256,
                "allocator": allocator,
                "overlay": asdict(item.overlay),
                "regions": [asdict(region) for region in item.regions],
            }
        )

    summary = {
        "schema_version": 1,
        "state_count": len(observations),
        "variants": sorted({item.variant for item in observations}),
        "observations": summary_observations,
    }
    (output_dir / "runtime_observations.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


def _resolve_argument(value: str, paths: Paths) -> Path:
    if value.startswith("@"):
        return resolve_alias(value, paths)
    return Path(value).resolve()


def _discover_inputs(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        raise MemoryMapError(f"Input path does not exist: {root}")
    result = sorted(path for path in root.rglob("*.p2s") if path.is_file())
    if not result:
        raise MemoryMapError(f"No .p2s savestates found below: {root}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate NA2's EE allocator and map savestate memory regions."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help=(
            "Savestate files/directories or @root paths. Defaults to this task's "
            "preserved 2026-07-22 capture set."
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Write TSV and JSON reports to this directory or @root path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = load_paths(REPOSITORY_ROOT)
    raw_inputs = args.inputs or [
        str(
            paths.path(
                "work", "EE Runtime Memory Map", "savestates", "2026-07-22"
            )
        )
    ]
    inputs: list[Path] = []
    for value in raw_inputs:
        inputs.extend(_discover_inputs(_resolve_argument(value, paths)))
    observations = analyze_states(inputs)

    if args.output_dir:
        output_dir = _resolve_argument(args.output_dir, paths)
        write_reports(output_dir, observations)
        print(f"Analyzed {len(observations)} savestates into {output_dir}")
    else:
        concise = [
            {
                "variant": item.variant,
                "slot": item.identity.slot,
                "screen": item.screen,
                "overlay": item.overlay.name,
                "heap_user_base": _hex(item.allocator.user_base),
                "total_free": _hex(item.allocator.computed_total_free),
                "largest_free": _hex(item.allocator.computed_largest_gap),
            }
            for item in observations
        ]
        print(json.dumps(concise, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MemoryMapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
