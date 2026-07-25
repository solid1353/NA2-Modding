from __future__ import annotations

import argparse
import csv
import gzip
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.modules.texture_patcher import engine  # noqa: E402
from na2_patcher.project_paths import load_project_paths  # noqa: E402


MODE1_PATH = re.compile(r"3EYE/3[A-Z0-9]{3}3PCT\.CCS")
VICTORY_PREFIX = "UI-VICTORY-"
ENDDEMO_ID = "enddemo"
ENDDEMO_PATH = "3EYE/ENDDEMO.CCS"
HAKU_ID = "mode1_hak"
SHIKAMARU_ID = "mode1_skn"
HAKU_CROP = (
    "indexed_crop_transparent_top_left_128x64_nearest_palette_"
    "0-1-2-3-4-7-14"
)
SHIKAMARU_PALETTE = (
    "indexed_crop_transparent_top_left_256x128_nearest_palette_"
    "0-1-2-3-4-5-6-7-9-10-11-12-13-14"
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_rows(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def texture_by_object(
    entries: dict[str, engine.TextureEntry],
    object_name: str,
) -> engine.TextureEntry:
    matches = [
        entry
        for entry in entries.values()
        if any(section.object_name == object_name for section in entry.textures)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one {object_name} texture, found "
            + ", ".join(entry.name for entry in matches)
        )
    return matches[0]


def visual_differences_by_object(
    target_payload: bytes,
    donor_payload: bytes,
) -> set[str]:
    target_entries = engine.parse_ccs(target_payload)
    donor_entries = engine.parse_ccs(donor_payload)

    def index(
        entries: dict[str, engine.TextureEntry],
    ) -> dict[str, engine.TextureEntry]:
        result: dict[str, engine.TextureEntry] = {}
        for entry in entries.values():
            if len(entry.textures) != 1 or entry.textures[0].object_name is None:
                raise RuntimeError(f"Unsupported texture ownership for {entry.name}")
            object_name = entry.textures[0].object_name
            if object_name in result:
                raise RuntimeError(f"Duplicate texture object {object_name}")
            result[object_name] = entry
        return result

    target_by_object = index(target_entries)
    donor_by_object = index(donor_entries)
    if target_by_object.keys() != donor_by_object.keys():
        raise RuntimeError("Target and donor texture-object inventories differ")
    return {
        object_name
        for object_name in target_by_object
        if engine.decoded_rgba(target_payload, target_by_object[object_name])
        != engine.decoded_rgba(donor_payload, donor_by_object[object_name])
    }


def build_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[tuple[str, int]],
]:
    paths = load_project_paths(REPOSITORY)
    data_root = paths.path("features") / "localization" / "texture_patcher"
    container_path = data_root / "containers.tsv"
    mapping_path = data_root / "mappings.tsv"
    strategy_path = data_root / "strategies.tsv"
    containers = read_rows(container_path)
    mappings = [
        row
        for row in read_rows(mapping_path)
        if not row["mapping_id"].startswith(VICTORY_PREFIX)
    ]
    strategies = read_rows(strategy_path)

    container_by_id = {row["container_id"]: row for row in containers}
    strategy_by_id = {row["container_id"]: row for row in strategies}
    mode1 = [
        row
        for row in containers
        if row["container_id"].startswith("mode1_")
    ]
    if len(mode1) != 61:
        raise RuntimeError(f"Expected 61 mode1 containers, found {len(mode1)}")
    if any(MODE1_PATH.fullmatch(row["path"]) is None for row in mode1):
        raise RuntimeError("Unexpected mode1 container path")

    target_iso, donor_iso, _ = engine.source_members(
        paths.path("source_na2"),
        paths.path("source_nun5"),
    )
    enddemo_target = target_iso.read_file(target_iso.by_path[ENDDEMO_PATH])
    enddemo_donor = donor_iso.read_file(donor_iso.by_path[ENDDEMO_PATH])
    container_by_id[ENDDEMO_ID] = {
        "container_id": ENDDEMO_ID,
        "path": ENDDEMO_PATH,
        "target_sha256": engine.sha256(enddemo_target),
        "donor_sha256": engine.sha256(enddemo_donor),
    }

    new_mappings: list[dict[str, str]] = [
        {
            "mapping_id": f"{VICTORY_PREFIX}001",
            "enabled": "1",
            "container_id": ENDDEMO_ID,
            "target_texture": r"x\enddemo\tex\enddemo01.bmp",
            "donor_texture": r"x\enddemo\tex\enddemo01.bmp",
            "transform": "copy",
            "reason": (
                "Official English Winner emblem; preserve the unrelated NA2 "
                "background textures and CCS structure."
            ),
        }
    ]
    affected_payloads: dict[str, tuple[bytes, bytes]] = {
        ENDDEMO_ID: (
            gzip.decompress(enddemo_target),
            gzip.decompress(enddemo_donor),
        )
    }

    for number, row in enumerate(sorted(mode1, key=lambda item: item["container_id"]), 2):
        container_id = row["container_id"]
        path = row["path"].upper()
        target_raw = target_iso.read_file(target_iso.by_path[path])
        donor_raw = donor_iso.read_file(donor_iso.by_path[path])
        target_payload = gzip.decompress(target_raw)
        donor_payload = gzip.decompress(donor_raw)
        target_entries = engine.parse_ccs(target_payload)
        donor_entries = engine.parse_ccs(donor_payload)
        target_name = texture_by_object(target_entries, "TEX_name")
        donor_name = texture_by_object(donor_entries, "TEX_name")
        differences = visual_differences_by_object(target_payload, donor_payload)
        allowed = {
            "TEX_name",
            "TEX_mode1name1",
            "TEX_mode1name2",
            "TEX_mode1name3",
        }
        if "TEX_name" not in differences or not differences <= allowed:
            raise RuntimeError(
                f"{container_id}: unexpected decoded visual differences "
                + ", ".join(sorted(differences))
            )

        if container_id == HAKU_ID:
            transform = HAKU_CROP
            strategy = "mapped"
            strategy_reason = (
                "Import the official English awakening label and a transparent-"
                "canvas crop of the NUN5 Haku name. The complete donor misses "
                "the fixed member capacity by 348 bytes, so the cropped name "
                "uses the nearest seven colors from its own donor palette."
            )
            mapping_reason = (
                "Official English Haku victory-name artwork; discard only "
                "transparent canvas and use the nearest seven colors from the "
                "same donor palette to fit the fixed member."
            )
        elif container_id == SHIKAMARU_ID:
            transform = SHIKAMARU_PALETTE
            strategy = "mapped"
            strategy_reason = (
                "Import only the official English name and awakening label. "
                "The complete donor misses the fixed member capacity by 72 bytes, "
                "so the name maps its faintest antialias shade to the nearest "
                "remaining color from the same NUN5 palette."
            )
            mapping_reason = (
                "Official English Shikamaru victory-name artwork; retain the "
                "compatible NA2 CCS structure and omit only the faintest donor "
                "antialias shade to fit the fixed member."
            )
        else:
            transform = "whole"
            strategy = "whole"
            strategy_reason = (
                "Import the complete official English character resource; its "
                "only decoded visual changes are the victory name and ordinary-"
                "awakening label or labels."
            )
            mapping_reason = (
                "Official English victory character-name artwork imported with "
                "the complete NUN5 character resource."
            )

        new_mappings.append(
            {
                "mapping_id": f"{VICTORY_PREFIX}{number:03d}",
                "enabled": "1",
                "container_id": container_id,
                "target_texture": target_name.name,
                "donor_texture": donor_name.name,
                "transform": transform,
                "reason": mapping_reason,
            }
        )
        strategy_by_id[container_id]["strategy"] = strategy
        strategy_by_id[container_id]["reason"] = strategy_reason
        affected_payloads[container_id] = (target_payload, donor_payload)

    strategy_by_id[ENDDEMO_ID] = {
        "container_id": ENDDEMO_ID,
        "strategy": "mapped",
        "replacement_sha256": "0" * 64,
        "payload_sha256": "0" * 64,
        "reason": (
            "Import only the official English Winner emblem; preserve the "
            "unrelated NA2 background textures and target CCS structure."
        ),
    }
    mappings.extend(new_mappings)
    mappings_by_container: dict[str, list[engine.Mapping]] = defaultdict(list)
    for row in mappings:
        if row["enabled"] != "1":
            continue
        mappings_by_container[row["container_id"]].append(
            engine.Mapping(
                mapping_id=row["mapping_id"],
                container_id=row["container_id"],
                target_texture=row["target_texture"],
                donor_texture=row["donor_texture"],
                transform=row["transform"],
                reason=row["reason"],
            )
        )

    capacities: list[tuple[str, int]] = []
    for container_id, (target_payload, donor_payload) in affected_payloads.items():
        spec = container_by_id[container_id]
        target_raw = target_iso.read_file(target_iso.by_path[spec["path"].upper()])
        strategy_row = strategy_by_id[container_id]
        strategy = engine.Strategy(
            container_id=container_id,
            strategy=strategy_row["strategy"],
            replacement_sha256="0" * 64,
            payload_sha256="0" * 64,
            reason=strategy_row["reason"],
        )
        selected = mappings_by_container[container_id]
        target_entries = engine.parse_ccs(target_payload)
        donor_entries = engine.parse_ccs(donor_payload)
        for mapping in selected:
            engine.validate_mapping(
                mapping,
                target_payload,
                donor_payload,
                target_entries,
                donor_entries,
            )
        engine.validate_visual_coverage(
            strategy,
            selected,
            target_payload,
            donor_payload,
            target_entries,
            donor_entries,
        )
        payload = engine.expected_payload(
            strategy,
            target_payload,
            donor_payload,
            selected,
        )
        replacement, _stream_size, padding = engine.repack_gzip_exact(
            target_raw,
            payload,
        )
        strategy_row["replacement_sha256"] = engine.sha256(replacement)
        strategy_row["payload_sha256"] = engine.sha256(payload)
        capacities.append((container_id, padding))

    final_containers = sorted(container_by_id.values(), key=lambda row: row["container_id"])
    final_strategies = sorted(strategy_by_id.values(), key=lambda row: row["container_id"])
    if len(final_containers) != 96 or len(final_strategies) != 96:
        raise RuntimeError("Victory generation produced an unexpected container inventory")
    if len(mappings) != 210:
        raise RuntimeError(
            f"Victory generation expected 210 mappings, found {len(mappings)}"
        )
    return final_containers, mappings, final_strategies, sorted(capacities)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate canonical NUN5-backed Victory texture mappings."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite the canonical texture-patcher TSVs after validation.",
    )
    args = parser.parse_args()

    containers, mappings, strategies, capacities = build_rows()
    data_root = (
        load_project_paths(REPOSITORY).path("features")
        / "localization"
        / "texture_patcher"
    )
    if args.write:
        write_rows(data_root / "containers.tsv", engine.CONTAINER_FIELDS, containers)
        write_rows(data_root / "mappings.tsv", engine.MAPPING_FIELDS, mappings)
        write_rows(data_root / "strategies.tsv", engine.STRATEGY_FIELDS, strategies)
    print(
        f"Victory texture plan: {len(containers)} containers, "
        f"{len(mappings)} mappings, write={'yes' if args.write else 'no'}"
    )
    for container_id, padding in capacities:
        print(f"{container_id}\tpadding={padding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
