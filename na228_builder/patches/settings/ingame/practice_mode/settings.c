/* Paged Practice Settings row map over the native controller and renderer. */

#include "../shared/menu_pages.h"

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define PRACTICE_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define PRACTICE_SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define MANAGER_POINTER_ADDRESS 0x00607600u

#define CONTROLLER_BACKING_OBJECT_OFFSET 0x2Cu
#define CONTROLLER_PHASE_OFFSET 0x38u
#define CONTROLLER_SELECTED_ROW_OFFSET 0x3Cu
#define CONTROLLER_REPEAT_COUNTDOWN_OFFSET 0x40u
#define CONTROLLER_NEW_INPUT_OFFSET 0x60u
#define CONTROLLER_EFFECTIVE_INPUT_OFFSET 0x68u
#define CONTROLLER_SCROLL_OFFSET 0x44u
#define CONTROLLER_UPPER_WINDOW_OFFSET 0xB0u
#define CONTROLLER_LOWER_WINDOW_OFFSET 0xB4u
#define CONTROLLER_HELP_OBJECT_OFFSET 0x34u
#define CONTROLLER_HEALTH_VALUE_OFFSET 0x6Cu
#define CONTROLLER_COMMANDS_VALUE_OFFSET 0x84u
#define CONTROLLER_LINKED_ATTACK_VALUE_OFFSET 0xA8u

#define INPUT_PREVIOUS_ROW 0x1000u
#define INPUT_NEXT_ROW 0x4000u
#define INPUT_NEXT_VALUE 0x2000u
#define INPUT_PREVIOUS_VALUE 0x8000u

#define NATIVE_SNAPSHOT_ADDRESS 0x00880FB0u
#define NATIVE_APPLY_ADDRESS 0x008811A0u
#define NATIVE_DEFAULTS_ADDRESS 0x00881390u
#define NATIVE_PROFILE_FLAG_ADDRESS 0x001F7780u
#define NATIVE_HELP_RESET_ADDRESS 0x0037EEE0u
#define NATIVE_SOUND_ADDRESS 0x001D7E20u


#define ROW_ID_STATUS 9u
#define ROW_ID_HEALTH 0u
#define ROW_ID_COMMANDS 6u
#define ROW_ID_DAMAGE 7u
#define ROW_ID_STRENGTH 10u
#define ROW_ID_ATTACK 11u
#define ROW_ID_GUARD 12u
#define ROW_ID_MOVE 13u
#define ROW_ID_SUBSTITUTION_JUTSU 14u
#define ROW_ID_LINKED_ATTACK 15u
#define ROW_ID_EXTRA_HIT_COUNTER 16u
#define ROW_ID_ULTIMATE_JUTSU 3u
#define ROW_ID_CHAKRA 1u
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
#define ROW_FLAG_CUSTOM_CHAKRA 0x1000u
#define ROW_FLAG_SUBMENU SETTINGS_MENU_ROW_FLAG_SUBMENU

#define ULTIMATE_JUTSU_NATIVE_MODE_COUNT 6u
#define ULTIMATE_JUTSU_NATIVE_DEFAULT 2u

typedef void (*NativeControllerCall)(void *controller);
typedef s32 (*NativeProfileFlag)(void *manager, s32 slot);
typedef void (*NativeHelpSet)(
    float scale,
    void *help_object,
    const u8 *text,
    s32 style,
    s32 argument
);
typedef void (*NativeHelpReset)(void *help_object);
typedef void (*NativeSound)(u32 sound_id);

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
    const u32 *value_pages;
    volatile SettingsMenuOption *runtime_option;
} PracticeSettingsRow;

typedef struct PracticeSettingsSchema {
    u32 row_count;
    u32 page_count;
    u32 pages_reference;
    u32 rows_reference;
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
    u32 help_set;
} PracticeSettingsSchema;

extern const PracticeSettingsSchema practice_settings_schema;
extern const PracticeSettingsSchema mod_settings_schema;
extern volatile u32 mod_settings_child;
extern volatile u32 practice_settings_active_labels[];
extern volatile u32 practice_settings_active_value_tables[];
extern u32 chakra_mode_get(void);
extern void chakra_mode_set(u32 mode);
extern void save_native_setting_set(u32 argument, u32 value);
void practice_settings_prepare_backing_and_compose(void *backing);
void practice_settings_update_help(void *controller);
typedef u32 (*UltimateJutsuModeGet)(void);
typedef void (*UltimateJutsuModeSet)(u32 mode);
typedef u32 (*ToggleModeGet)(void);
typedef void (*ToggleModeSet)(u32 enabled);

volatile u32 practice_settings_ultimate_jutsu_values[
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2u
] __attribute__((section(".bss.practice_settings_ultimate_jutsu_values")));
volatile u32 practice_settings_active_page_index
    __attribute__((section(".bss.practice_settings_active_page_index")));
volatile SettingsMenuActivePage practice_settings_active_page
    __attribute__((section(".bss.practice_settings_active_page")));
volatile s32 practice_settings_chakra_staged
    __attribute__((section(".bss.practice_settings_chakra_staged")));
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

static u32 practice_settings_is_mod(void *controller)
{
    return controller != (void *)0 && (u32)controller == mod_settings_child;
}

static const PracticeSettingsSchema *practice_settings_schema_for(
    void *controller
)
{
    return practice_settings_is_mod(controller) != 0u
        ? &mod_settings_schema
        : &practice_settings_schema;
}

static const SettingsMenuPage *practice_settings_page(
    void *controller,
    u32 index
)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );

    return settings_menu_page(
        (const SettingsMenuPage *)schema->pages_reference,
        schema->page_count,
        index
    );
}

static const PracticeSettingsRow *practice_settings_model_row(
    void *controller,
    u32 index
)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );

    if (index >= schema->row_count) {
        return (const PracticeSettingsRow *)0;
    }
    return &((const PracticeSettingsRow *)
        schema->rows_reference)[index];
}

static const PracticeSettingsRow *practice_settings_row(
    void *controller,
    s32 index
)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    s32 model_index = settings_menu_model_index(
        &practice_settings_active_page,
        index,
        schema->row_count
    );

    if (model_index < 0) {
        return (const PracticeSettingsRow *)0;
    }
    return practice_settings_model_row(controller, (u32)model_index);
}

static const PracticeSettingsRow *practice_settings_row_for_id(
    void *controller,
    u32 id
)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    u32 index;

    for (index = 0u; index < schema->row_count; ++index) {
        const PracticeSettingsRow *row = practice_settings_model_row(
            controller,
            index
        );

        if (row != (const PracticeSettingsRow *)0 && row->id == id) {
            return row;
        }
    }
    return (const PracticeSettingsRow *)0;
}

static u32 practice_settings_reference(u32 reference, u32 indirect)
{
    if (indirect == 0u) {
        return reference;
    }
    return *(volatile u32 *)reference;
}

static void practice_settings_initialize_tables(void *controller)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    u32 index;

    settings_menu_initialize_open_values();
    for (
        index = 0u;
        index < practice_settings_active_page.row_count;
        ++index
    ) {
        const PracticeSettingsRow *row = practice_settings_row(
            controller,
            (s32)index
        );

        practice_settings_active_labels[index] = practice_settings_reference(
            row->label_reference,
            row->flags & ROW_FLAG_LABEL_SLOT
        );
        if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
            practice_settings_active_value_tables[index] =
                (u32)settings_menu_open_values;
        } else if ((row->flags & ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) != 0u) {
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
                schema->ultimate_jutsu_no_contest_label;
            practice_settings_ultimate_jutsu_values[7] =
                schema->ultimate_jutsu_no_hud_label;
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

static void practice_settings_select_page(
    void *controller,
    u32 page_index,
    u32 selected_row
)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    const SettingsMenuPage *page = practice_settings_page(
        controller,
        page_index
    );
    u32 active_selected = selected_row;

    if (
        settings_menu_select_page(
            (const SettingsMenuPage *)schema->pages_reference,
            schema->page_count,
            schema->row_count,
            page_index,
            selected_row,
            &practice_settings_active_page_index,
            &practice_settings_active_page,
            &active_selected
        ) == 0
    ) {
        return;
    }
    *(volatile u32 *)((u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET) =
        active_selected;
    *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_REPEAT_COUNTDOWN_OFFSET
    ) = 0;
    settings_menu_initialize_window(controller, &practice_settings_active_page, active_selected);
    practice_settings_initialize_tables(controller);
}

static void practice_settings_reset_help(void *controller)
{
    NativeHelpReset reset_help =
        (NativeHelpReset)NATIVE_HELP_RESET_ADDRESS;

    reset_help(*(void * volatile *)(
        (u8 *)controller + CONTROLLER_HELP_OBJECT_OFFSET
    ));
    practice_settings_update_help(controller);
}

static void practice_settings_recompose_backing(void *controller)
{
    practice_settings_prepare_backing_and_compose(
        *(void * volatile *)(
            (u8 *)controller + CONTROLLER_BACKING_OBJECT_OFFSET
        )
    );
}

static s32 practice_settings_status(void *controller)
{
    const PracticeSettingsRow *row = practice_settings_row_for_id(
        controller,
        ROW_ID_STATUS
    );

    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    return *(volatile s32 *)(
        (u8 *)controller + row->local_offset
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_get_max_value")
s32 practice_settings_get_max_value(void *controller, s32 index)
{
    const PracticeSettingsRow *row = practice_settings_row(controller, index);
    void *manager;
    s32 maximum;

    (void)controller;
    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return SETTINGS_MENU_SUBMENU_MAX_VALUE;
    }
    if (row->option_count == 0u) {
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

static s32 practice_settings_get_row_value(
    void *controller,
    const PracticeSettingsRow *row
)
{
    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return 0;
    }
    if (row->runtime_option != (volatile SettingsMenuOption *)0) {
        return (s32)row->runtime_option->staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_CHAKRA) != 0u) {
        return practice_settings_chakra_staged;
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

PRACTICE_SETTINGS_SECTION(".text.practice_settings_get_value")
s32 practice_settings_get_value(void *controller, s32 index)
{
    return practice_settings_get_row_value(
        controller,
        practice_settings_row(controller, index)
    );
}

static void practice_settings_set_row_value(
    void *controller,
    const PracticeSettingsRow *row,
    s32 value
)
{
    if (
        row == (const PracticeSettingsRow *)0 ||
        (row->flags & ROW_FLAG_SUBMENU) != 0u
    ) {
        return;
    }
    if (row->runtime_option != (volatile SettingsMenuOption *)0) {
        row->runtime_option->staged = (u32)value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_CHAKRA) != 0u) {
        practice_settings_chakra_staged = value;
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

static void practice_settings_set_value(
    void *controller,
    s32 index,
    s32 value
)
{
    practice_settings_set_row_value(
        controller,
        practice_settings_row(controller, index),
        value
    );
}

static void practice_settings_stage_runtime_mode(
    void *controller,
    u32 row_id,
    u32 getter_address
)
{
    const PracticeSettingsRow *row;

    if (getter_address == 0u) {
        return;
    }
    row = practice_settings_row_for_id(controller, row_id);
    if (row != (const PracticeSettingsRow *)0) {
        practice_settings_set_row_value(
            controller,
            row,
            (s32)((ToggleModeGet)getter_address)()
        );
    }
}

static void practice_settings_runtime_options(void *controller, u32 commit)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    u32 index;
    for (index = 0u; index < schema->row_count; ++index) {
        volatile SettingsMenuOption *option =
            practice_settings_model_row(controller, index)->runtime_option;
        if (option == (volatile SettingsMenuOption *)0) {
            continue;
        }
        if (commit != 0u) {
            option->set(option->argument, option->staged);
        } else {
            option->staged = option->get(option->argument);
        }
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_snapshot")
void practice_settings_snapshot(void *controller)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    NativeControllerCall native_snapshot =
        (NativeControllerCall)NATIVE_SNAPSHOT_ADDRESS;

    if (practice_settings_is_mod(controller) == 0u) {
        native_snapshot(controller);
    }
    practice_settings_runtime_options(controller, 0u);
    practice_settings_select_page(controller, 0u, 0u);
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_CHAKRA,
        (u32)chakra_mode_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUBSTITUTION,
        schema->substitution_mode_get
    );
    if (schema->ultimate_jutsu_mode_get != 0u) {
        const PracticeSettingsRow *row = practice_settings_row_for_id(
            controller,
            ROW_ID_ULTIMATE_JUTSU
        );
        u32 mode = (
            (UltimateJutsuModeGet)
                schema->ultimate_jutsu_mode_get
        )();

        if (row != (const PracticeSettingsRow *)0) {
            practice_settings_set_row_value(controller, row, (s32)mode);
        }
    }
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SHADOWBLUR,
        schema->shadowblur_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_EXTRA_HIT,
        schema->extra_hit_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUB_ACTIVE_FRAMES,
        schema->sub_active_frames_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_XDASH_CHAKRA_COST,
        schema->xdash_chakra_cost_option_get
    );
    practice_settings_stage_runtime_mode(
        controller,
        ROW_ID_SUPPORT,
        schema->support_get
    );
}

static void practice_settings_commit_runtime_mode(
    void *controller,
    u32 row_id,
    u32 setter_address
)
{
    const PracticeSettingsRow *row = practice_settings_row_for_id(
        controller,
        row_id
    );

    if (row != (const PracticeSettingsRow *)0 && setter_address != 0u) {
        ((ToggleModeSet)setter_address)(
            (u32)practice_settings_get_row_value(controller, row)
        );
    }
}

static void practice_settings_commit_native_setting(
    void *controller,
    u32 row_id
)
{
    const PracticeSettingsRow *row = practice_settings_row_for_id(
        controller,
        row_id
    );

    if (row != (const PracticeSettingsRow *)0) {
        save_native_setting_set(
            0x200u | row_id,
            (u32)practice_settings_get_row_value(controller, row)
        );
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_apply")
void practice_settings_apply(void *controller)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    NativeControllerCall native_apply =
        (NativeControllerCall)NATIVE_APPLY_ADDRESS;

    if (practice_settings_is_mod(controller) == 0u) {
        native_apply(controller);
        practice_settings_commit_native_setting(controller, ROW_ID_HEALTH);
        practice_settings_commit_native_setting(controller, ROW_ID_COMMANDS);
        practice_settings_commit_native_setting(controller, ROW_ID_DAMAGE);
        practice_settings_commit_native_setting(controller, ROW_ID_STATUS);
        practice_settings_commit_native_setting(controller, ROW_ID_STRENGTH);
        practice_settings_commit_native_setting(controller, ROW_ID_ATTACK);
        practice_settings_commit_native_setting(controller, ROW_ID_GUARD);
        practice_settings_commit_native_setting(controller, ROW_ID_MOVE);
        practice_settings_commit_native_setting(
            controller,
            ROW_ID_SUBSTITUTION_JUTSU
        );
        practice_settings_commit_native_setting(
            controller,
            ROW_ID_LINKED_ATTACK
        );
        practice_settings_commit_native_setting(
            controller,
            ROW_ID_EXTRA_HIT_COUNTER
        );
    }
    practice_settings_runtime_options(controller, 1u);
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_CHAKRA,
        (u32)chakra_mode_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUBSTITUTION,
        schema->substitution_mode_set
    );
    if (
        schema->ultimate_jutsu_mode_set != 0u &&
        practice_settings_row_for_id(controller, ROW_ID_ULTIMATE_JUTSU) !=
            (const PracticeSettingsRow *)0
    ) {
        ((UltimateJutsuModeSet)
            schema->ultimate_jutsu_mode_set)(
                (u32)practice_settings_ultimate_jutsu_staged
            );
    }
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SHADOWBLUR,
        schema->shadowblur_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_EXTRA_HIT,
        schema->extra_hit_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUB_ACTIVE_FRAMES,
        schema->sub_active_frames_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_XDASH_CHAKRA_COST,
        schema->xdash_chakra_cost_option_set
    );
    practice_settings_commit_runtime_mode(
        controller,
        ROW_ID_SUPPORT,
        schema->support_set
    );
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_defaults")
void practice_settings_defaults(void *controller)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    NativeControllerCall native_defaults =
        (NativeControllerCall)NATIVE_DEFAULTS_ADDRESS;
    u32 index;

    if (practice_settings_is_mod(controller) == 0u) {
        native_defaults(controller);
    }
    for (index = 0u; index < schema->row_count; ++index) {
        const PracticeSettingsRow *row = practice_settings_model_row(
            controller,
            index
        );

        practice_settings_set_row_value(
            controller,
            row,
            (s32)row->default_value
        );
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_confirm")
void practice_settings_confirm(void *controller)
{
    practice_settings_apply(controller);
}

static s32 practice_settings_open_submenu(
    void *controller,
    const PracticeSettingsRow *row
)
{
    u32 child;
    if (row == (const PracticeSettingsRow *)0) {
        return 0;
    }
    child = settings_menu_value_page(
        row->value_pages, row->option_count,
        (u32)practice_settings_get_row_value(controller, row)
    );
    if (practice_settings_page(controller, child) ==
        (const SettingsMenuPage *)0) {
        return 0;
    }
    *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_PHASE_OFFSET
    ) = 2u;
    practice_settings_select_page(
        controller,
        child,
        0u
    );
    practice_settings_recompose_backing(controller);
    practice_settings_reset_help(controller);
    return 1;
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_cancel")
void practice_settings_cancel(void *controller)
{
    NativeSound play_sound = (NativeSound)NATIVE_SOUND_ADDRESS;
    const SettingsMenuPage *page = practice_settings_page(
        controller,
        practice_settings_active_page_index
    );

    if (
        practice_settings_active_page_index != 0u &&
        page != (const SettingsMenuPage *)0
    ) {
        practice_settings_select_page(
            controller,
            page->parent_page,
            page->parent_row
        );
        practice_settings_recompose_backing(controller);
        practice_settings_reset_help(controller);
        play_sound(0x35u);
    } else {
        *(volatile u32 *)(
            (u8 *)controller + CONTROLLER_PHASE_OFFSET
        ) = 1u;
        play_sound(0x33u);
    }
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_row_enabled")
s32 practice_settings_row_enabled(void *controller, s32 index)
{
    const PracticeSettingsRow *row = practice_settings_row(controller, index);
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
    s32 row_count = (s32)practice_settings_active_page.row_count;

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
    u32 new_input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_NEW_INPUT_OFFSET
    );
    const PracticeSettingsRow *row = practice_settings_row(controller, index);
    s32 value;
    s32 maximum;

    if (practice_settings_row_enabled(controller, index) == 0) {
        return 0;
    }
    if ((new_input & SETTINGS_MENU_INPUT_OPEN_SUBMENU) != 0u &&
        practice_settings_open_submenu(controller, row) != 0) {
        return 1;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
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

PRACTICE_SETTINGS_SECTION(
    ".text.practice_settings_prepare_backing_and_compose"
)
void practice_settings_prepare_backing_and_compose(void *backing)
{
    settings_menu_prepare_practice_backing(
        backing,
        practice_settings_active_page.primary_row_count,
        practice_settings_active_page.secondary_row_count
    );
}

static u32 practice_settings_presentation_label(s32 row)
{
    return practice_settings_active_labels[row];
}

static u32 practice_settings_presentation_values(s32 row)
{
    return practice_settings_active_value_tables[row];
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_draw_content")
void practice_settings_draw_content(void *controller)
{
    SettingsMenuPresentation view;
    view.page = &practice_settings_active_page;
    view.owner = controller;
    view.label = practice_settings_presentation_label;
    view.values = practice_settings_presentation_values;
    view.value = practice_settings_get_value;
    view.maximum = practice_settings_get_max_value;
    view.enabled = practice_settings_row_enabled;
    settings_menu_draw_content(controller, &view);
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_update_window")
void practice_settings_update_window(void *controller)
{
    settings_menu_update_window(controller, &practice_settings_active_page);
}

PRACTICE_SETTINGS_SECTION(".text.practice_settings_update_help")
void practice_settings_update_help(void *controller)
{
    const PracticeSettingsSchema *schema = practice_settings_schema_for(
        controller
    );
    NativeHelpSet set_help = (NativeHelpSet)schema->help_set;
    s32 index = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    const PracticeSettingsRow *row = practice_settings_row(controller, index);
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
