/* Shared page selection and common resources for in-game settings menus. */

#include "menu_pages.h"

typedef unsigned char u8;
typedef unsigned short u16;
typedef signed int s32;
typedef unsigned int u32;

#define SETTINGS_MENU_SECTION(name) \
    __attribute__((section(name), noinline))
#define SETTINGS_MENU_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define NATIVE_BACKING_COMPOSE_ADDRESS 0x001BB6F0u
#define NATIVE_BACKING_DRAW_ADDRESS 0x001BB790u
#define NATIVE_SPRITE_DRAW_ADDRESS 0x00190F40u

#define PRACTICE_BACKING_RECORDS_POINTER_OFFSET 0xFCu
#define PRACTICE_BACKING_RECORD_COUNT 18u
#define PRACTICE_BACKING_RECORD_SIZE 0x10u
#define PRACTICE_BACKING_RECORD_OBJECT_POINTER_OFFSET 0x00u
#define PRACTICE_BACKING_RECORD_DRAW_FLAGS_OFFSET 0x0Au
#define PRACTICE_BACKING_RECORD_DRAW_FLAG 0x04u
#define PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET 0x78u
#define PRACTICE_BACKING_RECORD_WORLD_Y_OFFSET 0x38u
#define PRACTICE_BACKING_OBJECT_ALPHA_OFFSET 0x88u
#define PRACTICE_BACKING_PLAYER_FIRST_RECORD 1u
#define PRACTICE_BACKING_PLAYER_REMAINING_FIRST_RECORD 10u
#define PRACTICE_BACKING_PLAYER_REMAINING_CAPACITY 8u
#define PRACTICE_BACKING_PLAYER_CAPACITY 9u
#define PRACTICE_BACKING_PLAYER_MIDDLE_LAST_RECORD 16u
#define PRACTICE_BACKING_PLAYER_TERMINAL_RECORD 17u
#define PRACTICE_BACKING_SECONDARY_FIRST_RECORD 2u
#define PRACTICE_BACKING_SECONDARY_CAPACITY 8u
#define PRACTICE_BACKING_SECONDARY_MIDDLE_LAST_RECORD 8u
#define PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD 9u
#define PRACTICE_BACKING_ROW_STEP 26.88f

#define SPRITE_MODEL_POINTER_OFFSET 0x94u
#define MODEL_PART_COUNT_OFFSET 0x16u
#define MODEL_PART_RECORDS_POINTER_OFFSET 0x08u
#define MODEL_PART_VERTEX_COUNT_OFFSET 0x04u
#define MODEL_PART_COLORS_POINTER_OFFSET 0x1Cu
#define ROW_LABEL_VERTEX_COUNT 18u

typedef void (*NativeBackingCall)(void *backing);
typedef void (*NativeSpriteDraw)(float alpha, void *object);

typedef struct SettingsMenuBackingLayout {
    u32 records;
    u32 objects[PRACTICE_BACKING_RECORD_COUNT];
    float native_local_y[PRACTICE_BACKING_RECORD_COUNT];
} SettingsMenuBackingLayout;

volatile SettingsMenuBackingLayout settings_menu_backing_layout
    __attribute__((section(".bss.settings_menu_backing_layout")));

static const unsigned char settings_open_label[]
    SETTINGS_MENU_USED_SECTION(
        ".rodata.settings_open_label"
    ) = "Open <iconSQUARE>";

volatile unsigned int settings_menu_open_values[1]
    __attribute__((section(".bss.settings_menu_open_values")));

SETTINGS_MENU_SECTION(".text.settings_menu_value_page")
unsigned int settings_menu_value_page(
    const unsigned int *pages, unsigned int count, unsigned int value
)
{
    return pages != (const unsigned int *)0 && value < count
        ? pages[value] : SETTINGS_MENU_NO_PAGE;
}

SETTINGS_MENU_SECTION(".text.settings_menu_page")
const SettingsMenuPage *settings_menu_page(
    const SettingsMenuPage *pages,
    unsigned int page_count,
    unsigned int page_index
)
{
    if (pages == (const SettingsMenuPage *)0 || page_index >= page_count) {
        return (const SettingsMenuPage *)0;
    }
    return &pages[page_index];
}

SETTINGS_MENU_SECTION(".text.settings_menu_select_page")
signed int settings_menu_select_page(
    const SettingsMenuPage *pages,
    unsigned int page_count,
    unsigned int model_row_count,
    unsigned int page_index,
    unsigned int requested_row,
    volatile unsigned int *active_page_index,
    volatile SettingsMenuActivePage *active_page,
    unsigned int *selected_row
)
{
    const SettingsMenuPage *page = settings_menu_page(
        pages,
        page_count,
        page_index
    );

    if (
        page == (const SettingsMenuPage *)0 ||
        page->row_count == 0u ||
        page->row_start > model_row_count ||
        page->row_count > model_row_count - page->row_start ||
        active_page_index == (volatile unsigned int *)0 ||
        active_page == (volatile SettingsMenuActivePage *)0 ||
        selected_row == (unsigned int *)0
    ) {
        return 0;
    }
    *active_page_index = page_index;
    active_page->row_start = page->row_start;
    active_page->row_count = page->row_count;
    active_page->primary_row_count = page->primary_row_count;
    active_page->secondary_row_count = page->secondary_row_count;
    active_page->heading_reference = page->heading_reference;
    *selected_row = requested_row < page->row_count ? requested_row : 0u;
    return 1;
}

SETTINGS_MENU_SECTION(".text.settings_menu_model_index")
signed int settings_menu_model_index(
    const volatile SettingsMenuActivePage *active_page,
    signed int page_row,
    unsigned int model_row_count
)
{
    unsigned int model_index;

    if (
        active_page == (const volatile SettingsMenuActivePage *)0 ||
        page_row < 0 ||
        (unsigned int)page_row >= active_page->row_count
    ) {
        return -1;
    }
    model_index = active_page->row_start + (unsigned int)page_row;
    return model_index < model_row_count ? (signed int)model_index : -1;
}

SETTINGS_MENU_SECTION(".text.settings_menu_initialize_open_values")
void settings_menu_initialize_open_values(void)
{
    settings_menu_open_values[0] = (unsigned int)settings_open_label;
}

static volatile u8 *settings_menu_backing_record_flags(
    u8 *records,
    u32 index
)
{
    return records +
        index * PRACTICE_BACKING_RECORD_SIZE +
        PRACTICE_BACKING_RECORD_DRAW_FLAGS_OFFSET;
}

static void settings_menu_set_backing_record(
    u8 *records,
    u32 index,
    u32 draw
)
{
    volatile u8 *flags = settings_menu_backing_record_flags(records, index);

    if (draw != 0u) {
        *flags |= PRACTICE_BACKING_RECORD_DRAW_FLAG;
    } else {
        *flags &= (u8)~PRACTICE_BACKING_RECORD_DRAW_FLAG;
    }
}

static u8 *settings_menu_backing_record_object(u8 *records, u32 index)
{
    return *(u8 **)(
        records +
        index * PRACTICE_BACKING_RECORD_SIZE +
        PRACTICE_BACKING_RECORD_OBJECT_POINTER_OFFSET
    );
}

static u32 settings_menu_backing_layout_changed(u8 *records)
{
    u32 index;

    if (settings_menu_backing_layout.records != (u32)records) {
        return 1u;
    }
    for (index = 0u; index < PRACTICE_BACKING_RECORD_COUNT; ++index) {
        if (
            settings_menu_backing_layout.objects[index] !=
            (u32)settings_menu_backing_record_object(records, index)
        ) {
            return 1u;
        }
    }
    return 0u;
}

static void settings_menu_capture_backing_layout(u8 *records)
{
    u32 index;

    settings_menu_backing_layout.records = (u32)records;
    for (index = 0u; index < PRACTICE_BACKING_RECORD_COUNT; ++index) {
        u8 *object = settings_menu_backing_record_object(records, index);

        settings_menu_backing_layout.objects[index] = (u32)object;
        settings_menu_backing_layout.native_local_y[index] =
            object == (u8 *)0
                ? 0.0f
                : *(volatile float *)(
                    object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
                );
    }
}

static float settings_menu_player_grid_y(u32 index)
{
    if (index == 0u) {
        return settings_menu_backing_layout.native_local_y[
            PRACTICE_BACKING_PLAYER_FIRST_RECORD
        ];
    }
    if (index < PRACTICE_BACKING_PLAYER_CAPACITY - 1u) {
        return settings_menu_backing_layout.native_local_y[
            PRACTICE_BACKING_PLAYER_REMAINING_FIRST_RECORD + index - 1u
        ];
    }
    return settings_menu_backing_layout.native_local_y[
        PRACTICE_BACKING_PLAYER_MIDDLE_LAST_RECORD
    ] - PRACTICE_BACKING_ROW_STEP *
        (float)(index - (PRACTICE_BACKING_PLAYER_CAPACITY - 2u));
}

static float settings_menu_player_terminal_y(u32 index)
{
    float terminal_phase =
        settings_menu_backing_layout.native_local_y[
            PRACTICE_BACKING_PLAYER_TERMINAL_RECORD
        ] -
        (
            settings_menu_backing_layout.native_local_y[
                PRACTICE_BACKING_PLAYER_MIDDLE_LAST_RECORD
            ] - PRACTICE_BACKING_ROW_STEP
        );

    return settings_menu_player_grid_y(index) + terminal_phase;
}

static float settings_menu_secondary_delta(u32 primary_row_count)
{
    return -PRACTICE_BACKING_ROW_STEP *
        (float)((s32)primary_row_count - (s32)PRACTICE_BACKING_PLAYER_CAPACITY);
}

static float settings_menu_secondary_grid_y(u32 index, float delta)
{
    if (index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u) {
        return settings_menu_backing_layout.native_local_y[
            PRACTICE_BACKING_SECONDARY_FIRST_RECORD + index
        ] + delta;
    }
    return settings_menu_backing_layout.native_local_y[
        PRACTICE_BACKING_SECONDARY_MIDDLE_LAST_RECORD
    ] + delta - PRACTICE_BACKING_ROW_STEP *
        (float)(index - (PRACTICE_BACKING_SECONDARY_CAPACITY - 2u));
}

static float settings_menu_secondary_terminal_y(u32 index, float delta)
{
    float terminal_phase =
        settings_menu_backing_layout.native_local_y[
            PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD
        ] -
        (
            settings_menu_backing_layout.native_local_y[
                PRACTICE_BACKING_SECONDARY_MIDDLE_LAST_RECORD
            ] - PRACTICE_BACKING_ROW_STEP
        );

    return settings_menu_secondary_grid_y(index, delta) + terminal_phase;
}

static void settings_menu_restore_backing_y(u8 *records)
{
    u32 index;

    for (index = 0u; index < PRACTICE_BACKING_RECORD_COUNT; ++index) {
        u8 *object = settings_menu_backing_record_object(records, index);

        if (object != (u8 *)0) {
            *(volatile float *)(
                object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
            ) = settings_menu_backing_layout.native_local_y[index];
        }
    }
}

static void settings_menu_place_backing(
    u8 *records,
    u32 primary_row_count,
    u32 secondary_row_count
)
{
    float secondary_delta = settings_menu_secondary_delta(primary_row_count);
    u8 *object;
    u32 index;

    settings_menu_restore_backing_y(records);
    if (primary_row_count > 1u) {
        object = settings_menu_backing_record_object(
            records,
            PRACTICE_BACKING_PLAYER_TERMINAL_RECORD
        );
        if (object != (u8 *)0) {
            *(volatile float *)(
                object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
            ) = settings_menu_player_terminal_y(primary_row_count - 1u);
        }
    }
    object = settings_menu_backing_record_object(records, 0u);
    if (object != (u8 *)0) {
        *(volatile float *)(object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET) =
            settings_menu_backing_layout.native_local_y[0] + secondary_delta;
    }
    for (index = 0u; index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u; ++index) {
        object = settings_menu_backing_record_object(
            records,
            PRACTICE_BACKING_SECONDARY_FIRST_RECORD + index
        );
        if (object != (u8 *)0) {
            *(volatile float *)(
                object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
            ) = settings_menu_secondary_grid_y(index, secondary_delta);
        }
    }
    if (secondary_row_count > 1u) {
        object = settings_menu_backing_record_object(
            records,
            PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD
        );
        if (object != (u8 *)0) {
            *(volatile float *)(
                object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
            ) = settings_menu_secondary_terminal_y(
                secondary_row_count - 1u,
                secondary_delta
            );
        }
    }

}

static void settings_menu_select_backing_records(
    u8 *records,
    u32 primary_row_count,
    u32 secondary_row_count
)
{
    u32 index;

    settings_menu_set_backing_record(
        records,
        PRACTICE_BACKING_PLAYER_FIRST_RECORD,
        primary_row_count != 0u
    );
    for (index = 0u; index < PRACTICE_BACKING_PLAYER_REMAINING_CAPACITY - 1u; ++index) {
        settings_menu_set_backing_record(
            records,
            PRACTICE_BACKING_PLAYER_REMAINING_FIRST_RECORD + index,
            index + 2u < primary_row_count
        );
    }
    settings_menu_set_backing_record(
        records,
        PRACTICE_BACKING_PLAYER_TERMINAL_RECORD,
        primary_row_count > 1u
    );
    settings_menu_set_backing_record(
        records,
        0u,
        secondary_row_count != 0u
    );
    for (index = 0u; index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u; ++index) {
        settings_menu_set_backing_record(
            records,
            PRACTICE_BACKING_SECONDARY_FIRST_RECORD + index,
            index == 0u
                ? secondary_row_count != 0u
                : index + 1u < secondary_row_count
        );
    }
    settings_menu_set_backing_record(
        records,
        PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD,
        secondary_row_count > 1u
    );
}

SETTINGS_MENU_SECTION(".text.settings_menu_prepare_practice_backing")
void settings_menu_prepare_practice_backing(
    void *backing,
    u32 primary_row_count,
    u32 secondary_row_count
)
{
    NativeBackingCall compose =
        (NativeBackingCall)NATIVE_BACKING_COMPOSE_ADDRESS;
    u8 *records;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)(
        (u8 *)backing + PRACTICE_BACKING_RECORDS_POINTER_OFFSET
    );
    if (records == (u8 *)0) {
        compose(backing);
        return;
    }
    if (settings_menu_backing_layout_changed(records) != 0u) {
        settings_menu_capture_backing_layout(records);
    }
    if (settings_menu_backing_layout.records != (u32)records) {
        compose(backing);
        return;
    }

    settings_menu_place_backing(
        records,
        primary_row_count,
        secondary_row_count
    );
    settings_menu_select_backing_records(
        records,
        primary_row_count,
        secondary_row_count
    );
    compose(backing);
}

static volatile u32 *settings_menu_object_colors(void *object)
{
    u8 *model;
    u8 *part_records;

    if (object == (void *)0) {
        return (volatile u32 *)0;
    }
    model = *(u8 **)((u8 *)object + SPRITE_MODEL_POINTER_OFFSET);
    if (model == (u8 *)0) {
        return (volatile u32 *)0;
    }
    if (*(volatile u16 *)(model + MODEL_PART_COUNT_OFFSET) == 0u) {
        return (volatile u32 *)0;
    }
    part_records = *(u8 **)(model + MODEL_PART_RECORDS_POINTER_OFFSET);
    if (part_records == (u8 *)0) {
        return (volatile u32 *)0;
    }
    if (
        *(volatile u32 *)(
            part_records + MODEL_PART_VERTEX_COUNT_OFFSET
        ) < ROW_LABEL_VERTEX_COUNT
    ) {
        return (volatile u32 *)0;
    }
    return *(volatile u32 **)(
        part_records + MODEL_PART_COLORS_POINTER_OFFSET
    );
}

SETTINGS_MENU_SECTION(".text.settings_menu_draw_tinted_label")
void settings_menu_draw_tinted_label(float alpha, void *object, u32 color)
{
    NativeSpriteDraw draw_sprite =
        (NativeSpriteDraw)NATIVE_SPRITE_DRAW_ADDRESS;
    volatile u32 *colors = settings_menu_object_colors(object);
    u32 saved_colors[ROW_LABEL_VERTEX_COUNT];
    u32 index;

    if (object == (void *)0) {
        return;
    }
    if (colors == (volatile u32 *)0) {
        draw_sprite(alpha, object);
        return;
    }
    for (index = 0u; index < ROW_LABEL_VERTEX_COUNT; ++index) {
        saved_colors[index] = colors[index];
        colors[index] = color;
    }
    draw_sprite(alpha, object);
    for (index = 0u; index < ROW_LABEL_VERTEX_COUNT; ++index) {
        colors[index] = saved_colors[index];
    }
}

static void settings_menu_draw_backing_copy(
    u8 *object,
    u8 *anchor,
    float local_y,
    float alpha,
    u32 tinted
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
        object + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
    );
    object_world_y = (volatile float *)(
        object + PRACTICE_BACKING_RECORD_WORLD_Y_OFFSET
    );
    native_local_y = *object_local_y;
    native_world_y = *object_world_y;
    *object_local_y = local_y;
    *object_world_y = *(volatile float *)(
        anchor + PRACTICE_BACKING_RECORD_WORLD_Y_OFFSET
    ) + local_y - *(volatile float *)(
        anchor + PRACTICE_BACKING_RECORD_LOCAL_Y_OFFSET
    );
    if (tinted != 0u) {
        settings_menu_draw_tinted_label(
            alpha,
            object,
            SETTINGS_MENU_HEADER_ORANGE_TINT
        );
    } else {
        draw_sprite(alpha, object);
    }
    *object_local_y = native_local_y;
    *object_world_y = native_world_y;
}

static u32 settings_menu_player_record(u32 index, u32 row_count)
{
    if (index == 0u) {
        return PRACTICE_BACKING_PLAYER_FIRST_RECORD;
    }
    if (index + 1u == row_count) {
        return PRACTICE_BACKING_PLAYER_TERMINAL_RECORD;
    }
    if (index < PRACTICE_BACKING_PLAYER_CAPACITY - 1u) {
        return PRACTICE_BACKING_PLAYER_REMAINING_FIRST_RECORD + index - 1u;
    }
    return PRACTICE_BACKING_PLAYER_MIDDLE_LAST_RECORD;
}

static u32 settings_menu_secondary_record(u32 index, u32 row_count)
{
    if (index == 0u) {
        return PRACTICE_BACKING_SECONDARY_FIRST_RECORD;
    }
    if (index + 1u == row_count) {
        return PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD;
    }
    if (index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u) {
        return PRACTICE_BACKING_SECONDARY_FIRST_RECORD + index;
    }
    return PRACTICE_BACKING_SECONDARY_MIDDLE_LAST_RECORD;
}

SETTINGS_MENU_SECTION(".text.settings_menu_draw_practice_backing")
void settings_menu_draw_practice_backing(
    void *backing,
    u32 primary_row_count,
    u32 secondary_row_count,
    u32 submenu_rows
)
{
    NativeBackingCall draw = (NativeBackingCall)NATIVE_BACKING_DRAW_ADDRESS;
    u8 saved_flags[PRACTICE_BACKING_RECORD_COUNT];
    u8 *records;
    float alpha;
    float secondary_delta;
    u32 index;
    u32 record;

    if (backing == (void *)0) {
        return;
    }
    records = *(u8 **)(
        (u8 *)backing + PRACTICE_BACKING_RECORDS_POINTER_OFFSET
    );
    if (records == (u8 *)0) {
        draw(backing);
        return;
    }
    for (record = 0u; record < PRACTICE_BACKING_RECORD_COUNT; ++record) {
        saved_flags[record] = *settings_menu_backing_record_flags(
            records,
            record
        );
    }
    settings_menu_set_backing_record(
        records,
        PRACTICE_BACKING_PLAYER_TERMINAL_RECORD,
        0u
    );
    settings_menu_set_backing_record(
        records,
        PRACTICE_BACKING_SECONDARY_TERMINAL_RECORD,
        0u
    );
    for (index = 0u; index < primary_row_count; ++index) {
        if ((submenu_rows & (1u << index)) != 0u) {
            record = settings_menu_player_record(index, primary_row_count);
            if (record != PRACTICE_BACKING_PLAYER_MIDDLE_LAST_RECORD ||
                index < PRACTICE_BACKING_PLAYER_CAPACITY - 1u) {
                settings_menu_set_backing_record(records, record, 0u);
            }
        }
    }
    for (index = 0u; index < secondary_row_count; ++index) {
        if ((submenu_rows & (1u << (primary_row_count + index))) != 0u) {
            record = settings_menu_secondary_record(index, secondary_row_count);
            if (record != PRACTICE_BACKING_SECONDARY_MIDDLE_LAST_RECORD ||
                index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u) {
                settings_menu_set_backing_record(records, record, 0u);
            }
        }
    }
    draw(backing);
    alpha = *(volatile float *)(
        (u8 *)backing + PRACTICE_BACKING_OBJECT_ALPHA_OFFSET
    );
    for (index = 0u; index < primary_row_count; ++index) {
        u32 tinted = submenu_rows & (1u << index);

        if (tinted == 0u && index < PRACTICE_BACKING_PLAYER_CAPACITY - 1u &&
            index + 1u < primary_row_count) {
            continue;
        }
        if (tinted == 0u && index == 0u && primary_row_count == 1u) {
            continue;
        }
        record = settings_menu_player_record(index, primary_row_count);
        settings_menu_draw_backing_copy(
            settings_menu_backing_record_object(records, record),
            settings_menu_backing_record_object(
                records,
                PRACTICE_BACKING_PLAYER_FIRST_RECORD
            ),
            (index + 1u == primary_row_count && primary_row_count > 1u
                ? settings_menu_player_terminal_y(index)
                : settings_menu_player_grid_y(index)),
            alpha,
            tinted
        );
    }
    secondary_delta = settings_menu_secondary_delta(primary_row_count);
    for (index = 0u; index < secondary_row_count; ++index) {
        u32 page_index = primary_row_count + index;
        u32 tinted = submenu_rows & (1u << page_index);

        if (tinted == 0u &&
            index < PRACTICE_BACKING_SECONDARY_CAPACITY - 1u &&
            index + 1u < secondary_row_count) {
            continue;
        }
        if (tinted == 0u && index == 0u && secondary_row_count == 1u) {
            continue;
        }
        record = settings_menu_secondary_record(index, secondary_row_count);
        settings_menu_draw_backing_copy(
            settings_menu_backing_record_object(records, record),
            settings_menu_backing_record_object(
                records,
                PRACTICE_BACKING_SECONDARY_FIRST_RECORD
            ),
            (index + 1u == secondary_row_count && secondary_row_count > 1u
                ? settings_menu_secondary_terminal_y(index, secondary_delta)
                : settings_menu_secondary_grid_y(index, secondary_delta)),
            alpha,
            tinted
        );
    }
    for (record = 0u; record < PRACTICE_BACKING_RECORD_COUNT; ++record) {
        *settings_menu_backing_record_flags(records, record) =
            saved_flags[record];
    }
}
