#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* The NUN5 Jutsu display and Practice completion plate wrap and center at most two lines. */
#define FONT_JUTSU_DISPLAY_WIDTH 208u
/* Center the original text width on the complete plate, spanning X=126..386. */
#define FONT_PRACTICE_PLATE_CENTER_X 256.0f
#define FONT_PRACTICE_PLATE_TEXT_WIDTH 208u
#define FONT_MOVE_DISPLAY_LINES 2u
#define FONT_MOVE_DISPLAY_NATIVE_ADVANCE 20.0f
#define FONT_MOVE_DISPLAY_NATIVE_HEIGHT 28.0f

extern u32 font_glyph_metric_lookup(void *context, u32 value);

static FONT_V2_SECTION(".text.font_v2_move_display_callback")
int font_v2_move_display_callback(
    u32 renderer_address,
    u8 *text,
    u32 unused,
    FontV2Session *session
) {
    volatile float *renderer = (volatile float *)renderer_address;
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;
    float saved_x = renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)];
    float saved_y = renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)];
    float origin_x = renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(float)];
    float origin_y = renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(float)];
    u8 *line = text;
    u8 *cursor = text;
    u32 line_index = 0u;

    (void)unused;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            float width;
            *cursor = 0u;
            width = (float)(s32)font_v2_native_measure(line) * session->scale_x;
            set_position(
                session->box_x +
                    ((float)(s32)session->box_width - width) * 0.5f - origin_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height - origin_y,
                renderer_address
            );
            draw(renderer_address, line);
            *cursor = saved;
            if (!saved) {
                break;
            }
            line = cursor + 1;
            line_index += 1u;
        }
        cursor += 1;
    }
    set_position(saved_x - origin_x, saved_y - origin_y, renderer_address);
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_move_display_draw")
int font_v2_move_display_draw(
    u32 renderer_address,
    const u8 *text,
    u32 box_width,
    u32 box_height,
    u32 preserve_glyph_height,
    float box_x,
    float box_y
) {
    FontV2BodyFrame frame;
    volatile float *renderer = (volatile float *)renderer_address;
    float line_height;

    if (!renderer || !text || font_v2_wrap_retry(
            frame.buffer, text,
            box_width, FONT_MOVE_DISPLAY_LINES,
            &frame.session.measured_width, &frame.session.line_count
        )) {
        return -1;
    }
    line_height = (float)(s32)box_height / (float)(s32)frame.session.line_count;
    if (line_height > FONT_MOVE_DISPLAY_NATIVE_ADVANCE) {
        line_height = FONT_MOVE_DISPLAY_NATIVE_ADVANCE;
    }
    frame.session.text = frame.buffer;
    frame.session.box_x =
        box_x + renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(float)];
    frame.session.box_y =
        box_y + renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(float)];
    frame.session.box_width = box_width;
    frame.session.box_height = box_height;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags = FONT_V2_FLAG_PREMEASURED |
        FONT_V2_FLAG_SHRINK_X | FONT_V2_FLAG_GLYPH_HEIGHT;
    frame.session.line_limit = FONT_MOVE_DISPLAY_LINES;
    frame.session.line_height = line_height;
    frame.session.glyph_height = FONT_MOVE_DISPLAY_NATIVE_HEIGHT;
    if (preserve_glyph_height) {
        const u8 *cursor = frame.buffer;
        float line_y = 0.0f;
        float ink_top = 0.0f;
        float ink_bottom = 0.0f;
        u32 has_ink = 0u;

        /* Native metrics exclude one transparent border row on each side.
         * At the preserved 28-unit quad height, raster rows map 1:1 to Y:
         * the native texture also samples 28 rows, including its padding.
         */
        while (*cursor) {
            if (*cursor == (u8)'\n') {
                line_y += line_height;
            } else if (*cursor != (u8)' ') {
                u32 metric = font_glyph_metric_lookup(
                    (void *)renderer_address, *cursor
                );
                float top = line_y + (float)((metric >> 8) & 0xFFu) + 1.0f;
                float bottom = line_y + FONT_MOVE_DISPLAY_NATIVE_ADVANCE -
                    (float)(metric >> 24) - 1.0f;
                if (!has_ink || top < ink_top) {
                    ink_top = top;
                }
                if (!has_ink || bottom > ink_bottom) {
                    ink_bottom = bottom;
                }
                has_ink = 1u;
            }
            cursor += 1;
        }
        if (has_ink) {
            frame.session.box_y +=
                ((float)(s32)box_height - ink_top - ink_bottom) * 0.5f;
            frame.session.vertical_alignment = FONT_V2_ALIGN_START;
        }
    } else {
        frame.session.glyph_height *=
            line_height / FONT_MOVE_DISPLAY_NATIVE_ADVANCE;
    }
    frame.session.callback = (u32)font_v2_move_display_callback;
    frame.session.callback_arg0 = renderer_address;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0u;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_jutsu_display_entry")
int font_v2_jutsu_display_entry(
    u32 renderer_address,
    const u8 *text,
    float native_x,
    float native_y
) {
    return font_v2_move_display_draw(
        renderer_address, text, FONT_JUTSU_DISPLAY_WIDTH, 30u, 0u,
        native_x, native_y - 11.0f
    );
}

FONT_V2_SECTION(".text.font_v2_practice_completed_plate_entry")
int font_v2_practice_completed_plate_entry(
    u32 renderer_address,
    const u8 *text,
    float shake_x,
    float shake_y
) {
    return font_v2_move_display_draw(
        renderer_address, text, FONT_PRACTICE_PLATE_TEXT_WIDTH, 32u, 1u,
        shake_x + FONT_PRACTICE_PLATE_CENTER_X -
            (float)FONT_PRACTICE_PLATE_TEXT_WIDTH * 0.5f,
        shake_y + 300.0f - 16.0f
    );
}
