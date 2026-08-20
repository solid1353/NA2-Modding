#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import struct
import sys
from pathlib import Path
from types import ModuleType
from typing import Mapping, Sequence


REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY))

from scripts.lib.paths import load_paths
from scripts.research.substitution.catalog import (
    SUBSTITUTION_BLOCK_FLAG_MASK,
    _negative_rng_policy,
    _timing_policy,
    load_clean_catalog,
)


MANAGER_POINTER = 0x00607600
EE_RAM_END = 0x02000000
ACTION_RECORD_SIZE = 0x54


def _load_pine_module() -> ModuleType:
    path = load_paths(REPOSITORY).file("pcsx2_pine_command")
    spec = importlib.util.spec_from_file_location("na2_agent_pine", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load Workshop PINE module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    return module


PINE = _load_pine_module()
PineClient = PINE.PineClient
PadState = PINE.PadState


class Memory:
    def __init__(self, client: PineClient) -> None:
        self.client = client

    def bytes(self, address: int, size: int) -> bytes:
        if size < 0:
            raise ValueError("memory size must not be negative")
        start = address & ~3
        end = (address + size + 3) & ~3
        return self.client.read(start, end - start)[
            address - start : address - start + size
        ]

    def u8(self, address: int) -> int:
        return self.bytes(address, 1)[0]

    def i8(self, address: int) -> int:
        return struct.unpack("<b", self.bytes(address, 1))[0]

    def u16(self, address: int) -> int:
        return struct.unpack("<H", self.bytes(address, 2))[0]

    def i16(self, address: int) -> int:
        return struct.unpack("<h", self.bytes(address, 2))[0]

    def u32(self, address: int) -> int:
        return struct.unpack("<I", self.bytes(address, 4))[0]

    def f32(self, address: int) -> float:
        return struct.unpack("<f", self.bytes(address, 4))[0]


def valid_pointer(value: int) -> bool:
    return value % 4 == 0 and 0x00100000 <= value < EE_RAM_END


def definition_state(
    memory: Memory,
    address: int,
    record_tables: dict[str, tuple[int, int, int]],
    catalog: Mapping[tuple[int, int], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    flags_10 = memory.u32(address + 0x10)
    flags_14 = memory.u32(address + 0x14)
    raw_timing = memory.i8(address + 0x1A)
    effective_timing, timing_policy = _timing_policy(raw_timing, flags_10)
    rng_modulus, rng_passing_words = _negative_rng_policy(effective_timing)
    result: dict[str, object] = {
        "address": f"0x{address:08X}",
        "flags_10": f"0x{flags_10:08X}",
        "flags_14": f"0x{flags_14:08X}",
        "substitution_block_flags": (
            f"0x{flags_14 & SUBSTITUTION_BLOCK_FLAG_MASK:08X}"
        ),
        "substitution_timing_1a": raw_timing,
        "effective_substitution_timing": effective_timing,
        "timing_policy": timing_policy,
        "negative_rng_modulus": rng_modulus,
        "negative_rng_passing_u32_words": rng_passing_words,
        "negative_rng_total_u32_words": (
            1 << 32 if rng_modulus is not None else None
        ),
        "response_selector_2c": f"0x{memory.u8(address + 0x2C):02X}",
    }
    matches = []
    for owner, (base, count, character_id) in record_tables.items():
        distance = address - base
        if (
            valid_pointer(base)
            and distance >= 0
            and distance % ACTION_RECORD_SIZE == 0
            and distance // ACTION_RECORD_SIZE < count
        ):
            index = distance // ACTION_RECORD_SIZE
            match: dict[str, object] = {
                "owner": owner,
                "character_id": character_id,
                "index": index,
                "base": f"0x{base:08X}",
            }
            catalog_record = catalog.get((character_id, index)) if catalog else None
            if catalog_record is not None:
                match["catalog"] = {
                    key: catalog_record[key]
                    for key in (
                        "record_index_hex",
                        "timing_address",
                        "timing_file_offset",
                        "raw_timing",
                        "effective_timing",
                        "policy",
                        "negative_rng_modulus",
                        "negative_rng_passing_u32_words",
                        "negative_rng_total_u32_words",
                        "response_selector_2c",
                        "substitution_block_flags",
                        "runtime_timing_mutated",
                        "runtime_timing_writers",
                        "runtime_timing_values",
                        "runtime_substitution_block_mutated",
                        "runtime_mutation_summary",
                        "command_mapping_id",
                        "command_name",
                    )
                }
            matches.append(match)
    if matches:
        result["record_matches"] = matches
    return result


def temporary_effect_state(memory: Memory, fighter: int) -> dict[str, object]:
    count = memory.u32(fighter + 0x8C4)
    head = memory.u32(fighter + 0x8C8)
    result: dict[str, object] = {
        "count": count,
        "head": f"0x{head:08X}",
        "ids": [],
        "complete": True,
        "has_id_9": False,
    }
    if count > 0x100:
        result["complete"] = False
        result["error"] = "effect count exceeds observer safety bound"
        return result

    ids: list[int] = []
    pointer = head
    seen: set[int] = set()
    for _ in range(count):
        if not valid_pointer(pointer) or pointer in seen:
            result["complete"] = False
            result["error"] = "effect list ended, cycled, or left EE RAM"
            break
        seen.add(pointer)
        ids.append(memory.u32(pointer + 0x68))
        pointer = memory.u32(pointer + 0x1C)
    result["ids"] = ids
    result["has_id_9"] = 9 in ids
    return result


def input_state(memory: Memory, address: int) -> dict[str, object]:
    ring = memory.u32(address + 0x94)
    current = memory.u32(address + 0x9C)
    count = memory.u32(address + 0xA0)
    history: list[dict[str, object]] = []
    if valid_pointer(ring) and 0 < count <= 0x100 and current < count:
        index = current
        for age in range(min(count, 16)):
            record = ring + index * 0x18
            history.append(
                {
                    "age": age,
                    "index": index,
                    "word_0": f"0x{memory.u32(record):08X}",
                    "word_1": f"0x{memory.u32(record + 4):08X}",
                    "word_2": f"0x{memory.u32(record + 8):08X}",
                }
            )
            index = count - 1 if index == 0 else index - 1
    return {
        "address": f"0x{address:08X}",
        "guard_binding_6": f"0x{memory.u16(address + 0x74):04X}",
        "guard_binding_7": f"0x{memory.u16(address + 0x76):04X}",
        "history_ring": f"0x{ring:08X}",
        "history_index": current,
        "history_count": count,
        "logical_actions": f"0x{memory.u32(address + 0xAC):08X}",
        "analog_magnitude": memory.f32(address + 0xB0),
        "direction": f"0x{memory.u32(address + 0xB4):08X}",
        "history": history,
    }


def fighter_state(
    memory: Memory,
    address: int,
    record_tables: dict[str, tuple[int, int, int]],
    catalog: Mapping[tuple[int, int], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    control_word = memory.u16(address + 0x60)
    input_pointer = memory.u32(address + 0x24)
    action_pointer = memory.u32(address + 0x94)
    definition_pointers = {
        "hit_e50": memory.u32(address + 0xE50),
        "hit_e54": memory.u32(address + 0xE54),
        "fallback_a4c": memory.u32(address + 0xA4C),
    }
    definitions = {
        name: definition_state(memory, pointer, record_tables, catalog)
        for name, pointer in definition_pointers.items()
        if valid_pointer(pointer)
    }
    eligibility_object_c74 = memory.u32(address + 0xC74)
    result: dict[str, object] = {
        "address": f"0x{address:08X}",
        "opponent": f"0x{memory.u32(address + 0x20):08X}",
        "character_id": memory.u32(address + 0x68),
        "control_word_60": f"0x{control_word:04X}",
        "side": control_word & 1,
        "controller_mode": (control_word & 0x1FF) >> 5,
        "fighter_flags_61": f"0x{memory.u8(address + 0x61):02X}",
        "health": memory.f32(address + 0x6C),
        "substitution_resource": memory.f32(address + 0x70),
        "rng_word_88": f"0x{memory.u32(address + 0x88):08X}",
        "state_a8": f"0x{memory.u8(address + 0xA8):02X}",
        "major_state_18e": memory.i16(address + 0x18E),
        "action_substate_190": memory.i16(address + 0x190),
        "action_phase_192": memory.i16(address + 0x192),
        "logical_actions_338": f"0x{memory.u32(address + 0x338):08X}",
        "action_records": {
            "count_a38": memory.u16(address + 0xA38),
            "current_index_a3c": memory.i16(address + 0xA3C),
            "current_pointer_a4c": f"0x{memory.u32(address + 0xA4C):08X}",
            "base_a54": f"0x{memory.u32(address + 0xA54):08X}",
            "base_a58": f"0x{memory.u32(address + 0xA58):08X}",
        },
        "guard_held_frames_95c": memory.i16(address + 0x95C),
        "eligibility_object_b00": f"0x{memory.u32(address + 0xB00):08X}",
        "eligibility_object_c74": f"0x{eligibility_object_c74:08X}",
        "eligibility_object_c74_state": (
            memory.u32(eligibility_object_c74 + 0x0C)
            if valid_pointer(eligibility_object_c74)
            else None
        ),
        "temporary_effects": temporary_effect_state(memory, address),
        "definitions": definitions,
    }
    if valid_pointer(action_pointer):
        result["action"] = {
            "address": f"0x{action_pointer:08X}",
            "flags_18": f"0x{memory.u32(action_pointer + 0x18):08X}",
        }
    if valid_pointer(input_pointer):
        result["input"] = input_state(memory, input_pointer)
    return result


def observe(
    client: PineClient,
    catalog: Mapping[tuple[int, int], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    status = client.status()
    if status != "paused":
        raise RuntimeError(
            f"substitution observation requires a paused VM; got {status}"
        )
    memory = Memory(client)
    manager = memory.u32(MANAGER_POINTER)
    result: dict[str, object] = {
        "vm_status": status,
        "manager_pointer": f"0x{manager:08X}",
    }
    if not valid_pointer(manager):
        result["battle_active"] = False
        return result

    result["battle_active"] = True
    result["manager"] = {
        "state": memory.u32(manager + 0x08),
        "substate": memory.u32(manager + 0x0C),
        "p1_current_id": memory.u32(manager + 0x4C),
        "p2_current_id": memory.u32(manager + 0x74),
        "p1_match_start_id": memory.u32(manager + 0xC8),
        "p2_match_start_id": memory.u32(manager + 0xF0),
    }
    fighters = {
        "p1": memory.u32(manager + 0xDE4),
        "p2": memory.u32(manager + 0xDE8),
    }
    record_tables = {
        name: (
            memory.u32(pointer + 0xA54),
            memory.u16(pointer + 0xA38),
            memory.u32(pointer + 0x68),
        )
        for name, pointer in fighters.items()
        if valid_pointer(pointer)
    }
    result["fighters"] = {
        name: fighter_state(memory, pointer, record_tables, catalog)
        for name, pointer in fighters.items()
        if valid_pointer(pointer)
    }
    return result


def integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from exc


def pad_spec(value: str) -> tuple[int, PadState]:
    slot_text, separator, buttons_text = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("pad controls must use SLOT=BUTTON,...")
    slot = integer(slot_text)
    if not 0 <= slot <= 7:
        raise argparse.ArgumentTypeError("controller slot is outside 0..7")
    buttons = tuple(filter(None, buttons_text.lower().split(",")))
    try:
        return slot, PadState.from_controls(buttons)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def pad_map(specifications: Sequence[tuple[int, PadState]]) -> dict[int, PadState]:
    result = dict(specifications)
    if len(result) != len(specifications):
        raise ValueError("controller slots must be unique")
    return result


def step_output(
    client: PineClient,
    frames: int,
    states: Mapping[int, PadState],
    catalog: Mapping[tuple[int, int], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    step = client.step_frames(frames, states)
    status = client.status()
    output = observe(client, catalog) if status == "paused" else {"vm_status": status}
    output["frame_step"] = {
        "start": step.start_frame,
        "end": step.end_frame,
        "count": frames,
    }
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Frame-exact NA2 control and substitution-state observer."
    )
    parser.add_argument("--port", required=True, type=integer)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("observe")
    step = commands.add_parser("step")
    step.add_argument("frames", type=integer)
    step.add_argument(
        "--pad",
        action="append",
        type=pad_spec,
        required=True,
        help="Full state for one controlled slot, as SLOT=BUTTON,...",
    )
    release = commands.add_parser("release")
    release.add_argument("slots", nargs="*", type=integer)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("PINE port is outside 1..65535")
    catalog: dict[tuple[int, int], Mapping[str, object]] | None = None
    if args.command in {"observe", "step"}:
        catalog_records, _, _ = load_clean_catalog()
        catalog = {
            (int(record["character_id"]), int(record["record_index"])): record
            for record in catalog_records
        }
    with PineClient(args.port) as client:
        if args.command == "observe":
            output = observe(client, catalog)
        elif args.command == "step":
            output = step_output(client, args.frames, pad_map(args.pad), catalog)
        elif args.command == "release":
            client.release_pad_states(args.slots)
            output = {"released": args.slots or "all"}
        else:
            raise AssertionError(args.command)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
