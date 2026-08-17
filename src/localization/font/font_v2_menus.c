#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* === Control Settings: first eight action labels === */

/* Label box width; larger values delay shrinking and widen rendered labels. */
#define FONT_CONTROLS_BOX_WIDTH 128u

/* Label box height used for vertical centering. */
#define FONT_CONTROLS_BOX_HEIGHT 20u

/* Single-row layout height used by the Controls adapter. */
#define FONT_CONTROLS_LINE_HEIGHT 20.0f

/* Shared one-output-pixel raster phase for all first-eight labels. */
#define FONT_CONTROLS_X_OFFSET 0.8f
#define FONT_CONTROLS_Y_OFFSET 0.8f

/* === Command Chart: title === */

/* Left edge of the Command Chart title; increase to move it right. */
#define FONT_COMMAND_TITLE_BOX_X 28.0f

/* Title width; larger values shrink less and permit longer titles. */
#define FONT_COMMAND_TITLE_BOX_WIDTH 288u

/* Added to the native title Y; more negative moves the title up. */
#define FONT_COMMAND_TITLE_Y_OFFSET -2.2f

/* === Battle Settings: left and right Jutsu-selector lists === */

/* Nominal wrap width; larger values produce fewer or later line breaks. */
#define FONT_JUTSU_BOX_WIDTH 186u

/* Wrapped-block box height used for vertical centering. */
#define FONT_JUTSU_BOX_HEIGHT 32u

/* Horizontal correction for the left list; more negative moves rows left. */
#define FONT_JUTSU_LEFT_X_OFFSET -5.6f

/* Horizontal correction for the right list; more negative moves rows left. */
#define FONT_JUTSU_RIGHT_X_OFFSET -4.0f

/* Draw-width multiplier shared by one-line and wrapped Jutsu-title rows. */
#define FONT_JUTSU_HORIZONTAL_SCALE 1.0f

/* Vertical correction for fitting one-line rows; more negative moves them up. */
#define FONT_JUTSU_SINGLE_LINE_Y_OFFSET -1.6f

/* Applied only to wrapped blocks; more negative moves the block up. */
#define FONT_JUTSU_Y_OFFSET -5.7f

/* Native X below this value is classified as the left-side list. */
#define FONT_JUTSU_SIDE_THRESHOLD 256.0f

/* Vertical distance between wrapped Jutsu-title lines. */
#define FONT_JUTSU_LINE_ADVANCE 16.0f

/* Drawn glyph height for wrapped two-line rows; one-line rows bypass it. */
#define FONT_JUTSU_LAYOUT_GLYPH_HEIGHT 22.0f

/* Target maximum line count for adaptive wrapping. */
#define FONT_JUTSU_LINE_LIMIT 2u

/* Shared NUN5 overflow retry used by constrained two-line list families. */
#define FONT_WRAP_OVERFLOW_WIDTH_FACTOR 0.4f
#define FONT_WRAP_WIDTH_STEP 16.0f

/* === Practice: screen title === */

/* Left edge of the Practice title; increase to move it right. */
#define FONT_PRACTICE_TITLE_BOX_X 31.2f

/* Practice-title width; larger values shrink less. */
#define FONT_PRACTICE_TITLE_BOX_WIDTH 352u

/* Added to native Practice-title Y; more negative moves it up. */
#define FONT_PRACTICE_TITLE_Y_OFFSET -6.8f

/* === Shared Command Chart and Practice title geometry === */

/* Shared title box height used for vertical placement. */
#define FONT_TITLE_BOX_HEIGHT 20u

/* Shared single-line title height. */
#define FONT_TITLE_LINE_HEIGHT 20.0f

/* === Pause menu: Controls list === */

/* Pause label width; larger values shrink less. */
#define FONT_PAUSE_LIST_BOX_WIDTH 216u

/* Pause label box height used for vertical centering. */
#define FONT_PAUSE_LIST_BOX_HEIGHT 20u

/* Shared ordinary/selected Pause Controls row-origin correction. */
#define FONT_PAUSE_LIST_X_OFFSET 1.6f

/* Added to every Pause Controls row Y; more negative moves rows up. */
#define FONT_PAUSE_LIST_Y_OFFSET -2.4f

/* Extra X correction for the selected red row; positive moves it right. */
#define FONT_PAUSE_LIST_SELECTED_X_OFFSET 0.0f

/* Single-row layout height for Pause Controls labels. */
#define FONT_PAUSE_LIST_LINE_HEIGHT 20.0f

/* === Character Select: Linked Mode choices === */

/* Both choices share one centered horizontal-scale correction. */
#define FONT_LINKED_CHOICE_SCALE_X 1.05f

/* The native Linked selected helper always chooses the red selected style. */
#define FONT_LINKED_CHOICE_SELECTED_COLOR 0xFF0000D4u

/* One-line choice geometry; the native caller supplies the shared row Y. */
#define FONT_LINKED_CHOICE_BOX_HEIGHT 20u
#define FONT_LINKED_CHOICE_LINE_HEIGHT 20.0f

/* === Character Select: player-mode option list === */

/* Option-row width; larger values shrink less. */
#define FONT_CHARACTER_LIST_BOX_WIDTH 240u

/* Option-row box height used for vertical centering. */
#define FONT_CHARACTER_LIST_BOX_HEIGHT 20u

/* Added to every native option-row X; positive moves the row right. */
#define FONT_CHARACTER_LIST_X_OFFSET 5.8f

/* Selected helper consumes integer coordinates, so use the nearest integer. */
#define FONT_CHARACTER_LIST_SELECTED_X_OFFSET 6

/* The fifth structural row is a separate footer group below the options. */
#define FONT_CHARACTER_LIST_FOOTER_Y_THRESHOLD 96.0f
#define FONT_CHARACTER_LIST_SELECTED_FOOTER_Y_OFFSET (-1)

/* Single-row layout height for Character Select options. */
#define FONT_CHARACTER_LIST_LINE_HEIGHT 20.0f

/* === Shared Yes/No selectors: quit, return, and Special Controls === */

/* Exact native Y bit pattern identifying the ordinary Yes row. */
#define FONT_QUIT_YES_SOURCE_BITS 0x41C00000u

/* Exact native Y bit pattern identifying the ordinary No row. */
#define FONT_QUIT_NO_SOURCE_BITS 0x42600000u

/* Shared residual correction for the first row of confirmation selectors. */
#define FONT_CONFIRMATION_YES_X_OFFSET 0.0f
#define FONT_CONFIRMATION_YES_Y_OFFSET 0.0f

/* Selected confirmations retain one output-pixel vertical style residual. */
#define FONT_CONFIRMATION_SELECTED_Y_OFFSET (-0.8f)

/* Character Select's confirmation container is one output pixel lower. */
#define FONT_CHARACTER_CONFIRMATION_Y_OFFSET (-0.8f)

/* Target local Yes X; increase to move Yes right. */
#define FONT_QUIT_YES_X (64.5f + FONT_CONFIRMATION_YES_X_OFFSET)

/* Target local Yes Y; increase to move Yes down. */
#define FONT_QUIT_YES_Y (31.5f + FONT_CONFIRMATION_YES_Y_OFFSET)

/* Target local No X; increase to move No right. */
#define FONT_QUIT_NO_X 68.5f

/* Target local No Y; increase to move No down. */
#define FONT_QUIT_NO_Y 49.0f

/* Collection-local Yes X; increase to move Yes right. */
#define FONT_COLLECTION_YES_X \
    (63.2f + FONT_CONFIRMATION_YES_X_OFFSET)

/* Collection-local Yes Y; increase to move Yes down. */
#define FONT_COLLECTION_YES_Y \
    (28.85f + FONT_CONFIRMATION_YES_Y_OFFSET)

/* Collection-local No X; increase to move No right. */
#define FONT_COLLECTION_NO_X 68.1f

/* Collection-local No Y; increase to move No down. */
#define FONT_COLLECTION_NO_Y 48.2f

/* Marks the body-to-choice interval of the Collection exit prompt. */
#define FONT_COLLECTION_CHOICE_SCOPE 2u

/* Separates Character Select's structurally lower confirmation container. */
#define FONT_CHARACTER_CHOICE_SCOPE 3u

/* Mode Select bottom-body X origin; larger values move it right. */
#define FONT_MODE_SELECT_BODY_BOX_X 24.0f

/* Mode Select bottom-body Y origin; smaller values move it up. */
#define FONT_MODE_SELECT_BODY_BOX_Y 12.0f

/* Mode Select bottom-body width before wrapping or shrink-only fitting. */
#define FONT_MODE_SELECT_BODY_BOX_WIDTH 420u

/* Mode Select bottom-body height available to its single text line. */
#define FONT_MODE_SELECT_BODY_BOX_HEIGHT 40u

/* Mode Select bottom-body line cadence if the source ever contains a break. */
#define FONT_MODE_SELECT_BODY_LINE_HEIGHT 20.0f

/* Mode Select bottom body is intentionally limited to one line. */
#define FONT_MODE_SELECT_BODY_LINE_LIMIT 1u

/* Fixed runtime pointer identifying Special Controls ON. */
#define FONT_SPECIAL_ON_TEXT 0x006059F0u

/* Fixed runtime pointer identifying Special Controls OFF. */
#define FONT_SPECIAL_OFF_TEXT 0x006059F8u

/* Native source Y values identify the two structural selector rows. */
#define FONT_SPECIAL_ROW_0_SOURCE_Y_BITS 0x41C00000u
#define FONT_SPECIAL_ROW_1_SOURCE_Y_BITS 0x42600000u

/* Shared two-row formula; neither coordinate follows the selected text. */
#define FONT_SPECIAL_ROW_X 68.4f
#define FONT_SPECIAL_ROW_X_INTERVAL -7.0f
#define FONT_SPECIAL_ROW_Y 29.0f
#define FONT_SPECIAL_ROW_Y_INTERVAL 20.0f

/* Shared font-only geometry for both Special Controls choices. */
#define FONT_SPECIAL_CHOICE_BOX_WIDTH 104u
#define FONT_SPECIAL_CHOICE_BOX_HEIGHT 20u
#define FONT_SPECIAL_CHOICE_LINE_HEIGHT 20.0f
#define FONT_SPECIAL_CHOICE_SELECTED_X_OFFSET 0.0f
#define FONT_SPECIAL_CHOICE_SELECTED_SCALE_X 1.02f
#define FONT_SPECIAL_CHOICE_UNSELECTED_SCALE_X 1.01f
#define FONT_SPECIAL_CHOICE_GLYPH_HEIGHT 26.0f

/* === Shared temporary body storage: internal capacity === */

/* Maximum copied body/list text bytes including the terminator; not geometry. */
#define FONT_BODY_BUFFER_SIZE 0x100u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

FONT_V2_SECTION(".text.font_v2_controls_adapter")
int font_v2_controls_adapter(
    const u8 *text,
    u32 style,
    float center_x,
    float draw_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x =
        center_x - (float)(FONT_CONTROLS_BOX_WIDTH / 2u) +
        FONT_CONTROLS_X_OFFSET;
    session.box_y = draw_y + FONT_CONTROLS_Y_OFFSET;
    session.box_width = FONT_CONTROLS_BOX_WIDTH;
    session.box_height = FONT_CONTROLS_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CONTROLS_LINE_HEIGHT;
    session.callback = (u32)font_v2_controls_callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = (u32)&session;
    session.callback_arg3 = 0;

    return font_v2_adapter_call(&session);
}

static FONT_V2_SECTION(".text.font_v2_title_adapter_common")
int font_v2_title_adapter_common(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_y,
    float box_x,
    float y_offset,
    u32 box_width
) {
    FontV2Session session;

    session.text = text;
    session.box_x = box_x;
    session.box_y = native_y + y_offset;
    session.box_width = box_width;
    session.box_height = FONT_TITLE_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags =
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_NUN5_QUOTE_WIDTH |
        FONT_V2_FLAG_COLOR_TAGS;
    session.line_limit = 1;
    session.line_height = FONT_TITLE_LINE_HEIGHT;
    session.callback = (u32)font_v2_title_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_command_title_entry")
int font_v2_command_title_entry(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    u8 buffer[FONT_BODY_BUFFER_SIZE];
    u32 length = 0;

    (void)native_x;
    if (!text) {
        return -1;
    }
    while (text[length] && length < FONT_BODY_BUFFER_SIZE - 1u) {
        buffer[length] = text[length];
        length += 1;
    }
    if (text[length]) {
        return -1;
    }
    if (length && buffer[length - 1u] == 0x0Au) {
        length -= 1;
    }
    buffer[length] = 0;

    return font_v2_title_adapter_common(
        arg0,
        buffer,
        arg2,
        native_y,
        FONT_COMMAND_TITLE_BOX_X,
        FONT_COMMAND_TITLE_Y_OFFSET,
        FONT_COMMAND_TITLE_BOX_WIDTH
    );
}

FONT_V2_SECTION(".text.font_v2_practice_title_entry")
int font_v2_practice_title_entry(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_title_adapter_common(
        arg0,
        text,
        arg2,
        native_y,
        FONT_PRACTICE_TITLE_BOX_X,
        FONT_PRACTICE_TITLE_Y_OFFSET,
        FONT_PRACTICE_TITLE_BOX_WIDTH
    );
}

FONT_V2_SECTION(".text.font_v2_pause_list_adapter")
int font_v2_pause_list_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = native_x + FONT_PAUSE_LIST_X_OFFSET;
    session.box_y = native_y + FONT_PAUSE_LIST_Y_OFFSET;
    session.box_width = FONT_PAUSE_LIST_BOX_WIDTH;
    session.box_height = FONT_PAUSE_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_PAUSE_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_pause_list_selected_impl")
int font_v2_pause_list_selected_impl(
    u32 arg0,
    s32 native_x,
    s32 native_y,
    const u8 *text,
    u32 color
) {
    FontV2Session session;
    FontV2Bits color_bits;

    color_bits.u = color;
    session.text = text;
    session.box_x =
        (float)native_x + FONT_PAUSE_LIST_X_OFFSET +
        FONT_PAUSE_LIST_SELECTED_X_OFFSET;
    session.box_y = (float)native_y + FONT_PAUSE_LIST_Y_OFFSET;
    session.box_width = FONT_PAUSE_LIST_BOX_WIDTH;
    session.box_height = FONT_PAUSE_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_PAUSE_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_selected_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)native_x;
    session.callback_arg2 = (u32)native_y;
    session.callback_arg3 = (u32)&session;
    session.glyph_height = color_bits.f;

    return font_v2_adapter_call(&session);
}

static FONT_V2_SECTION(".text.font_v2_linked_choice_session_prepare")
int font_v2_linked_choice_session_prepare(
    FontV2Session *session,
    const u8 *text,
    float native_x,
    float native_y,
    u32 callback
) {
    u32 measured_width;
    u32 line_count;

    if (
        font_v2_measure(text, 0u, &measured_width, &line_count) != 0 ||
        measured_width == 0u ||
        line_count != 1u
    ) {
        return -1;
    }

    session->text = text;
    session->box_x = native_x;
    session->box_y = native_y;
    session->box_width = measured_width;
    session->box_height = FONT_LINKED_CHOICE_BOX_HEIGHT;
    session->horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session->vertical_alignment = FONT_V2_ALIGN_START;
    session->flags =
        FONT_V2_FLAG_FIXED_SCALE_X | FONT_V2_FLAG_PREMEASURED;
    session->line_limit = 1u;
    session->line_height = FONT_LINKED_CHOICE_LINE_HEIGHT;
    session->callback = callback;
    session->measured_width = measured_width;
    session->line_count = line_count;
    session->scale_x = FONT_LINKED_CHOICE_SCALE_X;
    return 0;
}

FONT_V2_SECTION(".text.font_v2_linked_choice_selected_impl")
int font_v2_linked_choice_selected_impl(
    u32 arg0,
    s32 native_x,
    s32 native_y,
    const u8 *text,
    u32 ignored_color
) {
    FontV2Session session;
    FontV2Bits color_bits;

    (void)ignored_color;

    if (font_v2_linked_choice_session_prepare(
            &session,
            text,
            (float)native_x,
            (float)native_y,
            (u32)font_v2_pause_list_selected_callback
        ) != 0) {
        return -1;
    }

    color_bits.u = FONT_LINKED_CHOICE_SELECTED_COLOR;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)native_x;
    session.callback_arg2 = (u32)native_y;
    session.callback_arg3 = (u32)&session;
    session.glyph_height = color_bits.f;
    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_linked_choice_unselected_adapter")
int font_v2_linked_choice_unselected_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    FontV2Session session;

    if (font_v2_linked_choice_session_prepare(
            &session,
            text,
            native_x,
            native_y,
            (u32)font_v2_pause_list_callback
        ) != 0) {
        return -1;
    }

    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;
    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_character_selected_adapter")
int font_v2_character_selected_adapter(
    u32 object,
    s32 draw_x,
    s32 draw_y,
    const u8 *text
) {
    FontV2Session session;
    s32 selected_y = draw_y;

    if ((float)selected_y > FONT_CHARACTER_LIST_FOOTER_Y_THRESHOLD) {
        selected_y += FONT_CHARACTER_LIST_SELECTED_FOOTER_Y_OFFSET;
    }

    session.text = text;
    session.box_x =
        (float)draw_x + (float)FONT_CHARACTER_LIST_SELECTED_X_OFFSET;
    session.box_y = (float)selected_y;
    session.box_width = FONT_CHARACTER_LIST_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CHARACTER_LIST_LINE_HEIGHT;
    session.callback = FONT_CHARACTER_SELECTED_DRAW_ADDRESS;
    session.callback_arg0 = object;
    session.callback_arg1 =
        (u32)(draw_x + FONT_CHARACTER_LIST_SELECTED_X_OFFSET);
    session.callback_arg2 = (u32)selected_y;
    session.callback_arg3 = (u32)text;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_character_unselected_adapter")
int font_v2_character_unselected_adapter(
    u32 object,
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = native_x + FONT_CHARACTER_LIST_X_OFFSET;
    session.box_y = native_y;
    session.box_width = FONT_CHARACTER_LIST_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CHARACTER_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_callback;
    session.callback_arg0 = object;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = color;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_quit_scope_enter")
u32 font_v2_quit_scope_enter(void) {
    u32 previous = font_v2_quit_active;
    if (previous != FONT_COLLECTION_CHOICE_SCOPE) {
        font_v2_quit_active = 1;
    }
    return previous;
}

FONT_V2_SECTION(".text.font_v2_character_scope_enter")
u32 font_v2_character_scope_enter(void) {
    u32 previous = font_v2_quit_active;
    font_v2_quit_active = FONT_CHARACTER_CHOICE_SCOPE;
    return previous;
}

FONT_V2_SECTION(".text.font_v2_quit_scope_leave")
void font_v2_quit_scope_leave(u32 previous) {
    font_v2_quit_active =
        previous == FONT_COLLECTION_CHOICE_SCOPE ? 0u : previous;
}

static FONT_V2_SECTION(".text.font_v2_map_choice")
u32 font_v2_map_choice(
    u32 text,
    u32 source_y,
    u32 *target_x,
    u32 *target_y
) {
    FontV2Bits x;
    FontV2Bits y;

    if (
        text == 0x00604570u &&
        source_y == FONT_QUIT_YES_SOURCE_BITS
    ) {
        x.f = FONT_COLLECTION_YES_X;
        y.f = FONT_COLLECTION_YES_Y;
    } else if (
        text == 0x00604568u &&
        source_y == FONT_QUIT_NO_SOURCE_BITS
    ) {
        x.f = FONT_COLLECTION_NO_X;
        y.f = FONT_COLLECTION_NO_Y;
    } else if (font_v2_quit_active == FONT_COLLECTION_CHOICE_SCOPE) {
        if (source_y == FONT_QUIT_YES_SOURCE_BITS) {
            x.f = FONT_COLLECTION_YES_X;
            y.f = FONT_COLLECTION_YES_Y;
        } else if (source_y == FONT_QUIT_NO_SOURCE_BITS) {
            x.f = FONT_COLLECTION_NO_X;
            y.f = FONT_COLLECTION_NO_Y;
        } else {
            return 0;
        }
    } else if (font_v2_quit_active) {
        if (source_y == FONT_QUIT_YES_SOURCE_BITS) {
            x.f = FONT_QUIT_YES_X;
            y.f = FONT_QUIT_YES_Y;
        } else if (source_y == FONT_QUIT_NO_SOURCE_BITS) {
            x.f = FONT_QUIT_NO_X;
            y.f = FONT_QUIT_NO_Y;
        } else {
            return 0;
        }
    } else if (
        text == FONT_SPECIAL_ON_TEXT || text == FONT_SPECIAL_OFF_TEXT
    ) {
        u32 row;

        if (source_y == FONT_SPECIAL_ROW_0_SOURCE_Y_BITS) {
            row = 0u;
        } else if (source_y == FONT_SPECIAL_ROW_1_SOURCE_Y_BITS) {
            row = 1u;
        } else {
            return 0;
        }
        x.f = FONT_SPECIAL_ROW_X +
            (float)(s32)row * FONT_SPECIAL_ROW_X_INTERVAL;
        y.f = FONT_SPECIAL_ROW_Y +
            (float)(s32)row * FONT_SPECIAL_ROW_Y_INTERVAL;
    } else {
        return 0;
    }

    if (font_v2_quit_active == FONT_CHARACTER_CHOICE_SCOPE) {
        y.f += FONT_CHARACTER_CONFIRMATION_Y_OFFSET;
    }

    *target_x = x.u;
    *target_y = y.u;
    return 1;
}

FONT_V2_SECTION(".text.font_v2_quit_selected_map")
u32 font_v2_quit_selected_map(
    u32 text,
    u32 source_y,
    u32 source_x,
    u32 *target_y
) {
    u32 target_x = source_x;
    u32 mapped_y = source_y;
    FontV2Bits selected_y;

    if (font_v2_map_choice(text, source_y, &target_x, &mapped_y)) {
        if (
            font_v2_quit_active != FONT_CHARACTER_CHOICE_SCOPE &&
            !(
                font_v2_quit_active == FONT_COLLECTION_CHOICE_SCOPE &&
                source_y == FONT_QUIT_NO_SOURCE_BITS
            )
        ) {
            selected_y.u = mapped_y;
            selected_y.f += FONT_CONFIRMATION_SELECTED_Y_OFFSET;
            mapped_y = selected_y.u;
        }
    }
    *target_y = mapped_y;
    return target_x;
}

static FONT_V2_SECTION(".text.font_v2_special_choice_session_init")
void font_v2_special_choice_session_init(
    FontV2Session *session,
    const u8 *text,
    float draw_x,
    float draw_y,
    float scale_x,
    u32 callback
) {
    session->text = text;
    session->box_x = draw_x;
    session->box_y = draw_y;
    session->box_width = FONT_SPECIAL_CHOICE_BOX_WIDTH;
    session->box_height = FONT_SPECIAL_CHOICE_BOX_HEIGHT;
    session->horizontal_alignment = FONT_V2_ALIGN_START;
    session->vertical_alignment = FONT_V2_ALIGN_START;
    session->flags =
        FONT_V2_FLAG_FIXED_SCALE_X | FONT_V2_FLAG_GLYPH_HEIGHT;
    session->line_limit = 1u;
    session->line_height = FONT_SPECIAL_CHOICE_LINE_HEIGHT;
    session->callback = callback;
    session->scale_x = scale_x;
    session->glyph_height = FONT_SPECIAL_CHOICE_GLYPH_HEIGHT;
}

FONT_V2_SECTION(".text.font_v2_special_choice_selected_adapter")
int font_v2_special_choice_selected_adapter(
    u32 text,
    u32 arg1,
    u32 arg2,
    u32 arg3,
    u32 native_x_bits,
    u32 native_y_bits
) {
    FontV2SpecialChoiceFrame frame;
    FontV2Bits draw_x;
    FontV2Bits draw_y;

    draw_x.u = native_x_bits;
    draw_y.u = native_y_bits;
    font_v2_map_choice(text, native_y_bits, &draw_x.u, &draw_y.u);
    draw_x.f += FONT_SPECIAL_CHOICE_SELECTED_X_OFFSET;
    font_v2_special_choice_session_init(
        &frame.session,
        (const u8 *)text,
        draw_x.f,
        draw_y.f,
        FONT_SPECIAL_CHOICE_SELECTED_SCALE_X,
        (u32)font_v2_special_choice_selected_callback
    );
    frame.session.callback_arg0 = text;
    frame.session.callback_arg1 = arg1;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame;
    frame.native_arg3 = arg3;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_quit_unselected_adapter")
int font_v2_quit_unselected_adapter(
    u32 arg0,
    u32 *record,
    u32 arg2,
    u32 arg3
) {
    FontV2Session session;
    u32 original_x;
    u32 original_y;
    u32 target_x;
    u32 target_y;
    u32 text;
    u32 special_choice;
    int result;

    original_x = record[0];
    original_y = record[1];
    text = record[2];
    special_choice =
        text == FONT_SPECIAL_ON_TEXT || text == FONT_SPECIAL_OFF_TEXT;

    target_x = original_x;
    target_y = original_y;
    if (!font_v2_map_choice(text, original_y, &target_x, &target_y)) {
        return font_v2_quit_unselected_callback(
            arg0, (u32)record, arg2, arg3
        );
    }

    record[0] = target_x;
    record[1] = target_y;
    if (special_choice) {
        FontV2Bits draw_x;
        FontV2Bits draw_y;

        draw_x.u = target_x;
        draw_y.u = target_y;
        font_v2_special_choice_session_init(
            &session,
            (const u8 *)text,
            draw_x.f,
            draw_y.f,
            FONT_SPECIAL_CHOICE_UNSELECTED_SCALE_X,
            (u32)font_v2_quit_unselected_callback
        );
        session.callback_arg0 = arg0;
        session.callback_arg1 = (u32)record;
        session.callback_arg2 = arg2;
        session.callback_arg3 = arg3;
        result = font_v2_adapter_call(&session);
    } else {
        result = font_v2_quit_unselected_callback(
            arg0, (u32)record, arg2, arg3
        );
    }
    record[0] = original_x;
    record[1] = original_y;
    return result;
}

FONT_V2_SECTION(".text.font_v2_native_measure")
u32 font_v2_native_measure(const u8 *text) {
    u32 width = font_v2_native_measure_callback(text);
    const u8 *cursor = text;

    while (*cursor) {
        if (*cursor == (u8)' ') {
            width -= 6u;
        }
        cursor += 1;
    }
    return width;
}

FONT_V2_SECTION(".text.font_v2_wrap_native")
int font_v2_wrap_native(
    u8 *text,
    u32 box_width,
    u32 line_limit,
    u32 *measured_width,
    u32 *line_count
) {
    volatile u32 *renderer;
    u32 saved_tracking = 0;
    u8 *cursor;
    u8 *line_start;
    u8 *last_space = (u8 *)0;
    u32 lines = 1;
    u32 maximum_width = 0;

    if (!text || !measured_width || !line_count) {
        return -1;
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (renderer) {
        saved_tracking =
            renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)];
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
    }

    cursor = text;
    line_start = text;
    while (*cursor) {
        if (*cursor == (u8)'\n') {
            line_start = cursor + 1;
            last_space = (u8 *)0;
            lines += 1;
        } else if (*cursor == (u8)' ') {
            u32 width;
            *cursor = 0;
            width = font_v2_native_measure(line_start);
            *cursor = (u8)' ';
            if (
                width > box_width &&
                (!line_limit || lines < line_limit)
            ) {
                u8 *wrap = last_space ? last_space : cursor;
                *wrap = (u8)'\n';
                line_start = wrap + 1;
                lines += 1;
            }
            last_space = cursor;
        }
        cursor += 1;
    }

    if (
        font_v2_native_measure(line_start) > box_width &&
        last_space &&
        (!line_limit || lines < line_limit)
    ) {
        *last_space = (u8)'\n';
        lines += 1;
    }

    cursor = text;
    line_start = text;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            u32 width;
            *cursor = 0;
            width = font_v2_native_measure(line_start);
            if (width > maximum_width) {
                maximum_width = width;
            }
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
        } else {
            cursor += 1;
        }
    }

    if (renderer) {
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] =
            saved_tracking;
    }
    *measured_width = maximum_width;
    *line_count = lines;
    return 0;
}

FONT_V2_SECTION(".text.font_v2_wrap_retry")
int font_v2_wrap_retry(
    u8 *buffer,
    const u8 *text,
    u32 box_width,
    u32 line_limit,
    u32 *measured_width,
    u32 *line_count
) {
    volatile u32 *renderer_words =
        *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    float wrap_width;
    u32 index = 0u;

    if (
        !buffer || !text || !line_limit ||
        !measured_width || !line_count
    ) {
        return -1;
    }

    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        buffer[index] = text[index];
        index += 1u;
    }
    buffer[index] = 0u;
    if (
        font_v2_wrap_native(
            buffer,
            box_width,
            0u,
            measured_width,
            line_count
        )
    ) {
        return -1;
    }

    if (*line_count > line_limit) {
        u8 *cursor = buffer;
        u8 *line_start = cursor;
        u32 line_index = 0u;
        u32 overflow_width = 0u;
        u32 overflow_lines = 0u;
        u32 saved_tracking = 0u;

        if (renderer_words) {
            saved_tracking = renderer_words[
                FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)
            ];
            renderer_words[
                FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)
            ] = 0u;
        }
        for (;;) {
            if (!*cursor || *cursor == (u8)'\n') {
                u8 saved = *cursor;
            if (saved) {
                *cursor = 0u;
            }
                if (line_index >= line_limit) {
                    overflow_width += font_v2_native_measure(line_start);
                    overflow_lines += 1u;
                }
                *cursor = saved;
                if (!saved) {
                    break;
                }
                cursor += 1;
                line_start = cursor;
                line_index += 1u;
            } else {
                cursor += 1;
            }
        }
        if (renderer_words) {
            renderer_words[
                FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)
            ] = saved_tracking;
        }

        wrap_width = (float)(s32)box_width;
        if (overflow_lines) {
            wrap_width +=
                (
                    (float)(s32)overflow_width /
                    (float)(s32)overflow_lines
                ) * FONT_WRAP_OVERFLOW_WIDTH_FACTOR;
        }

        do {
            index = 0u;
            while (
                index < FONT_BODY_BUFFER_SIZE - 1u &&
                text[index]
            ) {
                buffer[index] = text[index];
                index += 1u;
            }
            buffer[index] = 0u;
            if (
                font_v2_wrap_native(
                    buffer,
                    (u32)wrap_width,
                    0u,
                    measured_width,
                    line_count
                )
            ) {
                return -1;
            }
            wrap_width += FONT_WRAP_WIDTH_STEP;
        } while (*line_count > line_limit);
    }

    return 0;
}
