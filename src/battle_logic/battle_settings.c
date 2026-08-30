/* Feature-aware Battle Settings row map over the native menu. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define BATTLE_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define BATTLE_SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define BATTLE_SETTINGS_MAX_ROWS 16u
#define BATTLE_SETTINGS_VISIBLE_ROWS 7u
#define BATTLE_SETTINGS_WINDOW_MARGIN_ROWS 2

#define MANAGER_POINTER_ADDRESS 0x00607600u
#define CONTROLLER_SELECTED_ROW_OFFSET 0x48u
#define CONTROLLER_EFFECTIVE_INPUT_OFFSET 0x64u

#define INPUT_PREVIOUS_ROW 0x1000u
#define INPUT_NEXT_ROW 0x4000u
#define INPUT_NEXT_VALUE 0x2000u
#define INPUT_PREVIOUS_VALUE 0x8000u

#define NATIVE_SNAPSHOT_ADDRESS 0x0087F870u
#define NATIVE_SOUND_ADDRESS 0x001D7E20u
#define NATIVE_PROFILE_FLAG_ADDRESS 0x001F7780u
#define NATIVE_WINDOW_UPDATE_ADDRESS 0x0037D9C0u
#define NATIVE_ROWS_DRAW_ADDRESS 0x008801E0u
#define NATIVE_CURSOR_DRAW_ADDRESS 0x008804F0u
#define NATIVE_BACKING_DRAW_ADDRESS 0x001BB790u
#define NATIVE_SPRITE_DRAW_ADDRESS 0x00190F40u

#define PROFILE_ULTIMATE_DIFFICULTY_SLOT 0x6Au

#define BACKING_RECORDS_POINTER_OFFSET 0xFCu
#define BACKING_RECORD_SIZE 0x10u
#define BACKING_RECORD_OBJECT_POINTER_OFFSET 0x00u
#define BACKING_RECORD_DRAW_FLAGS_OFFSET 0x0Au
#define BACKING_RECORD_DRAW_FLAG 0x04u
#define BACKING_HANDICAP_RECORD 0u
#define BACKING_LAST_ORDINARY_RECORD 5u
#define BACKING_OBJECT_ALPHA_OFFSET 0x88u
#define BACKING_OBJECT_WORLD_Y_OFFSET 0x38u
#define BACKING_OBJECT_LOCAL_Y_OFFSET 0x78u

#define ROW_FLAG_LABEL_SLOT 0x01u
#define ROW_FLAG_HELP_SLOT 0x02u
#define ROW_FLAG_VALUES_SLOT 0x04u
#define ROW_FLAG_CUSTOM_SUBSTITUTION 0x08u
#define ROW_FLAG_DIFFICULTY_LIMIT 0x10u
#define ROW_FLAG_TIME 0x20u
#define ROW_FLAG_HANDICAP 0x40u
#define ROW_FLAG_ULTIMATE_JUTSU 0x80u
#define ROW_FLAG_CUSTOM_ULTIMATE_JUTSU 0x100u
#define ROW_FLAG_CUSTOM_SHADOWBLUR 0x200u
#define ROW_FLAG_CUSTOM_EXTRA_HIT 0x400u
#define ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES 0x800u
#define ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST 0x1000u
#define ROW_FLAG_CUSTOM_SUPPORT 0x2000u

#define ULTIMATE_JUTSU_NATIVE_MODE_COUNT 6u
#define ULTIMATE_JUTSU_NATIVE_DEFAULT 2u
#define ULTIMATE_JUTSU_MODE_NO_HUD 7u

typedef void (*NativeControllerCall)(void *controller);
typedef void (*NativeSound)(u32 sound_id);
typedef s32 (*NativeProfileFlag)(void *manager, s32 slot);
typedef s32 (*NativeWindowUpdate)(
    s32 selection,
    s32 current_start,
    s32 visible_rows,
    s32 margin_rows,
    s32 row_count
);
typedef void (*NativeBackingDraw)(void *backing);
typedef void (*NativeSpriteDraw)(void *object, float alpha);

typedef struct BattleSettingsRow {
    u32 id;
    u32 local_offset;
    u32 label_reference;
    u32 help_reference;
    u32 values_reference;
    u32 option_count;
    u32 default_value;
    u32 flags;
} BattleSettingsRow;

typedef struct BattleSettingsSchema {
    u32 row_count;
    u32 substitution_mode_get;
    u32 substitution_mode_set;
    u32 ultimate_jutsu_mode_get;
    u32 ultimate_jutsu_mode_set;
    u32 ultimate_jutsu_no_contest_label;
    u32 ultimate_jutsu_no_hud_label;
    u32 shadowblur_get;
    u32 shadowblur_set;
    u32 extra_hit_get;
    u32 extra_hit_set;
    u32 sub_active_frames_get;
    u32 sub_active_frames_set;
    u32 xdash_chakra_cost_option_get;
    u32 xdash_chakra_cost_option_set;
    u32 support_get;
    u32 support_set;
    BattleSettingsRow rows[1];
} BattleSettingsSchema;

extern const BattleSettingsSchema battle_settings_schema;
typedef u32 (*UltimateJutsuModeGet)(void);
typedef void (*UltimateJutsuModeSet)(u32 mode);
typedef u32 (*ToggleModeGet)(void);
typedef void (*ToggleModeSet)(u32 mode);

const u8 battle_settings_substitution_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_substitution_label"
    ) = "Substitution";

const u8 battle_settings_substitution_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_substitution_help"
    ) = "Choose whether substitutions consume chakra, the gauge, or nothing.";

const u8 battle_settings_sub_active_frames_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_sub_active_frames_label"
    ) = "Sub Active Frames";

const u8 battle_settings_sub_active_frames_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_sub_active_frames_help"
    ) = "Choose how many frames Substitution remains active.";

const u8 battle_settings_xdash_chakra_cost_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_xdash_chakra_cost_label"
    ) = "X-dash Chakra Cost";

const u8 battle_settings_xdash_chakra_cost_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_xdash_chakra_cost_help"
    ) = "Choose the chakra percentage spent when X-dash commits.";

const u8 battle_settings_support_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_support_label"
    ) = "Support";

const u8 battle_settings_support_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_support_help"
    ) = "Choose whether field support and its gauge are available.";

const u8 battle_settings_shadowblur_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_shadowblur_label"
    ) = "Shadowblur Extra Hit";

const u8 battle_settings_shadowblur_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_shadowblur_help"
    ) = "Choose whether Shadowblur Extra Hit is enabled.";

const u8 battle_settings_extra_hit_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_extra_hit_label"
    ) = "Extra Hit";

const u8 battle_settings_extra_hit_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_extra_hit_help"
    ) = "Choose whether Extra Hit is enabled.";

const u8 battle_settings_off_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_off_label"
    ) = "Off";

const u8 battle_settings_on_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_on_label"
    ) = "On";

const u8 battle_settings_handicap_text[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_handicap_text"
    ) =
        "0-10\0"
        "1-9\0"
        "2-8\0"
        "3-7\0"
        "4-6\0"
        "5-5\0"
        "6-4\0"
        "7-3\0"
        "8-2\0"
        "9-1\0"
        "10-0";

volatile u32 battle_settings_active_labels[BATTLE_SETTINGS_VISIBLE_ROWS]
    __attribute__((section(".bss.battle_settings_active_labels")));
volatile u32 battle_settings_active_help[BATTLE_SETTINGS_MAX_ROWS]
    __attribute__((section(".bss.battle_settings_active_help")));
volatile u32 battle_settings_active_value_tables[BATTLE_SETTINGS_VISIBLE_ROWS]
    __attribute__((section(".bss.battle_settings_active_value_tables")));
volatile u32 battle_settings_ultimate_jutsu_values[
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2u
] __attribute__((section(".bss.battle_settings_ultimate_jutsu_values")));
volatile u32 battle_settings_handicap_values[11]
    __attribute__((section(".bss.battle_settings_handicap_values")));
volatile s32 battle_settings_substitution_staged
    __attribute__((section(".bss.battle_settings_substitution_staged")));
volatile s32 battle_settings_ultimate_jutsu_staged
    __attribute__((section(".bss.battle_settings_ultimate_jutsu_staged")));
volatile s32 battle_settings_shadowblur_staged
    __attribute__((section(".bss.battle_settings_shadowblur_staged")));
volatile s32 battle_settings_extra_hit_staged
    __attribute__((section(".bss.battle_settings_extra_hit_staged")));
volatile s32 battle_settings_sub_active_frames_staged
    __attribute__((section(".bss.battle_settings_sub_active_frames_staged")));
volatile s32 battle_settings_xdash_chakra_cost_staged
    __attribute__((section(".bss.battle_settings_xdash_chakra_cost_staged")));
volatile s32 battle_settings_support_staged
    __attribute__((section(".bss.battle_settings_support_staged")));
void * volatile battle_settings_active_controller
    __attribute__((section(".bss.battle_settings_active_controller")));
volatile s32 battle_settings_window_start
    __attribute__((section(".bss.battle_settings_window_start")));

static const BattleSettingsRow *battle_settings_row(s32 index)
{
    if (
        index < 0 ||
        (u32)index >= battle_settings_schema.row_count ||
        battle_settings_schema.row_count > BATTLE_SETTINGS_MAX_ROWS
    ) {
        return (const BattleSettingsRow *)0;
    }
    return &battle_settings_schema.rows[index];
}

static s32 battle_settings_index_with_flag(u32 flag)
{
    u32 index;

    for (index = 0u; index < battle_settings_schema.row_count; ++index) {
        if ((battle_settings_schema.rows[index].flags & flag) != 0u) {
            return (s32)index;
        }
    }
    return -1;
}

static u32 battle_settings_reference(u32 reference, u32 indirect)
{
    if (indirect == 0u) {
        return reference;
    }
    return *(volatile u32 *)reference;
}

static u32 battle_settings_value_table(const BattleSettingsRow *row)
{
    if ((row->flags & ROW_FLAG_HANDICAP) != 0u) {
        return (u32)battle_settings_handicap_values;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
        return (u32)battle_settings_ultimate_jutsu_values;
    }
    return battle_settings_reference(
        row->values_reference,
        row->flags & ROW_FLAG_VALUES_SLOT
    );
}

static void battle_settings_initialize_handicap_values(void)
{
    const u8 *text = battle_settings_handicap_text;
    u32 value;

    for (value = 0u; value < 11u; ++value) {
        battle_settings_handicap_values[value] = (u32)text;
        while (*text != 0u) {
            ++text;
        }
        ++text;
    }
}

static void battle_settings_refresh_visible_tables(void)
{
    u32 slot;

    for (slot = 0u; slot < BATTLE_SETTINGS_VISIBLE_ROWS; ++slot) {
        s32 index = battle_settings_window_start + (s32)slot;
        const BattleSettingsRow *row = battle_settings_row(index);

        if (row == (const BattleSettingsRow *)0) {
            battle_settings_active_labels[slot] = 0u;
            battle_settings_active_value_tables[slot] = 0u;
            continue;
        }
        battle_settings_active_labels[slot] = battle_settings_reference(
            row->label_reference,
            row->flags & ROW_FLAG_LABEL_SLOT
        );
        battle_settings_active_value_tables[slot] =
            battle_settings_value_table(row);
    }
}

static void battle_settings_initialize_tables(void)
{
    u32 index;

    battle_settings_initialize_handicap_values();
    for (index = 0u; index < battle_settings_schema.row_count; ++index) {
        const BattleSettingsRow *row = &battle_settings_schema.rows[index];

        battle_settings_active_help[index] = battle_settings_reference(
            row->help_reference,
            row->flags & ROW_FLAG_HELP_SLOT
        );
        if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
            const u32 *native_values = (const u32 *)
                battle_settings_reference(
                    row->values_reference,
                    row->flags & ROW_FLAG_VALUES_SLOT
                );
            u32 value;

            for (
                value = 0u;
                value < ULTIMATE_JUTSU_NATIVE_MODE_COUNT;
                ++value
            ) {
                battle_settings_ultimate_jutsu_values[value] =
                    native_values[value];
            }
            battle_settings_ultimate_jutsu_values[6] =
                battle_settings_schema.ultimate_jutsu_no_contest_label;
            battle_settings_ultimate_jutsu_values[7] =
                battle_settings_schema.ultimate_jutsu_no_hud_label;
        }
    }
    battle_settings_refresh_visible_tables();
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_row_id")
s32 battle_settings_row_id(s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);

    return row == (const BattleSettingsRow *)0 ? -1 : (s32)row->id;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_visible_row_id")
s32 battle_settings_visible_row_id(s32 slot)
{
    if (slot < 0 || (u32)slot >= BATTLE_SETTINGS_VISIBLE_ROWS) {
        return -1;
    }
    return battle_settings_row_id(battle_settings_window_start + slot);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_max_value")
s32 battle_settings_get_max_value(void *controller, s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);
    void *manager;
    s32 maximum;

    (void)controller;
    if (row == (const BattleSettingsRow *)0 || row->option_count == 0u) {
        return 0;
    }
    maximum = (s32)row->option_count - 1;
    if ((row->flags & ROW_FLAG_DIFFICULTY_LIMIT) == 0u) {
        return maximum;
    }
    manager = *(void * volatile *)MANAGER_POINTER_ADDRESS;
    if (
        manager != (void *)0 &&
        ((NativeProfileFlag)NATIVE_PROFILE_FLAG_ADDRESS)(
            manager,
            PROFILE_ULTIMATE_DIFFICULTY_SLOT
        ) == 0 &&
        maximum > 4
    ) {
        maximum = 4;
    }
    return maximum;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_value")
s32 battle_settings_get_value(void *controller, s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);

    if (row == (const BattleSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUBSTITUTION) != 0u) {
        return battle_settings_substitution_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
        return battle_settings_ultimate_jutsu_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SHADOWBLUR) != 0u) {
        return battle_settings_shadowblur_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_EXTRA_HIT) != 0u) {
        return battle_settings_extra_hit_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES) != 0u) {
        return battle_settings_sub_active_frames_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST) != 0u) {
        return battle_settings_xdash_chakra_cost_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUPPORT) != 0u) {
        return battle_settings_support_staged;
    }
    return *(volatile s32 *)((u8 *)controller + row->local_offset);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_visible_max_value")
s32 battle_settings_get_visible_max_value(void *controller, s32 slot)
{
    return battle_settings_get_max_value(
        controller,
        battle_settings_window_start + slot
    );
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_visible_value")
s32 battle_settings_get_visible_value(void *controller, s32 slot)
{
    return battle_settings_get_value(
        controller,
        battle_settings_window_start + slot
    );
}

static void battle_settings_set_value(
    void *controller,
    s32 index,
    s32 value
)
{
    const BattleSettingsRow *row = battle_settings_row(index);

    if (row == (const BattleSettingsRow *)0) {
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUBSTITUTION) != 0u) {
        battle_settings_substitution_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
        battle_settings_ultimate_jutsu_staged = value;
        *(volatile s32 *)((u8 *)controller + row->local_offset) =
            (u32)value < ULTIMATE_JUTSU_NATIVE_MODE_COUNT
            ? value
            : (s32)ULTIMATE_JUTSU_NATIVE_DEFAULT;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SHADOWBLUR) != 0u) {
        battle_settings_shadowblur_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_EXTRA_HIT) != 0u) {
        battle_settings_extra_hit_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES) != 0u) {
        battle_settings_sub_active_frames_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST) != 0u) {
        battle_settings_xdash_chakra_cost_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUPPORT) != 0u) {
        battle_settings_support_staged = value;
        return;
    }
    *(volatile s32 *)((u8 *)controller + row->local_offset) = value;
}

static void battle_settings_stage_runtime_mode(
    void *controller,
    u32 flag,
    u32 getter_address
)
{
    s32 index;

    if (getter_address == 0u) {
        return;
    }
    index = battle_settings_index_with_flag(flag);
    if (index >= 0) {
        battle_settings_set_value(
            controller,
            index,
            (s32)((ToggleModeGet)getter_address)()
        );
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_snapshot")
void battle_settings_snapshot(void *controller)
{
    NativeControllerCall native_snapshot =
        (NativeControllerCall)NATIVE_SNAPSHOT_ADDRESS;

    native_snapshot(controller);
    battle_settings_active_controller = controller;
    battle_settings_window_start = 0;
    battle_settings_initialize_tables();
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_SUBSTITUTION,
        battle_settings_schema.substitution_mode_get
    );
    if (battle_settings_schema.ultimate_jutsu_mode_get != 0u) {
        s32 index = battle_settings_index_with_flag(
            ROW_FLAG_CUSTOM_ULTIMATE_JUTSU
        );
        u32 mode = (
            (UltimateJutsuModeGet)
                battle_settings_schema.ultimate_jutsu_mode_get
        )();

        if (index >= 0) {
            battle_settings_set_value(controller, index, (s32)mode);
        }
    }
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_SHADOWBLUR,
        battle_settings_schema.shadowblur_get
    );
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_EXTRA_HIT,
        battle_settings_schema.extra_hit_get
    );
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
        battle_settings_schema.sub_active_frames_get
    );
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
        battle_settings_schema.xdash_chakra_cost_option_get
    );
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_SUPPORT,
        battle_settings_schema.support_get
    );
}

static void battle_settings_commit_runtime_mode(u32 flag, u32 setter_address)
{
    s32 index = battle_settings_index_with_flag(flag);

    if (
        index >= 0 &&
        setter_address != 0u &&
        battle_settings_active_controller != (void *)0
    ) {
        ((ToggleModeSet)setter_address)(
            (u32)battle_settings_get_value(
                (void *)battle_settings_active_controller,
                index
            )
        );
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_confirm_sound")
void battle_settings_confirm_sound(u32 sound_id)
{
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_SUBSTITUTION,
        battle_settings_schema.substitution_mode_set
    );
    if (
        battle_settings_index_with_flag(
            ROW_FLAG_CUSTOM_ULTIMATE_JUTSU
        ) >= 0
    ) {
        ((UltimateJutsuModeSet)
            battle_settings_schema.ultimate_jutsu_mode_set)(
                (u32)battle_settings_ultimate_jutsu_staged
            );
    }
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_SHADOWBLUR,
        battle_settings_schema.shadowblur_set
    );
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_EXTRA_HIT,
        battle_settings_schema.extra_hit_set
    );
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
        battle_settings_schema.sub_active_frames_set
    );
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
        battle_settings_schema.xdash_chakra_cost_option_set
    );
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_SUPPORT,
        battle_settings_schema.support_set
    );
    ((NativeSound)NATIVE_SOUND_ADDRESS)(sound_id);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_defaults_sound")
void battle_settings_defaults_sound(u32 sound_id)
{
    u32 index;

    if (battle_settings_active_controller != (void *)0) {
        for (index = 0u; index < battle_settings_schema.row_count; ++index) {
            battle_settings_set_value(
                (void *)battle_settings_active_controller,
                (s32)index,
                (s32)battle_settings_schema.rows[index].default_value
            );
        }
    }
    ((NativeSound)NATIVE_SOUND_ADDRESS)(sound_id);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_navigate")
s32 battle_settings_navigate(void *controller)
{
    volatile short *selected = (volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    u32 input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_EFFECTIVE_INPUT_OFFSET
    );
    s32 row_count = (s32)battle_settings_schema.row_count;

    if (row_count <= 0) {
        return 0;
    }
    if ((input & INPUT_PREVIOUS_ROW) != 0u) {
        *selected -= 1;
        if (*selected < 0) {
            *selected = (short)(row_count - 1);
        }
        return 1;
    }
    if ((input & INPUT_NEXT_ROW) != 0u) {
        *selected += 1;
        if ((s32)*selected >= row_count) {
            *selected = 0;
        }
        return 1;
    }
    return 0;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_change_value")
s32 battle_settings_change_value(void *controller)
{
    s32 index = *(volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    u32 input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_EFFECTIVE_INPUT_OFFSET
    );
    s32 value = battle_settings_get_value(controller, index);
    s32 maximum = battle_settings_get_max_value(controller, index);

    if ((input & INPUT_NEXT_VALUE) != 0u && value < maximum) {
        battle_settings_set_value(controller, index, value + 1);
        return 1;
    }
    if ((input & INPUT_PREVIOUS_VALUE) != 0u && value > 0) {
        battle_settings_set_value(controller, index, value - 1);
        return 1;
    }
    return 0;
}

static u8 *battle_settings_backing_object(u8 *records, u32 index)
{
    return *(u8 **)(
        records +
        index * BACKING_RECORD_SIZE +
        BACKING_RECORD_OBJECT_POINTER_OFFSET
    );
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_draw_backing")
void battle_settings_draw_backing(void *backing)
{
    NativeBackingDraw native_draw =
        (NativeBackingDraw)NATIVE_BACKING_DRAW_ADDRESS;
    NativeSpriteDraw draw_sprite =
        (NativeSpriteDraw)NATIVE_SPRITE_DRAW_ADDRESS;
    u8 *records;
    volatile u8 *handicap_flags;
    u8 saved_handicap_flags;
    u8 *last;
    u8 *previous;
    volatile float *last_local_y;
    volatile float *last_world_y;
    float native_local_y;
    float native_world_y;
    float local_step;
    float world_step;
    float alpha;
    u32 row;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)((u8 *)backing + BACKING_RECORDS_POINTER_OFFSET);
    if (records == (u8 *)0) {
        native_draw(backing);
        return;
    }
    handicap_flags = records +
        BACKING_HANDICAP_RECORD * BACKING_RECORD_SIZE +
        BACKING_RECORD_DRAW_FLAGS_OFFSET;
    saved_handicap_flags = *handicap_flags;
    *handicap_flags &= (u8)~BACKING_RECORD_DRAW_FLAG;
    native_draw(backing);
    *handicap_flags = saved_handicap_flags;

    last = battle_settings_backing_object(
        records,
        BACKING_LAST_ORDINARY_RECORD
    );
    previous = battle_settings_backing_object(
        records,
        BACKING_LAST_ORDINARY_RECORD - 1u
    );
    if (last == (u8 *)0 || previous == (u8 *)0) {
        return;
    }
    last_local_y = (volatile float *)(
        last + BACKING_OBJECT_LOCAL_Y_OFFSET
    );
    last_world_y = (volatile float *)(
        last + BACKING_OBJECT_WORLD_Y_OFFSET
    );
    native_local_y = *last_local_y;
    native_world_y = *last_world_y;
    local_step = native_local_y - *(volatile float *)(
        previous + BACKING_OBJECT_LOCAL_Y_OFFSET
    );
    world_step = native_world_y - *(volatile float *)(
        previous + BACKING_OBJECT_WORLD_Y_OFFSET
    );
    alpha = *(volatile float *)(
        (u8 *)backing + BACKING_OBJECT_ALPHA_OFFSET
    );
    for (row = 1u; row <= 2u; ++row) {
        *last_local_y = native_local_y + local_step * (float)row;
        *last_world_y = native_world_y + world_step * (float)row;
        draw_sprite(last, alpha);
    }
    *last_local_y = native_local_y;
    *last_world_y = native_world_y;
}

static void battle_settings_update_view(void *controller)
{
    NativeWindowUpdate update =
        (NativeWindowUpdate)NATIVE_WINDOW_UPDATE_ADDRESS;
    s32 selected = *(volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 row_count = (s32)battle_settings_schema.row_count;
    s32 maximum_start = row_count - (s32)BATTLE_SETTINGS_VISIBLE_ROWS;
    s32 start;

    if (maximum_start <= 0) {
        start = 0;
    } else {
        start = update(
            selected,
            battle_settings_window_start,
            (s32)BATTLE_SETTINGS_VISIBLE_ROWS,
            BATTLE_SETTINGS_WINDOW_MARGIN_ROWS,
            row_count
        );
        if (start < 0) {
            start = 0;
        } else if (start > maximum_start) {
            start = maximum_start;
        }
    }
    battle_settings_window_start = start;
    battle_settings_refresh_visible_tables();
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_draw_rows")
void battle_settings_draw_rows(void *controller)
{
    NativeControllerCall draw =
        (NativeControllerCall)NATIVE_ROWS_DRAW_ADDRESS;
    volatile short *selected;
    short semantic_selection;

    if (controller == (void *)0) {
        return;
    }
    battle_settings_update_view(controller);
    selected = (volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    semantic_selection = *selected;
    *selected = (short)(semantic_selection - battle_settings_window_start);
    draw(controller);
    *selected = semantic_selection;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_draw_cursor")
void battle_settings_draw_cursor(void *controller)
{
    NativeControllerCall draw =
        (NativeControllerCall)NATIVE_CURSOR_DRAW_ADDRESS;
    volatile short *selected;
    short semantic_selection;

    if (controller == (void *)0) {
        return;
    }
    battle_settings_update_view(controller);
    selected = (volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    semantic_selection = *selected;
    *selected = (short)(semantic_selection - battle_settings_window_start);
    draw(controller);
    *selected = semantic_selection;
}
