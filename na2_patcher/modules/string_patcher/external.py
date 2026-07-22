from __future__ import annotations

import csv
import hashlib
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..translation_importer import engine as translation_importer


MANIFEST_FIELDS = ["key", "value"]
REFERENCE_FIELDS = [
    "mapping_id",
    "target",
    "target_file_offset",
    "target_runtime_address",
    "resolution",
    "reference_binary",
    "reference_file_offsets",
    "parent_mapping_id",
    "parent_file_offset",
    "parent_runtime_address",
]
TARGET_PATHS = {
    "SLPS": "SLPS_258.37",
    "BTL": "PRG/BTL.BIN",
    "ETC": "PRG/ETC.BIN",
}
TARGET_RUNTIME_BASES = {
    "SLPS": 0x000FFF00,
    "BTL": 0x006B3F00,
    "ETC": 0x006B3F00,
}
VALID_RESOLUTIONS = {"direct", "parent_message"}


@dataclass(frozen=True)
class PatchEdit:
    path: str
    offset: int
    expected: bytes
    replacement: bytes
    mapping_id: str
    kind: str
    reason: str


@dataclass(frozen=True)
class ExternalStringPlan:
    edits: tuple[PatchEdit, ...]
    insertions: dict[str, bytes]
    summary: dict[str, object]
    excluded_mapping_ids: frozenset[str]


@dataclass(frozen=True)
class Reference:
    mapping_id: str
    target: str
    target_file_offset: int
    target_runtime_address: int
    resolution: str
    reference_binary: str
    reference_file_offsets: tuple[int, ...]
    parent_mapping_id: str | None
    parent_file_offset: int | None
    parent_runtime_address: int | None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != fields:
            raise ValueError(f"{path}: expected columns " + "\t".join(fields))
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    return rows


def _parse_int(value: str, label: str) -> int:
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc
    if result < 0:
        raise ValueError(f"{label}: negative integer")
    return result


def _load_config(package_directory: Path) -> dict[str, str]:
    rows = _read_tsv(package_directory / "config.tsv", MANIFEST_FIELDS)
    manifest = {row["key"]: row["value"] for row in rows}
    if len(manifest) != len(rows):
        raise ValueError("string patcher config contains duplicate keys")
    required = {
        "schema_version",
        "mapping_sha256",
        "shortening_count",
        "direct_reference_count",
        "parent_message_count",
        "external_string_count",
        "derived_string_count",
        "pointer_edit_count",
        "distinct_string_count",
        "encoded_string_bytes",
        "na2_slps_sha256",
        "na2_btl_sha256",
        "na2_etc_sha256",
        "nun5_texteng_sha256",
        "output_path",
        "mod_load_base",
        "mod_entry_offset",
        "mod_strings_offset",
        "mod_output_size",
        "mod_output_sha256",
        "reservation_end",
        "loader_function",
        "original_constructor_function",
        "hook_file_offset",
        "cave_file_offset",
        "cave_runtime_address",
        "destination_table_file_offset",
        "old_memory_boundary",
    }
    missing = sorted(required - manifest.keys())
    extra = sorted(manifest.keys() - required)
    if missing or extra:
        raise ValueError(
            "string patcher config key mismatch; "
            f"missing={missing}, extra={extra}"
        )
    if manifest["schema_version"] != "2":
        raise ValueError("string patcher schema_version must be 2")
    for key in (
        "mapping_sha256",
        "na2_slps_sha256",
        "na2_btl_sha256",
        "na2_etc_sha256",
        "nun5_texteng_sha256",
        "mod_output_sha256",
    ):
        value = manifest[key].upper()
        if len(value) != 64 or any(char not in "0123456789ABCDEF" for char in value):
            raise ValueError(f"config {key} must be 64 hexadecimal digits")
        manifest[key] = value
    return manifest


def _load_references(package_directory: Path) -> tuple[Reference, ...]:
    rows = _read_tsv(package_directory / "pointer_refs.tsv", REFERENCE_FIELDS)
    references: list[Reference] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        label = f"pointer_refs.tsv line {line} ({row['mapping_id']})"
        mapping_id = row["mapping_id"]
        if not mapping_id or mapping_id in seen:
            raise ValueError(f"{label}: duplicate or empty mapping_id")
        seen.add(mapping_id)
        target = row["target"].upper()
        reference_binary = row["reference_binary"].upper()
        if target not in TARGET_PATHS or reference_binary not in TARGET_PATHS:
            raise ValueError(f"{label}: unsupported target/reference binary")
        resolution = row["resolution"]
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"{label}: unsupported resolution {resolution!r}")
        reference_offsets = tuple(
            _parse_int(value.strip(), label)
            for value in row["reference_file_offsets"].split(",")
            if value.strip()
        )
        if not reference_offsets or len(set(reference_offsets)) != len(reference_offsets):
            raise ValueError(f"{label}: empty or duplicate reference offsets")

        parent_id = row["parent_mapping_id"]
        parent_offset = row["parent_file_offset"]
        parent_runtime = row["parent_runtime_address"]
        if resolution == "direct":
            if (parent_id, parent_offset, parent_runtime) != ("-", "-", "-"):
                raise ValueError(f"{label}: direct rows must not declare a parent")
            parent_id_value = None
            parent_offset_value = None
            parent_runtime_value = None
        else:
            if not parent_id or "-" in (parent_id, parent_offset, parent_runtime):
                raise ValueError(f"{label}: parent_message row requires a complete parent")
            parent_id_value = parent_id
            parent_offset_value = _parse_int(parent_offset, label)
            parent_runtime_value = _parse_int(parent_runtime, label)

        references.append(
            Reference(
                mapping_id=mapping_id,
                target=target,
                target_file_offset=_parse_int(row["target_file_offset"], label),
                target_runtime_address=_parse_int(row["target_runtime_address"], label),
                resolution=resolution,
                reference_binary=reference_binary,
                reference_file_offsets=reference_offsets,
                parent_mapping_id=parent_id_value,
                parent_file_offset=parent_offset_value,
                parent_runtime_address=parent_runtime_value,
            )
        )
    return tuple(references)


def _require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise RuntimeError(f"Unexpected {label} SHA-256: {actual}; expected {expected}")


def _translation_inputs(
    translation_plan: translation_importer.TranslationImportPlan,
    manifest: dict[str, str],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, bytes],
    dict[str, bytes],
]:
    if translation_plan.packaged_mappings_sha256.upper() != manifest["mapping_sha256"]:
        raise RuntimeError("translation metadata hash disagrees with string-patcher config")
    text_by_id = {str(row["id"]): row for row in translation_plan.text_mappings}
    if len(text_by_id) != len(translation_plan.text_mappings):
        raise ValueError("canonical translation mappings contain duplicate enabled text IDs")
    clean_targets = translation_plan.clean_targets
    expected_hashes = {
        "SLPS": manifest["na2_slps_sha256"],
        "BTL": manifest["na2_btl_sha256"],
        "ETC": manifest["na2_etc_sha256"],
    }
    for target, data in clean_targets.items():
        _require_hash(data, expected_hashes[target], f"NA2 {target}")

    official_sources = translation_plan.official_sources
    _require_hash(
        official_sources["NUN5_TEXTENG"],
        manifest["nun5_texteng_sha256"],
        "NUN5 TEXTENG.BIN",
    )
    return text_by_id, clean_targets, official_sources


def _validate_reference_coverage(
    references: tuple[Reference, ...],
    text_by_id: dict[str, dict[str, object]],
    manifest: dict[str, str],
) -> set[str]:
    shortening_ids = {
        mapping_id
        for mapping_id, row in text_by_id.items()
        if row["mode"] == "shorten"
    }
    reference_ids = {row.mapping_id for row in references}
    if reference_ids != shortening_ids:
        raise RuntimeError(
            "pointer reference coverage differs from enabled shortening mappings: "
            f"missing={sorted(shortening_ids - reference_ids)}, "
            f"extra={sorted(reference_ids - shortening_ids)}"
        )
    if len(shortening_ids) != _parse_int(manifest["shortening_count"], "shortening_count"):
        raise RuntimeError("unexpected enabled shortening count")

    counts = Counter(row.resolution for row in references)
    if counts["direct"] != _parse_int(
        manifest["direct_reference_count"], "direct_reference_count"
    ):
        raise RuntimeError("unexpected direct reference count")
    if counts["parent_message"] != _parse_int(
        manifest["parent_message_count"], "parent_message_count"
    ):
        raise RuntimeError("unexpected parent-message count")

    for row in references:
        mapping = text_by_id[row.mapping_id]
        if mapping["target"] != row.target:
            raise RuntimeError(f"{row.mapping_id}: target differs from pointer inventory")
        if int(mapping["target_offset"]) != row.target_file_offset:
            raise RuntimeError(f"{row.mapping_id}: target offset differs from pointer inventory")
        expected_runtime = TARGET_RUNTIME_BASES[row.target] + row.target_file_offset
        if expected_runtime != row.target_runtime_address:
            raise RuntimeError(f"{row.mapping_id}: target runtime address is inconsistent")
        if row.resolution == "parent_message":
            assert row.parent_mapping_id is not None
            assert row.parent_file_offset is not None
            assert row.parent_runtime_address is not None
            parent = text_by_id.get(row.parent_mapping_id)
            if parent is None:
                raise RuntimeError(f"{row.mapping_id}: missing parent {row.parent_mapping_id}")
            if parent["target"] != row.target:
                raise RuntimeError(f"{row.mapping_id}: parent target differs")
            if int(parent["target_offset"]) != row.parent_file_offset:
                raise RuntimeError(f"{row.mapping_id}: parent offset differs")
            if (
                TARGET_RUNTIME_BASES[row.target] + row.parent_file_offset
                != row.parent_runtime_address
            ):
                raise RuntimeError(f"{row.mapping_id}: parent runtime address is inconsistent")
    return shortening_ids


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def _build_compact_mod(
    references: tuple[Reference, ...],
    text_by_id: dict[str, dict[str, object]],
    official_sources: dict[str, bytes],
    manifest: dict[str, str],
) -> tuple[bytes, dict[str, int], list[dict[str, object]]]:
    output_size = _parse_int(manifest["mod_output_size"], "mod_output_size")
    load_base = _parse_int(manifest["mod_load_base"], "mod_load_base")
    entry_offset = _parse_int(manifest["mod_entry_offset"], "mod_entry_offset")
    strings_offset = _parse_int(manifest["mod_strings_offset"], "mod_strings_offset")
    output_path = manifest["output_path"]
    output_name = Path(output_path).name
    if output_path != f"PRG/{output_name}" or output_name != output_name.upper():
        raise ValueError("output_path must be an uppercase file directly under PRG")
    internal_name = output_name.lower().encode("ascii") + b"\0"
    if len(internal_name) != 8:
        raise ValueError("compact module filename must encode to seven ASCII bytes")
    if entry_offset != 0x40 or strings_offset < entry_offset + 8:
        raise RuntimeError("compact MOD code/string layout is invalid")

    parent_ids = {
        row.parent_mapping_id
        for row in references
        if row.parent_mapping_id is not None
    }
    effective_ids = {
        row.parent_mapping_id if row.parent_mapping_id is not None else row.mapping_id
        for row in references
    }
    if None in effective_ids:
        raise AssertionError("effective external mapping ID cannot be None")
    if len(effective_ids) != _parse_int(
        manifest["external_string_count"], "external_string_count"
    ):
        raise RuntimeError("unexpected external string count")

    result = bytearray(output_size)
    struct.pack_into(
        "<4s7I",
        result,
        0,
        b"MWo3",
        8,
        load_base,
        entry_offset,
        output_size - 0x50,
        0,
        load_base + output_size,
        load_base + output_size,
    )
    result[0x20:0x28] = internal_name
    struct.pack_into("<II", result, entry_offset, 0x03E00008, 0)

    addresses: dict[str, int] = {}
    string_rows: list[dict[str, object]] = []
    locations: dict[bytes, int] = {}
    cursor = strings_offset
    for mapping_id in sorted(str(value) for value in effective_ids):
        mapping = text_by_id[mapping_id]
        source_id = str(mapping["source"])
        source_offset = int(mapping["source_offset"])
        if source_id != "NUN5_TEXTENG":
            raise RuntimeError(f"{mapping_id}: external source must be NUN5_TEXTENG")

        if mapping_id in parent_ids or not str(mapping["transform"]):
            text = translation_importer.read_official_z(
                official_sources[source_id], source_offset, mapping_id
            )
            materialization = "packed_donor"
        else:
            text = translation_importer.resolve_source_text(
                mapping, official_sources, mapping_id
            )
            materialization = "packed_derived"
        encoded = text.encode("cp1252") + b"\0"
        file_offset = locations.get(encoded)
        if file_offset is None:
            file_offset = _align(cursor, 4)
            end = file_offset + len(encoded)
            if end > output_size:
                raise RuntimeError(
                    f"compact MOD string pool exceeds 0x{output_size:X} bytes"
                )
            result[file_offset:end] = encoded
            locations[encoded] = file_offset
            cursor = end
        else:
            materialization = "deduplicated"
        address = load_base + file_offset
        addresses[mapping_id] = address
        string_rows.append(
            {
                "mapping_id": mapping_id,
                "materialization": materialization,
                "file_offset": f"0x{file_offset:X}",
                "runtime_address": f"0x{address:X}",
                "encoded_bytes": len(encoded),
                "text_sha256": sha256(encoded[:-1]),
            }
        )

    derived_count = sum(row["materialization"] == "packed_derived" for row in string_rows)
    if derived_count != _parse_int(manifest["derived_string_count"], "derived_string_count"):
        raise RuntimeError("unexpected derived-string count")
    if len(locations) != _parse_int(
        manifest["distinct_string_count"], "distinct_string_count"
    ):
        raise RuntimeError("unexpected distinct external-string count")
    if sum(len(value) for value in locations) != _parse_int(
        manifest["encoded_string_bytes"], "encoded_string_bytes"
    ):
        raise RuntimeError("unexpected compact external-string byte count")
    if _align(cursor, 0x10) != output_size:
        raise RuntimeError(
            f"compact MOD payload ends at 0x{cursor:X}, not the declared 0x{output_size:X} envelope"
        )
    return bytes(result), addresses, string_rows


def _encode_i(opcode: int, rs: int, rt: int, immediate: int) -> int:
    if not -0x8000 <= immediate <= 0xFFFF:
        raise ValueError(f"MIPS immediate is out of range: {immediate}")
    return (opcode << 26) | (rs << 21) | (rt << 16) | (immediate & 0xFFFF)


def _addiu(rt: int, rs: int, immediate: int) -> int:
    return _encode_i(0x09, rs, rt, immediate)


def _lui(rt: int, immediate: int) -> int:
    return _encode_i(0x0F, 0, rt, immediate)


def _sd(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x3F, base, rt, offset)


def _ld(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x37, base, rt, offset)


def _jal(address: int) -> int:
    if address & 3 or not 0 <= address < 0x10000000:
        raise ValueError(f"JAL target is not encodable: 0x{address:X}")
    return 0x0C000000 | (address >> 2)


def _words(values: list[int]) -> bytes:
    return struct.pack("<" + "I" * len(values), *values)


def _pointer_edits(
    references: tuple[Reference, ...],
    addresses: dict[str, int],
    clean_targets: dict[str, bytes],
    manifest: dict[str, str],
) -> list[PatchEdit]:
    edits: dict[tuple[str, int], PatchEdit] = {}
    for row in references:
        external_id = row.parent_mapping_id or row.mapping_id
        replacement_address = addresses[external_id]
        expected_address = (
            row.parent_runtime_address
            if row.parent_runtime_address is not None
            else row.target_runtime_address
        )
        for offset in row.reference_file_offsets:
            path = TARGET_PATHS[row.reference_binary]
            clean = clean_targets[row.reference_binary]
            if offset + 4 > len(clean):
                raise RuntimeError(f"{row.mapping_id}: pointer offset is outside {path}")
            expected = struct.pack("<I", expected_address)
            if clean[offset : offset + 4] != expected:
                actual = struct.unpack_from("<I", clean, offset)[0]
                raise RuntimeError(
                    f"{row.mapping_id}: pointer {path} 0x{offset:X} is 0x{actual:X}, "
                    f"expected 0x{expected_address:X}"
                )
            edit = PatchEdit(
                path=path,
                offset=offset,
                expected=expected,
                replacement=struct.pack("<I", replacement_address),
                mapping_id=row.mapping_id,
                kind="redirect_pointer",
                reason=f"Redirect {row.mapping_id} to official external text {external_id}.",
            )
            key = (path, offset)
            prior = edits.get(key)
            if prior is not None:
                if prior.expected != edit.expected or prior.replacement != edit.replacement:
                    raise RuntimeError(f"conflicting duplicate pointer edit at {path} 0x{offset:X}")
                continue
            edits[key] = edit

    result = [edits[key] for key in sorted(edits)]
    expected_count = _parse_int(manifest["pointer_edit_count"], "pointer_edit_count")
    if len(result) != expected_count:
        raise RuntimeError(f"unexpected pointer edit count: {len(result)}")
    return result


def _guarded_edit(
    clean: bytes,
    *,
    offset: int,
    expected: bytes,
    replacement: bytes,
    mapping_id: str,
    kind: str,
    reason: str,
) -> PatchEdit:
    if len(expected) != len(replacement):
        raise ValueError(f"{mapping_id}: structural edit changes file size")
    actual = clean[offset : offset + len(expected)]
    if actual != expected:
        raise RuntimeError(
            f"{mapping_id}: unexpected clean ELF bytes at 0x{offset:X}: "
            f"{actual.hex().upper()}"
        )
    return PatchEdit(
        path=TARGET_PATHS["SLPS"],
        offset=offset,
        expected=expected,
        replacement=replacement,
        mapping_id=mapping_id,
        kind=kind,
        reason=reason,
    )


def _structural_edits(clean: bytes, manifest: dict[str, str]) -> list[PatchEdit]:
    loader = _parse_int(manifest["loader_function"], "loader_function")
    original_constructor = _parse_int(
        manifest["original_constructor_function"], "original_constructor_function"
    )
    hook_offset = _parse_int(manifest["hook_file_offset"], "hook_file_offset")
    cave_offset = _parse_int(manifest["cave_file_offset"], "cave_file_offset")
    cave_address = _parse_int(manifest["cave_runtime_address"], "cave_runtime_address")
    destination_offset = _parse_int(
        manifest["destination_table_file_offset"], "destination_table_file_offset"
    )
    mod_base = _parse_int(manifest["mod_load_base"], "mod_load_base")
    mod_entry = mod_base + _parse_int(manifest["mod_entry_offset"], "mod_entry_offset")
    old_boundary = _parse_int(manifest["old_memory_boundary"], "old_memory_boundary")
    new_boundary = _parse_int(manifest["reservation_end"], "reservation_end")
    filename = Path(manifest["output_path"]).name.encode("ascii") + b"\0"
    if len(filename) != 8:
        raise ValueError("compact module loader filename must be seven ASCII bytes")
    if new_boundary != mod_base + _parse_int(manifest["mod_output_size"], "mod_output_size"):
        raise RuntimeError("reservation_end does not match the fixed MOD envelope")

    edits: list[PatchEdit] = []
    edits.append(
        _guarded_edit(
            clean,
            offset=0x2C,
            expected=struct.pack("<H", 5),
            replacement=struct.pack("<H", 6),
            mapping_id="ELF-XT-PHNUM",
            kind="memory_layout",
            reason="Declare the added fixed no-file reservation program header.",
        )
    )
    old_final = struct.pack(
        "<8I", 1, 0x507480, old_boundary, old_boundary, 0, 0, 6, 0x10
    )
    reservation = struct.pack(
        "<8I",
        1,
        0x507480,
        mod_base,
        mod_base,
        0,
        new_boundary - mod_base,
        7,
        0x80,
    )
    new_final = struct.pack(
        "<8I", 1, 0x507480, new_boundary, new_boundary, 0, 0, 6, 0x10
    )
    edits.append(
        _guarded_edit(
            clean,
            offset=0xB4,
            expected=old_final + b"\0" * 32,
            replacement=reservation + new_final,
            mapping_id="ELF-XT-PHEADERS",
            kind="memory_layout",
            reason="Reserve the compact resident MOD code/data envelope and retain a final zero-size marker.",
        )
    )

    boundary_words = (
        (0x220, 0x3C03008E, 0x3C03008F, "ELF-XT-BOUNDARY-1H"),
        (0x228, 0x2463D080, 0x24634460, "ELF-XT-BOUNDARY-1L"),
        (0x2D0, 0x3C04008E, 0x3C04008F, "ELF-XT-BOUNDARY-2H"),
        (0x2D8, 0x2484D080, 0x24844460, "ELF-XT-BOUNDARY-2L"),
        (0x1885C, 0x3C17008E, 0x3C17008F, "ELF-XT-BOUNDARY-3H"),
        (0x18860, 0x26F7D080, 0x26F74460, "ELF-XT-BOUNDARY-3L"),
        (0x4D6908, 0x3C03008E, 0x3C03008F, "ELF-XT-BOUNDARY-4H"),
        (0x4D690C, 0x2463D080, 0x24634460, "ELF-XT-BOUNDARY-4L"),
    )
    for offset, expected_word, replacement_word, mapping_id in boundary_words:
        edits.append(
            _guarded_edit(
                clean,
                offset=offset,
                expected=struct.pack("<I", expected_word),
                replacement=struct.pack("<I", replacement_word),
                mapping_id=mapping_id,
                kind="memory_layout",
                reason="Move a hardcoded resident-memory boundary to the compact MOD end.",
            )
        )
    for offset, mapping_id, reason in (
        (0x2F79F4, "ELF-XT-BOUNDARY-LITERAL", "Move the literal final memory-boundary pointer."),
        (0x50763C, "ELF-XT-SECTION-END", "Move the zero-size final section marker."),
    ):
        edits.append(
            _guarded_edit(
                clean,
                offset=offset,
                expected=struct.pack("<I", old_boundary),
                replacement=struct.pack("<I", new_boundary),
                mapping_id=mapping_id,
                kind="memory_layout",
                reason=reason,
            )
        )

    edits.append(
        _guarded_edit(
            clean,
            offset=destination_offset + 8,
            expected=b"\0" * 4,
            replacement=struct.pack("<I", mod_base),
            mapping_id="ELF-XT-LOAD-SLOTS",
            kind="loader",
            reason="Assign generic PRG loader slot 2 to the compact translation module.",
        )
    )

    cave_string_address = cave_address + 17 * 4
    cave_code = _words(
        [
            _addiu(29, 29, -0x20),
            _sd(31, 29, 0x10),
            _sd(4, 29, 0),
            _addiu(4, 0, 2),
            _lui(5, cave_string_address >> 16),
            _addiu(5, 5, cave_string_address & 0xFFFF),
            _jal(loader),
            0,
            _jal(mod_entry),
            0,
            _ld(4, 29, 0),
            _jal(original_constructor),
            0,
            _ld(31, 29, 0x10),
            _addiu(29, 29, 0x20),
            0x03E00008,
            0,
        ]
    )
    cave_payload = cave_code + filename
    edits.append(
        _guarded_edit(
            clean,
            offset=cave_offset,
            expected=b"\0" * len(cave_payload),
            replacement=cave_payload,
            mapping_id="ELF-XT-BOOTSTRAP",
            kind="loader",
            reason=f"Load {filename[:-1].decode('ascii')} once during the existing constructor path, invoke its entry, then preserve the original call.",
        )
    )
    edits.append(
        _guarded_edit(
            clean,
            offset=hook_offset,
            expected=struct.pack("<I", _jal(original_constructor)),
            replacement=struct.pack("<I", _jal(cave_address)),
            mapping_id="ELF-XT-HOOK",
            kind="loader",
            reason="Redirect the original constructor call through the resident external-file bootstrap.",
        )
    )
    return edits


def _validate_nonoverlap(edits: list[PatchEdit]) -> tuple[PatchEdit, ...]:
    ordered = sorted(edits, key=lambda item: (item.path, item.offset, item.mapping_id))
    prior_by_path: dict[str, PatchEdit] = {}
    for edit in ordered:
        if not edit.expected or len(edit.expected) != len(edit.replacement):
            raise RuntimeError(f"{edit.mapping_id}: invalid fixed-size edit")
        prior = prior_by_path.get(edit.path)
        if prior is not None and edit.offset < prior.offset + len(prior.expected):
            raise RuntimeError(
                f"overlapping external edits: {prior.mapping_id} and {edit.mapping_id}"
            )
        prior_by_path[edit.path] = edit
    return tuple(ordered)


def build_external_string_plan(
    *,
    package_directory: Path,
    translation_plan: translation_importer.TranslationImportPlan,
) -> ExternalStringPlan:
    package_directory = package_directory.resolve()
    manifest = _load_config(package_directory)
    references = _load_references(package_directory)
    text_by_id, clean_targets, official_sources = _translation_inputs(
        translation_plan, manifest
    )
    shortening_ids = _validate_reference_coverage(references, text_by_id, manifest)

    mod, addresses, string_rows = _build_compact_mod(
        references, text_by_id, official_sources, manifest
    )
    actual_mod_hash = sha256(mod)
    if actual_mod_hash != manifest["mod_output_sha256"]:
        raise RuntimeError(
            "generated compact MOD hash mismatch: "
            f"{actual_mod_hash} expected={manifest['mod_output_sha256']}"
        )

    edits = _validate_nonoverlap(
        _pointer_edits(references, addresses, clean_targets, manifest)
        + _structural_edits(clean_targets["SLPS"], manifest)
    )
    counts = Counter(edit.kind for edit in edits)
    insertions = dict(
        sorted(
            {
                manifest["output_path"]: mod,
            }.items()
        )
    )
    summary: dict[str, object] = {
        "schema_version": 2,
        "mapping_sha256": manifest["mapping_sha256"],
        "edit_count": len(edits),
        "edits_by_kind": dict(sorted(counts.items())),
        "patched_paths": sorted({edit.path for edit in edits}),
        "insertions": {
            path: {"size": len(payload), "sha256": sha256(payload)}
            for path, payload in insertions.items()
        },
        "external_strings": {
            "count": len(string_rows),
            "distinct": len({row["runtime_address"] for row in string_rows}),
            "encoded_bytes": _parse_int(
                manifest["encoded_string_bytes"], "encoded_string_bytes"
            ),
            "derived": sum(
                row["materialization"] == "packed_derived" for row in string_rows
            ),
            "rows": string_rows,
        },
        "inline_shortening_imports_omitted": len(shortening_ids),
    }
    return ExternalStringPlan(
        edits,
        insertions,
        summary,
        frozenset(shortening_ids),
    )


def patch_log_rows(plan: ExternalStringPlan) -> list[dict[str, object]]:
    return [
        {
            "target": edit.path,
            "offset": f"0x{edit.offset:X}",
            "length": len(edit.expected),
            "original_hex": edit.expected.hex().upper(),
            "new_hex": edit.replacement.hex().upper(),
            "mapping_id": edit.mapping_id,
            "kind": edit.kind,
            "reason": edit.reason,
        }
        for edit in plan.edits
    ]
