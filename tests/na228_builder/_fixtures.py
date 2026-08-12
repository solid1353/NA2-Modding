"""Small synthetic fixtures shared by builder unit tests."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from na228_builder.payload_builder.builder import ResidentPayloadConfig


def resident_payload_config(
    *,
    reservation_end: int = 0x008F8000,
    maximum_end: int = 0x00900000,
) -> ResidentPayloadConfig:
    return ResidentPayloadConfig(
        output_path="PRG/TST.BIN",
        load_base=0x008F3D00,
        entry_offset=0x40,
        minimum_data_offset=0x100,
        maximum_end=maximum_end,
        reservation_end=reservation_end,
        loader_function=0x001BDA50,
        original_constructor_function=0x001B1230,
        hook_file_offset=0x1000,
        cave_file_offset=0x1200,
        cave_runtime_address=0x00200000,
        destination_table_file_offset=0x1400,
        old_memory_boundary=0x008ED080,
        development_injection_base=0x008F0000,
        development_injection_end=0x008F3D00,
    )


def write_resident_payload_config(
    path: Path,
    config: ResidentPayloadConfig,
    **overrides: int | str,
) -> None:
    values = asdict(config)
    values.update(overrides)
    lines = ["key\tvalue"]
    for key, value in values.items():
        rendered = value if isinstance(value, str) else f"0x{value:X}"
        lines.append(f"{key}\t{rendered}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
