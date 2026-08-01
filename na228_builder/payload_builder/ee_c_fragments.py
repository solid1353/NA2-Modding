#!/usr/bin/env python3
"""Compile PS2 EE C and extract relocatable runtime-injector fragments.

The compiler produces an ordinary ELF32 little-endian MIPS relocatable object.
This module converts its allocated sections and supported MIPS relocations into
the payload-builder model without assigning final resident addresses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)
from scripts.lib.project_paths import load_project_paths


EM_MIPS = 8
ET_REL = 1
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_NOBITS = 8
SHT_REL = 9
SHF_WRITE = 0x1
SHF_ALLOC = 0x2
SHF_EXECINSTR = 0x4
SHN_UNDEF = 0
SHN_ABS = 0xFFF1
STB_GLOBAL = 1
STB_WEAK = 2
R_MIPS_32 = 2
R_MIPS_26 = 4
R_MIPS_HI16 = 5
R_MIPS_LO16 = 6
SUPPORTED_RELOCATIONS = frozenset(
    {R_MIPS_32, R_MIPS_26, R_MIPS_HI16, R_MIPS_LO16}
)
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


@dataclass(frozen=True)
class SymbolReference:
    symbol: str
    addend: int = 0


@dataclass(frozen=True)
class ExtractedEeObject:
    fragments: tuple[PayloadFragment, ...]
    symbols: dict[str, SymbolReference]

    @property
    def fingerprint(self) -> str:
        digest = hashlib.sha256()
        for fragment in self.fragments:
            digest.update(fragment.symbol.encode("ascii"))
            digest.update(b"\0")
            digest.update(fragment.kind.encode("ascii"))
            digest.update(struct.pack("<I", fragment.alignment))
            digest.update(fragment.payload)
            for relocation in fragment.relocations:
                digest.update(struct.pack("<I", relocation.offset))
                digest.update(relocation.kind.encode("ascii"))
                digest.update(b"\0")
                digest.update(relocation.symbol.encode("ascii"))
                digest.update(b"\0")
                digest.update(struct.pack("<i", relocation.addend))
        for name, reference in sorted(self.symbols.items()):
            digest.update(name.encode("ascii"))
            digest.update(b"\0")
            digest.update(reference.symbol.encode("ascii"))
            digest.update(b"\0")
            digest.update(struct.pack("<i", reference.addend))
        return digest.hexdigest().upper()


@dataclass(frozen=True)
class _Section:
    index: int
    name: str
    type: int
    flags: int
    offset: int
    size: int
    link: int
    info: int
    alignment: int
    entry_size: int


@dataclass(frozen=True)
class _Symbol:
    name: str
    value: int
    size: int
    bind: int
    type: int
    section_index: int


@dataclass(frozen=True)
class _Relocation:
    offset: int
    type: int
    symbol_index: int


def default_toolchain_bin(repository_root: Path) -> Path:
    return load_project_paths(repository_root).path(
        "ps2_msys",
        "1.0",
        "local",
        "ps2dev",
        "ee",
        "bin",
    )


def compile_ee_c(
    source: Path,
    output_object: Path,
    *,
    toolchain_bin: Path,
    include_dirs: Sequence[Path] = (),
    defines: Mapping[str, str | None] | None = None,
) -> None:
    """Compile one C translation unit with the maintained deterministic flags."""

    source = source.resolve()
    output_object = output_object.resolve()
    compiler = toolchain_bin.resolve() / "ee-gcc.exe"
    if not compiler.is_file():
        raise FileNotFoundError(compiler)
    if not source.is_file():
        raise FileNotFoundError(source)
    output_object.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(compiler),
        "-w",
        "-D_EE",
        "-G0",
        "-O2",
        "-std=c99",
        "-ffreestanding",
        "-fno-builtin",
        "-fno-common",
    ]
    for path in include_dirs:
        command.extend(("-I", str(path.resolve())))
    for name, value in sorted((defines or {}).items()):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid C preprocessor name: {name!r}")
        command.append(f"-D{name}" if value is None else f"-D{name}={value}")
    command.extend(("-c", str(source), "-o", str(output_object)))
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    environment["SOURCE_DATE_EPOCH"] = "0"
    result = subprocess.run(
        command,
        cwd=source.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"EE C compilation failed ({result.returncode}): {detail}"
        )


def _slice(blob: bytes, offset: int, length: int, label: str) -> bytes:
    if offset < 0 or length < 0 or offset + length > len(blob):
        raise ValueError(f"{label} exceeds ELF object")
    return blob[offset : offset + length]


def _cstring(table: bytes, offset: int, label: str) -> str:
    if not 0 <= offset < len(table):
        raise ValueError(f"{label} string offset exceeds table")
    end = table.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"{label} is not null-terminated")
    return table[offset:end].decode("ascii")


def _fragment_suffix(section_name: str) -> str:
    suffix = re.sub(r"[^A-Za-z0-9]+", ".", section_name.lstrip(".")).strip(".")
    if not suffix:
        raise ValueError(f"Allocated ELF section has unusable name {section_name!r}")
    return suffix


def _section_kind(section: _Section) -> str:
    if section.flags & SHF_EXECINSTR:
        return "code"
    if section.flags & SHF_WRITE:
        return "data"
    return "rodata"


def _signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def _signed32(value: int) -> int:
    return value - 0x100000000 if value & 0x80000000 else value


def _read_instruction(payload: bytes, offset: int, label: str) -> int:
    return struct.unpack("<I", _slice(payload, offset, 4, label))[0]


def _encoded_relocation_addends(
    relocations: Sequence[_Relocation], payload: bytes, label: str
) -> list[int]:
    addends: list[int] = []
    for index, relocation in enumerate(relocations):
        word = _read_instruction(payload, relocation.offset, label)
        if relocation.type == R_MIPS_32:
            addends.append(_signed32(word))
            continue
        if relocation.type == R_MIPS_26:
            opcode = word >> 26
            if opcode not in {2, 3}:
                raise ValueError(
                    f"{label}: R_MIPS_26 at 0x{relocation.offset:X} "
                    "does not target a j/jal instruction"
                )
            addends.append((word & 0x03FFFFFF) << 2)
            continue
        immediate = word & 0xFFFF
        if relocation.type == R_MIPS_LO16:
            prior = next(
                (
                    candidate
                    for candidate in reversed(relocations[:index])
                    if candidate.type == R_MIPS_HI16
                    and candidate.symbol_index == relocation.symbol_index
                ),
                None,
            )
            if prior is None:
                addends.append(_signed16(immediate))
            else:
                high = _read_instruction(payload, prior.offset, label) & 0xFFFF
                addends.append((high << 16) + _signed16(immediate))
            continue
        if relocation.type == R_MIPS_HI16:
            following = next(
                (
                    candidate
                    for candidate in relocations[index + 1 :]
                    if candidate.type == R_MIPS_LO16
                    and candidate.symbol_index == relocation.symbol_index
                ),
                None,
            )
            if following is None:
                raise ValueError(
                    f"{label}: R_MIPS_HI16 at 0x{relocation.offset:X} "
                    "has no following matching R_MIPS_LO16"
                )
            low = (
                _read_instruction(payload, following.offset, label) & 0xFFFF
            )
            addends.append((immediate << 16) + _signed16(low))
            continue
        raise ValueError(
            f"{label}: unsupported MIPS relocation {relocation.type} "
            f"at 0x{relocation.offset:X}"
        )
    return addends


def extract_ee_object(
    object_path: Path,
    *,
    namespace: str,
    owner: str = "localization.runtime_injector",
    external_symbols: Mapping[str, SymbolReference] | None = None,
) -> ExtractedEeObject:
    """Extract allocated ELF sections and payload-builder relocations."""

    if not IDENTIFIER.fullmatch(namespace):
        raise ValueError(f"Invalid fragment namespace: {namespace!r}")
    if not IDENTIFIER.fullmatch(owner):
        raise ValueError(f"Invalid fragment owner: {owner!r}")
    external_symbols = dict(external_symbols or {})
    blob = object_path.read_bytes()
    if len(blob) < 52 or blob[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError(f"{object_path}: expected ELF32 little-endian object")
    header = struct.unpack_from("<HHIIIIIHHHHHH", blob, 16)
    if header[0] != ET_REL or header[1] != EM_MIPS:
        raise ValueError(f"{object_path}: expected relocatable MIPS ELF")
    section_offset = header[5]
    section_entry_size = header[10]
    section_count = header[11]
    section_name_index = header[12]
    if section_entry_size != 40 or not 0 < section_count < 0x10000:
        raise ValueError(f"{object_path}: unsupported section table")

    raw_sections: list[tuple[int, ...]] = []
    for index in range(section_count):
        offset = section_offset + index * section_entry_size
        raw_sections.append(
            struct.unpack("<IIIIIIIIII", _slice(blob, offset, 40, "section table"))
        )
    if not 0 <= section_name_index < section_count:
        raise ValueError(f"{object_path}: invalid section-name table index")
    name_header = raw_sections[section_name_index]
    name_table = _slice(blob, name_header[4], name_header[5], "section names")
    sections = [
        _Section(
            index=index,
            name=_cstring(name_table, values[0], f"section {index} name"),
            type=values[1],
            flags=values[2],
            offset=values[4],
            size=values[5],
            link=values[6],
            info=values[7],
            alignment=max(values[8], 1),
            entry_size=values[9],
        )
        for index, values in enumerate(raw_sections)
    ]

    allocated = [
        section
        for section in sections
        if section.flags & SHF_ALLOC
        and section.type in {SHT_PROGBITS, SHT_NOBITS}
        and section.size
    ]
    fragment_names: dict[int, str] = {}
    used_fragment_names: set[str] = set()
    for section in allocated:
        base = f"{namespace}.{_fragment_suffix(section.name)}"
        fragment_name = base
        suffix = 2
        while fragment_name in used_fragment_names:
            fragment_name = f"{base}.{suffix}"
            suffix += 1
        used_fragment_names.add(fragment_name)
        fragment_names[section.index] = fragment_name

    symbol_tables: dict[int, list[_Symbol]] = {}
    for section in sections:
        if section.type != SHT_SYMTAB:
            continue
        if section.entry_size != 16 or not 0 <= section.link < len(sections):
            raise ValueError(f"{object_path}: unsupported symbol table")
        strings_header = sections[section.link]
        strings = _slice(
            blob, strings_header.offset, strings_header.size, "symbol strings"
        )
        entries: list[_Symbol] = []
        for offset in range(
            section.offset, section.offset + section.size, section.entry_size
        ):
            name, value, size, info, _other, section_index = struct.unpack(
                "<IIIBBH", _slice(blob, offset, 16, "symbol table")
            )
            entries.append(
                _Symbol(
                    name=_cstring(strings, name, "symbol name"),
                    value=value,
                    size=size,
                    bind=info >> 4,
                    type=info & 0xF,
                    section_index=section_index,
                )
            )
        symbol_tables[section.index] = entries
    if not symbol_tables:
        raise ValueError(f"{object_path}: ELF object has no symbol table")

    exported_symbols: dict[str, SymbolReference] = {}
    for symbols in symbol_tables.values():
        for symbol in symbols:
            if (
                symbol.name
                and symbol.bind in {STB_GLOBAL, STB_WEAK}
                and symbol.section_index in fragment_names
            ):
                reference = SymbolReference(
                    fragment_names[symbol.section_index], symbol.value
                )
                previous = exported_symbols.setdefault(symbol.name, reference)
                if previous != reference:
                    raise ValueError(
                        f"{object_path}: conflicting exported symbol {symbol.name!r}"
                    )

    payloads: dict[int, bytearray] = {}
    relocation_lists: dict[int, list[PayloadRelocation]] = {
        section.index: [] for section in allocated
    }
    for section in allocated:
        if section.type == SHT_NOBITS:
            payloads[section.index] = bytearray(section.size)
        else:
            payloads[section.index] = bytearray(
                _slice(blob, section.offset, section.size, section.name)
            )

    for relocation_section in sections:
        if relocation_section.type != SHT_REL:
            continue
        if relocation_section.info not in fragment_names:
            continue
        if (
            relocation_section.entry_size != 8
            or relocation_section.link not in symbol_tables
        ):
            raise ValueError(f"{object_path}: unsupported relocation table")
        symbols = symbol_tables[relocation_section.link]
        entries: list[_Relocation] = []
        for offset in range(
            relocation_section.offset,
            relocation_section.offset + relocation_section.size,
            relocation_section.entry_size,
        ):
            relocation_offset, info = struct.unpack(
                "<II", _slice(blob, offset, 8, "relocation table")
            )
            entries.append(
                _Relocation(
                    offset=relocation_offset,
                    type=info & 0xFF,
                    symbol_index=info >> 8,
                )
            )
        unsupported = sorted(
            {entry.type for entry in entries} - SUPPORTED_RELOCATIONS
        )
        if unsupported:
            raise ValueError(
                f"{object_path}: unsupported MIPS relocations {unsupported}"
            )
        target_payload = payloads[relocation_section.info]
        addends = _encoded_relocation_addends(
            entries,
            target_payload,
            f"{object_path}:{sections[relocation_section.info].name}",
        )
        for entry, encoded_addend in zip(entries, addends):
            if not 0 <= entry.symbol_index < len(symbols):
                raise ValueError(f"{object_path}: invalid relocation symbol index")
            symbol = symbols[entry.symbol_index]
            if symbol.section_index in fragment_names:
                target = SymbolReference(
                    fragment_names[symbol.section_index], symbol.value
                )
            elif symbol.section_index == SHN_UNDEF and symbol.name:
                try:
                    target = external_symbols[symbol.name]
                except KeyError as exc:
                    raise ValueError(
                        f"{object_path}: unresolved external C symbol "
                        f"{symbol.name!r}"
                    ) from exc
            elif symbol.section_index == SHN_ABS:
                raise ValueError(
                    f"{object_path}: absolute C symbol {symbol.name!r} "
                    "cannot be emitted as a payload relocation"
                )
            else:
                raise ValueError(
                    f"{object_path}: relocation targets unsupported symbol "
                    f"{symbol.name!r}"
                )
            if not IDENTIFIER.fullmatch(target.symbol):
                raise ValueError(
                    f"Invalid payload symbol for {symbol.name!r}: {target.symbol!r}"
                )
            word = _read_instruction(
                target_payload,
                entry.offset,
                f"{object_path}:{sections[relocation_section.info].name}",
            )
            if entry.type == R_MIPS_26:
                kind = "j26" if word >> 26 == 2 else "jal26"
            else:
                kind = {
                    R_MIPS_32: "abs32",
                    R_MIPS_HI16: "hi16",
                    R_MIPS_LO16: "lo16",
                }[entry.type]
            relocation_lists[relocation_section.info].append(
                PayloadRelocation(
                    offset=entry.offset,
                    kind=kind,
                    symbol=target.symbol,
                    addend=target.addend + encoded_addend,
                )
            )

    fragments = tuple(
        PayloadFragment(
            owner=owner,
            symbol=fragment_names[section.index],
            kind=_section_kind(section),
            alignment=section.alignment,
            payload=bytes(payloads[section.index]),
            relocations=tuple(relocation_lists[section.index]),
        )
        for section in allocated
    )
    return ExtractedEeObject(fragments=fragments, symbols=exported_symbols)


def compile_and_extract(
    source: Path,
    output_object: Path,
    *,
    namespace: str,
    toolchain_bin: Path,
    owner: str = "localization.runtime_injector",
    include_dirs: Sequence[Path] = (),
    defines: Mapping[str, str | None] | None = None,
    external_symbols: Mapping[str, SymbolReference] | None = None,
) -> ExtractedEeObject:
    compile_ee_c(
        source,
        output_object,
        toolchain_bin=toolchain_bin,
        include_dirs=include_dirs,
        defines=defines,
    )
    return extract_ee_object(
        output_object,
        namespace=namespace,
        owner=owner,
        external_symbols=external_symbols,
    )


def manifest(extracted: ExtractedEeObject) -> dict[str, object]:
    return {
        "schema_version": 1,
        "fingerprint": extracted.fingerprint,
        "fragments": [
            {
                "symbol": fragment.symbol,
                "kind": fragment.kind,
                "alignment": fragment.alignment,
                "length": len(fragment.payload),
                "sha256": hashlib.sha256(fragment.payload).hexdigest().upper(),
                "relocations": [
                    {
                        "offset": f"0x{relocation.offset:X}",
                        "kind": relocation.kind,
                        "symbol": relocation.symbol,
                        "addend": relocation.addend,
                    }
                    for relocation in fragment.relocations
                ],
            }
            for fragment in extracted.fragments
        ],
        "symbols": {
            name: {
                "fragment": reference.symbol,
                "offset": f"0x{reference.addend:X}",
            }
            for name, reference in sorted(extracted.symbols.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--object", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    extracted = compile_and_extract(
        arguments.source,
        arguments.object,
        namespace=arguments.namespace,
        toolchain_bin=default_toolchain_bin(arguments.repository_root.resolve()),
    )
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(
        json.dumps(manifest(extracted), indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{len(extracted.fragments)} fragments, "
        f"{sum(len(item.relocations) for item in extracted.fragments)} relocations, "
        f"fingerprint {extracted.fingerprint}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
