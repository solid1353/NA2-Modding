#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* === Ninja Song objective and arithmetic rows === */

/* NUN5 objective row geometry converted to NA2 renderer coordinates. */
#define FONT_NINJA_OBJECTIVE_INDEX_ORIGIN_X 81.6f
#define FONT_NINJA_OBJECTIVE_INDEX_LEADING_SPACE_OFFSET 5.6f
#define FONT_NINJA_OBJECTIVE_MARKER_ORIGIN_X 88.0f
#define FONT_NINJA_OBJECTIVE_PROSE_X 113.6f
#define FONT_NINJA_OBJECTIVE_INDEX_Y_OFFSET 0.8f
#define FONT_NINJA_OBJECTIVE_MARKER_Y_OFFSET -1.6f
#define FONT_NINJA_OBJECTIVE_PROSE_Y_OFFSET 0.8f
#define FONT_NINJA_OBJECTIVE_Y_OFFSET -9.6f
#define FONT_NINJA_OBJECTIVE_WIDTH 288u
#define FONT_NINJA_OBJECTIVE_HEIGHT 32u
#define FONT_NINJA_OBJECTIVE_LINE_LIMIT 2u
/* Layout-only height reproduces donor line-count centering; glyphs stay native. */
#define FONT_NINJA_OBJECTIVE_LAYOUT_LINE_HEIGHT 12.8f
/* Visible baselines retain the donor's full 16-unit separation. */
#define FONT_NINJA_OBJECTIVE_LINE_ADVANCE 16.0f

/* NUN5 arithmetic positions relative to the shared formula origin. */
#define FONT_NINJA_FORMULA_Y_OFFSET 0.975f
#define FONT_NINJA_UNIT_X_OFFSET 176.0f
#define FONT_NINJA_UNIT_Y_OFFSET -6.0f
#define FONT_NINJA_UNIT_SCALE_X 0.62f
#define FONT_NINJA_UNIT_WIDTH 52u
#define FONT_NINJA_UNIT_HEIGHT 32u
#define FONT_NINJA_EQUALS_X_OFFSET 227.0f
#define FONT_NINJA_TOTAL_X_OFFSET 263.4f
#define FONT_NINJA_TOTAL_WIDTH 64u
#define FONT_NINJA_EMPTY_X_OFFSET 256.075f
#define FONT_NINJA_EMPTY_WIDTH 96u
#define FONT_NINJA_EMPTY_SCALE_X 0.97f
#define FONT_NINJA_SINGLE_LINE_HEIGHT 20.0f

/* Fixed NA2 Ninja Song renderer data contracts; do not tune. */
#define FONT_NINJA_MULTIPLY_POINTER_ADDRESS 0x00899A90u
#define FONT_NINJA_EQUALS_POINTER_ADDRESS 0x00899A94u
#define FONT_NINJA_EMPTY_POINTER_ADDRESS 0x00899A98u
#define FONT_NINJA_MARKER_POINTER_ADDRESS 0x00899A9Cu
#define FONT_NINJA_INDEX_TABLE_ADDRESS 0x008993E0u
#define FONT_NINJA_UNIT_TABLE_ADDRESS 0x00899AE0u
#define FONT_NINJA_MULTIPLIER_TABLE_ADDRESS 0x008C3CB0u
#define FONT_NINJA_RENDERER_FLAGS_OFFSET 0x70u

/* === Shared temporary body storage: internal capacity === */

/* Maximum copied body/list text bytes including the terminator; not geometry. */
#define FONT_BODY_BUFFER_SIZE 0x100u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

static FONT_V2_SECTION(".text.font_v2_ninja_text_callback")
int font_v2_ninja_text_callback(
    u32 renderer_address,
    u32 text,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;

    (void)unused;
    set_position(session->draw_x, session->draw_y, renderer_address);
    draw(renderer_address, (const u8 *)text);
    return 0;
}
static FONT_V2_SECTION(".text.font_v2_ninja_text_common")
int font_v2_ninja_text_common(
    u32 renderer_address,
    const u8 *text,
    float x_offset,
    float y_offset,
    u32 box_width,
    u32 box_height,
    u32 horizontal_alignment,
    float fixed_scale_x
) {
    volatile float *renderer = (volatile float *)renderer_address;
    FontV2Session session;

    if (!renderer || !text) {
        return -1;
    }
    session.text = text;
    session.box_x =
        renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)] +
        x_offset;
    session.box_y =
        renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)] +
        y_offset;
    session.box_width = box_width;
    session.box_height = box_height;
    session.horizontal_alignment = horizontal_alignment;
    session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    if (fixed_scale_x > 0.0f) {
        session.flags = FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x = fixed_scale_x;
    } else {
        session.flags = FONT_V2_FLAG_SHRINK_X;
    }
    session.line_limit = 1u;
    session.line_height = FONT_NINJA_SINGLE_LINE_HEIGHT;
    session.callback = (u32)font_v2_ninja_text_callback;
    session.callback_arg0 = renderer_address;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    return font_v2_adapter_call(&session);
}

static FONT_V2_SECTION(".text.font_v2_ninja_compact_adapter")
int font_v2_ninja_compact_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        512u,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_START,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_unit_adapter")
int font_v2_ninja_unit_adapter(
    u32 renderer_address,
    const u8 *text
) {
    if (!text || !*text) {
        return 0;
    }
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_UNIT_WIDTH,
        FONT_NINJA_UNIT_HEIGHT,
        FONT_V2_ALIGN_START,
        FONT_NINJA_UNIT_SCALE_X
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_equals_adapter")
int font_v2_ninja_equals_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        32u,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_START,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_total_adapter")
int font_v2_ninja_total_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_TOTAL_WIDTH,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_CENTER,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_empty_adapter")
int font_v2_ninja_empty_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_EMPTY_WIDTH,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_CENTER,
        FONT_NINJA_EMPTY_SCALE_X
    );
}

FONT_V2_SECTION(".text.font_v2_ninja_arithmetic_template")
void font_v2_ninja_arithmetic_template(
    float native_x,
    float native_y,
    u32 row_set,
    s32 row_index
) {
    FontV2NativeSetColor set_color =
        (FontV2NativeSetColor)FONT_SET_RGBA_COLOR_ADDRESS;
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    u32 renderer_address = *(volatile u32 *)FONT_RENDERER_POINTER_ADDRESS;
    volatile u8 *renderer_flags;
    s32 *row;
    u32 descriptor;
    const u8 *unit_text;
    u8 number[32];

    if (!renderer_address || !row_set) {
        return;
    }
    renderer_flags = (volatile u8 *)(
        renderer_address + FONT_NINJA_RENDERER_FLAGS_OFFSET
    );
    native_x += 10.0f;
    native_y += FONT_NINJA_FORMULA_Y_OFFSET;
    row = (s32 *)(
        *(u32 *)(row_set + 4u) + (u32)row_index * 12u
    );
    descriptor = (u32)row[0];
    set_color(renderer_address, 0x00404070u, 1u);

    if (row[2] == 0) {
        set_position(
            native_x + FONT_NINJA_EMPTY_X_OFFSET,
            native_y,
            renderer_address
        );
        font_v2_ninja_empty_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_EMPTY_POINTER_ADDRESS
        );
        return;
    }

    *renderer_flags &= (u8)0xF7u;
    if (row_index != 10 && row_index != 13 && row_index != 9) {
        font_ninja_song_ascii_number(
            0u,
            (s32)*(s16 *)descriptor,
            3,
            number,
            0
        );
        set_position(native_x + 30.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(renderer_address, number);

        set_position(native_x + 90.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_MULTIPLY_POINTER_ADDRESS
        );

        font_ninja_song_ascii_number(
            0u,
            row[1],
            3,
            number,
            0
        );
        if (
            row[1] == (s32)*(s16 *)(
                FONT_NINJA_MULTIPLIER_TABLE_ADDRESS +
                (s32)*(s8 *)(descriptor + 4u) * 2
            )
        ) {
            set_color(renderer_address, 0x000000D4u, 1u);
        } else {
            set_color(renderer_address, 0x00404070u, 1u);
        }
        set_position(native_x + 120.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(renderer_address, number);
        set_color(renderer_address, 0x00404070u, 1u);

        unit_text = ((const u8 **)FONT_NINJA_UNIT_TABLE_ADDRESS)[
            (u32)*(s16 *)(descriptor + 2u)
        ];
        set_position(
            native_x + FONT_NINJA_UNIT_X_OFFSET,
            native_y + FONT_NINJA_UNIT_Y_OFFSET,
            renderer_address
        );
        font_v2_ninja_unit_adapter(renderer_address, unit_text);

        set_position(
            native_x + FONT_NINJA_EQUALS_X_OFFSET,
            native_y,
            renderer_address
        );
        font_v2_ninja_equals_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_EQUALS_POINTER_ADDRESS
        );
    }

    font_ninja_song_ascii_number(0u, row[2], 5, number, 0);
    set_position(
        native_x + FONT_NINJA_TOTAL_X_OFFSET,
        native_y,
        renderer_address
    );
    font_v2_ninja_total_adapter(renderer_address, number);
    *renderer_flags = (*renderer_flags & (u8)0xF7u) | (u8)8u;
}

static FONT_V2_SECTION(".text.font_v2_ninja_objective_callback")
int font_v2_ninja_objective_callback(
    u32 text,
    u32 color,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_BODY_DRAW_ADDRESS;
    u8 *cursor = (u8 *)text;
    u8 *line_start = cursor;
    u32 line_index = 0u;

    (void)unused;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            draw(
                session->draw_x,
                session->draw_y +
                    (float)(s32)line_index *
                        FONT_NINJA_OBJECTIVE_LINE_ADVANCE,
                line_start,
                color
            );
            if (!saved) {
                break;
            }
            *cursor = saved;
            line_index += 1u;
            cursor += 1;
            line_start = cursor;
        } else {
            cursor += 1;
        }
    }
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_ninja_objective_draw")
int font_v2_ninja_objective_draw(
    const u8 *text,
    u32 color,
    float box_x,
    float native_y
) {
    FontV2BodyFrame frame;
    u32 index = 0u;

    if (!text) {
        return -1;
    }
    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        frame.buffer[index] = text[index];
        index += 1u;
    }
    frame.buffer[index] = 0u;
    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_NINJA_OBJECTIVE_WIDTH,
            FONT_NINJA_OBJECTIVE_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x = box_x;
    frame.session.box_y = native_y + FONT_NINJA_OBJECTIVE_Y_OFFSET;
    frame.session.box_width = FONT_NINJA_OBJECTIVE_WIDTH;
    frame.session.box_height = FONT_NINJA_OBJECTIVE_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_NINJA_OBJECTIVE_LINE_LIMIT;
    frame.session.line_height = FONT_NINJA_OBJECTIVE_LAYOUT_LINE_HEIGHT;
    frame.session.callback = (u32)font_v2_ninja_objective_callback;
    frame.session.callback_arg0 = (u32)frame.buffer;
    frame.session.callback_arg1 = color;
    frame.session.callback_arg2 = 0u;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_ninja_objective_row_adapter")
void font_v2_ninja_objective_row_adapter(
    u32 page,
    u32 row_record,
    u32 display_index,
    u32 row_y_bits
) {
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeSetColor set_color =
        (FontV2NativeSetColor)FONT_SET_INDEXED_COLOR_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;
    u32 renderer_address = *(volatile u32 *)FONT_RENDERER_POINTER_ADDRESS;
    const u8 *const *index_table =
        (const u8 *const *)FONT_NINJA_INDEX_TABLE_ADDRESS;
    const u8 *marker = *(const u8 **)FONT_NINJA_MARKER_POINTER_ADDRESS;
    u32 descriptor = *(u32 *)row_record;
    const u8 *prose = *(const u8 **)(descriptor + 8u);
    FontV2Bits row_y;
    const u8 *index_text;
    const u8 *index_end;
    u32 index_width;
    u32 index_lines;

    (void)page;
    row_y.u = row_y_bits;
    index_text = index_table[display_index];
    if (font_v2_measure(index_text, 0u, &index_width, &index_lines)) {
        return;
    }
    index_end = index_text;
    while (*index_end) {
        index_end += 1;
    }
    while (index_end > index_text && index_end[-1] == (u8)' ') {
        index_width -= font_v2_ascii_widths[0];
        index_end -= 1;
    }

    set_color(renderer_address, 10u, 1u);
    set_position(
        FONT_NINJA_OBJECTIVE_INDEX_ORIGIN_X -
            (index_text[0] == (u8)' '
                ? FONT_NINJA_OBJECTIVE_INDEX_LEADING_SPACE_OFFSET
                : 0.0f),
        row_y.f + FONT_NINJA_OBJECTIVE_INDEX_Y_OFFSET,
        renderer_address
    );
    draw(renderer_address, index_text);

    set_color(renderer_address, 15u, 1u);
    set_position(
        FONT_NINJA_OBJECTIVE_MARKER_ORIGIN_X + (float)(s32)index_width,
        row_y.f + FONT_NINJA_OBJECTIVE_MARKER_Y_OFFSET,
        renderer_address
    );
    draw(renderer_address, marker);

    font_v2_ninja_objective_draw(
        prose,
        15u,
        FONT_NINJA_OBJECTIVE_PROSE_X,
        row_y.f + FONT_NINJA_OBJECTIVE_PROSE_Y_OFFSET
    );
}
