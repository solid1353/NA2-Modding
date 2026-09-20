typedef unsigned char u8;
typedef unsigned int u32;

#define MANAGER_MODE_OFFSET 0x0Cu
#define MANAGER_SIDE_OFFSET 0x18u
#define MANAGER_BATTLE_SETTINGS_OFFSET 0x9F4u
#define MANAGER_POINTER_ADDRESS 0x00607600u

#define SAVE_NATIVE_BATTLE 0x100u
#define SAVE_NATIVE_PRACTICE 0x200u
#define SAVE_NATIVE_SCOPE_MASK 0xF00u
#define SAVE_NATIVE_ROW_MASK 0x0FFu

#define NATIVE_MANAGER_SET_ADDRESS 0x001F59F0u
#define NATIVE_LINKED_MODE_SET_ADDRESS 0x00882670u

#define SETTINGS_DEFAULTS_SECTION(name) \
    __attribute__((section(name), used))

typedef void (*NativeManagerSet)(void *manager, u32 key, u32 value);
typedef void (*NativeLinkedModeSet)(u32 side, u32 value);

typedef struct NativeSettingsDefaults {
    u8 battle_values[12];
    u8 battle_masks[12];
    u8 practice_values[12];
    u8 practice_masks[12];
} NativeSettingsDefaults;

extern NativeSettingsDefaults native_settings_defaults;

static void settings_apply_default_block(
    u8 *settings,
    const u8 *values,
    const u8 *masks
) SETTINGS_DEFAULTS_SECTION(".text.settings_native_defaults_helpers");

static void settings_apply_default_block(
    u8 *settings,
    const u8 *values,
    const u8 *masks
)
{
    u32 index;

    for (index = 0u; index < 12u; ++index) {
        settings[index] = (u8)(
            (settings[index] & (u8)~masks[index]) |
            (values[index] & masks[index])
        );
    }
}

SETTINGS_DEFAULTS_SECTION(".text.settings_apply_selected_defaults")
void settings_apply_selected_defaults(void *manager)
{
    u32 mode;

    mode = *(volatile u32 *)((u8 *)manager + MANAGER_MODE_OFFSET);
    if (mode == 2u) {
        settings_apply_default_block(
            (u8 *)manager + MANAGER_BATTLE_SETTINGS_OFFSET,
            native_settings_defaults.battle_values,
            native_settings_defaults.battle_masks
        );
    } else if (mode == 3u) {
        settings_apply_default_block(
            (u8 *)manager + MANAGER_BATTLE_SETTINGS_OFFSET,
            native_settings_defaults.practice_values,
            native_settings_defaults.practice_masks
        );
        ((NativeLinkedModeSet)NATIVE_LINKED_MODE_SET_ADDRESS)(
            *(volatile u32 *)((u8 *)manager + MANAGER_SIDE_OFFSET),
            1u
        );
    }
}

SETTINGS_DEFAULTS_SECTION(".text.settings_apply_native_defaults")
void settings_apply_native_defaults(void *manager, u32 key, u32 value)
{
    ((NativeManagerSet)NATIVE_MANAGER_SET_ADDRESS)(manager, key, value);
    settings_apply_selected_defaults(manager);
}

static u8 *save_native_settings(u32 argument)
    SETTINGS_DEFAULTS_SECTION(".text.settings_native_defaults_helpers");

static u8 *save_native_settings(u32 argument)
{
    if ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_BATTLE) {
        return native_settings_defaults.battle_values;
    }
    if ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_PRACTICE) {
        return native_settings_defaults.practice_values;
    }
    return (u8 *)0;
}

static u32 save_native_read_field(u32 argument, const u8 *settings)
    SETTINGS_DEFAULTS_SECTION(".text.settings_native_defaults_helpers");

static u32 save_native_read_field(u32 argument, const u8 *settings)
{
    u32 row = argument & SAVE_NATIVE_ROW_MASK;

    if ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_BATTLE) {
        if (row == 0u) {
            u32 raw = settings[3];
            if (raw == 100u) {
                return 10u;
            }
            if (raw == 99u) {
                return 9u;
            }
            return raw / 10u - 1u;
        }
        if (row == 1u) {
            return settings[7];
        }
        if (row == 5u) {
            return settings[5];
        }
        return 0u;
    }
    if (row == 0u) {
        return settings[1];
    }
    if (row == 6u) {
        return settings[0] & 0x01u;
    }
    if (row == 7u) {
        return (settings[0] >> 4) & 0x01u;
    }
    if (row == 9u) {
        return settings[6];
    }
    if (row == 10u) {
        return settings[7];
    }
    if (row == 11u) {
        return settings[8];
    }
    if (row == 12u) {
        return settings[9];
    }
    if (row == 13u) {
        return settings[10];
    }
    if (row == 14u) {
        return (settings[0] >> 7) & 0x01u;
    }
    if (row == 15u) {
        return settings[11];
    }
    if (row == 16u) {
        return (settings[0] >> 6) & 0x01u;
    }
    return 0u;
}

static void save_native_write_field(u32 argument, u8 *settings, u32 value)
    SETTINGS_DEFAULTS_SECTION(".text.settings_native_defaults_helpers");

static void save_native_write_field(u32 argument, u8 *settings, u32 value)
{
    u32 row = argument & SAVE_NATIVE_ROW_MASK;

    if ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_BATTLE) {
        if (row == 0u) {
            settings[3] = (u8)(
                value < 9u ? (value + 1u) * 10u :
                value == 9u ? 99u : 100u
            );
        } else if (row == 1u) {
            settings[7] = (u8)value;
        } else if (row == 3u) {
            settings[2] = (u8)value;
        } else if (row == 5u) {
            settings[5] = (u8)value;
        }
        return;
    }
    if (row == 0u) {
        settings[1] = (u8)value;
    } else if (row == 6u) {
        settings[0] = (u8)((settings[0] & ~0x01u) | (value & 0x01u));
    } else if (row == 7u) {
        settings[0] = (u8)((settings[0] & ~0x10u) | ((value & 0x01u) << 4));
    } else if (row == 3u) {
        settings[2] = (u8)value;
    } else if (row == 9u) {
        settings[6] = (u8)value;
    } else if (row == 10u) {
        settings[7] = (u8)value;
    } else if (row == 11u) {
        settings[8] = (u8)value;
    } else if (row == 12u) {
        settings[9] = (u8)value;
    } else if (row == 13u) {
        settings[10] = (u8)value;
    } else if (row == 14u) {
        settings[0] = (u8)((settings[0] & ~0x80u) | ((value & 0x01u) << 7));
    } else if (row == 15u) {
        settings[11] = (u8)value;
    } else if (row == 16u) {
        settings[0] = (u8)((settings[0] & ~0x40u) | ((value & 0x01u) << 6));
    }
}

SETTINGS_DEFAULTS_SECTION(".text.save_native_setting_get")
u32 save_native_setting_get(u32 argument)
{
    u8 *settings = save_native_settings(argument);

    if (settings == (u8 *)0) {
        return 0u;
    }
    return save_native_read_field(argument, settings);
}

SETTINGS_DEFAULTS_SECTION(".text.save_native_setting_set")
void save_native_setting_set(u32 argument, u32 value)
{
    u8 *settings = save_native_settings(argument);
    u8 *manager;
    u32 mode;

    if (settings == (u8 *)0) {
        return;
    }
    save_native_write_field(argument, settings, value);
    manager = *(u8 **)MANAGER_POINTER_ADDRESS;
    if (manager == (u8 *)0) {
        return;
    }
    mode = *(volatile u32 *)(manager + MANAGER_MODE_OFFSET);
    if (
        ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_BATTLE && mode == 2u) ||
        ((argument & SAVE_NATIVE_SCOPE_MASK) == SAVE_NATIVE_PRACTICE && mode == 3u)
    ) {
        settings_apply_selected_defaults(manager);
    }
}
