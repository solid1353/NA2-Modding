/* Feature-aware Battle Settings row map over the native menu. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define BATTLE_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define BATTLE_SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define BATTLE_SETTINGS_MAX_ROWS 7u

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
#define NATIVE_BACKING_DRAW_ADDRESS 0x001BB790u
#define NATIVE_SPRITE_DRAW_ADDRESS 0x00190F40u

#define PROFILE_ULTIMATE_DIFFICULTY_SLOT 0x6Au

#define BACKING_RECORDS_POINTER_OFFSET 0xFCu
#define BACKING_RECORD_COUNT 6u
#define BACKING_RECORD_SIZE 0x10u
#define BACKING_RECORD_OBJECT_POINTER_OFFSET 0x00u
#define BACKING_RECORD_DRAW_FLAGS_OFFSET 0x0Au
#define BACKING_RECORD_DRAW_FLAG 0x04u
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

typedef void (*NativeControllerCall)(void *controller);
typedef void (*NativeSound)(u32 sound_id);
typedef s32 (*NativeProfileFlag)(void *manager, s32 slot);
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
    BattleSettingsRow rows[1];
} BattleSettingsSchema;

extern const BattleSettingsSchema battle_settings_schema;
typedef u32 (*SubstitutionModeGet)(void);
typedef void (*SubstitutionModeSet)(u32 mode);

const u8 battle_settings_substitution_label[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_substitution_label"
    ) = "Substitution";

const u8 battle_settings_substitution_help[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_substitution_help"
    ) = "Choose whether substitutions consume chakra, the gauge, or nothing.";

volatile u32 battle_settings_active_labels[BATTLE_SETTINGS_MAX_ROWS]
    __attribute__((section(".bss.battle_settings_active_labels")));
volatile u32 battle_settings_active_help[BATTLE_SETTINGS_MAX_ROWS]
    __attribute__((section(".bss.battle_settings_active_help")));
volatile u32 battle_settings_active_value_tables[BATTLE_SETTINGS_MAX_ROWS]
    __attribute__((section(".bss.battle_settings_active_value_tables")));
volatile s32 battle_settings_substitution_staged
    __attribute__((section(".bss.battle_settings_substitution_staged")));

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

static void battle_settings_initialize_tables(void)
{
    u32 index;

    for (index = 0u; index < battle_settings_schema.row_count; ++index) {
        const BattleSettingsRow *row = &battle_settings_schema.rows[index];

        battle_settings_active_labels[index] = battle_settings_reference(
            row->label_reference,
            row->flags & ROW_FLAG_LABEL_SLOT
        );
        battle_settings_active_help[index] = battle_settings_reference(
            row->help_reference,
            row->flags & ROW_FLAG_HELP_SLOT
        );
        battle_settings_active_value_tables[index] =
            battle_settings_reference(
                row->values_reference,
                row->flags & ROW_FLAG_VALUES_SLOT
            );
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_row_id")
s32 battle_settings_row_id(s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);

    return row == (const BattleSettingsRow *)0 ? -1 : (s32)row->id;
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
    return *(volatile s32 *)((u8 *)controller + row->local_offset);
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
    *(volatile s32 *)((u8 *)controller + row->local_offset) = value;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_snapshot")
void battle_settings_snapshot(void *controller)
{
    NativeControllerCall native_snapshot =
        (NativeControllerCall)NATIVE_SNAPSHOT_ADDRESS;

    native_snapshot(controller);
    battle_settings_initialize_tables();
    if (battle_settings_schema.substitution_mode_get != 0u) {
        battle_settings_substitution_staged = (s32)(
            (SubstitutionModeGet)battle_settings_schema.substitution_mode_get
        )();
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_confirm_sound")
void battle_settings_confirm_sound(u32 sound_id)
{
    if (
        battle_settings_index_with_flag(
            ROW_FLAG_CUSTOM_SUBSTITUTION
        ) >= 0
    ) {
        ((SubstitutionModeSet)battle_settings_schema.substitution_mode_set)(
            (u32)battle_settings_substitution_staged
        );
    }
    ((NativeSound)NATIVE_SOUND_ADDRESS)(sound_id);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_defaults_sound")
void battle_settings_defaults_sound(u32 sound_id)
{
    s32 index = battle_settings_index_with_flag(
        ROW_FLAG_CUSTOM_SUBSTITUTION
    );

    if (index >= 0) {
        battle_settings_substitution_staged =
            (s32)battle_settings_schema.rows[index].default_value;
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

static void battle_settings_set_backing_record(
    u8 *records,
    u32 index,
    u32 draw
)
{
    volatile u8 *flags = records +
        index * BACKING_RECORD_SIZE +
        BACKING_RECORD_DRAW_FLAGS_OFFSET;

    if (draw != 0u) {
        *flags |= BACKING_RECORD_DRAW_FLAG;
    } else {
        *flags &= (u8)~BACKING_RECORD_DRAW_FLAG;
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_draw_backing")
void battle_settings_draw_backing(void *backing)
{
    NativeBackingDraw native_draw =
        (NativeBackingDraw)NATIVE_BACKING_DRAW_ADDRESS;
    NativeSpriteDraw draw_sprite =
        (NativeSpriteDraw)NATIVE_SPRITE_DRAW_ADDRESS;
    u8 *records;
    u8 *last;
    u8 *previous;
    volatile float *last_local_y;
    volatile float *last_world_y;
    float native_local_y;
    float native_world_y;
    float local_step;
    float world_step;
    float alpha;
    u32 index;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)((u8 *)backing + BACKING_RECORDS_POINTER_OFFSET);
    if (records != (u8 *)0) {
        for (index = 0u; index < BACKING_RECORD_COUNT; ++index) {
            battle_settings_set_backing_record(
                records,
                index,
                index < battle_settings_schema.row_count
            );
        }
    }
    native_draw(backing);
    if (
        records == (u8 *)0 ||
        battle_settings_schema.row_count <= BACKING_RECORD_COUNT
    ) {
        return;
    }
    last = battle_settings_backing_object(
        records,
        BACKING_RECORD_COUNT - 1u
    );
    previous = battle_settings_backing_object(
        records,
        BACKING_RECORD_COUNT - 2u
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
    *last_local_y = native_local_y + local_step;
    *last_world_y = native_world_y + world_step;
    alpha = *(volatile float *)(
        (u8 *)backing + BACKING_OBJECT_ALPHA_OFFSET
    );
    draw_sprite(last, alpha);
    *last_local_y = native_local_y;
    *last_world_y = native_world_y;
}
