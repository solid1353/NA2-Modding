"""Small synthetic fixtures shared by builder unit tests."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from na228_builder.infrastructure.modules.payload_builder.builder import ResidentPayloadConfig
from na228_builder.patches.settings.ingame.battle_mechanics.items.items_settings import FIELD_ITEMS


def test_features() -> dict[str, object]:
    """A complete test input independent of the user's base configuration."""
    return {
        "localization": "en",
        "general": {
            "new_controls": True,
            "music_override": True,
            "practice_stage_select": True,
            "stage_selection_persistence": True,
            "battle_results_rematch": True,
            "unlock_all": {"demon_wind_bomb": True},
            "mode_availability": {"remove_adventure": True, "remove_shop": True},
        },
        "startup": {"faster_loading": True, "loading_screen": True},
        "memory_card": {
            "auto_loading": True,
            "dialogs_rework": True,
            "skip_initial_check": True,
            "extended_save_data": True,
        },
        "rendering": {"native_16_9_horizontal_scale": False},
        "menu_composition": {
            "mod_settings": {
                "battle_mechanics": True,
                "character_selection": True,
                "battle_settings": True,
                "practice_settings": True,
                "control_settings": True,
            },
            "battle_settings": {"battle_mechanics": True},
            "practice_settings": {"battle_mechanics": True},
        },
        "default_settings": {
            "mod_settings": {
                "character_selection": {
                    "support_selection": "none",
                    "character_balance": "overrides",
                    "balance_overlay": "on",
                },
                "simple_display": "off",
            },
            "battle_mechanics": {
                "chakra": "normal",
                "ultimate_jutsu": "no_hud",
                "shadowblur": "off",
                "extra_hit": "off",
                "sub_active_frames": 5,
                "xdash_chakra_cost": 10,
                "support": "off",
                "substitution": {
                    "value": "gauge",
                    "chakra": {"minimum_chakra": "match_cost"},
                    "gauge": {
                        "recovery_delay_seconds": 14.0,
                        "refill_seconds_per_stock": 1.0,
                        "damage_recovery": "on",
                        "damage_percent_for_full_refill": 125,
                    },
                },
                "items": {
                    "value": "custom",
                    "custom": {
                        "availability": "normal",
                        **{key: True for _code, key, _label in FIELD_ITEMS},
                    },
                },
            },
            "battle_settings": {"time": 99, "difficulty": "normal", "handicap": 5},
            "practice_settings": {
                "opponent_settings": {
                    "status": "manual",
                    "strength": "normal",
                    "attack": "no",
                    "guard": "no",
                    "move": "stay",
                    "substitution_jutsu": "normal",
                    "linked_attack": "dont_use",
                    "extra_hit_counter": "normal",
                },
                "health": "normal",
                "commands": "off",
                "damage": "on",
            },
        },
    }


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
