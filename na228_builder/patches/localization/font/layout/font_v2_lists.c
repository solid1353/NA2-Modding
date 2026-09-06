#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* === Battle Settings: left and right Jutsu-selector lists === */

/* Nominal wrap width; larger values produce fewer or later line breaks. */
#define FONT_JUTSU_BOX_WIDTH 186u

/* Wrapped-block box height used for vertical centering. */
#define FONT_JUTSU_BOX_HEIGHT 32u

/* Horizontal correction for the left list; more negative moves rows left. */
#define FONT_JUTSU_LEFT_X_OFFSET -6.4f

/* Horizontal correction for the right list; more negative moves rows left. */
#define FONT_JUTSU_RIGHT_X_OFFSET -4.0f

/* Vertical correction for fitting one-line rows; more negative moves them up. */
#define FONT_JUTSU_SINGLE_LINE_Y_OFFSET -4.0f

/* Applied only to wrapped blocks; more negative moves the block up. */
#define FONT_JUTSU_Y_OFFSET -6.5f

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

/* === Collection: shared list-family classification === */

/* Fixed native centered Collection text draw; do not tune. */
#define FONT_COLLECTION_HEADER_DRAW_ADDRESS 0x00379240u

/* Shared top-plaque origin correction for the non-Figure Collection screens. */
#define FONT_COLLECTION_PLAQUE_Y_OFFSET -5.6f

/* NUN5's shared one-line Collection top-plaque box. */
#define FONT_COLLECTION_PLAQUE_BOX_WIDTH 190u
#define FONT_COLLECTION_PLAQUE_BOX_HEIGHT 32u

/* Shared Collection list-row raster origin. */
#define FONT_COLLECTION_X_OFFSET 0.0f

/* Figure rows are the only target family whose native X is above this. */
#define FONT_COLLECTION_NARROW_X_THRESHOLD 320.0f

/* Every other target list is right of this; companion lists remain native. */
#define FONT_COLLECTION_WIDE_X_THRESHOLD 256.0f

/* Collection Opponents is the sole target list at this native draw origin. */
#define FONT_COLLECTION_OPPONENT_X 30.0f

/* Added to wrapped Collection rows; more negative moves the block up. */
#define FONT_COLLECTION_LIST_BOX_Y_OFFSET -8.0f

/* Fitting target rows share the same native-origin vertical correction. */
#define FONT_COLLECTION_SINGLE_LINE_Y_OFFSET -4.0f

/* Narrow Figure-page wrap width; larger values wrap later. */
#define FONT_COLLECTION_NARROW_BOX_WIDTH 152u

/* Shared wide-list wrap width; larger values wrap later. */
#define FONT_COLLECTION_WIDE_BOX_WIDTH 192u

/* Collection row box height used for vertical block placement. */
#define FONT_COLLECTION_LIST_BOX_HEIGHT 32u

/* Vertical distance between wrapped Collection-row lines. */
#define FONT_COLLECTION_LIST_LINE_ADVANCE 16.0f

/* Glyph height used for Collection block layout, not automatic squeezing. */
#define FONT_COLLECTION_LIST_GLYPH_HEIGHT 20.0f

/* Maximum wrapped lines supported by the Collection list adapter. */
#define FONT_COLLECTION_LIST_LINE_LIMIT 2u

/* === Collection Figures: Diorama plaque and localized viewer prompts === */

/* NA2 passes the center of NUN5's 190-by-32 Diorama title plaque. */
#define FONT_COLLECTION_DIORAMA_BOX_HALF_WIDTH 95.0f
#define FONT_COLLECTION_DIORAMA_BOX_HALF_HEIGHT 20.0f
#define FONT_COLLECTION_DIORAMA_BOX_WIDTH 190u
/* Keep the accepted non-collapsed vertical layout instead of squeezing to 32. */
#define FONT_COLLECTION_DIORAMA_BOX_HEIGHT 40u

/* NUN5 places the boxed title four units below the plaque record's top. */
#define FONT_COLLECTION_DIORAMA_BOX_Y_OFFSET 4.0f

/* NUN5's two-line title layout preserves native glyph height and spacing. */
#define FONT_COLLECTION_DIORAMA_LINE_ADVANCE 16.0f
#define FONT_COLLECTION_DIORAMA_GLYPH_HEIGHT 22.0f
#define FONT_COLLECTION_DIORAMA_LINE_LIMIT 2u

/* NUN5 passes the title plaque's exact width to its two-line wrapper. */
#define FONT_COLLECTION_DIORAMA_WRAP_WIDTH FONT_COLLECTION_DIORAMA_BOX_WIDTH

/* Preserve the taller raster while matching each NUN5 title baseline. */
#define FONT_COLLECTION_DIORAMA_SINGLE_LINE_Y_OFFSET -5.0f
#define FONT_COLLECTION_DIORAMA_WRAPPED_Y_OFFSET 0.0f

/* Fixed NA2 sprite helper used by the localized NUN5 atlas rectangles. */
#define FONT_COLLECTION_SPRITE_DRAW_ADDRESS 0x0037BB40u

/* Official NUN5 HOME atlas records selected by its Collection accessor. */
static const s16 font_v2_collection_diorama_prompt_records[]
__attribute__((
    section(".rodata.font_v2_collection_diorama_prompt_records"),
    aligned(2)
)) = {
    144, 72, 112, 24,
    208, 96, 48, 24,
    132, 96, 76, 24
};

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

static FONT_V2_SECTION(".text.font_v2_jutsu_draw_callback")
int font_v2_jutsu_draw_callback(
    u32 renderer_address,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    volatile float *renderer = (volatile float *)renderer_address;
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;
    float saved_x;
    float saved_y;
    float origin_x;
    float origin_y;
    u8 *cursor;
    u8 *line_start;
    u32 line_index;

    (void)arg2;
    if (!renderer || !text || !session) {
        return -1;
    }

    saved_x = renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)];
    saved_y = renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)];
    origin_x = renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(float)];
    origin_y = renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(float)];
    cursor = (u8 *)text;
    line_start = cursor;
    line_index = 0;

    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            set_position(
                session->draw_x - origin_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height -
                    origin_y,
                renderer_address
            );
            draw(renderer_address, line_start);
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
            line_index += 1;
        } else {
            cursor += 1;
        }
    }

    set_position(
        saved_x - origin_x,
        saved_y - origin_y,
        renderer_address
    );
    return 0;
}
FONT_V2_SECTION(".text.font_v2_jutsu_draw_entry")
int font_v2_jutsu_draw_entry(
    u32 renderer_address,
    const u8 *text
) {
    FontV2BodyFrame frame;
    volatile float *renderer = (volatile float *)renderer_address;
    float native_x;
    float native_y;

    if (!renderer || !text) {
        return -1;
    }

    if (
        font_v2_wrap_retry(
            frame.buffer,
            text,
            FONT_JUTSU_BOX_WIDTH,
            FONT_JUTSU_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        )
    ) {
        return -1;
    }

    native_x =
        renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)];
    native_y =
        renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)];

    if (frame.session.line_count <= 1u) {
        frame.session.text = frame.buffer;
        frame.session.box_x =
            native_x +
            (
                native_x < FONT_JUTSU_SIDE_THRESHOLD
                    ? FONT_JUTSU_LEFT_X_OFFSET
                    : FONT_JUTSU_RIGHT_X_OFFSET
            );
        frame.session.box_y =
            native_y + FONT_JUTSU_SINGLE_LINE_Y_OFFSET;
        frame.session.box_width = FONT_JUTSU_BOX_WIDTH;
        frame.session.box_height = FONT_JUTSU_BOX_HEIGHT;
        frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
        frame.session.vertical_alignment = FONT_V2_ALIGN_START;
        frame.session.flags =
            FONT_V2_FLAG_SHRINK_X |
            FONT_V2_FLAG_PREMEASURED;
        frame.session.line_limit = 1u;
        frame.session.line_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
        frame.session.glyph_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
        frame.session.callback = (u32)font_v2_jutsu_draw_callback;
        frame.session.callback_arg0 = renderer_address;
        frame.session.callback_arg1 = (u32)frame.buffer;
        frame.session.callback_arg2 = 0;
        frame.session.callback_arg3 = (u32)&frame.session;
        return font_v2_adapter_call(&frame.session);
    }

    frame.session.text = frame.buffer;
    frame.session.box_x =
        native_x +
        (
            native_x < FONT_JUTSU_SIDE_THRESHOLD
                ? FONT_JUTSU_LEFT_X_OFFSET
                : FONT_JUTSU_RIGHT_X_OFFSET
        );
    frame.session.box_y = native_y + FONT_JUTSU_Y_OFFSET;
    frame.session.box_width = FONT_JUTSU_BOX_WIDTH;
    frame.session.box_height = FONT_JUTSU_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_GLYPH_HEIGHT |
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_JUTSU_LINE_LIMIT;
    frame.session.line_height = FONT_JUTSU_LINE_ADVANCE;
    frame.session.glyph_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_jutsu_draw_callback;
    frame.session.callback_arg0 = renderer_address;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

static FONT_V2_SECTION(".text.font_v2_collection_list_callback")
int font_v2_collection_list_callback(
    u32 text,
    u32 highlighted,
    u32 arg2,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;
    u8 *cursor = (u8 *)text;
    u8 *line_start = cursor;
    u32 line_index = 0;

    (void)arg2;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            draw(
                session->draw_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height,
                line_start,
                highlighted
            );
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
            line_index += 1;
        } else {
            cursor += 1;
        }
    }
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_collection_plaque_callback")
int font_v2_collection_plaque_callback(
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

static FONT_V2_SECTION(".text.font_v2_collection_diorama_title_callback")
int font_v2_collection_diorama_title_callback(
    u32 text,
    u32 style,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;
    u8 *cursor = (u8 *)text;
    u8 *line_start = cursor;
    u32 line_index = 0u;

    (void)unused;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            u32 line_width;
            u32 line_count;
            float line_x = session->draw_x;

            *cursor = 0u;
            if (
                font_v2_measure(
                    line_start,
                    0u,
                    &line_width,
                    &line_count
                ) == 0
            ) {
                line_x =
                    session->box_x +
                    (
                        (float)(s32)session->box_width -
                        (float)(s32)line_width * session->scale_x
                    ) * 0.5f;
            }
            draw(
                line_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height,
                line_start,
                style
            );
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
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_collection_plaque_draw")
int font_v2_collection_plaque_draw(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style,
    u32 measured_width,
    u32 line_count
) {
    FontV2Session session;

    session.text = text;
    session.box_x =
        native_x - (float)(FONT_COLLECTION_PLAQUE_BOX_WIDTH / 2u);
    session.box_y = native_y + FONT_COLLECTION_PLAQUE_Y_OFFSET;
    session.box_width = FONT_COLLECTION_PLAQUE_BOX_WIDTH;
    session.box_height = FONT_COLLECTION_PLAQUE_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X | FONT_V2_FLAG_PREMEASURED;
    session.line_limit = 1u;
    session.line_height = (float)FONT_COLLECTION_PLAQUE_BOX_HEIGHT;
    session.callback = (u32)font_v2_collection_plaque_callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    session.measured_width = measured_width;
    session.line_count = line_count;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_collection_plaque_adapter")
int font_v2_collection_plaque_adapter(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style
) {
    FontV2NativeDraw native_draw =
        (FontV2NativeDraw)FONT_COLLECTION_HEADER_DRAW_ADDRESS;
    u32 measured_width;
    u32 line_count;

    if (
        font_v2_measure(text, 0u, &measured_width, &line_count) != 0 ||
        font_v2_collection_plaque_draw(
            native_x,
            native_y,
            text,
            style,
            measured_width,
            line_count
        ) != 0
    ) {
        native_draw(native_x, native_y, text, style);
        return -1;
    }
    return 0;
}

FONT_V2_SECTION(".text.font_v2_collection_diorama_title_adapter")
int font_v2_collection_diorama_title_adapter(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style
) {
    FontV2BodyFrame frame;
    FontV2NativeDraw native_draw =
        (FontV2NativeDraw)FONT_COLLECTION_HEADER_DRAW_ADDRESS;
    if (!text) {
        return -1;
    }
    if (
        font_v2_wrap_retry(
            frame.buffer,
            text,
            FONT_COLLECTION_DIORAMA_WRAP_WIDTH,
            FONT_COLLECTION_DIORAMA_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        )
    ) {
        native_draw(native_x, native_y, text, style);
        return -1;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x =
        native_x - FONT_COLLECTION_DIORAMA_BOX_HALF_WIDTH;
    frame.session.box_y =
        native_y - FONT_COLLECTION_DIORAMA_BOX_HALF_HEIGHT +
        FONT_COLLECTION_DIORAMA_BOX_Y_OFFSET +
        (
            frame.session.line_count == 1u
                ? FONT_COLLECTION_DIORAMA_SINGLE_LINE_Y_OFFSET
                : FONT_COLLECTION_DIORAMA_WRAPPED_Y_OFFSET
        );
    frame.session.box_width = FONT_COLLECTION_DIORAMA_BOX_WIDTH;
    frame.session.box_height = FONT_COLLECTION_DIORAMA_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED |
        FONT_V2_FLAG_SHRINK_X;
    frame.session.line_limit = FONT_COLLECTION_DIORAMA_LINE_LIMIT;
    frame.session.line_height = FONT_COLLECTION_DIORAMA_LINE_ADVANCE;
    frame.session.glyph_height = FONT_COLLECTION_DIORAMA_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_collection_diorama_title_callback;
    frame.session.callback_arg0 = (u32)frame.buffer;
    frame.session.callback_arg1 = style;
    frame.session.callback_arg2 = 0u;
    frame.session.callback_arg3 = (u32)&frame.session;

    if (font_v2_adapter_call(&frame.session) != 0) {
        native_draw(native_x, native_y, text, style);
        return -1;
    }
    return 0;
}

FONT_V2_SECTION(".text.font_v2_collection_diorama_prompt_adapter")
void font_v2_collection_diorama_prompt_adapter(
    float native_x,
    float native_y,
    u32 renderer,
    const s16 *native_record
) {
    typedef void (*FontV2NativeSpriteDraw)(
        float draw_x,
        float draw_y,
        u32 renderer_address,
        const s16 *record
    );
    FontV2NativeSpriteDraw draw =
        (FontV2NativeSpriteDraw)FONT_COLLECTION_SPRITE_DRAW_ADDRESS;
    const s16 *record = native_record;
    float draw_x = native_x;
    float draw_y = native_y;

    if (native_x == 374.0f && native_y == 324.0f) {
        record = font_v2_collection_diorama_prompt_records;
        draw_y = 309.0f;
    } else if (native_x == 442.0f && native_y == 324.0f) {
        record = font_v2_collection_diorama_prompt_records + 4;
        draw_x = 414.0f;
    }
    draw(draw_x, draw_y, renderer, record);
}

FONT_V2_SECTION(".text.font_v2_collection_diorama_display_prompt_adapter")
void font_v2_collection_diorama_display_prompt_adapter(
    float native_x,
    float native_y,
    u32 renderer,
    const s16 *native_record
) {
    typedef void (*FontV2NativeSpriteDraw)(
        float draw_x,
        float draw_y,
        u32 renderer_address,
        const s16 *record
    );
    FontV2NativeSpriteDraw draw =
        (FontV2NativeSpriteDraw)FONT_COLLECTION_SPRITE_DRAW_ADDRESS;

    (void)native_x;
    (void)native_y;
    (void)native_record;
    draw(
        414.0f,
        324.0f,
        renderer,
        font_v2_collection_diorama_prompt_records + 8
    );
}

FONT_V2_SECTION(".text.font_v2_collection_list_entry")
int font_v2_collection_list_entry(
    const u8 *text,
    u32 highlighted,
    float native_x,
    float native_y
) {
    FontV2BodyFrame frame;
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;
    u32 box_width = 0;

    if (!text) {
        return -1;
    }
    if (native_x == FONT_COLLECTION_OPPONENT_X) {
        box_width = FONT_COLLECTION_WIDE_BOX_WIDTH;
    } else if (native_x > FONT_COLLECTION_NARROW_X_THRESHOLD) {
        box_width = FONT_COLLECTION_NARROW_BOX_WIDTH;
    } else if (native_x > FONT_COLLECTION_WIDE_X_THRESHOLD) {
        box_width = FONT_COLLECTION_WIDE_BOX_WIDTH;
    } else {
        draw(native_x, native_y, text, highlighted);
        return 0;
    }

    if (
        font_v2_wrap_retry(
            frame.buffer,
            text,
            box_width,
            FONT_COLLECTION_LIST_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        )
    ) {
        return -1;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x = native_x + FONT_COLLECTION_X_OFFSET;
    frame.session.box_y = native_y + (
        frame.session.line_count == 1u
            ? FONT_COLLECTION_SINGLE_LINE_Y_OFFSET
            : FONT_COLLECTION_LIST_BOX_Y_OFFSET
    );
    frame.session.box_width = box_width;
    frame.session.box_height = frame.session.line_count == 1u
        ? (u32)FONT_COLLECTION_LIST_GLYPH_HEIGHT
        : FONT_COLLECTION_LIST_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED |
        FONT_V2_FLAG_SHRINK_X;
    if (frame.session.line_count == 1u) {
        frame.session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        frame.session.scale_x = 1.0f;
    }
    frame.session.line_limit = FONT_COLLECTION_LIST_LINE_LIMIT;
    frame.session.line_height = FONT_COLLECTION_LIST_LINE_ADVANCE;
    frame.session.glyph_height = FONT_COLLECTION_LIST_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_collection_list_callback;
    frame.session.callback_arg0 = (u32)frame.buffer;
    frame.session.callback_arg1 = highlighted;
    frame.session.callback_arg2 = 0;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}
