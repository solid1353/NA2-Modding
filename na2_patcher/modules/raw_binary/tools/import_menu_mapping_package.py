#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from na2_patcher.project_paths import load_project_paths, resolve_alias

PROJECT_PATHS = load_project_paths(REPOSITORY_ROOT)


MAPPING_FIELDS = [
    "mapping_id", "component", "na2_path", "un5_path", "na2_sha256", "un5_sha256",
    "na2_file_offset_start", "na2_file_offset_end_exclusive",
    "un5_file_offset_start", "un5_file_offset_end_exclusive",
    "na2_virtual_address_start", "na2_virtual_address_end_exclusive",
    "un5_virtual_address_start", "un5_virtual_address_end_exclusive",
    "na2_function_or_range", "un5_function_or_range", "semantic_role",
    "likely_ui_location", "matching_evidence", "na2_instruction_or_sequence",
    "un5_equivalent_instruction_or_sequence", "na2_expected_bytes",
    "proposed_replacement_bytes_if_justified",
    "relevant_surrounding_instructions_and_delay_slot", "dependencies_on_other_edits",
    "confidence", "ambiguity_and_competing_matches", "safety_classification",
    "relocation_risks", "approval_state",
]
CANDIDATE_FIELDS = [
    "candidate_id", "mapping_id", "component", "na2_path", "un5_path",
    "na2_sha256", "un5_sha256", "na2_file_offset", "un5_file_offset",
    "na2_virtual_address", "un5_virtual_address", "semantic_role",
    "likely_ui_location", "na2_instruction", "un5_equivalent_instruction",
    "na2_expected_bytes", "proposed_replacement_bytes", "na2_preceding_instructions",
    "na2_branch_or_jump", "na2_delay_slot", "na2_following_instructions",
    "un5_surrounding_instructions", "dependencies", "confidence",
    "ambiguity_and_competing_matches", "safety_classification", "relocation_risks",
    "approval_state",
]

MANIFEST_FIELDS = ["schema_version", "package_id", "package_version", "game", "description", "evidence_path"]
TARGET_FIELDS = ["target_id", "root_id", "role", "path", "expected_size", "expected_sha256"]
PATCH_FIELDS = ["patch_id", "default_enabled", "status", "confidence", "name", "description", "source_mapping_id", "runtime_classification", "review_notes"]
RELATION_FIELDS = ["patch_id", "relation", "related_patch_id"]
EDIT_FIELDS = [
    "edit_id", "patch_id", "order", "destination_target_id", "destination_offset",
    "operation", "length", "expected_hex", "expected_sha256", "replacement_hex",
    "source_target_id", "source_offset", "source_expected_hex",
    "source_expected_sha256", "blob_path", "blob_offset", "blob_sha256", "fill_hex",
    "reason",
]


def repository_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be repository-relative")
    return path


def read_archive_tsv(archive: zipfile.ZipFile, name: str, fields: list[str]) -> list[dict[str, str]]:
    try:
        text = archive.read(name).decode("utf-8-sig")
    except KeyError as exc:
        raise ValueError(f"Archive is missing {name}") from exc
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if reader.fieldnames != fields:
        raise ValueError(f"Unexpected columns in {name}")
    rows = [{key: value.strip() for key, value in row.items()} for row in reader if any(value.strip() for value in row.values())]
    return rows


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def logical_parts(value: str) -> tuple[str, str]:
    path = PurePosixPath(value.replace("\\", "/"))
    if len(path.parts) < 2 or path.parts[0] not in {"NA2", "UN5"}:
        raise ValueError(f"Unsupported logical path: {value}")
    return path.parts[0].lower(), PurePosixPath(*path.parts[1:]).as_posix()


def main() -> int:
    project_paths = PROJECT_PATHS
    parser = argparse.ArgumentParser(description="Normalize GPT menu mapping TSVs into raw patcher schema v1.")
    parser.add_argument("--archive", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", action="append")
    args = parser.parse_args()

    archive_path = project_paths.repository / repository_relative(args.archive, "--archive")
    output = project_paths.repository / repository_relative(args.output, "--output")
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    roots: dict[str, Path] = {
        "na2": project_paths.path("source", "NA2"),
        "un5": project_paths.path("source", "UN5"),
    }
    for binding in args.root or []:
        root_id, separator, value = binding.partition("=")
        if not separator or not re.fullmatch(r"[a-z][a-z0-9_-]*", root_id):
            raise ValueError(f"Invalid root binding: {binding}")
        if value.startswith("@"):
            roots[root_id] = resolve_alias(value, project_paths)
        else:
            roots[root_id] = project_paths.repository / repository_relative(
                value, f"root {root_id}"
            )

    with zipfile.ZipFile(archive_path) as archive:
        mappings = read_archive_tsv(archive, "handler_mappings.tsv", MAPPING_FIELDS)
        candidates = read_archive_tsv(archive, "patch_candidates.tsv", CANDIDATE_FIELDS)

    mapping_by_id = {row["mapping_id"]: row for row in mappings}
    if len(mapping_by_id) != len(mappings):
        raise ValueError("Duplicate mapping IDs")
    candidate_ids = {row["candidate_id"] for row in candidates}
    if len(candidate_ids) != len(candidates):
        raise ValueError("Duplicate candidate IDs")

    target_descriptions: dict[tuple[str, str], dict[str, str]] = {}
    for candidate in candidates:
        if candidate["mapping_id"] not in mapping_by_id:
            raise ValueError(f"Unknown mapping ID: {candidate['mapping_id']}")
        for side, role in (("na2", "destination"), ("un5", "source")):
            root_id, path = logical_parts(candidate[f"{side}_path"])
            component = candidate["component"].lower()
            target_id = f"{root_id}_{component}"
            key = (root_id, path)
            description = {
                "target_id": target_id,
                "root_id": root_id,
                "role": role,
                "path": path,
                "expected_sha256": candidate[f"{side}_sha256"].upper(),
            }
            previous = target_descriptions.get(key)
            if previous and previous != description:
                raise ValueError(f"Inconsistent target description for {root_id}/{path}")
            target_descriptions[key] = description

    targets = []
    target_id_by_logical: dict[str, str] = {}
    for (root_id, path), description in sorted(target_descriptions.items()):
        if root_id not in roots:
            raise ValueError(f"No root binding for {root_id}")
        file_path = roots[root_id] / Path(path)
        if not file_path.is_file():
            raise ValueError(f"Missing target file: {root_id}/{path}")
        actual_hash = file_hash(file_path)
        if actual_hash != description["expected_sha256"]:
            raise ValueError(f"Hash mismatch for {root_id}/{path}")
        targets.append({**description, "expected_size": file_path.stat().st_size})
        target_id_by_logical[f"{root_id.upper()}/{path}"] = description["target_id"]

    candidates_by_mapping: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        candidates_by_mapping[candidate["mapping_id"]].append(candidate)

    patches = []
    edits = []
    for mapping_id in sorted(candidates_by_mapping):
        mapping = mapping_by_id[mapping_id]
        group = sorted(candidates_by_mapping[mapping_id], key=lambda row: int(row["na2_file_offset"], 0))
        dependency_notes = sorted({row["dependencies"] for row in group if row["dependencies"]})
        notes = [mapping["ambiguity_and_competing_matches"]]
        notes.extend(dependency_notes)
        patches.append(
            {
                "patch_id": mapping_id,
                "default_enabled": 0,
                "status": "pending",
                "confidence": mapping["confidence"],
                "name": mapping["semantic_role"],
                "description": mapping["likely_ui_location"],
                "source_mapping_id": mapping_id,
                "runtime_classification": "",
                "review_notes": " | ".join(note for note in notes if note),
            }
        )
        for order, candidate in enumerate(group, 10):
            na2_root, na2_path = logical_parts(candidate["na2_path"])
            un5_root, un5_path = logical_parts(candidate["un5_path"])
            old_hex = candidate["na2_expected_bytes"].upper()
            new_hex = candidate["proposed_replacement_bytes"].upper()
            if len(old_hex) != 8 or len(new_hex) != 8:
                raise ValueError(f"Candidate is not one 4-byte instruction: {candidate['candidate_id']}")
            edits.append(
                {
                    "edit_id": candidate["candidate_id"],
                    "patch_id": mapping_id,
                    "order": order,
                    "destination_target_id": target_id_by_logical[f"{na2_root.upper()}/{na2_path}"],
                    "destination_offset": candidate["na2_file_offset"],
                    "operation": "copy",
                    "length": 4,
                    "expected_hex": old_hex,
                    "expected_sha256": "",
                    "replacement_hex": "",
                    "source_target_id": target_id_by_logical[f"{un5_root.upper()}/{un5_path}"],
                    "source_offset": candidate["un5_file_offset"],
                    "source_expected_hex": new_hex,
                    "source_expected_sha256": "",
                    "blob_path": "",
                    "blob_offset": "",
                    "blob_sha256": "",
                    "fill_hex": "",
                    "reason": candidate["semantic_role"],
                }
            )

    write_tsv(
        output / "manifest.tsv",
        MANIFEST_FIELDS,
        [{
            "schema_version": 1,
            "package_id": "menu_input_candidates_20260716",
            "package_version": "1",
            "game": "NA2",
            "description": "Disabled UN5-to-NA2 menu-input candidates pending review and runtime classification.",
            "evidence_path": archive_path.as_posix(),
        }],
    )
    write_tsv(output / "targets.tsv", TARGET_FIELDS, targets)
    write_tsv(output / "patches.tsv", PATCH_FIELDS, patches)
    write_tsv(output / "relations.tsv", RELATION_FIELDS, [])
    write_tsv(output / "edits.tsv", EDIT_FIELDS, edits)
    print(f"Imported {len(patches)} atomic patches and {len(edits)} edits into {output.as_posix()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
