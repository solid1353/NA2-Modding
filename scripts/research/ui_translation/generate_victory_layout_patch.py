from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from scripts.lib.paths import load_paths  # noqa: E402


PATCH_ID = "ui_layout_victory_names"
EDIT_ROOT_ID = "e__localization__ui_layout__record_tables"
TABLE_ID = "victory_name_descriptors"
CHARACTER_COUNT = 94
NA2_BTL_EXPECTED_SIZE = 2_237_184
NA2_BTL_EXPECTED_SHA256 = (
    "56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C"
)
NUN5_ELF_EXPECTED_SIZE = 5_340_912
NUN5_ELF_EXPECTED_SHA256 = (
    "20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D"
)
NUN5_BTL_EXPECTED_SIZE = 2_253_184
NUN5_BTL_EXPECTED_SHA256 = (
    "7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3"
)
NA2_BTL_RUNTIME_BASE = 0x006B3F00
NA2_POINTER_TABLE_OFFSET = 0x001F1D40
NUN5_ENGLISH_WIDTH_TABLE_OFFSET = 0x004DE6D0
NUN5_TEMPLATE_OFFSETS = (0x0021B9C0, 0x0021B9E0)
DESCRIPTOR_SIZE = 24
WIDTH_OFFSET = 4
TABLE_OFFSET = 0x002161B0
RECORD_STRIDE = 32
MERGED_SOURCE_IDS = {
    frozenset(
        {
            "e__localization__ui_layout__victory_names_na2_btl_at_00216610",
            "e__localization__ui_layout__victory_names_na2_btl_at_00216c30",
        }
    )
}


def read_verified(
    path: Path,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest().upper()
    if len(payload) != expected_size or digest != expected_sha256:
        raise RuntimeError(
            f"Unexpected source identity for {path}: "
            f"size={len(payload)} sha256={digest}"
        )
    return payload


def build_patch_rows() -> list[dict[str, str]]:
    paths = load_paths(REPOSITORY)
    na2_btl = read_verified(
        paths.path("source_na2", "PRG", "BTL.BIN"),
        NA2_BTL_EXPECTED_SIZE,
        NA2_BTL_EXPECTED_SHA256,
    )
    nun5_elf = read_verified(
        paths.path("source_nun5", "SLES_556.05"),
        NUN5_ELF_EXPECTED_SIZE,
        NUN5_ELF_EXPECTED_SHA256,
    )
    nun5_btl = read_verified(
        paths.path("source_nun5", "PRG", "BTL.BIN"),
        NUN5_BTL_EXPECTED_SIZE,
        NUN5_BTL_EXPECTED_SHA256,
    )
    templates = tuple(
        nun5_btl[offset : offset + DESCRIPTOR_SIZE]
        for offset in NUN5_TEMPLATE_OFFSETS
    )
    if templates != (
        bytes.fromhex("0100010000003E00000000000000F8C10000000000000000"),
        bytes.fromhex("0100410000003E00000000000000F8C10000000000000000"),
    ):
        raise RuntimeError("Unexpected NUN5 Victory frame templates")

    pointers = struct.unpack_from(
        f"<{CHARACTER_COUNT * 2}I",
        na2_btl,
        NA2_POINTER_TABLE_OFFSET,
    )
    desired_by_pointer: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for character_id in range(CHARACTER_COUNT):
        first_width, second_width = struct.unpack_from(
            "<HH",
            nun5_elf,
            NUN5_ENGLISH_WIDTH_TABLE_OFFSET + character_id * 8,
        )
        for frame, donor_width in enumerate((first_width, second_width)):
            pointer = pointers[character_id * 2 + frame]
            if pointer == 0:
                if donor_width != 0:
                    raise RuntimeError(
                        f"Character {character_id} frame {frame} has donor "
                        "width but no NA2 descriptor"
                    )
                continue
            desired_by_pointer[pointer].append(
                (character_id, frame, donor_width)
            )

    edits: list[dict[str, str]] = []
    for pointer, references in sorted(desired_by_pointer.items()):
        nonzero_widths = {width for _, _, width in references if width != 0}
        nonzero_frames = {
            frame for _, frame, width in references if width != 0
        }
        if not nonzero_widths:
            continue
        if len(nonzero_widths) != 1 or len(nonzero_frames) != 1:
            detail = ", ".join(
                f"{character_id}/f{frame}={width}"
                for character_id, frame, width in references
            )
            raise RuntimeError(
                f"Conflicting NUN5 layouts for 0x{pointer:08X}: {detail}"
            )

        donor_width = next(iter(nonzero_widths))
        descriptor_offset = pointer - NA2_BTL_RUNTIME_BASE
        if descriptor_offset < 0 or descriptor_offset + DESCRIPTOR_SIZE > len(na2_btl):
            raise RuntimeError(
                f"NA2 descriptor pointer escapes BTL.BIN: 0x{pointer:08X}"
            )
        descriptor = na2_btl[
            descriptor_offset : descriptor_offset + DESCRIPTOR_SIZE
        ]
        x, y, target_width, height = struct.unpack_from("<HHHH", descriptor)
        if x not in {1, 2} or y not in {1, 65} or height not in {62, 63}:
            raise RuntimeError(
                f"Unexpected NA2 descriptor at 0x{descriptor_offset:X}: "
                f"{(x, y, target_width, height)}"
            )

        frame = next(iter(nonzero_frames))
        replacement_width = donor_width - 2
        expected = descriptor
        replacement_record = bytearray(templates[frame])
        struct.pack_into("<H", replacement_record, WIDTH_OFFSET, replacement_width)
        replacement = bytes(replacement_record)
        if expected == replacement:
            continue
        source_rows = ", ".join(
            f"{character_id}/f{frame}"
            for character_id, frame, width in references
            if width == donor_width
        )
        edits.append(
            {
                "edit_id": (
                    "e__localization__ui_layout__victory_names_na2_btl_at_"
                    f"{descriptor_offset:08x}"
                ),
                "patch_id": PATCH_ID,
                "order": str((len(edits) + 1) * 10),
                "destination_target_id": "na2_btl",
                "destination_offset": f"0x{descriptor_offset:X}",
                "operation": "replace",
                "length": str(DESCRIPTOR_SIZE),
                "expected_hex": expected.hex().upper(),
                "expected_sha256": "",
                "replacement_hex": replacement.hex().upper(),
                "source_target_id": "",
                "source_offset": "",
                "source_expected_hex": "",
                "source_expected_sha256": "",
                "blob_path": "",
                "blob_offset": "",
                "blob_sha256": "",
                "fill_hex": "",
                "reason": (
                    f"NUN5 English width row(s) {source_rows} supply atlas "
                    f"width {donor_width}; derive the complete NA2 descriptor "
                    f"from NUN5 frame-{frame} template 0x"
                    f"{NUN5_TEMPLATE_OFFSETS[frame]:X} and its renderer width "
                    f"{donor_width}-2={replacement_width}."
                ),
            }
        )

    return edits


def build_definitions(
    generated_edits: list[dict[str, str]],
) -> dict[str, object]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for edit in generated_edits:
        signature = (
            edit["operation"],
            edit["destination_target_id"],
            edit["expected_hex"],
            edit["replacement_hex"],
        )
        grouped[signature].append(edit)

    records: dict[str, dict[str, object]] = {}
    for group in grouped.values():
        source_ids = frozenset(edit["edit_id"] for edit in group)
        if len(group) > 1 and source_ids not in MERGED_SOURCE_IDS:
            raise ValueError(
                "Equivalent Victory edits need one declared multi-offset "
                f"identity: {sorted(source_ids)}"
            )
        character_ids: list[int] = []
        frames: set[int] = set()
        for edit in group:
            rows = re.search(
                r"row\(s\) (.+?) supply atlas width",
                edit["reason"],
            )
            if rows is None:
                raise ValueError(
                    f"Victory edit has no donor-row identity: {edit['edit_id']}"
                )
            for character_id, frame in re.findall(r"(\d+)/f([01])", rows.group(1)):
                character_ids.append(int(character_id))
                frames.add(int(frame))
        if len(frames) != 1:
            raise ValueError(f"Victory edit group mixes frames: {sorted(source_ids)}")
        frame = next(iter(frames))
        member_id = (
            "character_ids_"
            + "_".join(f"{character_id:02d}" for character_id in character_ids)
            + f"_frame_{frame}"
        )
        if member_id in records:
            raise ValueError(f"Duplicate Victory member identity: {member_id}")
        first = group[0]
        indices: list[int] = []
        for edit in group:
            destination = int(edit["destination_offset"], 0)
            relative = destination - TABLE_OFFSET
            if relative < 0 or relative % RECORD_STRIDE != 0:
                raise ValueError(
                    f"Victory descriptor is outside the fixed-stride table: "
                    f"0x{destination:X}"
                )
            indices.append(relative // RECORD_STRIDE)
        index_field = (
            {"record_index": indices[0]}
            if len(indices) == 1
            else {"record_indices": indices}
        )
        records[member_id] = {
            **index_field,
            "expected_hex": first["expected_hex"],
            "replacement_hex": first["replacement_hex"],
        }
    return {
        "description": "Patch behavior-equivalent localized Victory name descriptors.",
        "operation": "replace_table",
        "destination_target_id": "na2_btl",
        "table_offset": f"0x{TABLE_OFFSET:X}",
        "record_stride": RECORD_STRIDE,
        "field_offset": 0,
        "record_patches": dict(sorted(records.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the stored Victory name-width edits against their original "
            "NA2 and NUN5 derivation."
        )
    )
    parser.parse_args()

    generated_edits = build_patch_rows()
    generated = build_definitions(generated_edits)
    edits_path = load_paths(REPOSITORY).path("builder", "catalog", "edits.json")
    stored_edits = json.loads(edits_path.read_text(encoding="utf-8"))
    stored_root = stored_edits.get(EDIT_ROOT_ID, {})
    stored_tables = stored_root.get("edits", {})
    stored = stored_tables.get(TABLE_ID)
    if stored != generated:
        raise ValueError(
            "Stored Victory table differs from the verified derivation"
        )

    print(f"patch_id={PATCH_ID}")
    print(f"edits={len(generated_edits)}")
    print("tables=1")
    print(f"records={len(generated['record_patches'])}")
    print("mode=check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
