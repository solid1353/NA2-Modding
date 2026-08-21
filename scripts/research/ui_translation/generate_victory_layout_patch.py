from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from scripts.lib.paths import load_paths  # noqa: E402


PATCH_ID = "ui_layout_victory_names"
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
MERGED_DEFINITIONS = {
    frozenset(
        {
            "e__localization__ui_layout__victory_names_na2_btl_at_00216610",
            "e__localization__ui_layout__victory_names_na2_btl_at_00216c30",
        }
    ): (
        "e__localization__ui_layout__victory_names_width_154_frame_0_na2_btl",
        "Use the NUN5 frame-0 template with atlas width 156 and renderer "
        "width 154 for all matching Victory name descriptors.",
    ),
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
) -> dict[str, dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for edit in generated_edits:
        signature = (
            edit["operation"],
            edit["destination_target_id"],
            edit["expected_hex"],
            edit["replacement_hex"],
        )
        grouped[signature].append(edit)

    generated: dict[str, dict[str, object]] = {}
    for group in grouped.values():
        source_ids = frozenset(edit["edit_id"] for edit in group)
        if len(group) == 1:
            edit_id = group[0]["edit_id"]
            description = group[0]["reason"]
        else:
            merged = MERGED_DEFINITIONS.get(source_ids)
            if merged is None:
                raise ValueError(
                    "Equivalent Victory edits need one declared multi-offset "
                    f"identity: {sorted(source_ids)}"
                )
            edit_id, description = merged
        first = group[0]
        generated[edit_id] = {
            "description": description,
            "operation": first["operation"],
            "destination_target_id": first["destination_target_id"],
            "destination_offsets": [
                edit["destination_offset"] for edit in group
            ],
            "expected_hex": first["expected_hex"],
            "replacement_hex": first["replacement_hex"],
        }
    return generated


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
    stored = {
        edit_id: definition
        for edit_id, definition in stored_edits.items()
        if edit_id.startswith("e__localization__ui_layout__victory_names_")
    }
    if stored != generated:
        missing = sorted(set(generated) - set(stored))
        unexpected = sorted(set(stored) - set(generated))
        changed = sorted(
            edit_id
            for edit_id in set(stored) & set(generated)
            if stored[edit_id] != generated[edit_id]
        )
        raise ValueError(
            "Stored Victory definitions differ from the verified derivation: "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )

    print(f"patch_id={PATCH_ID}")
    print(f"edits={len(generated_edits)}")
    print(f"definitions={len(generated)}")
    print("mode=check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
