#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

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

/* === Collection: shared list-family classification === */

/* Fixed native centered Collection text draw; do not tune. */
#define FONT_COLLECTION_HEADER_DRAW_ADDRESS 0x00379240u

/* Collection Characters selected-name origin correction. */
#define FONT_COLLECTION_INDEX_NAME_Y_OFFSET -5.6f

/* Collection Characters selected-name plaque box. */
#define FONT_COLLECTION_INDEX_NAME_BOX_WIDTH 190u
#define FONT_COLLECTION_INDEX_NAME_BOX_HEIGHT 32u

/* Shared Collection list-row raster origin. */
#define FONT_COLLECTION_X_OFFSET 1.2f

/* All three character-header callers share one centered-plaque X origin. */
#define FONT_COLLECTION_HEADER_X_OFFSET 1.6f

/* Figure and Music share one corrected direct-draw vertical origin. */
#define FONT_COLLECTION_FIGURE_MUSIC_HEADER_Y_OFFSET -5.0f

/* The parent Jutsu plaque starts seven output pixels below its NUN5 homolog. */
#define FONT_COLLECTION_JUTSU_HEADER_Y_OFFSET -5.6f

/* Figure rows are the only target family whose native X is above this. */
#define FONT_COLLECTION_NARROW_X_THRESHOLD 320.0f

/* Every other target list is right of this; companion lists remain native. */
#define FONT_COLLECTION_WIDE_X_THRESHOLD 256.0f

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
            FONT_V2_FLAG_FIXED_SCALE_X |
            FONT_V2_FLAG_PREMEASURED;
        frame.session.line_limit = 1u;
        frame.session.line_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
        frame.session.scale_x = FONT_JUTSU_HORIZONTAL_SCALE;
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
        FONT_V2_FLAG_FIXED_SCALE_X |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_JUTSU_LINE_LIMIT;
    frame.session.line_height = FONT_JUTSU_LINE_ADVANCE;
    frame.session.scale_x = FONT_JUTSU_HORIZONTAL_SCALE;
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

static FONT_V2_SECTION(".text.font_v2_collection_index_name_callback")
int font_v2_collection_index_name_callback(
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

FONT_V2_SECTION(".text.font_v2_collection_index_name_adapter")
int font_v2_collection_index_name_adapter(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style
) {
    FontV2Session session;
    u32 measured_width;
    u32 line_count;

    if (font_v2_measure(text, 0u, &measured_width, &line_count) != 0) {
        return -1;
    }
    if (
        text[0] == (u8)'G' &&
        text[1] == (u8)'r' &&
        text[2] == (u8)'a' &&
        text[3] == (u8)'n' &&
        text[4] == (u8)'n' &&
        text[5] == (u8)'y' &&
        text[6] == (u8)' ' &&
        text[7] == (u8)'C' &&
        text[8] == (u8)'h' &&
        text[9] == (u8)'i' &&
        text[10] == (u8)'y' &&
        text[11] == (u8)'o' &&
        text[12] == 0
    ) {
        /* NUN5's Collection table stores this label with one trailing space. */
        measured_width += font_v2_ascii_widths[0];
    }

    session.text = text;
    session.box_x =
        native_x - (float)(FONT_COLLECTION_INDEX_NAME_BOX_WIDTH / 2u);
    session.box_y = native_y + FONT_COLLECTION_INDEX_NAME_Y_OFFSET;
    session.box_width = FONT_COLLECTION_INDEX_NAME_BOX_WIDTH;
    session.box_height = FONT_COLLECTION_INDEX_NAME_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X | FONT_V2_FLAG_PREMEASURED;
    session.line_limit = 1u;
    session.line_height = (float)FONT_COLLECTION_INDEX_NAME_BOX_HEIGHT;
    session.callback = (u32)font_v2_collection_index_name_callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    session.measured_width = measured_width;
    session.line_count = line_count;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_collection_figure_music_header_adapter")
void font_v2_collection_figure_music_header_adapter(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style
) {
    FontV2NativeDraw draw =
        (FontV2NativeDraw)FONT_COLLECTION_HEADER_DRAW_ADDRESS;

    draw(
        native_x + FONT_COLLECTION_HEADER_X_OFFSET,
        native_y + FONT_COLLECTION_FIGURE_MUSIC_HEADER_Y_OFFSET,
        text,
        style
    );
}

FONT_V2_SECTION(".text.font_v2_collection_jutsu_header_adapter")
void font_v2_collection_jutsu_header_adapter(
    float native_x,
    float native_y,
    const u8 *text,
    u32 style
) {
    FontV2NativeDraw draw =
        (FontV2NativeDraw)FONT_COLLECTION_HEADER_DRAW_ADDRESS;

    draw(
        native_x + FONT_COLLECTION_HEADER_X_OFFSET,
        native_y + FONT_COLLECTION_JUTSU_HEADER_Y_OFFSET,
        text,
        style
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
    if (native_x > FONT_COLLECTION_NARROW_X_THRESHOLD) {
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
