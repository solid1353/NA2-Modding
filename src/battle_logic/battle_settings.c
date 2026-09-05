/* Paged Battle Settings row map over the native controller and renderer. */

#include "../settings/menu_pages.h"

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define BATTLE_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define BATTLE_SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define BATTLE_SETTINGS_VISIBLE_ROWS 7u
#define BATTLE_SETTINGS_HANDICAP_VISIBLE_ROWS 6u
#define BATTLE_SETTINGS_WINDOW_MARGIN_ROWS 2
#define BATTLE_SETTINGS_ROW_STEP 28.0f

#define MANAGER_POINTER_ADDRESS 0x00607600u
#define CONTROLLER_HELP_OBJECT_OFFSET 0x18u
#define CONTROLLER_PHASE_OFFSET 0x58u
#define CONTROLLER_SELECTED_ROW_OFFSET 0x48u
#define CONTROLLER_REPEAT_COUNTDOWN_OFFSET 0x4Au
#define CONTROLLER_NEW_INPUT_OFFSET 0x60u
#define CONTROLLER_EFFECTIVE_INPUT_OFFSET 0x64u

#define INPUT_PREVIOUS_ROW 0x1000u
#define INPUT_NEXT_ROW 0x4000u
#define INPUT_NEXT_VALUE 0x2000u
#define INPUT_PREVIOUS_VALUE 0x8000u

#define NATIVE_SNAPSHOT_ADDRESS 0x0087F870u
#define NATIVE_SOUND_ADDRESS 0x001D7E20u
#define NATIVE_PROFILE_FLAG_ADDRESS 0x001F7780u
#define NATIVE_WINDOW_UPDATE_ADDRESS 0x0037D9C0u
#define NATIVE_HELP_RESET_ADDRESS 0x0037EEE0u
#define NATIVE_HELP_SET_ADDRESS 0x0037F760u
#define NATIVE_ROWS_DRAW_ADDRESS 0x008801E0u
#define NATIVE_CURSOR_DRAW_ADDRESS 0x008804F0u
#define NATIVE_BACKING_DRAW_ADDRESS 0x001BB790u
#define NATIVE_SPRITE_DRAW_ADDRESS 0x00190F40u
#define NATIVE_RESOURCE_LOAD_ADDRESS 0x0037E1A0u
#define NATIVE_ANIMATION_CREATE_ADDRESS 0x0037D5B0u
#define NATIVE_ANIMATION_DESTROY_ADDRESS 0x001B7570u
#define NATIVE_SPRITE_CONTEXT_DESTROY_ADDRESS 0x001CBDF0u
#define NATIVE_ARCHIVE_RELEASE_ADDRESS 0x001A9790u
#define NATIVE_CONTROLLER_FREE_ADDRESS 0x00117000u
#define NATIVE_SPRITE_CONTEXT_CREATE_ADDRESS 0x0037B670u
#define NATIVE_SPRITE_UPDATE_ADDRESS 0x001CC070u

#define PROFILE_ULTIMATE_DIFFICULTY_SLOT 0x6Au
#define HANDICAP_ROW_ID 5u
#define HANDICAP_NATIVE_VISIBLE_SLOT 5
#define HANDICAP_NATIVE_VALUE_Y 257.0f

#define BACKING_RECORDS_POINTER_OFFSET 0xFCu
#define BACKING_RECORD_COUNT 6u
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
#define ROW_FLAG_SUBMENU SETTINGS_MENU_ROW_FLAG_SUBMENU
#define ROW_FLAG_CUSTOM_CHAKRA 0x8000u

#define ULTIMATE_JUTSU_NATIVE_MODE_COUNT 6u
#define ULTIMATE_JUTSU_NATIVE_DEFAULT 2u

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
typedef void (*NativeHelpSet)(
    float scale,
    void *help_object,
    const u8 *text,
    s32 style,
    s32 argument
);
typedef void (*NativeHelpReset)(void *help_object);
typedef void (*NativeBackingDraw)(void *backing);
typedef void (*NativeSpriteDraw)(float alpha, void *object);
typedef void *(*NativeResourceLoad)(const u8 *path, volatile u8 *loaded);
typedef void *(*NativeAnimationCreate)(void *archive, const u8 *name);
typedef void *(*NativeSpriteContextCreate)(
    void *archive,
    const u8 *texture_name,
    s32 capacity,
    s32 enabled,
    void *render_context
);
typedef void (*NativeDestroy)(void *object, u32 release_memory);

typedef struct BattleSettingsRow {
    u32 id;
    u32 local_offset;
    u32 label_reference;
    u32 help_reference;
    u32 values_reference;
    u32 option_count;
    u32 default_value;
    u32 flags;
    const u32 *value_pages;
    volatile SettingsMenuOption *runtime_option;
} BattleSettingsRow;

typedef struct BattleSettingsSchema {
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
} BattleSettingsSchema;

extern const BattleSettingsSchema battle_settings_schema;
extern volatile u32 battle_settings_active_help[];
extern u32 chakra_mode_get(void);
extern void chakra_mode_set(u32 mode);
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
    ) = "Choose the total input window. Default uses vanilla attack timing.";

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
    ) = "Nerfed: full gauge, immediate attack. Normal or Unlimited: standard support.";

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
    ) = "Enable Extra Hit, disable it, or charge chakra for attempting it.";

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
volatile u32 battle_settings_active_value_tables[BATTLE_SETTINGS_VISIBLE_ROWS]
    __attribute__((section(".bss.battle_settings_active_value_tables")));
volatile u32 battle_settings_ultimate_jutsu_values[
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2u
] __attribute__((section(".bss.battle_settings_ultimate_jutsu_values")));
volatile u32 battle_settings_handicap_values[11]
    __attribute__((section(".bss.battle_settings_handicap_values")));
volatile u32 battle_settings_active_page_index
    __attribute__((section(".bss.battle_settings_active_page_index")));
volatile SettingsMenuActivePage battle_settings_active_page
    __attribute__((section(".bss.battle_settings_active_page")));
volatile s32 battle_settings_chakra_staged
    __attribute__((section(".bss.battle_settings_chakra_staged")));
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
volatile u32 battle_settings_visible_count
    __attribute__((section(".bss.battle_settings_visible_count")));
volatile float battle_settings_handicap_value_y
    __attribute__((section(".bss.battle_settings_handicap_value_y")));
void * volatile battle_settings_practice_archive
    __attribute__((section(".bss.battle_settings_practice_archive")));
volatile u8 battle_settings_practice_archive_owned
    __attribute__((section(".bss.battle_settings_practice_archive_owned")));
void * volatile battle_settings_practice_backing
    __attribute__((section(".bss.battle_settings_practice_backing")));
void * volatile battle_settings_practice_arrows
    __attribute__((section(".bss.battle_settings_practice_arrows")));

/* Native Practice presentation fields; storage remains in the Battle controller. */
u8 battle_settings_presentation_controller[0xB8]
    __attribute__((section(".bss.battle_settings_presentation_controller"), aligned(16)));
void *battle_settings_content_context
    __attribute__((section(".bss.battle_settings_content_context")));
void *battle_settings_arrow_context
    __attribute__((section(".bss.battle_settings_arrow_context")));
void *battle_settings_practice_cursor
    __attribute__((section(".bss.battle_settings_practice_cursor")));
static const u8 battle_settings_practice_cursor_name[]
    BATTLE_SETTINGS_USED_SECTION(".rodata.battle_settings_practice_cursor_name") = "ANM_carsol01_a";

static void *battle_settings_create_content_context(u32 priority)
{
    u8 *context = ((void *(*)(u32))0x00117150u)(0x40u);
    if (context == (u8 *)0) return (void *)0;
    ((void (*)(void *))0x00110340u)(context + 8u);
    *(u32 *)(context + 0x28u) = 0u;
    *(u32 *)(context + 0x2Cu) = 0u;
    ((void (*)(void *,u32,void *))0x0010A1D0u)(context, priority, (void *)0);
    ((void (*)(float,float,float,float,void *))0x0037DAA0u)(0.0f,70.0f,512.0f,210.0f,context);
    return context;
}

static const u8 battle_settings_practice_archive_path[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_practice_archive_path"
    ) = "prac.ccs";

static const u8 battle_settings_practice_backing_name[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_practice_backing_name"
    ) = "ANM_prac_cel";

static const u8 battle_settings_practice_texture_name[]
    BATTLE_SETTINGS_USED_SECTION(
        ".rodata.battle_settings_practice_texture_name"
    ) = "TEX_prac_t01";

static void battle_settings_release_style_resources(void)
{
    NativeDestroy destroy_animation =
        (NativeDestroy)NATIVE_ANIMATION_DESTROY_ADDRESS;
    NativeDestroy destroy_sprite_context =
        (NativeDestroy)NATIVE_SPRITE_CONTEXT_DESTROY_ADDRESS;
    NativeDestroy release_archive =
        (NativeDestroy)NATIVE_ARCHIVE_RELEASE_ADDRESS;

    if (battle_settings_practice_arrows != (void *)0) {
        destroy_sprite_context(
            (void *)battle_settings_practice_arrows,
            1u
        );
        battle_settings_practice_arrows = (void *)0;
    }
    if (battle_settings_practice_cursor != (void *)0) {
        destroy_animation(battle_settings_practice_cursor, 1u);
        battle_settings_practice_cursor = (void *)0;
    }
    if (battle_settings_arrow_context != (void *)0) {
        ((NativeDestroy)0x0010A0F0u)(battle_settings_arrow_context, 1u);
        battle_settings_arrow_context = (void *)0;
    }
    if (battle_settings_content_context != (void *)0) {
        ((NativeDestroy)0x0010A0F0u)(battle_settings_content_context, 1u);
        battle_settings_content_context = (void *)0;
    }
    if (battle_settings_practice_backing != (void *)0) {
        destroy_animation(
            (void *)battle_settings_practice_backing,
            1u
        );
        battle_settings_practice_backing = (void *)0;
    }
    if (
        battle_settings_practice_archive_owned != 0u &&
        battle_settings_practice_archive != (void *)0
    ) {
        release_archive(
            (void *)battle_settings_practice_archive,
            1u
        );
    }
    battle_settings_practice_archive = (void *)0;
    battle_settings_practice_archive_owned = 0u;
}

static void battle_settings_initialize_style_resources(void *controller)
{
    NativeResourceLoad load_resource =
        (NativeResourceLoad)NATIVE_RESOURCE_LOAD_ADDRESS;
    NativeAnimationCreate create_animation =
        (NativeAnimationCreate)NATIVE_ANIMATION_CREATE_ADDRESS;
    NativeSpriteContextCreate create_sprite_context =
        (NativeSpriteContextCreate)NATIVE_SPRITE_CONTEXT_CREATE_ADDRESS;

    if (
        battle_settings_practice_backing != (void *)0 &&
        battle_settings_practice_arrows != (void *)0 &&
        battle_settings_practice_cursor != (void *)0
    ) {
        return;
    }
    if (battle_settings_practice_archive == (void *)0) {
        battle_settings_practice_archive_owned = 0u;
        battle_settings_practice_archive = load_resource(
            battle_settings_practice_archive_path,
            &battle_settings_practice_archive_owned
        );
    }
    if (battle_settings_practice_archive == (void *)0) {
        return;
    }
    if (battle_settings_content_context == (void *)0)
        battle_settings_content_context = battle_settings_create_content_context(0xE8u);
    if (battle_settings_arrow_context == (void *)0)
        battle_settings_arrow_context = battle_settings_create_content_context(0xE9u);
    if (battle_settings_practice_cursor == (void *)0)
        battle_settings_practice_cursor = create_animation(
            (void *)battle_settings_practice_archive, battle_settings_practice_cursor_name);
    if (battle_settings_practice_backing == (void *)0) {
        battle_settings_practice_backing = create_animation(
            (void *)battle_settings_practice_archive,
            battle_settings_practice_backing_name
        );
    }
    if (battle_settings_practice_backing == (void *)0) {
        battle_settings_release_style_resources();
        return;
    }
    if (
        battle_settings_practice_arrows == (void *)0 &&
        controller != (void *)0
    ) {
        battle_settings_practice_arrows = create_sprite_context(
            (void *)battle_settings_practice_archive,
            battle_settings_practice_texture_name,
            10,
            1,
            battle_settings_arrow_context
        );
    }
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_free_bridge")
void battle_settings_free_bridge(void *controller)
{
    battle_settings_release_style_resources();
    ((NativeControllerCall)NATIVE_CONTROLLER_FREE_ADDRESS)(controller);
}

static const SettingsMenuPage *battle_settings_page(u32 page_index)
{
    return settings_menu_page(
        (const SettingsMenuPage *)battle_settings_schema.pages_reference,
        battle_settings_schema.page_count,
        page_index
    );
}

static const BattleSettingsRow *battle_settings_model_row(u32 model_index)
{
    if (model_index >= battle_settings_schema.row_count) {
        return (const BattleSettingsRow *)0;
    }
    return &((const BattleSettingsRow *)
        battle_settings_schema.rows_reference)[model_index];
}

static const BattleSettingsRow *battle_settings_row(s32 page_index)
{
    s32 model_index = settings_menu_model_index(
        &battle_settings_active_page,
        page_index,
        battle_settings_schema.row_count
    );

    if (model_index < 0) {
        return (const BattleSettingsRow *)0;
    }
    return battle_settings_model_row((u32)model_index);
}

static const BattleSettingsRow *battle_settings_row_with_flag(u32 flag)
{
    u32 index;

    for (index = 0u; index < battle_settings_schema.row_count; ++index) {
        const BattleSettingsRow *row = battle_settings_model_row(index);

        if (
            row != (const BattleSettingsRow *)0 &&
            (row->flags & flag) != 0u
        ) {
            return row;
        }
    }
    return (const BattleSettingsRow *)0;
}

static u32 battle_settings_visible_capacity(void)
{
    u32 index;

    for (index = 0u; index < battle_settings_active_page.row_count; ++index) {
        const BattleSettingsRow *row = battle_settings_row((s32)index);

        if (
            row != (const BattleSettingsRow *)0 &&
            (row->flags & ROW_FLAG_HANDICAP) != 0u
        ) {
            return BATTLE_SETTINGS_HANDICAP_VISIBLE_ROWS;
        }
    }
    return BATTLE_SETTINGS_VISIBLE_ROWS;
}

static u32 battle_settings_current_visible_count(void)
{
    s32 remaining = (s32)battle_settings_active_page.row_count -
        battle_settings_window_start;
    u32 capacity = battle_settings_visible_capacity();

    if (remaining <= 0) {
        return 0u;
    }
    return (u32)remaining < capacity ? (u32)remaining : capacity;
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
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return (u32)settings_menu_open_values;
    }
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

static void battle_settings_initialize_ultimate_jutsu_values(void)
{
    const BattleSettingsRow *row = battle_settings_row_with_flag(
        ROW_FLAG_CUSTOM_ULTIMATE_JUTSU
    );
    const u32 *native_values;
    u32 value;

    if (row == (const BattleSettingsRow *)0) {
        return;
    }
    native_values = (const u32 *)battle_settings_reference(
        row->values_reference,
        row->flags & ROW_FLAG_VALUES_SLOT
    );
    for (value = 0u; value < ULTIMATE_JUTSU_NATIVE_MODE_COUNT; ++value) {
        battle_settings_ultimate_jutsu_values[value] = native_values[value];
    }
    battle_settings_ultimate_jutsu_values[6] =
        battle_settings_schema.ultimate_jutsu_no_contest_label;
    battle_settings_ultimate_jutsu_values[7] =
        battle_settings_schema.ultimate_jutsu_no_hud_label;
}

static void battle_settings_refresh_visible_tables(void)
{
    s32 handicap_slot = -1;
    u32 slot;

    battle_settings_visible_count = battle_settings_current_visible_count();
    for (slot = 0u; slot < BATTLE_SETTINGS_VISIBLE_ROWS; ++slot) {
        s32 index = battle_settings_window_start + (s32)slot;
        const BattleSettingsRow *row = battle_settings_row(index);

        if (
            slot >= battle_settings_visible_count ||
            row == (const BattleSettingsRow *)0
        ) {
            battle_settings_active_labels[slot] = 0u;
            battle_settings_active_value_tables[slot] = 0u;
            continue;
        }
        if ((row->flags & ROW_FLAG_HANDICAP) != 0u) {
            handicap_slot = (s32)slot;
        }
        battle_settings_active_labels[slot] = battle_settings_reference(
            row->label_reference,
            row->flags & ROW_FLAG_LABEL_SLOT
        );
        battle_settings_active_value_tables[slot] =
            battle_settings_value_table(row);
    }
    battle_settings_handicap_value_y = handicap_slot < 0
        ? HANDICAP_NATIVE_VALUE_Y
        : HANDICAP_NATIVE_VALUE_Y +
            BATTLE_SETTINGS_ROW_STEP *
                (float)(handicap_slot - HANDICAP_NATIVE_VISIBLE_SLOT);
}

static void battle_settings_initialize_tables(void)
{
    u32 index;

    settings_menu_initialize_open_values();
    battle_settings_initialize_handicap_values();
    battle_settings_initialize_ultimate_jutsu_values();
    for (index = 0u; index < battle_settings_active_page.row_count; ++index) {
        const BattleSettingsRow *row = battle_settings_row((s32)index);

        battle_settings_active_help[index] = battle_settings_reference(
            row->help_reference,
            row->flags & ROW_FLAG_HELP_SLOT
        );
    }
    if (battle_settings_active_page_index == 0u) {
        battle_settings_refresh_visible_tables();
    }
}

static s32 battle_settings_select_page(
    void *controller,
    u32 page_index,
    u32 selected_row
)
{
    u32 active_selected = selected_row;

    if (
        settings_menu_select_page(
            (const SettingsMenuPage *)battle_settings_schema.pages_reference,
            battle_settings_schema.page_count,
            battle_settings_schema.row_count,
            page_index,
            selected_row,
            &battle_settings_active_page_index,
            &battle_settings_active_page,
            &active_selected
        ) == 0
    ) {
        return 0;
    }
    *(volatile short *)((u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET) =
        (short)active_selected;
    *(volatile short *)(
        (u8 *)controller + CONTROLLER_REPEAT_COUNTDOWN_OFFSET
    ) = 0;
    battle_settings_window_start = 0;
    *(s32 *)(battle_settings_presentation_controller + 0x3Cu) = (s32)active_selected;
    settings_menu_initialize_window(battle_settings_presentation_controller,
        &battle_settings_active_page, active_selected);
    battle_settings_initialize_tables();
    return 1;
}

static void battle_settings_update_help(void *controller)
{
    NativeHelpSet set_help = (NativeHelpSet)NATIVE_HELP_SET_ADDRESS;
    s32 index = *(volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    const BattleSettingsRow *row = battle_settings_row(index);

    if (row == (const BattleSettingsRow *)0) {
        return;
    }
    set_help(
        20.0f,
        *(void * volatile *)(
            (u8 *)controller + CONTROLLER_HELP_OBJECT_OFFSET
        ),
        (const u8 *)battle_settings_reference(
            row->help_reference,
            row->flags & ROW_FLAG_HELP_SLOT
        ),
        8,
        0
    );
}

static void battle_settings_reset_help(void *controller)
{
    NativeHelpReset reset_help = (NativeHelpReset)NATIVE_HELP_RESET_ADDRESS;

    reset_help(*(void * volatile *)(
        (u8 *)controller + CONTROLLER_HELP_OBJECT_OFFSET
    ));
    battle_settings_update_help(controller);
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
    if (slot < 0 || (u32)slot >= battle_settings_visible_count) {
        return -1;
    }
    return battle_settings_row_id(battle_settings_window_start + slot);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_use_native_handicap")
s32 battle_settings_use_native_handicap(s32 slot)
{
    return battle_settings_visible_row_id(slot) == (s32)HANDICAP_ROW_ID;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_max_value")
s32 battle_settings_get_max_value(void *controller, s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);
    void *manager;
    s32 maximum;

    (void)controller;
    if (row == (const BattleSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return SETTINGS_MENU_SUBMENU_MAX_VALUE;
    }
    if (row->option_count == 0u) {
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

static s32 battle_settings_get_row_value(
    void *controller,
    const BattleSettingsRow *row
)
{
    if (row == (const BattleSettingsRow *)0) {
        return 0;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return 0;
    }
    if (row->runtime_option != (volatile SettingsMenuOption *)0) {
        return (s32)row->runtime_option->staged;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_CHAKRA) != 0u) {
        return battle_settings_chakra_staged;
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

BATTLE_SETTINGS_SECTION(".text.battle_settings_get_value")
s32 battle_settings_get_value(void *controller, s32 index)
{
    return battle_settings_get_row_value(
        controller,
        battle_settings_row(index)
    );
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

static void battle_settings_set_row_value(
    void *controller,
    const BattleSettingsRow *row,
    s32 value
)
{
    if (
        row == (const BattleSettingsRow *)0 ||
        (row->flags & ROW_FLAG_SUBMENU) != 0u
    ) {
        return;
    }
    if (row->runtime_option != (volatile SettingsMenuOption *)0) {
        row->runtime_option->staged = (u32)value;
        return;
    }
    if ((row->flags & ROW_FLAG_CUSTOM_CHAKRA) != 0u) {
        battle_settings_chakra_staged = value;
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
    const BattleSettingsRow *row;

    if (getter_address == 0u) {
        return;
    }
    row = battle_settings_row_with_flag(flag);
    if (row != (const BattleSettingsRow *)0) {
        battle_settings_set_row_value(
            controller,
            row,
            (s32)((ToggleModeGet)getter_address)()
        );
    }
}

static void battle_settings_runtime_options(u32 commit)
{
    u32 index;
    for (index = 0u; index < battle_settings_schema.row_count; ++index) {
        volatile SettingsMenuOption *option =
            battle_settings_model_row(index)->runtime_option;
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

BATTLE_SETTINGS_SECTION(".text.battle_settings_snapshot")
void battle_settings_snapshot(void *controller)
{
    NativeControllerCall native_snapshot =
        (NativeControllerCall)NATIVE_SNAPSHOT_ADDRESS;

    native_snapshot(controller);
    battle_settings_runtime_options(0u);
    battle_settings_initialize_style_resources(controller);
    battle_settings_active_controller = controller;
    battle_settings_select_page(controller, 0u, 0u);
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_CHAKRA,
        (u32)chakra_mode_get
    );
    battle_settings_stage_runtime_mode(
        controller,
        ROW_FLAG_CUSTOM_SUBSTITUTION,
        battle_settings_schema.substitution_mode_get
    );
    if (battle_settings_schema.ultimate_jutsu_mode_get != 0u) {
        const BattleSettingsRow *row = battle_settings_row_with_flag(
            ROW_FLAG_CUSTOM_ULTIMATE_JUTSU
        );
        u32 mode = (
            (UltimateJutsuModeGet)
                battle_settings_schema.ultimate_jutsu_mode_get
        )();

        if (row != (const BattleSettingsRow *)0) {
            battle_settings_set_row_value(controller, row, (s32)mode);
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
    const BattleSettingsRow *row = battle_settings_row_with_flag(flag);

    if (
        row != (const BattleSettingsRow *)0 &&
        setter_address != 0u &&
        battle_settings_active_controller != (void *)0
    ) {
        ((ToggleModeSet)setter_address)(
            (u32)battle_settings_get_row_value(
                (void *)battle_settings_active_controller,
                row
            )
        );
    }
}

static void battle_settings_commit_runtime_modes(void)
{
    battle_settings_runtime_options(1u);
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_CHAKRA,
        (u32)chakra_mode_set
    );
    battle_settings_commit_runtime_mode(
        ROW_FLAG_CUSTOM_SUBSTITUTION,
        battle_settings_schema.substitution_mode_set
    );
    if (
        battle_settings_schema.ultimate_jutsu_mode_set != 0u &&
        battle_settings_row_with_flag(ROW_FLAG_CUSTOM_ULTIMATE_JUTSU) !=
            (const BattleSettingsRow *)0
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
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_confirm")
s32 battle_settings_confirm(void *controller)
{
    NativeSound play_sound = (NativeSound)NATIVE_SOUND_ADDRESS;

    *(volatile short *)((u8 *)controller + CONTROLLER_PHASE_OFFSET) = 1;
    battle_settings_commit_runtime_modes();
    play_sound(0x34u);
    return 0;
}

static s32 battle_settings_open_submenu(
    void *controller,
    const BattleSettingsRow *row
)
{
    u32 child;
    if (row == (const BattleSettingsRow *)0) {
        return 0;
    }
    child = settings_menu_value_page(
        row->value_pages, row->option_count,
        (u32)battle_settings_get_row_value(controller, row)
    );
    if (battle_settings_page(child) == (const SettingsMenuPage *)0) {
        return 0;
    }
    *(volatile short *)(
        (u8 *)controller + CONTROLLER_PHASE_OFFSET
    ) = 2;
    battle_settings_select_page(controller, child, 0u);
    battle_settings_reset_help(controller);
    return 1;
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_cancel")
void battle_settings_cancel(void *controller)
{
    NativeSound play_sound = (NativeSound)NATIVE_SOUND_ADDRESS;
    const SettingsMenuPage *page = battle_settings_page(
        battle_settings_active_page_index
    );

    if (
        battle_settings_active_page_index != 0u &&
        page != (const SettingsMenuPage *)0
    ) {
        battle_settings_select_page(
            controller,
            page->parent_page,
            page->parent_row
        );
        battle_settings_reset_help(controller);
    } else {
        *(volatile short *)(
            (u8 *)controller + CONTROLLER_PHASE_OFFSET
        ) = 1;
    }
    play_sound(0x33u);
}

BATTLE_SETTINGS_SECTION(".text.battle_settings_defaults_sound")
void battle_settings_defaults_sound(u32 sound_id)
{
    u32 index;

    if (battle_settings_active_controller != (void *)0) {
        for (index = 0u; index < battle_settings_schema.row_count; ++index) {
            const BattleSettingsRow *row = battle_settings_model_row(index);

            battle_settings_set_row_value(
                (void *)battle_settings_active_controller,
                row,
                (s32)row->default_value
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
    s32 row_count = (s32)battle_settings_active_page.row_count;

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
    u32 new_input = *(volatile u32 *)(
        (u8 *)controller + CONTROLLER_NEW_INPUT_OFFSET
    );
    const BattleSettingsRow *row = battle_settings_row(index);
    s32 value;
    s32 maximum;

    if (row == (const BattleSettingsRow *)0) {
        return 0;
    }
    if ((new_input & SETTINGS_MENU_INPUT_OPEN_SUBMENU) != 0u &&
        battle_settings_open_submenu(controller, row) != 0) {
        return 1;
    }
    if ((row->flags & ROW_FLAG_SUBMENU) != 0u) {
        return 0;
    }
    value = battle_settings_get_row_value(controller, row);
    maximum = battle_settings_get_max_value(controller, index);
    if ((input & INPUT_NEXT_VALUE) != 0u && value < maximum) {
        battle_settings_set_row_value(controller, row, value + 1);
        return 1;
    }
    if ((input & INPUT_PREVIOUS_VALUE) != 0u && value > 0) {
        battle_settings_set_row_value(controller, row, value - 1);
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

static volatile u8 *battle_settings_backing_flags(u8 *records, u32 index)
{
    return records +
        index * BACKING_RECORD_SIZE +
        BACKING_RECORD_DRAW_FLAGS_OFFSET;
}

static void battle_settings_set_backing_record(
    u8 *records,
    u32 index,
    u32 draw
)
{
    volatile u8 *flags = battle_settings_backing_flags(records, index);

    if (draw != 0u) {
        *flags |= BACKING_RECORD_DRAW_FLAG;
    } else {
        *flags &= (u8)~BACKING_RECORD_DRAW_FLAG;
    }
}

static s32 battle_settings_visible_handicap_slot(void)
{
    u32 slot;

    for (slot = 0u; slot < battle_settings_visible_count; ++slot) {
        if (battle_settings_use_native_handicap((s32)slot)) {
            return (s32)slot;
        }
    }
    return -1;
}

static u32 battle_settings_visible_row_is_submenu(u32 slot)
{
    const BattleSettingsRow *row = battle_settings_row(
        battle_settings_window_start + (s32)slot
    );

    return row != (const BattleSettingsRow *)0 &&
        (row->flags & ROW_FLAG_SUBMENU) != 0u;
}

static void battle_settings_update_view(void *controller);

BATTLE_SETTINGS_SECTION(".text.battle_settings_draw_backing")
void battle_settings_draw_backing(void *backing)
{
    NativeBackingDraw native_draw =
        (NativeBackingDraw)NATIVE_BACKING_DRAW_ADDRESS;
    NativeSpriteDraw draw_sprite =
        (NativeSpriteDraw)NATIVE_SPRITE_DRAW_ADDRESS;
    u8 *records;
    u8 saved_flags[BACKING_RECORD_COUNT];
    u8 *handicap;
    u8 *last;
    u8 *previous;
    volatile float *handicap_local_y;
    volatile float *handicap_world_y;
    volatile float *last_local_y;
    volatile float *last_world_y;
    float native_handicap_local_y;
    float native_handicap_world_y;
    float native_local_y;
    float native_world_y;
    float local_step;
    float world_step;
    float alpha;
    s32 handicap_slot;
    u32 ordinary_count;
    u32 record;
    u32 row;

    if (backing == (void *)0 || battle_settings_active_page_index != 0u) {
        return;
    }
    if (battle_settings_active_controller != (void *)0) {
        battle_settings_update_view(
            (void *)battle_settings_active_controller
        );
    }
    records = *(u8 **)((u8 *)backing + BACKING_RECORDS_POINTER_OFFSET);
    if (records == (u8 *)0) {
        native_draw(backing);
        return;
    }
    handicap_slot = battle_settings_visible_handicap_slot();
    ordinary_count = handicap_slot < 0
        ? battle_settings_visible_count
        : (u32)handicap_slot;
    handicap = battle_settings_backing_object(
        records,
        BACKING_HANDICAP_RECORD
    );
    last = battle_settings_backing_object(
        records,
        BACKING_LAST_ORDINARY_RECORD
    );
    previous = battle_settings_backing_object(
        records,
        BACKING_LAST_ORDINARY_RECORD - 1u
    );
    if (
        last == (u8 *)0 ||
        previous == (u8 *)0 ||
        (handicap_slot >= 0 && handicap == (u8 *)0)
    ) {
        native_draw(backing);
        return;
    }

    for (record = 0u; record < BACKING_RECORD_COUNT; ++record) {
        saved_flags[record] = *battle_settings_backing_flags(records, record);
    }
    battle_settings_set_backing_record(
        records,
        BACKING_HANDICAP_RECORD,
        handicap_slot >= 0
    );
    for (record = 1u; record < BACKING_RECORD_COUNT; ++record) {
        battle_settings_set_backing_record(
            records,
            record,
            record <= ordinary_count
        );
    }
    for (
        row = 0u;
        row < ordinary_count && row < BACKING_LAST_ORDINARY_RECORD;
        ++row
    ) {
        if (battle_settings_visible_row_is_submenu(row) != 0u) {
            battle_settings_set_backing_record(records, row + 1u, 0u);
        }
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
    if (handicap_slot >= 0) {
        handicap_local_y = (volatile float *)(
            handicap + BACKING_OBJECT_LOCAL_Y_OFFSET
        );
        handicap_world_y = (volatile float *)(
            handicap + BACKING_OBJECT_WORLD_Y_OFFSET
        );
        native_handicap_local_y = *handicap_local_y;
        native_handicap_world_y = *handicap_world_y;
        *handicap_local_y = native_handicap_local_y + local_step *
            (float)(handicap_slot - HANDICAP_NATIVE_VISIBLE_SLOT);
        *handicap_world_y = native_handicap_world_y + world_step *
            (float)(handicap_slot - HANDICAP_NATIVE_VISIBLE_SLOT);
    }

    native_draw(backing);
    alpha = *(volatile float *)(
        (u8 *)backing + BACKING_OBJECT_ALPHA_OFFSET
    );
    for (
        row = 0u;
        row < ordinary_count && row < BACKING_LAST_ORDINARY_RECORD;
        ++row
    ) {
        if (battle_settings_visible_row_is_submenu(row) != 0u) {
            settings_menu_draw_tinted_label(
                alpha,
                battle_settings_backing_object(records, row + 1u),
                SETTINGS_MENU_HEADER_ORANGE_TINT
            );
        }
    }
    for (row = 5u; row < ordinary_count; ++row) {
        *last_local_y = native_local_y + local_step * (float)(row - 4u);
        *last_world_y = native_world_y + world_step * (float)(row - 4u);
        if (battle_settings_visible_row_is_submenu(row) != 0u) {
            settings_menu_draw_tinted_label(
                alpha,
                last,
                SETTINGS_MENU_HEADER_ORANGE_TINT
            );
        } else {
            draw_sprite(alpha, last);
        }
    }
    *last_local_y = native_local_y;
    *last_world_y = native_world_y;
    if (handicap_slot >= 0) {
        *handicap_local_y = native_handicap_local_y;
        *handicap_world_y = native_handicap_world_y;
    }
    for (record = 0u; record < BACKING_RECORD_COUNT; ++record) {
        *battle_settings_backing_flags(records, record) = saved_flags[record];
    }
}

static void battle_settings_update_view(void *controller)
{
    NativeWindowUpdate update =
        (NativeWindowUpdate)NATIVE_WINDOW_UPDATE_ADDRESS;
    s32 selected = *(volatile short *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 row_count = (s32)battle_settings_active_page.row_count;
    s32 visible_capacity = (s32)battle_settings_visible_capacity();
    s32 maximum_start = row_count - visible_capacity;
    s32 start;

    if (maximum_start <= 0) {
        start = 0;
    } else {
        start = update(
            selected,
            battle_settings_window_start,
            visible_capacity,
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

static u32 battle_settings_presentation_label(s32 index)
{
    const BattleSettingsRow *row = battle_settings_row(index);
    return battle_settings_reference(row->label_reference, row->flags & ROW_FLAG_LABEL_SLOT);
}
static u32 battle_settings_presentation_values(s32 index)
{
    return battle_settings_value_table(battle_settings_row(index));
}
static s32 battle_settings_presentation_enabled(void *controller, s32 index)
{
    (void)controller;
    (void)index;
    return 1;
}
static void battle_settings_draw_child(void *controller)
{
    u8 *native = battle_settings_presentation_controller;
    u8 *battle = (u8 *)controller;
    SettingsMenuPresentation view;
    void *contexts[2];
    u32 i;
    float alpha;
    battle_settings_initialize_style_resources(controller);
    if (battle_settings_content_context == (void *)0 ||
        battle_settings_arrow_context == (void *)0 ||
        battle_settings_practice_cursor == (void *)0 ||
        battle_settings_practice_backing == (void *)0 ||
        battle_settings_practice_arrows == (void *)0) return;
    *(void **)(native + 0x10u) = battle_settings_content_context;
    *(void **)(native + 0x14u) = battle_settings_arrow_context;
    *(void **)(native + 0x24u) = (void *)battle_settings_practice_arrows;
    *(void **)(native + 0x2Cu) = (void *)battle_settings_practice_backing;
    *(void **)(native + 0x30u) = battle_settings_practice_cursor;
    *(s32 *)(native + 0x3Cu) = *(short *)(battle + CONTROLLER_SELECTED_ROW_OFFSET);
    *(float *)(native + 0x4Cu) = *(float *)(battle + 0x4Cu);
    *(float *)(native + 0x58u) = *(float *)(battle + 0x50u);
    settings_menu_update_window(native, &battle_settings_active_page);
    contexts[0] = battle_settings_content_context;
    contexts[1] = battle_settings_arrow_context;
    for (i = 0; i < 2u; ++i) {
        ((void (*)(void *,void *,u32))0x0010E220u)(
            *(void **)((u8 *)contexts[i] + 0x3Cu),
            *(void **)(*(u8 **)(battle + 0x24u) + 0x10Cu), 0u);
        ((void (*)(void *,u32))0x00109A10u)(contexts[i], 0u);
    }
    alpha = *(float *)(*(u8 **)(battle + 0x20u) + 0x88u);
    *(float *)((u8 *)battle_settings_practice_backing + 0x88u) = alpha;
    *(float *)((u8 *)battle_settings_practice_cursor + 0x88u) = alpha;
    ((void (*)(void *,u32,u32))0x001BB210u)(battle_settings_practice_cursor,
        *(unsigned short *)((u8 *)battle_settings_practice_cursor + 0x94u), 0u);
    ((NativeControllerCall)0x001BB6F0u)(battle_settings_practice_cursor);
    settings_menu_prepare_practice_backing((void *)battle_settings_practice_backing,
        battle_settings_active_page.primary_row_count,
        battle_settings_active_page.secondary_row_count);
    view.page = &battle_settings_active_page;
    view.owner = controller;
    view.label = battle_settings_presentation_label;
    view.values = battle_settings_presentation_values;
    view.value = battle_settings_get_value;
    view.maximum = battle_settings_get_max_value;
    view.enabled = battle_settings_presentation_enabled;
    view.submenu_rows = 0u;
    settings_menu_draw_content(native, &view);
    ((NativeControllerCall)NATIVE_SPRITE_UPDATE_ADDRESS)((void *)battle_settings_practice_arrows);
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
    if (battle_settings_active_page_index != 0u) {
        battle_settings_draw_child(controller);
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

    if (controller == (void *)0 || battle_settings_active_page_index != 0u) {
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
