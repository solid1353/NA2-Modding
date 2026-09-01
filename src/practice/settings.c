/* Compact Practice Settings row map over the native controller and renderer. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define PRACTICE_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define PRACTICE_SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define MANAGER_POINTER_ADDRESS 0x00607600u

#define CONTROLLER_SELECTED_ROW_OFFSET 0x3Cu
#define CONTROLLER_EFFECTIVE_INPUT_OFFSET 0x68u
#define CONTROLLER_SCROLL_OFFSET 0x44u
#define CONTROLLER_UPPER_WINDOW_OFFSET 0xB0u
#define CONTROLLER_LOWER_WINDOW_OFFSET 0xB4u
#define CONTROLLER_HELP_OBJECT_OFFSET 0x34u
#define CONTROLLER_HEALTH_VALUE_OFFSET 0x6Cu
#define CONTROLLER_COMMANDS_VALUE_OFFSET 0x84u
#define CONTROLLER_GUIDE_NINJA_SOUND_VALUE_OFFSET 0x8Cu
#define CONTROLLER_LINKED_ATTACK_VALUE_OFFSET 0xA8u
#define BACKING_RECORDS_POINTER_OFFSET 0xFCu
#define BACKING_RECORD_COUNT 18u
#define BACKING_RECORD_SIZE 0x10u
#define BACKING_RECORD_OBJECT_POINTER_OFFSET 0x00u
#define BACKING_RECORD_DRAW_FLAGS_OFFSET 0x0Au
#define BACKING_RECORD_DRAW_FLAG 0x04u
#define BACKING_RECORD_LOCAL_Y_OFFSET 0x78u
#define BACKING_PLAYER_FIRST_RECORD 1u
#define BACKING_PLAYER_REMAINING_FIRST_RECORD 10u
#define BACKING_PLAYER_REMAINING_CAPACITY 8u
#define BACKING_PLAYER_CAPACITY 9u
#define BACKING_PLAYER_MIDDLE_LAST_RECORD 16u
#define BACKING_PLAYER_TERMINAL_RECORD 17u
#define BACKING_OPPONENT_FIRST_RECORD 2u
#define BACKING_OPPONENT_CAPACITY 8u
#define BACKING_OPPONENT_MIDDLE_LAST_RECORD 8u
#define BACKING_OPPONENT_TERMINAL_RECORD 9u
#define BACKING_OBJECT_ALPHA_OFFSET 0x88u
#define BACKING_RECORD_WORLD_Y_OFFSET 0x38u

#define INPUT_PREVIOUS_ROW 0x1000u
#define INPUT_NEXT_ROW 0x4000u
#define INPUT_NEXT_VALUE 0x2000u
#define INPUT_PREVIOUS_VALUE 0x8000u

#define NATIVE_SNAPSHOT_ADDRESS 0x00880FB0u
#define NATIVE_APPLY_ADDRESS 0x008811A0u
#define NATIVE_DEFAULTS_ADDRESS 0x00881390u
#define NATIVE_PROFILE_FLAG_ADDRESS 0x001F7780u
#define NATIVE_WINDOW_UPDATE_ADDRESS 0x0037D9C0u
#define NATIVE_APPROACH_FLOAT_ADDRESS 0x006C12A0u
#define NATIVE_HELP_SET_ADDRESS 0x0037F760u
#define NATIVE_BACKING_COMPOSE_ADDRESS 0x001BB6F0u
#define NATIVE_BACKING_DRAW_ADDRESS 0x001BB790u
#define NATIVE_SPRITE_DRAW_ADDRESS 0x00190F40u

#define PLAYER_VISIBLE_ROWS 7
#define OPPONENT_VISIBLE_ROWS 6
#define WINDOW_MARGIN_ROWS 2
#define ROW_SCROLL_STEP 28.0f
#define ROW_DRAW_STEP 28.0f
#define SECTION_HEADING_GAP 18.0f
#define WINDOW_APPROACH_STEP 20.0f
#define BACKING_SCROLL_SCALE 0.96f
#define CURSOR_SCROLL_SCALE 0.939f
#define CURSOR_ROW_STEP 26.5f
#define CURSOR_BASE_Y 94.0f
#define CURSOR_SECTION_OFFSET 40.0f

#define ROW_ID_STATUS 9u
#define ROW_ID_ULTIMATE_JUTSU 3u
#define ROW_ID_SUBSTITUTION 17u
#define ROW_ID_SHADOWBLUR 18u
#define ROW_ID_EXTRA_HIT 19u
#define ROW_ID_SUB_ACTIVE_FRAMES 20u
#define ROW_ID_XDASH_CHAKRA_COST 21u
#define ROW_ID_SUPPORT 22u
#define PROFILE_ULTIMATE_DIFFICULTY_SLOT 0x6Au

#define ROW_AVAILABLE_ALWAYS 0u
#define ROW_AVAILABLE_STATUS_COM 1u
#define ROW_AVAILABLE_STATUS_ACTION 2u
#define ROW_AVAILABLE_STATUS_NOT_MANUAL 3u

#define ROW_FLAG_LABEL_SLOT 0x01u
#define ROW_FLAG_HELP_SLOT 0x02u
#define ROW_FLAG_HELP_BY_VALUE 0x04u
#define ROW_FLAG_VALUES_SLOT 0x08u
#define ROW_FLAG_STRENGTH_LIMIT 0x10u
#define ROW_FLAG_CUSTOM_SUBSTITUTION 0x20u
#define ROW_FLAG_CUSTOM_ULTIMATE_JUTSU 0x40u
#define ROW_FLAG_CUSTOM_SHADOWBLUR 0x80u
#define ROW_FLAG_CUSTOM_EXTRA_HIT 0x100u
#define ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES 0x200u
#define ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST 0x400u
#define ROW_FLAG_CUSTOM_SUPPORT 0x800u

#define ULTIMATE_JUTSU_NATIVE_MODE_COUNT 6u
#define ULTIMATE_JUTSU_NATIVE_DEFAULT 2u

typedef void (*NativeControllerCall)(void *controller);
typedef s32 (*NativeProfileFlag)(void *manager, s32 slot);
typedef s32 (*NativeWindowUpdate)(
    s32 selection,
    s32 current_start,
    s32 visible_rows,
    s32 margin_rows,
    s32 row_count
);
typedef void (*NativeApproachFloat)(
    float target,
    float step,
    volatile float *value
);
typedef void (*NativeHelpSet)(
    float scale,
    void *help_object,
    const u8 *text,
    s32 style,
    s32 argument
);
typedef void (*NativeBackingCall)(void *backing);
typedef void (*NativeSpriteDraw)(float alpha, void *object);

typedef struct PracticeSettingsRow {
    u32 id;
    u32 section;
    u32 local_offset;
    u32 label_reference;
    u32 help_reference;
    u32 values_reference;
    u32 option_count;
    u32 default_value;
    u32 availability;
    u32 flags;
} PracticeSettingsRow;

typedef struct PracticeSettingsSchema {
    u32 row_count;
    u32 player_row_count;
    u32 opponent_row_count;
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
    PracticeSettingsRow rows[1];
} PracticeSettingsSchema;

extern const PracticeSettingsSchema practice_settings_schema;
extern volatile u32 practice_settings_active_labels[];
extern volatile u32 practice_settings_active_value_tables[];
typedef u32 (*UltimateJutsuModeGet)(void);
typedef void (*UltimateJutsuModeSet)(u32 mode);
typedef u32 (*ToggleModeGet)(void);
typedef void (*ToggleModeSet)(u32 enabled);

volatile u32 practice_settings_ultimate_jutsu_values[
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2u
] __attribute__((section(".bss.practice_settings_ultimate_jutsu_values")));
volatile s32 practice_settings_substitution_staged
    __attribute__((section(".bss.practice_settings_substitution_staged")));
volatile s32 practice_settings_ultimate_jutsu_staged
    __attribute__((section(".bss.practice_settings_ultimate_jutsu_staged")));
volatile s32 practice_settings_shadowblur_staged
    __attribute__((section(".bss.practice_settings_shadowblur_staged")));
volatile s32 practice_settings_extra_hit_staged
    __attribute__((section(".bss.practice_settings_extra_hit_staged")));
volatile s32 practice_settings_sub_active_frames_staged
    __attribute__((section(".bss.practice_settings_sub_active_frames_staged")));
volatile s32 practice_settings_xdash_chakra_cost_staged
    __attribute__((section(".bss.practice_settings_xdash_chakra_cost_staged")));
volatile s32 practice_settings_support_staged
    __attribute__((section(".bss.practice_settings_support_staged")));

typedef struct PracticeSettingsBackingLayout {
    u32 records;
    u32 objects[BACKING_RECORD_COUNT];
    float native_local_y[BACKING_RECORD_COUNT];
} PracticeSettingsBackingLayout;

volatile PracticeSettingsBackingLayout practice_settings_backing_layout
    __attribute__((section(".bss.practice_settings_backing_layout")));

static const PracticeSettingsRow *practice_settings_row(s32 index)
{
    if (
        index < 0 ||
        (u32)index >= practice_settings_schema.row_count
    ) {
        return (const PracticeSettingsRow *)0;
    }
    return &practice_settings_schema.rows[index];
}

static s32 practice_settings_index_for_id(u32 id)
{
    u32 index;

    for (index = 0u; index < practice_settings_schema.row_count; ++index) {
        if (practice_settings_schema.rows[index].id == id) {
            return (s32)index;
        }
    }
    return -1;
}

static u32 practice_settings_reference(u32 reference, u32 indirect)
{
    if (indirect == 0u) {
        return reference;
    }
    return *(volatile u32 *)reference;
}

static void practice_settings_initialize_tables(void)
{
    u32 index;

    for (index = 0u; index < practice_settings_schema.row_count; ++index) {
        const PracticeSettingsRow *row = &practice_settings_schema.rows[index];

        practice_settings_active_labels[index] = practice_settings_reference(
            row->label_reference,
            row->flags & ROW_FLAG_LABEL_SLOT
        );
        if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
            const u32 *native_values = (const u32 *)
                practice_settings_reference(
                    row->values_reference,
                    row->flags & ROW_FLAG_VALUES_SLOT
                );
            u32 value;

            for (
                value = 0u;
                value < ULTIMATE_JUTSU_NATIVE_MODE_COUNT;
                ++value
            ) {
                practice_settings_ultimate_jutsu_values[value] =
                    native_values[value];
            }
            practice_settings_ultimate_jutsu_values[6] =
                practice_settings_schema.ultimate_jutsu_no_contest_label;
            practice_settings_ultimate_jutsu_values[7] =
                practice_settings_schema.ultimate_jutsu_no_hud_label;
            practice_settings_active_value_tables[index] =
                (u32)practice_settings_ultimate_jutsu_values;
        } else {
            practice_settings_active_value_tables[index] =
                practice_settings_reference(
                    row->values_reference,
                    row->flags & ROW_FLAG_VALUES_SLOT
                );
        }
    }
}

static s32 practice_settings_status(void *controller)
{
    s32 index = practice_settings_index_for_id(ROW_ID_STATUS);

    if (index < 0) {
        return 0;
    }
    return *(volatile s32 *)(
        (u8 *)controller + practice_settings_schema.rows[index].local_offset
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_get_max_value")
s32 practice_settings_get_max_value(void *controller, s32 index)
{
    const PracticeSettingsRow *row = practice_settings_row(index);
    void *manager;
    s32 maximum;

    (void)controller;
    if (row == (const PracticeSettingsRow *)0 || row->option_count == 0u) {
        return 0;
    }
    maximum = (s32)row->option_count - 1;
    if ((row->flags & ROW_FLAG_STRENGTH_LIMIT) == 0u) {
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

PRACTICE_SETTINGS_SECTION(".text.practice_settings_get_value")
s32 practice_settings_get_value(void *controller, s32 index)
{
    const PracticeSettingsRow *row = practice_settings_row(index);

    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUBSTITUTION) != 0u) {
        return practice_settings_substitution_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
        return practice_settings_ultimate_jutsu_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SHADOWBLUR) != 0u) {
        return practice_settings_shadowblur_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_EXTRA_HIT) != 0u) {
        return practice_settings_extra_hit_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES) != 0u) {
        return practice_settings_sub_active_frames_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST) != 0u) {
        return practice_settings_xdash_chakra_cost_staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUPPORT) != 0u) {
        return practice_settings_support_staged;
    }
    return *(volatile s32 *)((u8 *)controller + row->local_offset);
}

static void practice_settings_set_value(
    void *controller,
    s32 index,
    s32 value
)
{
    const PracticeSettingsRow *row = practice_settings_row(index);

    if (row == (const PracticeSettingsRow *)0) {
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUBSTITUTION) != 0u) {
        practice_settings_substitution_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
        practice_settings_ultimate_jutsu_staged = value;
        *(volatile s32 *)((u8 *)controller + row->local_offset) =
            (u32)value < ULTIMATE_JUTSU_NATIVE_MODE_COUNT
            ? value
            : (s32)ULTIMATE_JUTSU_NATIVE_DEFAULT;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SHADOWBLUR) != 0u) {
        practice_settings_shadowblur_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_EXTRA_HIT) != 0u) {
        practice_settings_extra_hit_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES) != 0u) {
        practice_settings_sub_active_frames_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST) != 0u) {
        practice_settings_xdash_chakra_cost_staged = value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_SUPPORT) != 0u) {
        practice_settings_support_staged = value;
        return;
    }
    *(volatile s32 *)((u8 *)controller + row->local_offset) = value;
}

static void practice_settings_stage_runtime_mode(
    void *controller,
    u32 row_id,
    u32 getter_address
)
{
    s32 index;

    if (getter_address == 0u) {
        return;
    }
    index = practice_settings_index_for_id(row_id);
    if (index >= 0) {
        practice_settings_set_value(
            controller,
            index,
            (s32)((ToggleModeGet)getter_address)()
        );
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_snapshot")
void practice_settings_snapshot(void *controller)
{
    NativeControllerCall native_snapshot =
        (NativeControllerCall)NATIVE_SNAPSHOT_ADDRESS;

    native_snapshot(controller);
    practice_settings_initialize_tables();
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUBSTITUTION,
        practice_settings_schema.substitution_mode_get
    );
    if (practice_settings_schema.ultimate_jutsu_mode_get != 0u) {
        s32 index = practice_settings_index_for_id(
            ROW_ID_ULTIMATE_JUTSU
        );
        u32 mode = (
            (UltimateJutsuModeGet)
                practice_settings_schema.ultimate_jutsu_mode_get
        )();

        if (index >= 0) {
            practice_settings_set_value(controller, index, (s32)mode);
        }
    }
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SHADOWBLUR,
        practice_settings_schema.shadowblur_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_EXTRA_HIT,
        practice_settings_schema.extra_hit_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUB_ACTIVE_FRAMES,
        practice_settings_schema.sub_active_frames_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_XDASH_CHAKRA_COST,
        practice_settings_schema.xdash_chakra_cost_option_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUPPORT,
        practice_settings_schema.support_get
    );
}

static void practice_settings_commit_runtime_mode(
    void *controller,
    u32 row_id,
    u32 setter_address
)
{
    s32 index = practice_settings_index_for_id(row_id);

    if (index >= 0 && setter_address != 0u) {
        ((ToggleModeSet)setter_address)(
            (u32)practice_settings_get_value(controller, index)
        );
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_apply")
void practice_settings_apply(void *controller)
{
    NativeControllerCall native_apply =
        (NativeControllerCall)NATIVE_APPLY_ADDRESS;

    native_apply(controller);
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUBSTITUTION,
        practice_settings_schema.substitution_mode_set
    );
    if (
        practice_settings_schema.ultimate_jutsu_mode_set != 0u &&
        practice_settings_index_for_id(ROW_ID_ULTIMATE_JUTSU) >= 0
    ) {
        ((UltimateJutsuModeSet)
            practice_settings_schema.ultimate_jutsu_mode_set)(
                (u32)practice_settings_ultimate_jutsu_staged
            );
    }
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SHADOWBLUR,
        practice_settings_schema.shadowblur_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_EXTRA_HIT,
        practice_settings_schema.extra_hit_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUB_ACTIVE_FRAMES,
        practice_settings_schema.sub_active_frames_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_XDASH_CHAKRA_COST,
        practice_settings_schema.xdash_chakra_cost_option_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUPPORT,
        practice_settings_schema.support_set
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_defaults")
void practice_settings_defaults(void *controller)
{
    NativeControllerCall native_defaults =
        (NativeControllerCall)NATIVE_DEFAULTS_ADDRESS;
    u32 index;

    native_defaults(controller);
    for (index = 0u; index < practice_settings_schema.row_count; ++index) {
        practice_settings_set_value(
            controller,
            (s32)index,
            (s32)practice_settings_schema.rows[index].default_value
        );
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_row_enabled")
s32 practice_settings_row_enabled(void *controller, s32 index)
{
    const PracticeSettingsRow *row = practice_settings_row(index);
    s32 status;

    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    status = practice_settings_status(controller);
    if (row->availability == ROW_AVAILABLE_ALWAYS) {
        return 1;
    }
    if (row->availability == ROW_AVAILABLE_STATUS_COM) {
        return status == 1;
    }
    if (row->availability == ROW_AVAILABLE_STATUS_ACTION) {
        return status >= 2 && status <= 4;
    }
    if (row->availability == ROW_AVAILABLE_STATUS_NOT_MANUAL) {
        return status != 0;
    }
    return 0;
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_navigate")
s32 practice_settings_navigate(void *controller)
{
    volatile s32 *selected = (volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    u32 input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_EFFECTIVE_INPUT_OFFSET
    );
    s32 row_count = (s32)practice_settings_schema.row_count;

    if (row_count <= 0) {
        return 0;
    }
    if ((input & INPUT_PREVIOUS_ROW) != 0u) {
        *selected -= 1;
        if (*selected < 0) {
            *selected = row_count - 1;
        }
        return 1;
    }
    if ((input & INPUT_NEXT_ROW) != 0u) {
        *selected += 1;
        if (*selected >= row_count) {
            *selected = 0;
        }
        return 1;
    }
    return 0;
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_change_value")
s32 practice_settings_change_value(void *controller)
{
    s32 index = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    u32 input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_EFFECTIVE_INPUT_OFFSET
    );
    s32 value;
    s32 maximum;

    if (practice_settings_row_enabled(controller, index) == 0) {
        return 0;
    }
    value = practice_settings_get_value(controller, index);
    maximum = practice_settings_get_max_value(controller, index);
    if ((input & INPUT_NEXT_VALUE) != 0u && value < maximum) {
        practice_settings_set_value(controller, index, value + 1);
        return 1;
    }
    if ((input & INPUT_PREVIOUS_VALUE) != 0u && value > 0) {
        practice_settings_set_value(controller, index, value - 1);
        return 1;
    }
    return 0;
}

static void practice_settings_set_backing_record(
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

static u8 *practice_settings_backing_record_object(u8 *records, u32 index)
{
    return *(u8 **)(
        records +
        index * BACKING_RECORD_SIZE +
        BACKING_RECORD_OBJECT_POINTER_OFFSET
    );
}

static u32 practice_settings_backing_layout_changed(u8 *records)
{
    u32 index;

    if (practice_settings_backing_layout.records != (u32)records) {
        return 1u;
    }
    for (index = 0u; index < BACKING_RECORD_COUNT; ++index) {
        if (
            practice_settings_backing_layout.objects[index] !=
            (u32)practice_settings_backing_record_object(records, index)
        ) {
            return 1u;
        }
    }
    return 0u;
}

static void practice_settings_capture_backing_layout(u8 *records)
{
    u32 index;

    practice_settings_backing_layout.records = (u32)records;
    for (index = 0u; index < BACKING_RECORD_COUNT; ++index) {
        u8 *object = practice_settings_backing_record_object(records, index);

        practice_settings_backing_layout.objects[index] = (u32)object;
        practice_settings_backing_layout.native_local_y[index] =
            object == (u8 *)0
                ? 0.0f
                : *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET);
    }
}

static float practice_settings_backing_step(void)
{
    return ROW_SCROLL_STEP * BACKING_SCROLL_SCALE;
}

static float practice_settings_player_grid_y(u32 index)
{
    if (index == 0u) {
        return practice_settings_backing_layout.native_local_y[
            BACKING_PLAYER_FIRST_RECORD
        ];
    }
    if (index < BACKING_PLAYER_CAPACITY - 1u) {
        return practice_settings_backing_layout.native_local_y[
            BACKING_PLAYER_REMAINING_FIRST_RECORD + index - 1u
        ];
    }
    return practice_settings_backing_layout.native_local_y[
        BACKING_PLAYER_MIDDLE_LAST_RECORD
    ] - practice_settings_backing_step() *
        (float)(index - (BACKING_PLAYER_CAPACITY - 2u));
}

static float practice_settings_player_terminal_y(u32 index)
{
    float terminal_phase =
        practice_settings_backing_layout.native_local_y[
            BACKING_PLAYER_TERMINAL_RECORD
        ] -
        (
            practice_settings_backing_layout.native_local_y[
                BACKING_PLAYER_MIDDLE_LAST_RECORD
            ] - practice_settings_backing_step()
        );

    return practice_settings_player_grid_y(index) + terminal_phase;
}

static float practice_settings_opponent_delta(u32 player_count)
{
    return -practice_settings_backing_step() *
        (float)((s32)player_count - (s32)BACKING_PLAYER_CAPACITY);
}

static float practice_settings_opponent_grid_y(u32 index, float delta)
{
    if (index < BACKING_OPPONENT_CAPACITY - 1u) {
        return practice_settings_backing_layout.native_local_y[
            BACKING_OPPONENT_FIRST_RECORD + index
        ] + delta;
    }
    return practice_settings_backing_layout.native_local_y[
        BACKING_OPPONENT_MIDDLE_LAST_RECORD
    ] + delta - practice_settings_backing_step() *
        (float)(index - (BACKING_OPPONENT_CAPACITY - 2u));
}

static float practice_settings_opponent_terminal_y(
    u32 index,
    float delta
)
{
    float terminal_phase =
        practice_settings_backing_layout.native_local_y[
            BACKING_OPPONENT_TERMINAL_RECORD
        ] -
        (
            practice_settings_backing_layout.native_local_y[
                BACKING_OPPONENT_MIDDLE_LAST_RECORD
            ] - practice_settings_backing_step()
        );

    return practice_settings_opponent_grid_y(index, delta) + terminal_phase;
}

static void practice_settings_restore_backing_y(u8 *records)
{
    u32 index;

    for (index = 0u; index < BACKING_RECORD_COUNT; ++index) {
        u8 *object = practice_settings_backing_record_object(records, index);

        if (object != (u8 *)0) {
            *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET) =
                practice_settings_backing_layout.native_local_y[index];
        }
    }
}

static void practice_settings_place_backing(
    u8 *records,
    u32 player_count,
    u32 opponent_count
)
{
    float opponent_delta = practice_settings_opponent_delta(player_count);
    u8 *object;
    u32 index;

    practice_settings_restore_backing_y(records);
    if (player_count > 1u) {
        object = practice_settings_backing_record_object(
            records,
            BACKING_PLAYER_TERMINAL_RECORD
        );
        if (object != (u8 *)0) {
            *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET) =
                practice_settings_player_terminal_y(player_count - 1u);
        }
    }
    object = practice_settings_backing_record_object(records, 0u);
    if (object != (u8 *)0) {
        *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET) =
            practice_settings_backing_layout.native_local_y[0] +
            opponent_delta;
    }
    for (index = 0u; index < BACKING_OPPONENT_CAPACITY - 1u; ++index) {
        object = practice_settings_backing_record_object(
            records,
            BACKING_OPPONENT_FIRST_RECORD + index
        );
        if (object != (u8 *)0) {
            *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET) =
                practice_settings_opponent_grid_y(index, opponent_delta);
        }
    }
    if (opponent_count > 1u) {
        object = practice_settings_backing_record_object(
            records,
            BACKING_OPPONENT_TERMINAL_RECORD
        );
        if (object != (u8 *)0) {
            *(volatile float *)(object + BACKING_RECORD_LOCAL_Y_OFFSET) =
                practice_settings_opponent_terminal_y(
                    opponent_count - 1u,
                    opponent_delta
                );
        }
    }
}

static void practice_settings_select_backing_records(
    u8 *records,
    u32 player_count,
    u32 opponent_count
)
{
    u32 index;

    practice_settings_set_backing_record(
        records,
        BACKING_PLAYER_FIRST_RECORD,
        player_count != 0u
    );
    for (index = 0u; index < BACKING_PLAYER_REMAINING_CAPACITY - 1u; ++index) {
        practice_settings_set_backing_record(
            records,
            BACKING_PLAYER_REMAINING_FIRST_RECORD + index,
            index + 2u < player_count
        );
    }
    practice_settings_set_backing_record(
        records,
        BACKING_PLAYER_TERMINAL_RECORD,
        player_count > 1u
    );
    practice_settings_set_backing_record(
        records,
        0u,
        opponent_count != 0u
    );
    for (index = 0u; index < BACKING_OPPONENT_CAPACITY - 1u; ++index) {
        practice_settings_set_backing_record(
            records,
            BACKING_OPPONENT_FIRST_RECORD + index,
            index == 0u
                ? opponent_count != 0u
                : index + 1u < opponent_count
        );
    }
    practice_settings_set_backing_record(
        records,
        BACKING_OPPONENT_TERMINAL_RECORD,
        opponent_count > 1u
    );
}

PRACTICE_SETTINGS_SECTION(
    ".text.practice_settings_prepare_backing_and_compose"
)
void practice_settings_prepare_backing_and_compose(void *backing)
{
    NativeBackingCall compose =
        (NativeBackingCall)NATIVE_BACKING_COMPOSE_ADDRESS;
    u8 *records;
    u32 player_count = practice_settings_schema.player_row_count;
    u32 opponent_count = practice_settings_schema.opponent_row_count;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)((u8 *)backing + BACKING_RECORDS_POINTER_OFFSET);
    if (records == (u8 *)0) {
        compose(backing);
        return;
    }
    if (practice_settings_backing_layout_changed(records) != 0u) {
        practice_settings_capture_backing_layout(records);
    }
    if (practice_settings_backing_layout.records != (u32)records) {
        compose(backing);
        return;
    }

    practice_settings_place_backing(records, player_count, opponent_count);
    practice_settings_select_backing_records(
        records,
        player_count,
        opponent_count
    );
    compose(backing);
}

static void practice_settings_draw_backing_copy(
    u8 *object,
    u8 *anchor,
    float local_y,
    float alpha
)
{
    NativeSpriteDraw draw_sprite =
        (NativeSpriteDraw)NATIVE_SPRITE_DRAW_ADDRESS;
    volatile float *object_local_y;
    volatile float *object_world_y;
    float native_local_y;
    float native_world_y;

    if (object == (u8 *)0 || anchor == (u8 *)0) {
        return;
    }
    object_local_y = (volatile float *)(
        object + BACKING_RECORD_LOCAL_Y_OFFSET
    );
    object_world_y = (volatile float *)(
        object + BACKING_RECORD_WORLD_Y_OFFSET
    );
    native_local_y = *object_local_y;
    native_world_y = *object_world_y;
    *object_local_y = local_y;
    *object_world_y = *(volatile float *)(
        anchor + BACKING_RECORD_WORLD_Y_OFFSET
    ) + local_y - *(volatile float *)(
        anchor + BACKING_RECORD_LOCAL_Y_OFFSET
    );
    draw_sprite(alpha, object);
    *object_local_y = native_local_y;
    *object_world_y = native_world_y;
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_draw_backing")
void practice_settings_draw_backing(void *backing)
{
    NativeBackingCall draw = (NativeBackingCall)NATIVE_BACKING_DRAW_ADDRESS;
    u32 player_count = practice_settings_schema.player_row_count;
    u32 opponent_count = practice_settings_schema.opponent_row_count;
    u8 *records;
    float alpha;
    float opponent_delta;
    u32 index;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)((u8 *)backing + BACKING_RECORDS_POINTER_OFFSET);
    if (records == (u8 *)0) {
        draw(backing);
        return;
    }
    practice_settings_set_backing_record(
        records,
        BACKING_PLAYER_TERMINAL_RECORD,
        0u
    );
    practice_settings_set_backing_record(
        records,
        BACKING_OPPONENT_TERMINAL_RECORD,
        0u
    );
    draw(backing);
    alpha = *(volatile float *)((u8 *)backing + BACKING_OBJECT_ALPHA_OFFSET);
    for (
        index = BACKING_PLAYER_CAPACITY - 1u;
        index + 1u < player_count;
        ++index
    ) {
        practice_settings_draw_backing_copy(
            practice_settings_backing_record_object(
                records,
                BACKING_PLAYER_MIDDLE_LAST_RECORD
            ),
            practice_settings_backing_record_object(
                records,
                BACKING_PLAYER_FIRST_RECORD
            ),
            practice_settings_player_grid_y(index),
            alpha
        );
    }
    if (player_count > 1u) {
        practice_settings_draw_backing_copy(
            practice_settings_backing_record_object(
                records,
                BACKING_PLAYER_TERMINAL_RECORD
            ),
            practice_settings_backing_record_object(
                records,
                BACKING_PLAYER_FIRST_RECORD
            ),
            practice_settings_player_terminal_y(player_count - 1u),
            alpha
        );
    }
    opponent_delta = practice_settings_opponent_delta(player_count);
    for (
        index = BACKING_OPPONENT_CAPACITY - 1u;
        index + 1u < opponent_count;
        ++index
    ) {
        practice_settings_draw_backing_copy(
            practice_settings_backing_record_object(
                records,
                BACKING_OPPONENT_MIDDLE_LAST_RECORD
            ),
            practice_settings_backing_record_object(
                records,
                BACKING_OPPONENT_FIRST_RECORD
            ),
            practice_settings_opponent_grid_y(index, opponent_delta),
            alpha
        );
    }
    if (opponent_count > 1u) {
        practice_settings_draw_backing_copy(
            practice_settings_backing_record_object(
                records,
                BACKING_OPPONENT_TERMINAL_RECORD
            ),
            practice_settings_backing_record_object(
                records,
                BACKING_OPPONENT_FIRST_RECORD
            ),
            practice_settings_opponent_terminal_y(
                opponent_count - 1u,
                opponent_delta
            ),
            alpha
        );
    }
    practice_settings_set_backing_record(
        records,
        BACKING_PLAYER_TERMINAL_RECORD,
        player_count > 1u
    );
    practice_settings_set_backing_record(
        records,
        BACKING_OPPONENT_TERMINAL_RECORD,
        opponent_count > 1u
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_update_window")
void practice_settings_update_window(void *controller)
{
    NativeWindowUpdate update =
        (NativeWindowUpdate)NATIVE_WINDOW_UPDATE_ADDRESS;
    NativeApproachFloat approach =
        (NativeApproachFloat)NATIVE_APPROACH_FLOAT_ADDRESS;
    s32 selected = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 player_count = (s32)practice_settings_schema.player_row_count;
    s32 start;
    float target;

    if (selected < player_count) {
        volatile s32 *upper = (volatile s32 *)(
            (u8 *)controller + CONTROLLER_UPPER_WINDOW_OFFSET
        );

        start = update(
            selected,
            *upper,
            PLAYER_VISIBLE_ROWS,
            WINDOW_MARGIN_ROWS,
            player_count
        );
        *upper = start;
        target = -ROW_SCROLL_STEP * (float)start;
    } else {
        volatile s32 *lower = (volatile s32 *)(
            (u8 *)controller + CONTROLLER_LOWER_WINDOW_OFFSET
        );
        s32 opponent_count =
            (s32)practice_settings_schema.opponent_row_count;

        start = update(
            selected - player_count,
            *lower,
            OPPONENT_VISIBLE_ROWS,
            WINDOW_MARGIN_ROWS,
            opponent_count
        );
        *lower = start;
        target = -SECTION_HEADING_GAP -
            ROW_DRAW_STEP * (float)player_count -
            ROW_SCROLL_STEP * (float)start;
    }
    approach(
        target,
        WINDOW_APPROACH_STEP,
        (volatile float *)((u8 *)controller + CONTROLLER_SCROLL_OFFSET)
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_cursor_y")
float practice_settings_cursor_y(void *controller)
{
    s32 selected = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 player_count = (s32)practice_settings_schema.player_row_count;
    s32 opponent_count = (s32)practice_settings_schema.opponent_row_count;
    float scroll = *(volatile float *)(
        (u8 *)controller + CONTROLLER_SCROLL_OFFSET
    );
    s32 local_index;
    s32 window_start;
    s32 visible_slot;
    s32 canonical_index;
    s32 canonical_start;
    float actual_target;
    float canonical_target;

    if (selected < player_count) {
        local_index = selected;
        window_start = *(volatile s32 *)(
            (u8 *)controller + CONTROLLER_UPPER_WINDOW_OFFSET
        );
        visible_slot = local_index - window_start;
        if (player_count > 1 && local_index == player_count - 1) {
            canonical_index = (s32)BACKING_PLAYER_CAPACITY - 1;
        } else if (local_index < (s32)BACKING_PLAYER_CAPACITY - 1) {
            canonical_index = local_index;
        } else {
            canonical_index = (s32)BACKING_PLAYER_CAPACITY - 2;
        }
        canonical_start = canonical_index - visible_slot;
        actual_target = -ROW_SCROLL_STEP * (float)window_start;
        canonical_target = -ROW_SCROLL_STEP * (float)canonical_start;
        scroll = canonical_target + scroll - actual_target;
        return CURSOR_BASE_Y -
            CURSOR_ROW_STEP * (float)canonical_index -
            CURSOR_SCROLL_SCALE * scroll;
    }

    local_index = selected - player_count;
    window_start = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_LOWER_WINDOW_OFFSET
    );
    visible_slot = local_index - window_start;
    if (opponent_count > 1 && local_index == opponent_count - 1) {
        canonical_index = (s32)BACKING_OPPONENT_CAPACITY - 1;
    } else if (local_index < (s32)BACKING_OPPONENT_CAPACITY - 1) {
        canonical_index = local_index;
    } else {
        canonical_index = (s32)BACKING_OPPONENT_CAPACITY - 2;
    }
    canonical_start = canonical_index - visible_slot;
    actual_target = -SECTION_HEADING_GAP -
        ROW_DRAW_STEP * (float)player_count -
        ROW_SCROLL_STEP * (float)window_start;
    canonical_target = -SECTION_HEADING_GAP -
        ROW_DRAW_STEP * (float)BACKING_PLAYER_CAPACITY -
        ROW_SCROLL_STEP * (float)canonical_start;
    scroll = canonical_target + scroll - actual_target;
    return CURSOR_BASE_Y -
        CURSOR_ROW_STEP *
            (float)((s32)BACKING_PLAYER_CAPACITY + canonical_index) -
        CURSOR_SCROLL_SCALE * scroll -
        CURSOR_SECTION_OFFSET;
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_update_help")
void practice_settings_update_help(void *controller)
{
    NativeHelpSet set_help = (NativeHelpSet)NATIVE_HELP_SET_ADDRESS;
    s32 index = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    const PracticeSettingsRow *row = practice_settings_row(index);
    const u8 *text;
    u32 reference;

    if (row == (const PracticeSettingsRow *)0) {
        return;
    }
    if ((row->flags & ROW_FLAG_HELP_BY_VALUE) != 0u) {
        s32 value = practice_settings_get_value(controller, index);

        reference = *(volatile u32 *)(
            row->help_reference + (u32)value * 4u
        );
    } else {
        reference = practice_settings_reference(
            row->help_reference,
            row->flags & ROW_FLAG_HELP_SLOT
        );
    }
    text = (const u8 *)reference;
    set_help(
        20.0f,
        *(void * volatile *)(
            (u8 *)controller + CONTROLLER_HELP_OBJECT_OFFSET
        ),
        text,
        8,
        0
    );
}
