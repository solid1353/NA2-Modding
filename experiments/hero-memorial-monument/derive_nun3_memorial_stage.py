"""Derive a NA2-compatible static Hero's Memorial Monument stage archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.research.ui_translation.texture_derivation import parse_toc, section_total_size


DONOR_SHA256 = "3720FB38174EE2B61057DECECDE79795936AE41FE51DA5E5F5556DDF22AB2CDB"
TARGET_SHA256 = "2F4418353B5A35F54BEF72415501AD3913CCC08B6222085D15CF9156E9269501"


def sections(payload: bytes):
    cursor = 0
    while cursor + 8 <= len(payload):
        kind, words = struct.unpack_from("<II", payload, cursor)
        size = section_total_size(payload, cursor, kind, words)
        if size < 8 or cursor + size > len(payload):
            raise ValueError(f"invalid CCS section at {cursor:#x}")
        yield cursor, size, kind
        cursor += size
    if cursor != len(payload):
        raise ValueError("trailing bytes after CCS sections")


def normalize_donor_names(payload: bytes) -> bytes:
    _, files, names, _ = parse_toc(payload, 60)
    replacements = {
        "DMY_b_cl_3_nor": "DMY_b_cl_1_nor",
        "DMY_b_cl_3_nor_1": "DMY_b_cl_1_nor_1",
    }
    model_sections = {}
    for offset, _, kind in sections(payload):
        if kind in {0xCCCC0100, 0xCCCC0A00}:
            model_sections.setdefault(struct.unpack_from("<I", payload, offset + 8)[0], set()).add(kind)
    for index, name in enumerate(names, 1):
        if name.startswith("OBJ_") and names.count(name) == 2:
            if 0xCCCC0A00 in model_sections.get(index, ()):
                other = [
                    candidate for candidate, candidate_name in enumerate(names, 1)
                    if candidate_name == name and candidate != index
                ]
                if len(other) != 1 or 0xCCCC0100 not in model_sections.get(other[0], ()):
                    raise ValueError(f"ambiguous duplicate model name: {name}")
                replacements[(index, name)] = "GRP_" + name[4:]
    data = bytearray(payload)
    objects_start = 60 + 80 + len(files) * 32
    for key, new_name in replacements.items():
        if isinstance(key, tuple):
            object_id, old_name = key
        else:
            old_name = key
            object_id = names.index(old_name) + 1
        if len(new_name.encode("ascii")) > 29:
            raise ValueError(f"new name too long: {new_name}")
        if names[object_id - 1] != old_name:
            raise ValueError("CCS object name drift")
        start = objects_start + (object_id - 1) * 32
        data[start : start + 30] = new_name.encode("ascii").ljust(30, b"\0")
    return bytes(data)


def bgdata_section(donor: bytes, target: bytes) -> bytes:
    _, _, donor_names, _ = parse_toc(donor, 60)
    _, _, target_names, _ = parse_toc(target, 60)
    source_section = next(
        target[offset : offset + size]
        for offset, size, kind in sections(target)
        if kind == 0xCCCC2400 and target_names[struct.unpack_from("<I", target, offset + 8)[0] - 1] == "BIN_bgdata"
    )
    header = re.match(rb"takaCreateBackGround\|1\.00\|(\d+)\|", source_section[12:])
    if header is None:
        raise ValueError("NA2 stage data header changed")
    count = int(header.group(1))
    triples_offset = 12 + header.end()
    string_offset = triples_offset + count * 6 + 2
    strings = source_section[string_offset:].split(b"|")[:count]
    records = [
        (*struct.unpack_from("<hhh", source_section, triples_offset + index * 6), strings[index].decode("ascii"))
        for index in range(count)
    ]

    essential = records[:8]
    if essential != [
        (4, 35, 2, "2"), (4, 36, 2, "2"),
        (4, 37, 2, "1"), (4, 38, 2, "1"),
        (4, 33, 2, "-1"), (4, 34, 2, "-1"),
        (1, 31, 0, "BLT_bg"), (2, 31, 2, "BLT_obj"),
    ]:
        raise ValueError("NA2 first-stage base records changed")
    required_nodes = (
        "DMY_line_010", "DMY_line_010_1", "DMY_line_020", "DMY_line_020_1",
        "DMY_linemin01", "DMY_linemax01", "DMY_linemin02", "DMY_linemax02",
        "DMY_b_cl_1_nor", "DMY_b_cl_1_nor_1", "DMY_f_cl_1_nor",
        "DMY_f_cl_1_nor_1",
    )
    missing = set(required_nodes) - set(donor_names)
    if missing:
        raise ValueError(f"donor missing line nodes: {sorted(missing)}")
    if {"BLT_bg", "BLT_obj"} - set(donor_names):
        raise ValueError("donor missing collision resources")

    static_models = [
        name for name in dict.fromkeys(donor_names)
        if re.fullmatch(r"OBJ_bac_\d{3}_(?:\d{2})?", name)
        or re.fullmatch(r"OBJ_s0bobj\d{2}", name)
        or re.fullmatch(r"OBJ_s0bbs00[ab]", name)
        or re.fullmatch(r"OBJ_s0bbac25[ab]", name)
        or name == "OBJ_s0briv01"
    ]
    static = [
        (1, 0, 1, f"{name},0,1,1") if name.startswith("OBJ_bac_")
        else (2, 0, 2, f"{name},0,1,1")
        for name in static_models
    ]
    models = {}
    for offset, _, kind in sections(donor):
        if kind == 0xCCCC0100:
            object_id = struct.unpack_from("<I", donor, offset + 8)[0]
            models.setdefault(donor_names[object_id - 1], []).append(object_id)
    invalid = [name for name in static_models if len(models.get(name, ())) != 1]
    if invalid:
        raise ValueError(f"donor static models do not resolve uniquely: {invalid}")
    records = essential + static
    data = (
        f"takaCreateBackGround|1.00|{len(records)}|".encode("ascii")
        + b"".join(struct.pack("<hhh", *record[:3]) for record in records)
        + b"||"
        + b"".join(record[3].encode("ascii") + b"|" for record in records)
    )
    body = struct.pack("<I", len(donor_names) + 1) + data
    body += b"\0" * (-len(body) % 4)
    return struct.pack("<II", 0xCCCC2400, len(body) // 4) + body


def add_bgdata(donor: bytes, section: bytes) -> bytes:
    toc_start = 60
    toc_total, _, names, _ = parse_toc(donor, toc_start)
    if "BIN_bgdata" in names:
        raise ValueError("NUN3 donor already has BIN_bgdata")
    toc = bytearray(donor[toc_start : toc_start + toc_total])
    object_count = struct.unpack_from("<I", toc, 12)[0]
    entry = b"BIN_bgdata" + b"\0" * (30 - len("BIN_bgdata")) + b"\0\0"
    toc[-8:-8] = entry
    struct.pack_into("<I", toc, 4, struct.unpack_from("<I", toc, 4)[0] + 8)
    struct.pack_into("<I", toc, 12, object_count + 1)
    original_end = list(sections(donor))[-2][0]
    converted = donor[:toc_start] + toc + donor[toc_start + toc_total : original_end] + section + donor[original_end:]
    _, _, converted_names, _ = parse_toc(converted, toc_start)
    if converted_names[-1] != "BIN_bgdata":
        raise ValueError("new CCS object not indexed")
    list(sections(converted))
    return converted


def checked_source(path: Path, expected_hash: str) -> bytes:
    source = path.read_bytes()
    digest = hashlib.sha256(source).hexdigest().upper()
    if digest != expected_hash:
        raise ValueError(f"source guard mismatch for {path}: {digest}")
    return gzip.decompress(source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--donor", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    donor = normalize_donor_names(checked_source(args.donor, DONOR_SHA256))
    target = checked_source(args.target, TARGET_SHA256)
    section = bgdata_section(donor, target)
    converted = add_bgdata(donor, section)
    compressed = gzip.compress(converted, compresslevel=9, mtime=0)
    args.output.write_bytes(compressed)
    print("donor", len(donor), hashlib.sha256(donor).hexdigest())
    print("converted", len(converted), hashlib.sha256(converted).hexdigest())
    print("compressed", len(compressed), args.output)
    print("bgdata section", len(section))


if __name__ == "__main__":
    main()
