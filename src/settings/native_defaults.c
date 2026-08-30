typedef unsigned char u8;
typedef unsigned int u32;

#define MANAGER_MODE_OFFSET 0x0Cu
#define MANAGER_SIDE_OFFSET 0x18u
#define MANAGER_BATTLE_SETTINGS_OFFSET 0x9F4u

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
    u8 practice_linked_mode_value;
    u8 practice_linked_mode_mask;
    u8 reserved[2];
} NativeSettingsDefaults;

extern const NativeSettingsDefaults native_settings_defaults;

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
        if (native_settings_defaults.practice_linked_mode_mask != 0u) {
            ((NativeLinkedModeSet)NATIVE_LINKED_MODE_SET_ADDRESS)(
                *(volatile u32 *)((u8 *)manager + MANAGER_SIDE_OFFSET),
                native_settings_defaults.practice_linked_mode_value
            );
        }
    }
}

SETTINGS_DEFAULTS_SECTION(".text.settings_apply_native_defaults")
void settings_apply_native_defaults(void *manager, u32 key, u32 value)
{
    ((NativeManagerSet)NATIVE_MANAGER_SET_ADDRESS)(manager, key, value);
    settings_apply_selected_defaults(manager);
}
