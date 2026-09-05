/* Shared native Practice presentation, independent of menu storage. */
#include "menu_pages.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int s32;
#define SETTINGS_MENU_SECTION(name) __attribute__((section(name), noinline))
#define CONTROLLER_SELECTED_ROW_OFFSET 0x3Cu
#define CONTROLLER_SCROLL_OFFSET 0x44u
#define CONTROLLER_UPPER_WINDOW_OFFSET 0xB0u
#define CONTROLLER_LOWER_WINDOW_OFFSET 0xB4u
#define BACKING_PLAYER_CAPACITY 9u
#define BACKING_OPPONENT_CAPACITY 8u
#define NATIVE_WINDOW_UPDATE_ADDRESS 0x0037D9C0u
#define NATIVE_APPROACH_FLOAT_ADDRESS 0x006C12A0u
#define PLAYER_VISIBLE_ROWS 7
#define OPPONENT_VISIBLE_ROWS 6
#define WINDOW_MARGIN_ROWS 2
#define ROW_SCROLL_STEP 28.0f
#define ROW_DRAW_STEP 28.0f
#define SECTION_HEADING_GAP 18.0f
#define WINDOW_APPROACH_STEP 20.0f
#define CURSOR_SCROLL_SCALE 0.939f
#define CURSOR_ROW_STEP 26.5f
#define CURSOR_BASE_Y 94.0f
#define CURSOR_SECTION_OFFSET 40.0f
typedef int (*NativeWindowUpdate)(int,int,int,int,int);
typedef void (*NativeApproachFloat)(float,float,volatile float *);
volatile SettingsMenuActivePage settings_menu_render_page
    __attribute__((section(".bss.settings_menu_render_page")));
const SettingsMenuPresentation *settings_menu_presentation
    __attribute__((section(".bss.settings_menu_presentation")));
extern void settings_menu_native_content(void *controller);

SETTINGS_MENU_SECTION(".text.settings_menu_draw_content")
void settings_menu_draw_content(void *controller, const SettingsMenuPresentation *view)
{
    u8 *renderer = *(u8 **)0x00607470u;
    void *saved_context = *(void **)(renderer + 0x6Cu);
    ((void (*)(void *,void *))0x001866D0u)(renderer,
        *(void **)((u8 *)controller + 0x14u));
    settings_menu_render_page = *view->page;
    settings_menu_presentation = view;
    settings_menu_native_content(controller);
    settings_menu_presentation = (const SettingsMenuPresentation *)0;
    ((void (*)(void *,void *))0x001866D0u)(renderer, saved_context);
}
SETTINGS_MENU_SECTION(".text.settings_menu_draw_backing")
void settings_menu_draw_backing(void *backing)
{
    settings_menu_draw_practice_backing(backing,
        settings_menu_render_page.primary_row_count,
        settings_menu_render_page.secondary_row_count, settings_menu_presentation->submenu_rows);
}

SETTINGS_MENU_SECTION(".text.settings_menu_label")
u32 settings_menu_label(int row) { return settings_menu_presentation->label(row); }
SETTINGS_MENU_SECTION(".text.settings_menu_value")
int settings_menu_value(void *controller, int row)
{
    (void)controller;
    return settings_menu_presentation->value(settings_menu_presentation->owner, row);
}
SETTINGS_MENU_SECTION(".text.settings_menu_value_text")
u32 settings_menu_value_text(int row)
{
    const u32 *values = (const u32 *)settings_menu_presentation->values(row);
    return values[settings_menu_presentation->value(settings_menu_presentation->owner, row)];
}
SETTINGS_MENU_SECTION(".text.settings_menu_maximum")
int settings_menu_maximum(void *controller, int row)
{
    (void)controller;
    return settings_menu_presentation->maximum(settings_menu_presentation->owner, row);
}
SETTINGS_MENU_SECTION(".text.settings_menu_enabled")
int settings_menu_enabled(void *controller, int row)
{
    (void)controller;
    return settings_menu_presentation->enabled(settings_menu_presentation->owner, row);
}

SETTINGS_MENU_SECTION(".text.settings_menu_initialize_window")
void settings_menu_initialize_window(
    void *controller,
    const volatile SettingsMenuActivePage *page,
    u32 selected_row
)
{
    NativeWindowUpdate update =
        (NativeWindowUpdate)NATIVE_WINDOW_UPDATE_ADDRESS;
    volatile s32 *upper = (volatile s32 *)(
        (u8 *)controller + CONTROLLER_UPPER_WINDOW_OFFSET
    );
    volatile s32 *lower = (volatile s32 *)(
        (u8 *)controller + CONTROLLER_LOWER_WINDOW_OFFSET
    );
    volatile float *scroll = (volatile float *)(
        (u8 *)controller + CONTROLLER_SCROLL_OFFSET
    );
    s32 start;

    *upper = 0;
    *lower = 0;
    if (selected_row < page->primary_row_count) {
        start = update(
            (s32)selected_row,
            0,
            PLAYER_VISIBLE_ROWS,
            WINDOW_MARGIN_ROWS,
            (s32)page->primary_row_count
        );
        *upper = start;
        *scroll = -ROW_SCROLL_STEP * (float)start;
    } else if (page->secondary_row_count != 0u) {
        start = update(
            (s32)(selected_row - page->primary_row_count),
            0,
            OPPONENT_VISIBLE_ROWS,
            WINDOW_MARGIN_ROWS,
            (s32)page->secondary_row_count
        );
        *lower = start;
        *scroll = -SECTION_HEADING_GAP -
            ROW_DRAW_STEP * (float)page->primary_row_count -
            ROW_SCROLL_STEP * (float)start;
    } else {
        *scroll = 0.0f;
    }
}

SETTINGS_MENU_SECTION(".text.settings_menu_update_window")
void settings_menu_update_window(void *controller, const volatile SettingsMenuActivePage *page)
{
    NativeWindowUpdate update =
        (NativeWindowUpdate)NATIVE_WINDOW_UPDATE_ADDRESS;
    NativeApproachFloat approach =
        (NativeApproachFloat)NATIVE_APPROACH_FLOAT_ADDRESS;
    s32 selected = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 player_count = (s32)page->primary_row_count;
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
            (s32)page->secondary_row_count;

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

SETTINGS_MENU_SECTION(".text.settings_menu_cursor_y")
float settings_menu_cursor_y(void *controller)
{
    s32 selected = *(volatile s32 *)(
        (u8 *)controller + CONTROLLER_SELECTED_ROW_OFFSET
    );
    s32 player_count = (s32)settings_menu_render_page.primary_row_count;
    s32 opponent_count =
        (s32)settings_menu_render_page.secondary_row_count;
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
