#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import subprocess
from pathlib import Path


ARCHIVED_COMMIT = "14083adac9c24c533a33876a23596c6a92d301ec"
MAPPINGS_REPOSITORY_PATH = (
    "na2_patcher/features/localization/translation_importer/mappings.tsv"
)
REBUILD_WORK_PATH = (
    "work/String translation/artifacts/diagnostic-rebuild/rebuild.tsv"
)
REBUILD_FIELDS = [
    "id",
    "display_context",
    "source",
    "donor",
    "prefix",
    "replacement",
    "display_basis",
    "source_ref",
    "donor_ref",
    "mode",
    "capacity",
    "transform",
    "arguments",
    "reference_refs",
    "parent_mapping_id",
    "legacy_ids",
]
SECTION_CONTEXTS = {
    "battle": "Unconfirmed > Battle",
    "battle_dialogs": "Unconfirmed > Battle dialogs",
    "character_command_chart": "Unconfirmed > Character command chart",
    "character_select": "Unconfirmed > Character Select",
    "character_ultimate_jutsu": "Unconfirmed > Character Ultimate Jutsu",
    "collection": "Unconfirmed > Collection",
    "command_chart": "Unconfirmed > Command Chart",
    "menus_data": "Unconfirmed > Menus and data",
    "options": "Unconfirmed > Options",
    "practice_settings": "Unconfirmed > Practice Settings",
    "save_load": "Unconfirmed > Save or Load",
    "shop": "Unconfirmed > Shop",
    "system_ui": "Unconfirmed > System UI",
}
SOURCE_REF = re.compile(
    r"NA2_(BTL|ETC|SLPS)@(0[xX][0-9A-Fa-f]+|[0-9]+)\Z"
)
LEGACY_ID = re.compile(r"M([0-9]+)\Z")
REBUILD_ID = re.compile(r"T([1-9][0-9]*)\Z")
TARGET_ORDER = {"BTL": 0, "ETC": 1, "SLPS": 2}


def _read_tsv_text(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter="\t")
    return [
        {key: value or "" for key, value in row.items()}
        for row in reader
    ]


def _read_tsv(path: Path) -> list[dict[str, str]]:
    return _read_tsv_text(path.read_text(encoding="utf-8-sig"))


def _archived_rows(repository: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        [
            "git",
            "show",
            f"{ARCHIVED_COMMIT}:{MAPPINGS_REPOSITORY_PATH}",
        ],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return _read_tsv_text(result.stdout.decode("utf-8-sig"))


def _source_key(row: dict[str, str]) -> tuple[int, int]:
    match = SOURCE_REF.fullmatch(row["source_ref"])
    if match is None:
        raise ValueError(f"malformed source_ref: {row['source_ref']!r}")
    return TARGET_ORDER[match.group(1)], int(match.group(2), 0)


def _legacy_key(value: str) -> tuple[int, str]:
    match = LEGACY_ID.fullmatch(value)
    if match is None:
        raise ValueError(f"malformed legacy mapping id: {value!r}")
    return int(match.group(1)), value


def _rebuild_number(value: str) -> int:
    match = REBUILD_ID.fullmatch(value)
    if match is None:
        raise ValueError(f"malformed rebuild mapping id: {value!r}")
    return int(match.group(1))


def _diagnostic_size(row: dict[str, str], mapping_id: str) -> int:
    if row["mode"] == "slot":
        return len(mapping_id.encode("ascii")) + 1
    if row["mode"] != "sequence":
        raise ValueError(
            f"{row['source_ref']}: unsupported mode {row['mode']!r}"
        )
    fragments = row["source"].split("<NUL>")
    if len(fragments) < 2 or any(not fragment for fragment in fragments):
        raise ValueError(
            f"{row['source_ref']}: sequence source must contain nonempty "
            "<NUL>-separated fragments"
        )
    return (
        sum(
            len(f"{mapping_id}.{index}".encode("ascii")) + 1
            for index in range(1, len(fragments) + 1)
        )
        + 1
    )


def _validate_compatible(
    source_ref: str,
    rows: list[dict[str, str]],
) -> None:
    signatures = {
        (row["source"], row["mode"], row["capacity"])
        for row in rows
    }
    if len(signatures) != 1:
        raise ValueError(
            f"{source_ref}: legacy/current source declarations disagree"
        )


def _candidate_rows(
    archived: list[dict[str, str]],
    current: list[dict[str, str]],
) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    current_by_ref: dict[str, list[dict[str, str]]] = {}
    for row in archived + current:
        grouped.setdefault(row["source_ref"], []).append(row)
    for row in current:
        current_by_ref.setdefault(row["source_ref"], []).append(row)

    candidates: list[dict[str, str]] = []
    for source_ref, rows in grouped.items():
        _validate_compatible(source_ref, rows)
        representative = (
            current_by_ref[source_ref][0]
            if source_ref in current_by_ref
            else rows[0]
        )
        current_contexts = {
            row.get("display_context", "").strip()
            for row in current_by_ref.get(source_ref, [])
            if row.get("display_context", "").strip()
        }
        if len(current_contexts) > 1:
            raise ValueError(
                f"{source_ref}: current mappings disagree on display_context"
            )
        if current_contexts:
            display_context = next(iter(current_contexts))
        else:
            sections = {
                row.get("section", "").strip()
                for row in rows
                if row.get("section", "").strip()
            }
            if len(sections) != 1:
                raise ValueError(
                    f"{source_ref}: archived mappings disagree on section"
                )
            section = next(iter(sections))
            display_context = SECTION_CONTEXTS.get(
                section,
                f"Unconfirmed > {section.replace('_', ' ').title()}",
            )
        legacy_ids = sorted(
            {
                row["id"]
                for row in rows
                if LEGACY_ID.fullmatch(row["id"]) is not None
            },
            key=_legacy_key,
        )
        candidates.append(
            {
                "id": "",
                "display_context": display_context,
                "source": representative["source"],
                "donor": "",
                "prefix": "",
                "replacement": "",
                "display_basis": "",
                "source_ref": source_ref,
                "donor_ref": "",
                "mode": representative["mode"],
                "capacity": representative["capacity"],
                "transform": "",
                "arguments": "",
                "reference_refs": "",
                "parent_mapping_id": "",
                "legacy_ids": ",".join(legacy_ids),
            }
        )
    return candidates


def _validate_existing(rows: list[dict[str, str]]) -> None:
    expected_ids = [f"T{index}" for index in range(1, len(rows) + 1)]
    actual_ids = [row["id"] for row in rows]
    if actual_ids != expected_ids:
        raise ValueError(
            "rebuild IDs must be T1..T<count> in physical row order"
        )
    source_refs = [row["source_ref"] for row in rows]
    if len(source_refs) != len(set(source_refs)):
        raise ValueError("rebuild table contains duplicate source_ref values")
    for row in rows:
        if set(row) != set(REBUILD_FIELDS):
            raise ValueError("rebuild table has an unexpected schema")
        required = ("display_context", "source", "source_ref", "mode", "capacity")
        if any(not row[field] for field in required):
            raise ValueError(f"{row['id']}: rebuild row is incomplete")
        capacity = int(row["capacity"], 0)
        required_size = _diagnostic_size(row, row["id"])
        if required_size > capacity:
            raise ValueError(
                f"{row['id']}: diagnostic token requires {required_size} bytes "
                f"but {row['source_ref']} allows {capacity}"
            )


def synchronize(
    archived: list[dict[str, str]],
    current: list[dict[str, str]],
    existing: list[dict[str, str]],
) -> list[dict[str, str]]:
    candidates = _candidate_rows(archived, current)
    if existing:
        _validate_existing(existing)
    by_ref = {row["source_ref"]: dict(row) for row in existing}
    candidate_by_ref = {row["source_ref"]: row for row in candidates}

    for source_ref, existing_row in by_ref.items():
        candidate = candidate_by_ref.get(source_ref)
        if candidate is None:
            continue
        _validate_compatible(source_ref, [existing_row, candidate])
        legacy_ids = {
            value
            for value in existing_row["legacy_ids"].split(",")
            if value
        }
        legacy_ids.update(
            value
            for value in candidate["legacy_ids"].split(",")
            if value
        )
        existing_row["legacy_ids"] = ",".join(
            sorted(legacy_ids, key=_legacy_key)
        )

    missing = [
        row for row in candidates if row["source_ref"] not in by_ref
    ]
    if not existing:
        short_slots = [
            row for row in missing if int(row["capacity"], 0) <= 5
        ]
        ordinary_slots = [
            row for row in missing if int(row["capacity"], 0) > 5
        ]
        short_slots.sort(
            key=lambda row: (
                row["display_context"].casefold(),
                *_source_key(row),
            )
        )
        ordinary_slots.sort(
            key=lambda row: (
                row["display_context"].casefold(),
                *_source_key(row),
            )
        )
        missing = short_slots + ordinary_slots
    else:
        missing.sort(
            key=lambda row: (
                row["display_context"].casefold(),
                *_source_key(row),
            )
        )

    next_number = len(existing) + 1
    for row in missing:
        mapping_id = f"T{next_number}"
        row["id"] = mapping_id
        required_size = _diagnostic_size(row, mapping_id)
        capacity = int(row["capacity"], 0)
        if required_size > capacity:
            raise ValueError(
                f"{mapping_id}: diagnostic token requires {required_size} bytes "
                f"but {row['source_ref']} allows {capacity}; stable IDs cannot "
                "be silently renumbered"
            )
        by_ref[row["source_ref"]] = row
        next_number += 1

    result = sorted(
        by_ref.values(),
        key=lambda row: _rebuild_number(row["id"]),
    )
    _validate_existing(result)
    return result


def _serialize(rows: list[dict[str, str]]) -> bytes:
    text = io.StringIO(newline="")
    writer = csv.DictWriter(
        text,
        fieldnames=REBUILD_FIELDS,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + text.getvalue().encode("utf-8")


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize or synchronize the stable String translation rebuild "
            "candidate inventory."
        )
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the retained task-local rebuild table is not synchronized.",
    )
    args = parser.parse_args()

    repository = args.repository.resolve()
    current_path = repository / MAPPINGS_REPOSITORY_PATH
    rebuild_path = repository / REBUILD_WORK_PATH
    archived = _archived_rows(repository)
    current = _read_tsv(current_path)
    existing = _read_tsv(rebuild_path) if rebuild_path.is_file() else []
    rows = synchronize(archived, current, existing)
    serialized = _serialize(rows)

    if args.check:
        if not rebuild_path.is_file() or rebuild_path.read_bytes() != serialized:
            raise SystemExit(
                f"{REBUILD_WORK_PATH} is not synchronized"
            )
        print(f"Verified {len(rows)} stable rebuild candidates.")
        return 0

    _write_atomic(rebuild_path, serialized)
    print(f"Wrote {len(rows)} stable rebuild candidates to {rebuild_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
