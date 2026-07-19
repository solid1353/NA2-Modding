from __future__ import annotations

import csv
import hashlib
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..translation import engine as translation_module


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
class ExternalTranslationPlan:
    edits: tuple[PatchEdit, ...]
    insertions: dict[str, bytes]
    summary: dict[str, object]


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


def _load_manifest(package_directory: Path) -> dict[str, str]:
    rows = _read_tsv(package_directory / "manifest.tsv", MANIFEST_FIELDS)
    manifest = {row["key"]: row["value"] for row in rows}
    if len(manifest) != len(rows):
        raise ValueError("external translation manifest contains duplicate keys")
    required = {
        "schema_version",
        "module_id",
        "mapping_sha256",
        "shortening_count",
        "direct_reference_count",
        "parent_message_count",
        "external_string_count",
        "derived_string_count",
        "pointer_edit_count",
        "restore_edit_count",
        "na2_slps_sha256",
        "na2_btl_sha256",
        "na2_etc_sha256",
        "nun5_texteng_sha256",
        "nun5_texteng_size",
        "text_load_base",
        "text_reserved_size",
        "text_output_size",
        "text_output_sha256",
        "mod_load_base",
        "mod_entry_offset",
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
            "external translation manifest key mismatch; "
            f"missing={missing}, extra={extra}"
        )
    if manifest["schema_version"] != "1":
        raise ValueError("external translation schema_version must be 1")
    for key in (
        "mapping_sha256",
        "na2_slps_sha256",
        "na2_btl_sha256",
        "na2_etc_sha256",
        "nun5_texteng_sha256",
        "text_output_sha256",
        "mod_output_sha256",
    ):
        value = manifest[key].upper()
        if len(value) != 64 or any(char not in "0123456789ABCDEF" for char in value):
            raise ValueError(f"manifest {key} must be 64 hexadecimal digits")
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


def _source_arguments(root: Path, prefix: str) -> dict[str, Path]:
    if root.is_dir():
        return {f"{prefix}_folder": root}
    if root.is_file():
        return {f"{prefix}_iso": root}
    raise FileNotFoundError(root)


def _read_source(root: Path, candidates: list[str], label: str) -> bytes:
    source = translation_module.source_from(
        root if root.is_dir() else None,
        root if root.is_file() else None,
        label,
    )
    return source.read(candidates, label)


def _require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise RuntimeError(f"Unexpected {label} SHA-256: {actual}; expected {expected}")


def _translation_inputs(
    package_directory: Path,
    roots: dict[str, Path],
    manifest: dict[str, str],
) -> tuple[
    dict[str, dict[str, object]],
    list[dict[str, str]],
    dict[str, bytes],
    dict[str, bytes],
]:
    if "na2" not in roots or "nun5" not in roots:
        raise ValueError("external translation requires na2 and nun5 roots")
    translation_directory = package_directory.parent / "translation"
    mappings_path = translation_directory / "mappings.tsv"
    _require_hash(mappings_path.read_bytes(), manifest["mapping_sha256"], "mappings.tsv")

    parsed = translation_module.parse_mappings(
        translation_module.read_rows(mappings_path)
    )
    text_by_id = {str(row["id"]): row for row in parsed["text"]}
    if len(text_by_id) != len(parsed["text"]):
        raise ValueError("canonical translation mappings contain duplicate enabled text IDs")

    translation_plan = translation_module.build_translation_plan(
        **_source_arguments(roots["na2"], "na2"),
        **_source_arguments(roots["nun5"], "nun5"),
        data_root=translation_directory,
        apply="BTL,ETC,SLPS",
    )
    if translation_plan.packaged_mappings_sha256.upper() != manifest["mapping_sha256"]:
        raise RuntimeError("translation metadata hash disagrees with external manifest")

    clean_targets = {
        target: _read_source(
            roots["na2"],
            translation_module.TARGET_SPECS[target][1],
            f"NA2 {target}",
        )
        for target in TARGET_PATHS
    }
    expected_hashes = {
        "SLPS": manifest["na2_slps_sha256"],
        "BTL": manifest["na2_btl_sha256"],
        "ETC": manifest["na2_etc_sha256"],
    }
    for target, data in clean_targets.items():
        _require_hash(data, expected_hashes[target], f"NA2 {target}")

    official_sources = {
        source_id: _read_source(roots["nun5"], candidates, source_id)
        for source_id, candidates in translation_module.SOURCE_SPECS.items()
    }
    _require_hash(
        official_sources["NUN5_TEXTENG"],
        manifest["nun5_texteng_sha256"],
        "NUN5 TEXTENG.BIN",
    )
    return text_by_id, translation_plan.patch_rows, clean_targets, official_sources


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


def _build_texteng(
    references: tuple[Reference, ...],
    text_by_id: dict[str, dict[str, object]],
    official_sources: dict[str, bytes],
    manifest: dict[str, str],
) -> tuple[bytes, dict[str, int], list[dict[str, object]]]:
    donor = official_sources["NUN5_TEXTENG"]
    donor_size = _parse_int(manifest["nun5_texteng_size"], "nun5_texteng_size")
    output_size = _parse_int(manifest["text_output_size"], "text_output_size")
    load_base = _parse_int(manifest["text_load_base"], "text_load_base")
    reserved_size = _parse_int(manifest["text_reserved_size"], "text_reserved_size")
    if len(donor) != donor_size:
        raise RuntimeError(f"Unexpected donor TEXTENG size: {len(donor)}")
    header = struct.unpack_from("<4s7I", donor, 0)
    expected_header = (
        b"MWo3",
        4,
        load_base,
        0xC0,
        donor_size - 0x100,
        0,
        load_base + donor_size,
        load_base + donor_size,
    )
    if header != expected_header:
        raise RuntimeError(f"Unexpected donor TEXTENG MWO3 header: {header!r}")

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

    result = bytearray(donor)
    addresses: dict[str, int] = {}
    string_rows: list[dict[str, object]] = []
    for mapping_id in sorted(str(value) for value in effective_ids):
        mapping = text_by_id[mapping_id]
        source_id = str(mapping["source"])
        source_offset = int(mapping["source_offset"])
        if source_id != "NUN5_TEXTENG":
            raise RuntimeError(f"{mapping_id}: external source must be NUN5_TEXTENG")

        raw_source = mapping_id in parent_ids or not str(mapping["transform"])
        if raw_source:
            text = translation_module.read_official_z(
                official_sources[source_id], source_offset, mapping_id
            )
            address = load_base + source_offset
            materialization = "donor"
            file_offset = source_offset
        else:
            text = translation_module.resolve_source_text(
                mapping, official_sources, mapping_id
            )
            encoded = text.encode("cp1252") + b"\0"
            file_offset = _align(len(result), 4)
            result.extend(b"\0" * (file_offset - len(result)))
            address = load_base + file_offset
            result.extend(encoded)
            materialization = "derived"
        addresses[mapping_id] = address
        string_rows.append(
            {
                "mapping_id": mapping_id,
                "materialization": materialization,
                "file_offset": f"0x{file_offset:X}",
                "runtime_address": f"0x{address:X}",
                "encoded_bytes": len(text.encode("cp1252")) + 1,
                "text_sha256": sha256(text.encode("cp1252")),
            }
        )

    derived_count = sum(row["materialization"] == "derived" for row in string_rows)
    if derived_count != _parse_int(manifest["derived_string_count"], "derived_string_count"):
        raise RuntimeError("unexpected derived-string count")
    if len(result) > output_size:
        raise RuntimeError(
            f"generated TEXTENG payload is 0x{len(result):X}, exceeds 0x{output_size:X}"
        )
    result.extend(b"\0" * (output_size - len(result)))
    struct.pack_into("<I", result, 0x10, output_size - 0x100)
    struct.pack_into("<II", result, 0x18, load_base + output_size, load_base + output_size)
    if len(result) > reserved_size:
        raise RuntimeError("generated TEXTENG exceeds its reserved memory envelope")
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


def _build_mod(manifest: dict[str, str]) -> bytes:
    size = _parse_int(manifest["mod_output_size"], "mod_output_size")
    load_base = _parse_int(manifest["mod_load_base"], "mod_load_base")
    entry_offset = _parse_int(manifest["mod_entry_offset"], "mod_entry_offset")
    loader = _parse_int(manifest["loader_function"], "loader_function")
    filename_offset = 0x70
    filename = b"TEXTENG.BIN\0"
    code = _words(
        [
            _addiu(29, 29, -0x20),
            _sd(31, 29, 0x10),
            _addiu(4, 0, 3),
            _lui(5, load_base >> 16),
            _addiu(5, 5, filename_offset),
            _jal(loader),
            0,
            _ld(31, 29, 0x10),
            _addiu(29, 29, 0x20),
            0x03E00008,
            0,
        ]
    )
    if entry_offset != 0x40 or entry_offset + len(code) > filename_offset:
        raise RuntimeError("MOD code/string layout no longer fits the fixed envelope")
    result = bytearray(size)
    struct.pack_into(
        "<4s7I",
        result,
        0,
        b"MWo3",
        8,
        load_base,
        0x40,
        size - 0x50,
        0,
        load_base + size,
        load_base + size,
    )
    result[0x20:0x28] = b"Mod.bin\0"
    result[entry_offset : entry_offset + len(code)] = code
    result[filename_offset : filename_offset + len(filename)] = filename
    return bytes(result)


def _restore_edits(
    patch_rows: list[dict[str, str]],
    text_by_id: dict[str, dict[str, object]],
    clean_targets: dict[str, bytes],
    manifest: dict[str, str],
) -> list[PatchEdit]:
    shortening = [row for row in text_by_id.values() if row["mode"] == "shorten"]
    edits: list[PatchEdit] = []
    restored_ids: set[str] = set()
    for row in patch_rows:
        if not row["replacement_text"].startswith("[S]"):
            continue
        path = row["path"].upper()
        offset = int(row["offset"], 0)
        expected = bytes.fromhex(row["replacement_hex"])
        replacement = bytes.fromhex(row["expected_hex"])
        matches = [
            mapping
            for mapping in shortening
            if TARGET_PATHS[str(mapping["target"])] == path
            and int(mapping["target_offset"]) <= offset
            and offset + len(expected)
            <= int(mapping["target_offset"]) + int(mapping["capacity"])
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"cannot associate shortened translation patch {path} 0x{offset:X}"
            )
        mapping_id = str(matches[0]["id"])
        target = str(matches[0]["target"])
        clean = clean_targets[target]
        if clean[offset : offset + len(replacement)] != replacement:
            raise RuntimeError(f"{mapping_id}: clean restoration bytes disagree")
        edits.append(
            PatchEdit(
                path=path,
                offset=offset,
                expected=expected,
                replacement=replacement,
                mapping_id=mapping_id,
                kind="restore_inline",
                reason="Restore the clean NA2 slot after redirecting its display pointer to official external text.",
            )
        )
        restored_ids.add(mapping_id)

    expected_count = _parse_int(manifest["restore_edit_count"], "restore_edit_count")
    shortening_ids = {str(row["id"]) for row in shortening}
    if len(edits) != expected_count or restored_ids != shortening_ids:
        raise RuntimeError(
            f"unexpected inline restoration coverage: edits={len(edits)}, "
            f"missing={sorted(shortening_ids - restored_ids)}"
        )
    return edits


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
    text_base = _parse_int(manifest["text_load_base"], "text_load_base")
    mod_base = _parse_int(manifest["mod_load_base"], "mod_load_base")
    mod_entry = mod_base + _parse_int(manifest["mod_entry_offset"], "mod_entry_offset")
    old_boundary = _parse_int(manifest["old_memory_boundary"], "old_memory_boundary")
    new_boundary = _parse_int(manifest["reservation_end"], "reservation_end")
    if new_boundary != mod_base + _parse_int(manifest["mod_output_size"], "mod_output_size"):
        raise RuntimeError("reservation_end does not match the fixed MOD envelope")
    if mod_base - text_base != _parse_int(
        manifest["text_reserved_size"], "text_reserved_size"
    ):
        raise RuntimeError("text reservation does not end at the MOD base")

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
        text_base,
        text_base,
        0,
        new_boundary - text_base,
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
            reason="Reserve resident TEXTENG/MOD memory and retain a final zero-size marker.",
        )
    )

    boundary_words = (
        (0x220, 0x3C03008E, 0x3C030094, "ELF-XT-BOUNDARY-1H"),
        (0x228, 0x2463D080, 0x24630100, "ELF-XT-BOUNDARY-1L"),
        (0x2D0, 0x3C04008E, 0x3C040094, "ELF-XT-BOUNDARY-2H"),
        (0x2D8, 0x2484D080, 0x24840100, "ELF-XT-BOUNDARY-2L"),
        (0x1885C, 0x3C17008E, 0x3C170094, "ELF-XT-BOUNDARY-3H"),
        (0x18860, 0x26F7D080, 0x26F70100, "ELF-XT-BOUNDARY-3L"),
        (0x4D6908, 0x3C03008E, 0x3C030094, "ELF-XT-BOUNDARY-4H"),
        (0x4D690C, 0x2463D080, 0x24630100, "ELF-XT-BOUNDARY-4L"),
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
                reason="Move a hardcoded resident-memory boundary to 0x00940100.",
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
            expected=b"\0" * 8,
            replacement=struct.pack("<II", mod_base, text_base),
            mapping_id="ELF-XT-LOAD-SLOTS",
            kind="loader",
            reason="Assign generic PRG loader slots 2 and 3 to MOD.BIN and TEXTENG.BIN.",
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
    cave_payload = cave_code + b"MOD.BIN\0"
    edits.append(
        _guarded_edit(
            clean,
            offset=cave_offset,
            expected=b"\0" * len(cave_payload),
            replacement=cave_payload,
            mapping_id="ELF-XT-BOOTSTRAP",
            kind="loader",
            reason="Load MOD.BIN once during the existing constructor path, invoke its bootstrap, then preserve the original call.",
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


def build_external_translation_plan(
    *,
    package_directory: Path,
    roots: dict[str, Path],
) -> ExternalTranslationPlan:
    package_directory = package_directory.resolve()
    manifest = _load_manifest(package_directory)
    references = _load_references(package_directory)
    text_by_id, translation_rows, clean_targets, official_sources = _translation_inputs(
        package_directory, roots, manifest
    )
    _validate_reference_coverage(references, text_by_id, manifest)

    texteng, addresses, string_rows = _build_texteng(
        references, text_by_id, official_sources, manifest
    )
    mod = _build_mod(manifest)
    actual_text_hash = sha256(texteng)
    actual_mod_hash = sha256(mod)
    if (
        actual_text_hash != manifest["text_output_sha256"]
        or actual_mod_hash != manifest["mod_output_sha256"]
    ):
        raise RuntimeError(
            "generated external payload hash mismatch: "
            f"TEXTENG={actual_text_hash} expected={manifest['text_output_sha256']}; "
            f"MOD={actual_mod_hash} expected={manifest['mod_output_sha256']}"
        )

    edits = _validate_nonoverlap(
        _restore_edits(translation_rows, text_by_id, clean_targets, manifest)
        + _pointer_edits(references, addresses, clean_targets, manifest)
        + _structural_edits(clean_targets["SLPS"], manifest)
    )
    counts = Counter(edit.kind for edit in edits)
    insertions = dict(
        sorted(
            {
                "PRG/MOD.BIN": mod,
                "PRG/TEXTENG.BIN": texteng,
            }.items()
        )
    )
    summary: dict[str, object] = {
        "schema_version": 1,
        "module_id": manifest["module_id"],
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
            "donor": sum(row["materialization"] == "donor" for row in string_rows),
            "derived": sum(row["materialization"] == "derived" for row in string_rows),
            "rows": string_rows,
        },
    }
    return ExternalTranslationPlan(edits, insertions, summary)


def patch_log_rows(plan: ExternalTranslationPlan) -> list[dict[str, object]]:
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
