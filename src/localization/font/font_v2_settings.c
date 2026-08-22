#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* === Battle Settings and Practice Settings rows === */

/* Shared one-pixel raster-origin correction for every Settings text box. */
#define FONT_SETTINGS_X_OFFSET 0.8f

/* NUN5 left edge and width for Battle Settings labels. */
#define FONT_BATTLE_SETTINGS_LABEL_X \
    (92.0f + FONT_SETTINGS_X_OFFSET)
#define FONT_BATTLE_SETTINGS_LABEL_WIDTH 158u

/* NUN5 left edge and width for Practice Settings labels. */
#define FONT_PRACTICE_SETTINGS_LABEL_X (92.0f + FONT_SETTINGS_X_OFFSET)
#define FONT_PRACTICE_SETTINGS_LABEL_WIDTH 150u

/* Selected labels use a wider native style; retain the matched horizontal fit. */
#define FONT_PRACTICE_SETTINGS_SELECTED_SCALE_X 0.93f

/* NUN5 left edge and width for both settings value columns. */
#define FONT_SETTINGS_VALUE_X (303.25f + FONT_SETTINGS_X_OFFSET)
#define FONT_SETTINGS_VALUE_WIDTH 104u

/* The primary text branch has a distinct center phase from other values. */
#define FONT_BATTLE_SETTINGS_VALUE_X_OFFSET (-0.8f)
#define FONT_BATTLE_SETTINGS_PRIMARY_TEXT_VALUE_X_OFFSET (-1.6f)
#define FONT_BATTLE_SETTINGS_NUMERIC_VALUE_X_OFFSET (-1.6f)
#define FONT_BATTLE_SETTINGS_NUMERIC_VALUE_Y_OFFSET (-1.2f)
#define FONT_BATTLE_SETTINGS_NUMERIC_VALUE_SCALE_X 1.0f
#define FONT_BATTLE_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT 27.0f

/* Practice values sit one output pixel left of the shared Battle position. */
#define FONT_PRACTICE_SETTINGS_VALUE_X_OFFSET (-0.8f)

/* Tokens no wider than half the value box use NUN5's alternate center phase. */
#define FONT_PRACTICE_SETTINGS_SHORT_VALUE_X_OFFSET 0.0f

/* NUN5 uses one 104-unit box; descriptive phrases retain their accepted fit. */
#define FONT_SETTINGS_PHRASE_FIT_WIDTH 99u
#define FONT_SETTINGS_PHRASE_X_OFFSET -1.5f

/* Shared geometry for digit-leading Settings values. */
#define FONT_SETTINGS_NUMERIC_VALUE_X_OFFSET 1.8f
#define FONT_SETTINGS_NUMERIC_VALUE_Y_OFFSET 1.875f
#define FONT_SETTINGS_NUMERIC_VALUE_SCALE_X 1.02f
#define FONT_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT 26.0f

/* Shared row baselines; selected labels use the taller selected glyph pass. */
#define FONT_BATTLE_SETTINGS_ROW_Y_OFFSET 0.0f
#define FONT_BATTLE_SETTINGS_SELECTED_Y_OFFSET -0.8f
#define FONT_BATTLE_SETTINGS_ORDINARY_Y_OFFSET 0.8f
#define FONT_BATTLE_SETTINGS_VALUE_Y_OFFSET 0.8f
#define FONT_PRACTICE_SETTINGS_ROW_Y_OFFSET 0.75f
#define FONT_PRACTICE_SETTINGS_SELECTED_Y_OFFSET (-1.6f)
#define FONT_SETTINGS_SELECTED_Y_OFFSET 1.5f

/* NUN5 left edge and width for the Practice Settings section heading. */
#define FONT_PRACTICE_SETTINGS_HEADING_X (84.0f + FONT_SETTINGS_X_OFFSET)
#define FONT_PRACTICE_SETTINGS_HEADING_WIDTH 158u

/* Native one-line height retained by every Settings row adapter. */
#define FONT_SETTINGS_LINE_HEIGHT 20.0f

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

static FONT_V2_SECTION(".text.font_v2_settings_label_callback")
int font_v2_settings_label_callback(
    u32 text,
    u32 style,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        style
    );
    return 0;
}
static FONT_V2_SECTION(".text.font_v2_settings_heading_callback")
int font_v2_settings_heading_callback(
    u32 text,
    u32 style,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw =
        (FontV2NativeDraw)FONT_HEADING_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        style
    );
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_value_callback")
int font_v2_settings_value_callback(
    u32 text,
    u32 color,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_BODY_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        color
    );
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_row_common")
int font_v2_settings_row_common(
    const u8 *text,
    u32 style,
    float native_y,
    float box_x,
    u32 box_width,
    u32 fit_width,
    float fixed_scale_x,
    float glyph_height,
    u32 horizontal_alignment,
    u32 use_donor_ascii_metrics,
    u32 callback
) {
    FontV2Session session;
    u32 measured_width = 0u;
    u32 measured_lines = 0u;

    session.text = text;
    session.box_x = box_x;
    session.box_y = native_y;
    session.box_width = box_width;
    session.box_height = (u32)FONT_SETTINGS_LINE_HEIGHT;
    session.horizontal_alignment = horizontal_alignment;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_PREMEASURED;
    if (glyph_height > 0.0f) {
        session.flags |= FONT_V2_FLAG_GLYPH_HEIGHT;
        session.glyph_height = glyph_height;
    }
    session.line_limit = 1u;
    session.line_height = FONT_SETTINGS_LINE_HEIGHT;
    if (
        use_donor_ascii_metrics &&
        font_v2_measure(
            text,
            0u,
            &measured_width,
            &measured_lines
        ) == 0 &&
        measured_lines == 1u
    ) {
        session.measured_width = measured_width;
    } else {
        session.measured_width = font_v2_native_measure(text);
    }
    if (fixed_scale_x > 0.0f) {
        session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x = fixed_scale_x;
    } else if (fit_width && session.measured_width > fit_width) {
        session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x =
            (float)(s32)fit_width / (float)(s32)session.measured_width;
    } else if (!fit_width) {
        session.flags |= FONT_V2_FLAG_SHRINK_X;
    }
    session.line_count = 1u;
    session.callback = callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_battle_settings_label_adapter")
int font_v2_battle_settings_label_adapter(
    const u8 *text,
    u32 style,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        style,
        native_y + FONT_BATTLE_SETTINGS_ROW_Y_OFFSET +
            (style
                ? FONT_SETTINGS_SELECTED_Y_OFFSET +
                    FONT_BATTLE_SETTINGS_SELECTED_Y_OFFSET
                : FONT_BATTLE_SETTINGS_ORDINARY_Y_OFFSET),
        FONT_BATTLE_SETTINGS_LABEL_X,
        FONT_BATTLE_SETTINGS_LABEL_WIDTH,
        0u,
        0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        0u,
        (u32)font_v2_settings_label_callback
    );
}

FONT_V2_SECTION(".text.font_v2_practice_settings_label_adapter")
int font_v2_practice_settings_label_adapter(
    const u8 *text,
    u32 style,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        style,
        native_y + FONT_PRACTICE_SETTINGS_ROW_Y_OFFSET +
            (style
                ? FONT_SETTINGS_SELECTED_Y_OFFSET +
                    FONT_PRACTICE_SETTINGS_SELECTED_Y_OFFSET
                : 0.0f),
        FONT_PRACTICE_SETTINGS_LABEL_X,
        FONT_PRACTICE_SETTINGS_LABEL_WIDTH,
        0u,
        style ? FONT_PRACTICE_SETTINGS_SELECTED_SCALE_X : 0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        1u,
        (u32)font_v2_settings_label_callback
    );
}

static FONT_V2_SECTION(".text.font_v2_settings_value_common")
int font_v2_settings_value_common(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y,
    float box_x_offset,
    float numeric_y_offset,
    float numeric_scale_x,
    float numeric_glyph_height
) {
    volatile u8 *renderer =
        *(volatile u8 **)FONT_RENDERER_POINTER_ADDRESS;
    const u8 *cursor = text;
    float box_x = FONT_SETTINGS_VALUE_X + box_x_offset;
    u32 fit_width = 0u;
    u8 saved_renderer_flags = 0u;
    u32 numeric_value = 0u;
    u32 restore_renderer_flags = 0u;
    int result;

    (void)native_x;
    if (text && *text) {
        numeric_value = *text >= (u8)'0' && *text <= (u8)'9';
    }
    if (numeric_value) {
        box_x += FONT_SETTINGS_NUMERIC_VALUE_X_OFFSET;
        native_y +=
            FONT_SETTINGS_NUMERIC_VALUE_Y_OFFSET + numeric_y_offset;
    }
    if (
        renderer && text && *text && !numeric_value &&
        !(renderer[FONT_RENDERER_FLAGS_OFFSET] &
            (u8)FONT_RENDERER_ASCII_MODE_FLAG)
    ) {
        saved_renderer_flags = renderer[FONT_RENDERER_FLAGS_OFFSET];
        renderer[FONT_RENDERER_FLAGS_OFFSET] =
            saved_renderer_flags | (u8)FONT_RENDERER_ASCII_MODE_FLAG;
        restore_renderer_flags = 1u;
    }
    while (cursor && *cursor) {
        if (*cursor == (u8)' ') {
            box_x += FONT_SETTINGS_PHRASE_X_OFFSET;
            fit_width = FONT_SETTINGS_PHRASE_FIT_WIDTH;
            break;
        }
        cursor += 1;
    }
    result = font_v2_settings_row_common(
        text,
        color,
        native_y,
        box_x,
        FONT_SETTINGS_VALUE_WIDTH,
        fit_width,
        numeric_value ? numeric_scale_x : 0.0f,
        numeric_value ? numeric_glyph_height : 0.0f,
        FONT_V2_ALIGN_CENTER,
        0u,
        (u32)font_v2_settings_value_callback
    );
    if (restore_renderer_flags) {
        renderer[FONT_RENDERER_FLAGS_OFFSET] = saved_renderer_flags;
    }
    return result;
}

FONT_V2_SECTION(".text.font_v2_settings_value_adapter")
int font_v2_settings_value_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    float box_x_offset = FONT_PRACTICE_SETTINGS_VALUE_X_OFFSET;

    if (
        text &&
        font_v2_native_measure(text) <= FONT_SETTINGS_VALUE_WIDTH / 2u
    ) {
        box_x_offset = FONT_PRACTICE_SETTINGS_SHORT_VALUE_X_OFFSET;
    }
    return font_v2_settings_value_common(
        text,
        color,
        native_x,
        native_y,
        box_x_offset,
        0.0f,
        FONT_SETTINGS_NUMERIC_VALUE_SCALE_X,
        FONT_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT
    );
}

FONT_V2_SECTION(".text.font_v2_battle_settings_value_adapter")
int font_v2_battle_settings_value_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    u32 numeric_value =
        text && *text >= (u8)'0' && *text <= (u8)'9';
    float box_x_offset = numeric_value
        ? FONT_BATTLE_SETTINGS_NUMERIC_VALUE_X_OFFSET
        : FONT_BATTLE_SETTINGS_VALUE_X_OFFSET;

    if (!numeric_value) {
        box_x_offset =
            FONT_BATTLE_SETTINGS_PRIMARY_TEXT_VALUE_X_OFFSET;
        native_y += FONT_BATTLE_SETTINGS_VALUE_Y_OFFSET;
    }
    return font_v2_settings_value_common(
        text,
        color,
        native_x,
        native_y,
        box_x_offset,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_Y_OFFSET,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_SCALE_X,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT
    );
}

FONT_V2_SECTION(".text.font_v2_battle_settings_alternate_value_adapter")
int font_v2_battle_settings_alternate_value_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    u32 numeric_value =
        text && *text >= (u8)'0' && *text <= (u8)'9';
    float box_x_offset = numeric_value
        ? FONT_BATTLE_SETTINGS_NUMERIC_VALUE_X_OFFSET
        : FONT_BATTLE_SETTINGS_VALUE_X_OFFSET;

    if (!numeric_value) {
        native_y += FONT_BATTLE_SETTINGS_VALUE_Y_OFFSET;
    }
    return font_v2_settings_value_common(
        text,
        color,
        native_x,
        native_y,
        box_x_offset,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_Y_OFFSET,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_SCALE_X,
        FONT_BATTLE_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT
    );
}

FONT_V2_SECTION(".text.font_v2_practice_settings_heading_adapter")
int font_v2_practice_settings_heading_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        color,
        native_y,
        FONT_PRACTICE_SETTINGS_HEADING_X,
        FONT_PRACTICE_SETTINGS_HEADING_WIDTH,
        0u,
        0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        0u,
        (u32)font_v2_settings_heading_callback
    );
}
