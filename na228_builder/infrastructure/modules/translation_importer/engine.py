from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

from ...common import file_sha256, parse_int, read_tsv, sha256_hex
from ...orchestration.source_media import read_root_file

TARGET_SPECS = {
    "BTL": "PRG/BTL.BIN",
    "ETC": "PRG/ETC.BIN",
    "SLPS": "SLPS_258.37",
}
DONOR_IDS = frozenset(
    {"NUN5_BTL", "NUN5_ETC", "NUN5_TEXTENG", "NUN5_SLES"}
)
SOURCE_IDS = {
    "NA2_BTL": "BTL",
    "NA2_ETC": "ETC",
    "NA2_SLPS": "SLPS",
}
MAPPING_FIELDS = [
    "id", "enabled", "display_context", "source", "donor", "prefix",
    "mod_string", "display_basis", "source_ref", "reference_refs", "donor_ref",
    "mode", "capacity", "transform", "arguments",
    "parent_mapping_id",
]
EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
}
VALID_MODES = {"slot", "sequence"}
PLACEHOLDER_TEXT = frozenset({"unknown", "placeholder", "dummy", "test", "todo", "temp"})
IDENTIFIER_TEXT = re.compile(r"[a-z][a-z0-9_./-]{3,}\Z")
POSITIONAL_FORMAT_TOKEN = re.compile(r"%([1-9][0-9]*)")
PRINTF_FORMAT_TOKEN = re.compile(
    r"%(?!%)(?:[-+ #0]*)(?:[0-9]+|\*)?(?:\.(?:[0-9]+|\*))?"
    r"(?:hh|h|ll|l|j|z|t|L)?[diuoxXfFeEgGaAcspn]"
)
NUN5_QUOTED_SPAN = re.compile(r"@([^@\r\n]+)@")
NUN5_MARKUP_EQUIVALENTS = {
    "<iconOK>": "<iconCROSS>",
}
NUN5_FORMULA_SYMBOLS = {
    "*": "*",
    "=": "=",
    "·": ".",
    "%": "%",
}
VALID_TRANSFORMS = {
    "",
    "empty",
    "format_arg1",
    "format_args",
    "format_literal_arg1",
    "format_literal_through_arg1",
    "format_prefix_arg2",
    "format_suffix_arg2",
    "between_placeholders",
    "after_placeholder2",
    "split_br",
    "split_br_sequence",
    "join_br_parts",
    "insert_br_after_words",
    "append_space",
    "flatten_br_slice",
    "memory_card_space",
    "escape_literal_percent",
    "normalize_formula_symbol",
}
TARGET_RUNTIME_BASES = {
    "SLPS": 0x000FFF00,
    "BTL": 0x006B3F00,
    "ETC": 0x006B3F00,
}
NAMED_COLOR_TAG_EQUIVALENTS = {
    "<WHITE>": ("<WHITE>", "<colorFFFFFF>"),
    "<BLACK>": ("<BLACK>", "<color000000>"),
    "<RED>": ("<RED>",),
}
NATIVE_NA2_COLOR_TAGS = frozenset({"<BLACK>"})


@dataclass(frozen=True)
class TranslationImportPlan:
    import_rows: list[dict[str, str]]
    targets: dict[str, dict[str, object]]
    text_mappings: tuple[dict[str, object], ...]
    references: tuple["Reference", ...]
    resolved_texts: dict[str, str]
    resolved_sequences: dict[str, tuple[str, ...]]
    clean_targets: dict[str, bytes]
    summary: dict[str, object]


@dataclass(frozen=True)
class Reference:
    mapping_id: str
    target: str
    target_runtime_address: int
    resolution: str
    reference_binary: str
    reference_file_offsets: tuple[int, ...]
    parent_mapping_id: str | None
    parent_runtime_address: int | None

    @property
    def pointer(self) -> int:
        """The clean value of every pointer this reference redirects."""
        if self.parent_runtime_address is not None:
            return self.parent_runtime_address
        return self.target_runtime_address


@dataclass(frozen=True)
class AdaptedText:
    """A mapping's clean target text and its adapted cp1252 replacement."""

    target_text: str
    fragments: tuple[str, ...]
    encoded: tuple[bytes, ...]


class AdaptedTexts:
    """Adapt each mapping's resolved replacement to its clean target once.

    Reading the clean slot or sequence, checking the declared source, adapting
    donor markup, rejecting placeholder donors, and encoding happen on first use.
    """

    def __init__(self, plan: TranslationImportPlan) -> None:
        self._plan = plan
        self._mappings = {str(row["id"]): row for row in plan.text_mappings}
        self._adapted: dict[str, AdaptedText] = {}

    def __getitem__(self, mapping_id: str) -> AdaptedText:
        if mapping_id not in self._adapted:
            self._adapted[mapping_id] = self._adapt(self._mappings[mapping_id])
        return self._adapted[mapping_id]

    def _adapt(self, row: dict[str, object]) -> AdaptedText:
        mapping_id = str(row["id"])
        target = str(row["target"])
        offset = int(row["target_offset"])
        capacity = int(row["capacity"])
        label = f"{mapping_id} {target} 0x{offset:X}"
        clean = self._plan.clean_targets[target]
        if row["mode"] == "sequence":
            target_fragments, _ = read_target_sequence(clean, offset, capacity, label)
            target_text = "<NUL>".join(target_fragments)
            replacements = self._plan.resolved_sequences[mapping_id]
        else:
            target_text, _ = read_target_slot(clean, offset, capacity, label)
            replacements = (self._plan.resolved_texts[mapping_id],)
        validate_declared_source(str(row["source"]), target_text, label)
        fragments = tuple(
            adapt_source_markup(text, target_text, label) for text in replacements
        )
        if row["mode"] != "sequence":
            validate_semantic_replacement(fragments[0], target_text, label)
        return AdaptedText(
            target_text=target_text,
            fragments=fragments,
            encoded=tuple(fragment.encode("cp1252") for fragment in fragments),
        )


def read_clean_targets(source_root: Path) -> dict[str, bytes]:
    """Read every translation target from an NA2 extraction or original ISO."""
    return {
        target: read_root_file(source_root, path)
        for target, path in TARGET_SPECS.items()
    }


def normalize_path(value: str) -> str:
    return value.strip("/\\").replace("\\", "/").upper()


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def normalize_fullwidth_ascii(text: str) -> str:
    """Normalize fullwidth ASCII-compatible characters in translated output."""
    result: list[str] = []
    for character in text:
        codepoint = ord(character)
        if character == "\u3000":
            result.append(" ")
        elif 0xFF01 <= codepoint <= 0xFF5E:
            result.append(chr(codepoint - 0xFEE0))
        else:
            result.append(character)
    return "".join(result)



def parse_arguments(value: str, label: str) -> dict[str, str]:
    result = {}
    if not value.strip():
        return result
    for item in value.split(";"):
        if "=" not in item:
            raise ValueError(f"{label}: malformed argument {item!r}")
        key, val = item.split("=", 1)
        key = key.strip().lower()
        if not key or key in result:
            raise ValueError(f"{label}: duplicate/empty argument key")
        result[key] = val.strip()
    return result


def parse_display_basis(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split("|") if item.strip())


def count_display_bases(mappings: Sequence[dict[str, object]]) -> Counter[str]:
    return Counter(basis for row in mappings for basis in row["display_basis"])


def parse_ref(
    value: str,
    label: str,
    *,
    allowed: frozenset[str] | set[str],
) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Za-z0-9_]+)@(0[xX][0-9A-Fa-f]+|[0-9]+)", value.strip())
    if not match:
        raise ValueError(f"{label}: malformed reference {value!r}")
    source = match.group(1).upper()
    if source not in allowed:
        raise ValueError(f"{label}: unsupported reference source {source!r}")
    return source, int(match.group(2), 0)


def parse_source_ref(value: str, label: str) -> tuple[str, int]:
    source, offset = parse_ref(
        value,
        label,
        allowed=frozenset(SOURCE_IDS),
    )
    return SOURCE_IDS[source], offset


def parse_donor_ref(value: str, label: str) -> tuple[str, int]:
    return parse_ref(value, label, allowed=DONOR_IDS)


def parse_reference_refs(
    value: str,
    label: str,
) -> tuple[tuple[str, int], ...]:
    refs = tuple(
        parse_source_ref(item.strip(), label)
        for item in value.split(",")
        if item.strip()
    )
    if len(refs) != len(set(refs)):
        raise ValueError(f"{label}: duplicate pointer references")
    return refs


def read_rows(path: Path) -> list[dict[str, str]]:
    rows = read_tsv(path, MAPPING_FIELDS, verbatim={"source", "donor", "prefix"})
    ids = [row["id"] for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"{path.name} contains empty or duplicate ids")
    return rows


def references_from_mappings(
    mappings: Sequence[dict[str, object]],
) -> tuple[Reference, ...]:
    by_id = {str(row["id"]): row for row in mappings}
    references: list[Reference] = []
    for row in mappings:
        mapping_id = str(row["id"])
        reference_refs = tuple(row["reference_refs"])
        parent_id_value = str(row["parent_mapping_id"]) or None
        if not reference_refs and parent_id_value is None:
            continue
        label = f"{mapping_id} reference inventory"
        if not reference_refs:
            raise ValueError(f"{label}: parent mappings require reference_refs")
        parent_runtime_value: int | None = None
        if parent_id_value is not None:
            parent = by_id.get(parent_id_value)
            if parent is None:
                raise ValueError(f"{label}: missing parent {parent_id_value}")
            if parent["target"] != row["target"]:
                raise ValueError(f"{label}: parent target differs")
            parent_runtime_value = (
                TARGET_RUNTIME_BASES[str(row["target"])] + int(parent["target_offset"])
            )
        grouped: dict[str, list[int]] = defaultdict(list)
        for reference_binary, reference_offset in reference_refs:
            grouped[reference_binary].append(reference_offset)
        for reference_binary in sorted(grouped):
            references.append(
                Reference(
                    mapping_id=mapping_id,
                    target=str(row["target"]),
                    target_runtime_address=(
                        TARGET_RUNTIME_BASES[str(row["target"])]
                        + int(row["target_offset"])
                    ),
                    resolution=(
                        "parent_message"
                        if parent_id_value is not None
                        else "direct"
                    ),
                    reference_binary=reference_binary,
                    reference_file_offsets=tuple(grouped[reference_binary]),
                    parent_mapping_id=parent_id_value,
                    parent_runtime_address=parent_runtime_value,
                )
            )
    return tuple(references)


def validate_references(
    references: tuple[Reference, ...],
    clean_targets: dict[str, bytes],
) -> dict[str, int]:
    """Require every declared pointer to hold its string's clean address."""
    pointer_sites: set[tuple[str, int]] = set()
    for row in references:
        clean = clean_targets[row.reference_binary]
        for offset in row.reference_file_offsets:
            if offset + 4 > len(clean):
                raise ValueError(
                    f"{row.mapping_id}: pointer offset is outside "
                    f"{TARGET_SPECS[row.reference_binary]}"
                )
            actual = int.from_bytes(clean[offset:offset + 4], "little")
            if actual != row.pointer:
                raise ValueError(
                    f"{row.mapping_id}: pointer at 0x{offset:X} is 0x{actual:X}, "
                    f"expected 0x{row.pointer:X}"
                )
            pointer_sites.add((row.reference_binary, offset))
    counts = Counter(row.resolution for row in references)
    return {
        "rows": len(references),
        "direct": counts["direct"],
        "parent_message": counts["parent_message"],
        "pointer_sites": sum(len(row.reference_file_offsets) for row in references),
        "redirect_edits": len(pointer_sites),
    }


def resolve_replacement_text(
    row: dict[str, object],
    label: str,
    donor_by_ref: dict[str, str] | None = None,
) -> str:
    template = select_replacement_template(row)
    prefix = normalize_fullwidth_ascii(str(row.get("prefix", "")))
    transform = str(row.get("transform", ""))
    arguments = dict(row.get("arguments", {}))

    def argument(name: str) -> str:
        value = arguments.get(name, "")
        if not value:
            raise ValueError(f"{label}: transform {transform!r} requires {name}")
        if donor_by_ref is None:
            raise ValueError(f"{label}: donor reference lookup is unavailable")
        parse_donor_ref(value, label)
        try:
            return normalize_nun5_donor_markup(donor_by_ref[value])
        except KeyError as exc:
            raise ValueError(
                f"{label}: donor reference {value!r} has no canonical donor text"
            ) from exc

    if transform == "":
        resolved = template
    elif transform == "empty":
        resolved = ""
    elif transform == "format_arg1":
        if "%1" not in template:
            raise ValueError(f"{label}: template has no %1")
        resolved = template.replace("%1", argument("arg1"))
    elif transform == "format_args":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = (
            template.replace("%1", argument("arg1"))
            .replace("%2", argument("arg2"))
        )
    elif transform == "format_literal_arg1":
        if "%1" not in template:
            raise ValueError(f"{label}: template has no %1")
        resolved = template.replace(
            "%1",
            normalize_fullwidth_ascii(arguments.get("arg1", "")),
        )
    elif transform == "format_literal_through_arg1":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.split("%1", 1)[0] + normalize_fullwidth_ascii(
            arguments.get("arg1", "")
        )
    elif transform == "format_prefix_arg2":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.replace("%1", argument("arg1")).split("%2", 1)[0]
    elif transform in {"format_suffix_arg2", "after_placeholder2"}:
        if "%2" not in template:
            raise ValueError(f"{label}: template has no %2")
        resolved = template.split("%2", 1)[1]
    elif transform == "between_placeholders":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.split("%1", 1)[1].split("%2", 1)[0]
    elif transform == "split_br":
        part = parse_int(arguments.get("part", ""), label)
        pieces = template.split("<br>")
        if part >= len(pieces):
            raise ValueError(f"{label}: split part {part} is outside {len(pieces)} parts")
        resolved = pieces[part]
    elif transform == "join_br_parts":
        parts = [
            parse_int(value, label)
            for value in arguments.get("parts", "").split(",")
            if value.strip()
        ]
        if not parts:
            raise ValueError(f"{label}: join_br_parts has no parts")
        pieces = template.split("<br>")
        if max(parts) >= len(pieces):
            raise ValueError(f"{label}: join part is outside {len(pieces)} parts")
        resolved = arguments.get("join", "<br>").join(pieces[index] for index in parts)
    elif transform == "insert_br_after_words":
        count = parse_int(arguments.get("words", ""), label)
        words = template.split(" ")
        if any(not word for word in words):
            raise ValueError(
                f"{label}: donor text does not use single-space word boundaries"
            )
        if count <= 0 or count >= len(words):
            raise ValueError(
                f"{label}: word break {count} is outside 1..{len(words) - 1}"
            )
        resolved = " ".join(words[:count]) + "<br>" + " ".join(words[count:])
    elif transform == "append_space":
        resolved = template + " "
    elif transform == "flatten_br_slice":
        flattened = template.replace("<br>", " ")
        start = parse_int(arguments.get("start", ""), label)
        end = parse_int(arguments.get("end", ""), label)
        if start > end or end > len(flattened):
            raise ValueError(
                f"{label}: slice {start}:{end} is outside flattened text length "
                f"{len(flattened)}"
            )
        resolved = flattened[start:end]
    elif transform == "memory_card_space":
        flattened = " ".join(template.replace("<br>", " ").split())
        warning, separator, requirement = flattened.partition(". ")
        if not separator or not requirement:
            raise ValueError(f"{label}: memory-card donor requires two sentences")
        if arguments["part"] == "0":
            resolved = warning + "."
        else:
            source = normalize_fullwidth_ascii(str(row["source"]))
            source_sizes = re.findall(r"([0-9]+)\s*KB\b", source)
            donor_sizes = tuple(re.finditer(r"[0-9]+\s+KB\b", requirement))
            if len(source_sizes) != 1 or len(donor_sizes) != 1:
                raise ValueError(
                    f"{label}: memory-card requirement needs one source and donor KB value"
                )
            size = donor_sizes[0]
            resolved = (
                requirement[:size.start()] + source_sizes[0] + " KB"
                + requirement[size.end():]
            )
    elif transform == "escape_literal_percent":
        if (
            "%" not in template
            or "%%" in template
            or POSITIONAL_FORMAT_TOKEN.search(template)
            or PRINTF_FORMAT_TOKEN.search(template)
        ):
            raise ValueError(
                f"{label}: escape_literal_percent requires an unescaped "
                "literal percent"
            )
        resolved = template.replace("%", "%%")
    elif transform == "normalize_formula_symbol":
        match = re.fullmatch(r"( *)([*=·%])( *)", template)
        if match is None:
            raise ValueError(
                f"{label}: normalize_formula_symbol requires one supported "
                "formula symbol with optional spaces"
            )
        resolved = (
            match.group(1)
            + NUN5_FORMULA_SYMBOLS[match.group(2)]
            + match.group(3)
        )
    else:
        raise ValueError(f"{label}: unsupported transform {transform!r}")
    return normalize_fullwidth_ascii(prefix + resolved)


def normalize_nun5_donor_markup(text: str) -> str:
    """Resolve NUN5 markup and semantic tokens for NA2 consumers."""
    normalized = NUN5_QUOTED_SPAN.sub(
        lambda match: f'"{match.group(1)}"',
        text,
    )
    for source, replacement in NUN5_MARKUP_EQUIVALENTS.items():
        normalized = normalized.replace(source, replacement)
    return normalized


def select_replacement_template(row: dict[str, object]) -> str:
    return normalize_fullwidth_ascii(normalize_nun5_donor_markup(str(row["donor"])))


def read_target_sequence(data: bytes, offset: int, capacity: int, label: str) -> tuple[list[str], bytes]:
    if capacity <= 0 or offset < 0 or offset + capacity > len(data):
        raise ValueError(f"{label}: invalid target range 0x{offset:X}+{capacity}")
    region = data[offset:offset + capacity]
    fragments: list[str] = []
    cursor = 0
    while cursor < len(region):
        if all(value == 0 for value in region[cursor:]):
            break
        end = region.find(b"\x00", cursor)
        if end < 0:
            raise ValueError(f"{label}: target sequence has no terminating NUL")
        raw = region[cursor:end]
        if not raw:
            raise ValueError(f"{label}: target sequence contains an empty fragment before its zero-padded tail")
        try:
            fragments.append(raw.decode("cp932"))
        except UnicodeDecodeError:
            fragments.append("")
        cursor = end + 1
    if not fragments:
        raise ValueError(f"{label}: target sequence is empty")
    return fragments, region[:cursor]


def write_sequence(output: bytearray, offset: int, capacity: int, fragments: list[bytes]) -> None:
    payload = b"".join(fragment + b"\x00" for fragment in fragments) + b"\x00"
    if len(payload) > capacity:
        raise ValueError(f"replacement sequence is {len(payload)} bytes but block allows {capacity}")
    output[offset:offset + capacity] = payload + b"\x00" * (capacity - len(payload))


def read_target_slot(data: bytes, offset: int, capacity: int, label: str) -> tuple[str, bytes]:
    if capacity <= 0 or offset < 0 or offset + capacity > len(data):
        raise ValueError(f"{label}: invalid target range 0x{offset:X}+{capacity}")
    slot = data[offset:offset + capacity]
    end = slot.find(b"\x00")
    if end < 0:
        raise ValueError(f"{label}: target slot has no NUL terminator")
    raw = slot[:end]
    padding = slot[end + 1:]
    first_structural = next((index for index, value in enumerate(padding, end + 1) if value != 0), None)
    if first_structural is not None:
        raise ValueError(
            f"{label}: declared slot crosses nonzero data at 0x{offset + first_structural:X}; "
            "reduce capacity to the actual zero-padded string boundary"
        )
    try:
        text = raw.decode("cp932")
    except UnicodeDecodeError:
        text = ""
    return text, raw


def adapt_source_markup(source_text: str, target_text: str, label: str) -> str:
    adapted = source_text
    positional_tokens = tuple(POSITIONAL_FORMAT_TOKEN.finditer(adapted))
    if positional_tokens:
        printf_tokens = tuple(
            match.group(0) for match in PRINTF_FORMAT_TOKEN.finditer(target_text)
        )
        indexes = tuple(int(match.group(1)) for match in positional_tokens)
        if (
            sorted(set(indexes)) != list(range(1, len(printf_tokens) + 1))
            or len(indexes) != len(printf_tokens)
        ):
            raise ValueError(
                f"{label}: donor positional placeholders do not match "
                f"the target printf placeholders"
            )
        adapted = POSITIONAL_FORMAT_TOKEN.sub(
            lambda match: printf_tokens[int(match.group(1)) - 1],
            adapted,
        )
    for source_tag, candidates in NAMED_COLOR_TAG_EQUIVALENTS.items():
        if source_tag not in adapted:
            continue
        replacement = next((candidate for candidate in candidates if candidate in target_text), None)
        if replacement is None and source_tag in NATIVE_NA2_COLOR_TAGS:
            replacement = source_tag
        if replacement is None:
            raise ValueError(f"{label}: cannot verify an NA2 equivalent for {source_tag}")
        adapted = adapted.replace(source_tag, replacement)
    return adapted


def validate_declared_source(
    declared_text: str,
    actual_text: str,
    label: str,
) -> None:
    if declared_text != actual_text:
        raise ValueError(
            f"{label}: declared source text {declared_text!r} does not match "
            f"clean target text {actual_text!r}"
        )


def write_slot(output: bytearray, offset: int, capacity: int, replacement: bytes) -> None:
    if len(replacement) > capacity - 1:
        raise ValueError(f"replacement is {len(replacement)} bytes but slot allows {capacity - 1}")
    output[offset:offset + capacity] = replacement + b"\x00" + b"\x00" * (capacity - len(replacement) - 1)


def parse_mappings(
    rows: list[dict[str, str]],
    *,
    table_name: str = "mappings.tsv",
) -> dict[str, list[dict[str, object]]]:
    result = {"text": [], "inactive": [], "owned": []}
    for line, row in enumerate(rows, 2):
        label = f"{table_name} line {line} ({row['id']})"
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"{label}: enabled must be 0 or 1")
        if not row["display_context"]:
            raise ValueError(f"{label}: display_context is required")
        display_basis = parse_display_basis(row["display_basis"])
        mode = row["mode"].lower()
        if mode not in VALID_MODES:
            raise ValueError(f"{label}: unsupported mode {mode!r}")
        target, target_offset = parse_source_ref(row["source_ref"], label)
        transform = row["transform"].lower()
        if transform not in VALID_TRANSFORMS:
            raise ValueError(f"{label}: unsupported transform {transform!r}")
        arguments = parse_arguments(row["arguments"], label)
        if transform == "":
            if arguments:
                raise ValueError(f"{label}: arguments require a transform")
        elif transform == "split_br":
            if set(arguments) != {"part"}:
                raise ValueError(f"{label}: split_br requires only part=<index>")
            parse_int(arguments["part"], label)
        elif transform == "memory_card_space":
            if set(arguments) != {"part"} or arguments["part"] not in {"0", "1"}:
                raise ValueError(f"{label}: memory_card_space requires only part=0 or part=1")
        elif transform == "split_br_sequence":
            if set(arguments) != {"parts"}:
                raise ValueError(
                    f"{label}: split_br_sequence requires only parts=<indexes>"
                )
            parts = [
                parse_int(value, label)
                for value in arguments["parts"].split(",")
                if value.strip()
            ]
            if not parts:
                raise ValueError(f"{label}: split_br_sequence has no parts")
        elif transform == "empty":
            if arguments:
                raise ValueError(f"{label}: empty does not accept arguments")
        elif transform in {
            "format_literal_arg1",
            "format_literal_through_arg1",
        }:
            if set(arguments) != {"arg1"} or not arguments["arg1"]:
                raise ValueError(
                    f"{label}: {transform} requires only nonempty arg1=<text>"
                )
        elif transform in {"format_arg1", "format_prefix_arg2"}:
            if set(arguments) != {"arg1"}:
                raise ValueError(f"{label}: {transform} requires only arg1=<ref>")
            parse_donor_ref(arguments["arg1"], label)
        elif transform == "format_args":
            if set(arguments) != {"arg1", "arg2"}:
                raise ValueError(
                    f"{label}: format_args requires arg1=<ref>;arg2=<ref>"
                )
            parse_donor_ref(arguments["arg1"], label)
            parse_donor_ref(arguments["arg2"], label)
        elif transform in {
            "format_suffix_arg2",
            "between_placeholders",
            "after_placeholder2",
            "append_space",
            "escape_literal_percent",
            "normalize_formula_symbol",
        }:
            if arguments:
                raise ValueError(f"{label}: {transform} does not accept arguments")
        elif transform == "join_br_parts":
            if not set(arguments).issubset({"parts", "join"}) or "parts" not in arguments:
                raise ValueError(
                    f"{label}: join_br_parts requires parts=<indexes> and optional join"
                )
            for value in arguments["parts"].split(","):
                if value.strip():
                    parse_int(value, label)
        elif transform == "insert_br_after_words":
            if set(arguments) != {"words"}:
                raise ValueError(
                    f"{label}: insert_br_after_words requires only words=<count>"
                )
            parse_int(arguments["words"], label)
        elif transform == "flatten_br_slice":
            if set(arguments) != {"start", "end"}:
                raise ValueError(
                    f"{label}: flatten_br_slice requires start=<index>;end=<index>"
                )
            parse_int(arguments["start"], label)
            parse_int(arguments["end"], label)
        if mode == "sequence" and transform not in {
            "", "split_br_sequence", "memory_card_space", "join_br_parts",
        }:
            raise ValueError(
                f"{label}: unsupported sequence transform {transform!r}"
            )
        donor_ref = row["donor_ref"]
        if donor_ref:
            parse_donor_ref(donor_ref, label)
        reference_refs = parse_reference_refs(row["reference_refs"], label)
        parsed = {
            "id": row["id"],
            "display_context": row["display_context"],
            "display_basis": display_basis,
            "mode": mode,
            "target": target,
            "target_offset": target_offset,
            "source_ref": row["source_ref"],
            "capacity": parse_int(row["capacity"], label),
            "source": row["source"],
            "donor_ref": donor_ref,
            "donor": row["donor"],
            "prefix": row["prefix"],
            "transform": transform,
            "arguments": arguments,
            "reference_refs": reference_refs,
            "parent_mapping_id": row["parent_mapping_id"],
        }
        # A mod string owns its mapping's slot in every language; see mod_strings.md.
        if row["mod_string"]:
            result["owned"].append({**parsed, "mod_string": row["mod_string"]})
        else:
            result["inactive" if row["enabled"] == "0" else "text"].append(parsed)
    return result


def validate_structured_message_families(
    mappings: Sequence[dict[str, object]],
    *,
    table_name: str,
) -> None:
    """Require canonical line transforms to cover complete messages."""
    families: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in mappings:
        if row["transform"] not in {"split_br", "join_br_parts"}:
            continue
        donor_ref = str(row["donor_ref"])
        if not donor_ref:
            raise ValueError(
                f"{table_name} ({row['id']}): structured message transform "
                "requires donor_ref"
            )
        families[donor_ref].append(row)

    for donor_ref, rows in families.items():
        templates = {
            normalize_fullwidth_ascii(str(row["donor"]))
            for row in rows
        }
        if len(templates) != 1:
            mapping_ids = ", ".join(str(row["id"]) for row in rows)
            raise ValueError(
                f"{table_name}: structured message family {donor_ref} has "
                f"inconsistent templates across {mapping_ids}"
            )
        template = next(iter(templates))
        part_count = len(template.split("<br>"))
        owners: dict[int, list[str]] = defaultdict(list)
        for row in rows:
            mapping_id = str(row["id"])
            arguments = dict(row["arguments"])
            if row["transform"] == "split_br":
                indexes = [parse_int(arguments["part"], mapping_id)]
            else:
                indexes = [
                    parse_int(value, mapping_id)
                    for value in arguments["parts"].split(",")
                    if value.strip()
                ]
            for index in indexes:
                owners[index].append(mapping_id)

        required = set(range(part_count))
        actual = set(owners)
        missing = sorted(required - actual)
        outside = sorted(actual - required)
        duplicates = {
            index: mapping_ids
            for index, mapping_ids in sorted(owners.items())
            if len(mapping_ids) > 1
        }
        if missing or outside or duplicates:
            details: list[str] = []
            if missing:
                details.append("missing parts " + ", ".join(map(str, missing)))
            if outside:
                details.append(
                    "out-of-range parts " + ", ".join(map(str, outside))
                )
            if duplicates:
                details.append(
                    "duplicate parts "
                    + ", ".join(
                        f"{index} ({'/'.join(mapping_ids)})"
                        for index, mapping_ids in duplicates.items()
                    )
                )
            raise ValueError(
                f"{table_name}: incomplete structured message family "
                f"{donor_ref}: " + "; ".join(details)
            )


def validate_semantic_replacement(source_text: str, target_text: str, label: str) -> None:
    """Reject donor sentinels that would overwrite identifier-like NA2 data."""
    if (
        IDENTIFIER_TEXT.fullmatch(target_text)
        and source_text.strip().casefold() in PLACEHOLDER_TEXT
    ):
        raise ValueError(
            f"{label}: refuses placeholder donor text {source_text!r} for "
            f"identifier-like target {target_text!r}"
        )


def resolve_text_materializations(
    mappings: Sequence[dict[str, object]],
    donor_catalog: Sequence[dict[str, object]] | None = None,
) -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    """Resolve each mapping's replacement text or sequence fragments."""
    donor_by_ref: dict[str, str] = {}
    for row in donor_catalog if donor_catalog is not None else mappings:
        donor_ref = str(row["donor_ref"])
        donor = str(row["donor"])
        if not donor_ref:
            continue
        prior = donor_by_ref.setdefault(donor_ref, donor)
        if prior != donor:
            raise ValueError(
                f"{row['id']}: donor reference {donor_ref!r} has conflicting text"
            )
    resolved_texts: dict[str, str] = {}
    resolved_sequences: dict[str, tuple[str, ...]] = {}
    for row in mappings:
        mapping_id = str(row["id"])
        if row["mode"] == "sequence":
            template = select_replacement_template(row)
            prefix = normalize_fullwidth_ascii(str(row["prefix"]))
            if row["transform"] in {"memory_card_space", "join_br_parts"}:
                sequence = (resolve_replacement_text(row, mapping_id, donor_by_ref),)
            elif row["transform"] == "split_br_sequence":
                arguments = dict(row["arguments"])
                parts = [
                    parse_int(value, mapping_id)
                    for value in arguments["parts"].split(",")
                    if value.strip()
                ]
                pieces = template.split("<br>")
                if max(parts) >= len(pieces):
                    raise ValueError(
                        f"{mapping_id}: sequence part is outside {len(pieces)} parts"
                    )
                sequence = tuple(pieces[index] for index in parts)
                if sequence:
                    sequence = (prefix + sequence[0], *sequence[1:])
            else:
                sequence = tuple((prefix + template).split("<NUL>"))
            if not sequence or any(not value for value in sequence):
                raise ValueError(f"{mapping_id}: sequence contains an empty fragment")
            resolved_sequences[mapping_id] = sequence
        else:
            resolved = resolve_replacement_text(row, mapping_id, donor_by_ref)
            resolved_texts[mapping_id] = resolved
    return resolved_texts, resolved_sequences


def apply_text_mappings(
    mappings: Sequence[dict[str, object]],
    adapted: AdaptedTexts,
    clean_targets: dict[str, bytes],
    output_targets: dict[str, bytearray],
    excluded_mapping_ids: frozenset[str],
):
    annotations = []
    occupied: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    stats = Counter()
    display_contexts = Counter()
    for row in mappings:
        target = str(row["target"])
        mapping_id = str(row["id"])
        if mapping_id in excluded_mapping_ids:
            continue
        offset = int(row["target_offset"])
        capacity = int(row["capacity"])
        label = f"{row['id']} {target} 0x{offset:X}"
        for start, end, prior in occupied[target]:
            if offset < end and start < offset + capacity:
                raise ValueError(f"{label}: overlaps {prior} at 0x{start:X}-0x{end:X}")
        text = adapted[mapping_id]
        if row["mode"] == "sequence":
            write_sequence(output_targets[target], offset, capacity, list(text.encoded))
        else:
            write_slot(output_targets[target], offset, capacity, text.encoded[0])
        occupied[target].append((offset, offset + capacity, str(row["id"])))
        mapping_kind = "official donor translation"
        if str(row["prefix"]):
            mapping_kind = f"prefixed {mapping_kind}"
        annotations.append({"path": TARGET_SPECS[target], "start": offset, "end": offset + capacity,
                            "source_text": text.target_text,
                            "replacement_text": "<NUL>".join(text.fragments),
                            "mapping_id": str(row["id"]),
                            "reason": f"Apply {mapping_kind} for {row['id']}."})
        stats["mapped"] += 1
        if clean_targets[target][offset:offset + capacity] != bytes(output_targets[target][offset:offset + capacity]):
            stats["changed"] += 1
        display_contexts[str(row["display_context"])] += 1
    return annotations, dict(stats), dict(sorted(display_contexts.items()))


def diff_rows(path: str, clean: bytes, output: bytes, annotations) -> list[dict[str, str]]:
    if len(clean) != len(output):
        raise ValueError(f"Cannot emit fixed-offset patches for size-changed file: {path}")
    normalized = normalize_path(path)
    relevant = [item for item in annotations if normalize_path(str(item["path"])) == normalized]
    ranges = []
    start = None
    for index, (before, after) in enumerate(zip(clean, output)):
        if before != after and start is None:
            start = index
        elif before == after and start is not None:
            ranges.append((start, index)); start = None
    if start is not None:
        ranges.append((start, len(clean)))
    rows = []
    for range_start, range_end in ranges:
        boundaries = {range_start, range_end}
        for annotation in relevant:
            a, b = int(annotation["start"]), int(annotation["end"])
            if range_start < b and a < range_end:
                boundaries.add(max(range_start, a)); boundaries.add(min(range_end, b))
        ordered = sorted(boundaries)
        for a, b in zip(ordered, ordered[1:]):
            if a >= b:
                continue
            matching = [item for item in relevant if a < int(item["end"]) and int(item["start"]) < b]
            annotation = matching[-1] if matching else None
            rows.append({
                "path": path,
                "offset": f"0x{a:X}",
                "expected_hex": clean[a:b].hex().upper(),
                "replacement_hex": output[a:b].hex().upper(),
                "source_text": str(annotation["source_text"]) if annotation else "",
                "replacement_text": str(annotation["replacement_text"]) if annotation else "",
                "source_mapping_id": str(annotation["mapping_id"]) if annotation else "",
                "reason": str(annotation["reason"]) if annotation else "Imported translation string.",
            })
    return rows


def write_import_tsv(
    path: Path,
    rows: list[dict[str, str]],
) -> None:
    if not rows:
        raise ValueError("No translation imports were generated")
    fields = [
        "import_id", "group_id", "path", "offset", "expected_hex",
        "replacement_hex", "source_text", "replacement_text",
        "source_mapping_id", "reason",
    ]
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader(); writer.writerows(rows); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_translation_import_plan(
    *,
    source_root: Path,
    data_root: Path,
) -> TranslationImportPlan:
    """Load accepted canonical translations for every target without choosing placement."""
    clean_targets = read_clean_targets(source_root)
    actual_hashes = {
        f"NA2_{target}": sha1(data) for target, data in clean_targets.items()
    }
    for key, actual in actual_hashes.items():
        if actual != EXPECTED_SHA1[key]:
            raise ValueError(
                f"Unexpected {key} SHA-1: {actual}; expected {EXPECTED_SHA1[key]}"
            )

    mapping_path = data_root.resolve() / "mappings.tsv"
    rows_raw = read_rows(mapping_path)
    mappings = parse_mappings(rows_raw, table_name=mapping_path.name)
    validate_structured_message_families(
        mappings["text"],
        table_name=mapping_path.name,
    )
    references = references_from_mappings(mappings["text"])
    reference_counts = validate_references(references, clean_targets)
    resolved_texts, resolved_sequences = resolve_text_materializations(
        mappings["text"],
        donor_catalog=tuple(mappings["text"]) + tuple(mappings["inactive"]),
    )
    import_targets = {
        path: {
            "root_id": "na2",
            "path": path,
            "expected_size": len(clean_targets[target]),
            "expected_sha256": sha256_hex(clean_targets[target]),
        }
        for target, path in TARGET_SPECS.items()
    }

    active_by_mode = Counter(row["mode"] for row in mappings["text"])
    active_display_contexts = Counter(
        str(row["display_context"]) for row in mappings["text"]
    )
    active_display_bases = count_display_bases(mappings["text"])
    summary: dict[str, object] = {
        "mode": "canonical translation declarations",
        f"{mapping_path.stem}_sha256": file_sha256(mapping_path),
        "table_rows": len(rows_raw),
        "inactive_rows": len(mappings["inactive"]),
        "targets": list(TARGET_SPECS),
        "output": {
            "import_rows": 0,
            "text_mappings_applied": 0,
            "text_mappings_changed": 0,
        },
        "active_mapping_coverage": {
            "by_mode": dict(sorted(active_by_mode.items())),
            "by_display_context": dict(sorted(active_display_contexts.items())),
            "by_display_basis": dict(sorted(active_display_bases.items())),
        },
        "source_hashes": actual_hashes,
        "reference_inventory": reference_counts,
    }
    return TranslationImportPlan(
        import_rows=[],
        targets=import_targets,
        text_mappings=tuple(mappings["text"]),
        references=references,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
        clean_targets=clean_targets,
        summary=summary,
    )


def compile_inline_imports(
    plan: TranslationImportPlan,
    *,
    adapted: AdaptedTexts,
    excluded_mapping_ids: frozenset[str] = frozenset(),
) -> TranslationImportPlan:
    """Compile every mapping not assigned to external storage."""
    unknown = excluded_mapping_ids - {
        str(row["id"]) for row in plan.text_mappings
    }
    if unknown:
        raise ValueError(
            "unknown externally placed mapping ids: " + ", ".join(sorted(unknown))
        )
    output_targets = {
        target: bytearray(clean) for target, clean in plan.clean_targets.items()
    }
    annotations, text_stats, text_contexts = apply_text_mappings(
        plan.text_mappings,
        adapted,
        plan.clean_targets,
        output_targets,
        excluded_mapping_ids,
    )
    import_rows: list[dict[str, str]] = []
    translated_hashes: dict[str, dict[str, object]] = {}
    for target, clean in plan.clean_targets.items():
        path = TARGET_SPECS[target]
        output = bytes(output_targets[target])
        for row in diff_rows(path, clean, output, annotations):
            row["import_id"] = f"{target}-I{len(import_rows) + 1:04d}"
            row["group_id"] = target
            import_rows.append(row)
        translated_hashes[path] = {
            "source_sha1": sha1(clean),
            "translated_sha1": sha1(output),
            "size": len(output),
        }
    summary = dict(plan.summary)
    summary["output"] = {
        "import_rows": len(import_rows),
        "text_mappings_applied": text_stats.get("mapped", 0),
        "text_mappings_changed": text_stats.get("changed", 0),
        "external_mappings_omitted": len(excluded_mapping_ids),
    }
    coverage = dict(summary["active_mapping_coverage"])
    coverage["inline_by_display_context"] = text_contexts
    summary["active_mapping_coverage"] = coverage
    summary["translated_file_hashes"] = translated_hashes
    return replace(plan, import_rows=import_rows, summary=summary)
