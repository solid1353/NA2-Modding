#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* === Command Chart: relationship descriptions and inline icons === */

/* Fixed runtime address of the Command Chart text table; do not tune. */
#define FONT_COMMAND_TEXT_TABLE_ADDRESS 0x008BD1D0u

/* Left edge of wrapped relationship text; increase to move it right. */
#define FONT_COMMAND_RELATION_BOX_X 44.0f

/* Added to wrapped-block Y; more negative moves multiline text up. */
#define FONT_COMMAND_RELATION_Y_OFFSET -11.5f

/* Added only to fitting one-line relationship text; more negative moves it up. */
#define FONT_COMMAND_RELATION_SINGLE_LINE_Y_OFFSET -7.2f

/* NUN5 relationship wrapper width captured live before style application. */
#define FONT_COMMAND_RELATION_BOX_WIDTH 272u

/* Relationship box height used to center one- or two-line output. */
#define FONT_COMMAND_RELATION_BOX_HEIGHT 32u

/* Vertical distance between wrapped relationship lines. */
#define FONT_COMMAND_RELATION_LINE_HEIGHT 30.0f

/* Requested relationship glyph-quad height when that override is enabled. */
#define FONT_COMMAND_RELATION_GLYPH_HEIGHT 14.0f

/* Maximum relationship lines; reduce only if truncation is intentionally desired. */
#define FONT_COMMAND_RELATION_LINE_LIMIT 2u

/* Icon X offset when the relationship-description row is present. */
#define FONT_COMMAND_ICON_RELATION_OFFSET 16.0f

/* Icon X offset when no relationship-description row precedes the commands. */
#define FONT_COMMAND_ICON_PLAIN_OFFSET 38.0f

/* === Shared temporary body storage: internal capacity === */

/* Maximum copied body/list text bytes including the terminator; not geometry. */
#define FONT_BODY_BUFFER_SIZE 0x100u

/* === Practice explanations and inline controller icons === */

/* Fixed runtime address of Practice's native icon records; do not tune. */
#define FONT_PRACTICE_ICON_TABLE_ADDRESS 0x008D14C0u

/* Fixed native Practice icon-draw entrypoint; do not tune. */
#define FONT_PRACTICE_ICON_DRAW_ADDRESS 0x0037BB40u

typedef void (*FontV2NativePracticeIconDraw)(
    u32 object,
    u32 record,
    float draw_x,
    float draw_y
);

/* Fixed runtime address of Practice's native text table; do not tune. */
#define FONT_PRACTICE_TEXT_TABLE_ADDRESS 0x008BD510u

/* Practice explanation left edge; increase to move the block right. */
#define FONT_PRACTICE_BOX_X 40.8f

/* Added to native explanation Y; increase to move the block down. */
#define FONT_PRACTICE_BOX_Y_OFFSET 21.2f

/* NUN5 centers one- and two-line mixed rows at distinct vertical phases. */
#define FONT_PRACTICE_SINGLE_LINE_Y_OFFSET 5.6f
#define FONT_PRACTICE_TWO_LINE_Y_OFFSET 3.2f

/* Explanation width; larger values wrap later. */
#define FONT_PRACTICE_BOX_WIDTH 364u

/* Explanation box height used for vertical placement. */
#define FONT_PRACTICE_BOX_HEIGHT 48u

/* Glyph-quad height used by the Practice explanation renderer. */
#define FONT_PRACTICE_GLYPH_HEIGHT 28.0f

/* Vertical distance between wrapped Practice explanation lines. */
#define FONT_PRACTICE_LINE_ADVANCE 14.0f

/* Zero means Practice explanations have no artificial line-count limit. */
#define FONT_PRACTICE_LINE_LIMIT 0u

/* Number of direct text/icon token records in the native token table. */
#define FONT_PRACTICE_TOKEN_COUNT 13u

/* Byte stride between direct Practice token records. */
#define FONT_PRACTICE_TOKEN_STRIDE 16u

/* Number of entries in the controller-icon remapping table. */
#define FONT_PRACTICE_ICON_MAP_COUNT 18u

/* Maximum assembled mixed text/icon bytes including the terminator. */
#define FONT_PRACTICE_BUFFER_SIZE 0x200u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

FONT_V2_SECTION(".text.font_v2_practice_append")
u8 *font_v2_practice_append(
    u8 *destination,
    const u8 *source,
    u8 *limit
) {
    while (*source && destination < limit) {
        *destination = *source;
        destination += 1;
        source += 1;
    }
    *destination = 0;
    return destination;
}
FONT_V2_SECTION(".text.font_v2_command_relationship_impl")
int font_v2_command_relationship_impl(
    u32 arg0,
    const u8 *record,
    u32 arg2,
    u32 native_y_bits
) {
    FontV2BodyFrame frame;
    const u8 *volatile *text_table =
        (const u8 *volatile *)FONT_COMMAND_TEXT_TABLE_ADDRESS;
    u8 *destination = frame.buffer;
    u8 *limit = frame.buffer + FONT_BODY_BUFFER_SIZE - 1u;
    FontV2Bits native_y;

    if (!record || !record[4]) {
        return -1;
    }

    *destination = 0;
    destination = font_v2_practice_append(
        destination, text_table[record[4]], limit
    );
    if (record[5]) {
        destination = font_v2_practice_append(
            destination, text_table[record[5]], limit
        );
    }

    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_COMMAND_RELATION_BOX_WIDTH,
            FONT_COMMAND_RELATION_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    native_y.u = native_y_bits;
    frame.session.text = frame.buffer;
    frame.session.box_x = FONT_COMMAND_RELATION_BOX_X;
    frame.session.box_y =
        native_y.f + FONT_COMMAND_RELATION_Y_OFFSET;
    if (frame.session.line_count == 1u) {
        frame.session.box_y +=
            FONT_COMMAND_RELATION_SINGLE_LINE_Y_OFFSET;
    }
    frame.session.box_width = FONT_COMMAND_RELATION_BOX_WIDTH;
    frame.session.box_height = FONT_COMMAND_RELATION_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_SCALE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_COMMAND_RELATION_LINE_LIMIT;
    frame.session.line_height = FONT_COMMAND_RELATION_LINE_HEIGHT;
    frame.session.glyph_height = FONT_COMMAND_RELATION_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_title_callback;
    frame.session.callback_arg0 = arg0;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_command_icon_offset")
float font_v2_command_icon_offset(const u8 *record) {
    if (record && record[4]) {
        return FONT_COMMAND_ICON_RELATION_OFFSET;
    }
    return FONT_COMMAND_ICON_PLAIN_OFFSET;
}

static FONT_V2_SECTION(".text.font_v2_icon_record")
const FontV2IconRecord *font_v2_icon_record(u32 token) {
    u32 mapped;
    if (token >= FONT_PRACTICE_ICON_MAP_COUNT) {
        return (const FontV2IconRecord *)0;
    }
    mapped = font_v2_practice_icon_map[token];
    if (mapped == 0xFFu) {
        return (const FontV2IconRecord *)0;
    }
    return (
        (const FontV2IconRecord *)FONT_PRACTICE_ICON_TABLE_ADDRESS
    ) + mapped;
}

FONT_V2_SECTION(".text.font_v2_practice_icon_metric")
void font_v2_practice_icon_metric(
    float *width,
    float *height,
    u32 token
) {
    const FontV2IconRecord *record = font_v2_icon_record(token);
    if (record) {
        *width = (float)record->width;
        *height = (float)record->height;
    }
}

FONT_V2_SECTION(".text.font_v2_practice_icon_draw")
void font_v2_practice_icon_draw(
    float *draw_x,
    float *draw_y,
    u32 token
) {
    const FontV2IconRecord *record = font_v2_icon_record(token);
    FontV2PracticeFrame *frame =
        (FontV2PracticeFrame *)font_v2_active_session;
    FontV2NativePracticeIconDraw draw =
        (FontV2NativePracticeIconDraw)FONT_PRACTICE_ICON_DRAW_ADDRESS;
    u32 object;
    float y;

    if (!record || !frame) {
        return;
    }

    object = frame->object_primary;
    if (token >= 4u && token < 8u) {
        object = frame->object_secondary;
    }
    y = *draw_y;
    if (token >= 11u && token < 15u) {
        y -= 3.0f;
    } else if (token == 17u) {
        y += 1.0f;
    }
    draw(
        object,
        (u32)record,
        *draw_x,
        y
    );
    *draw_x += (float)record->width;
}

FONT_V2_SECTION(".text.font_v2_practice_adapter_impl")
int font_v2_practice_adapter_impl(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 object_primary,
    u32 object_secondary,
    u32 native_y_bits
) {
    FontV2PracticeFrame frame;
    volatile u32 *renderer;
    const u8 *record = (const u8 *)(arg0 + arg1);
    const s32 *tokens = (const s32 *)(record + 0x40);
    u32 token_count = *(const u32 *)(record + 0x68);
    u8 *destination = frame.buffer;
    u8 *limit = frame.buffer + FONT_PRACTICE_BUFFER_SIZE - 1u;
    u32 index;
    u32 previous_was_text = 0;
    FontV2Bits native_y;
    int result;

    frame.object_primary = object_primary;
    frame.object_secondary = object_secondary;
    *destination = 0;
    for (index = 0; index < token_count; index += 1) {
        s32 token = tokens[index];
        const u8 *payload;

        if (token < 0 || token >= 26) {
            continue;
        }
        if ((u32)token >= FONT_PRACTICE_TOKEN_COUNT) {
            if (index) {
                destination = font_v2_practice_append(
                    destination,
                    font_v2_practice_tokens +
                        FONT_PRACTICE_TOKEN_COUNT *
                            FONT_PRACTICE_TOKEN_STRIDE,
                    limit
                );
            }
            payload = (
                (const u8 *volatile *)
                    FONT_PRACTICE_TEXT_TABLE_ADDRESS
            )[token - (s32)FONT_PRACTICE_TOKEN_COUNT];
            destination = font_v2_practice_append(
                destination, payload, limit
            );
            previous_was_text = 1;
        } else {
            if (index && previous_was_text) {
                destination = font_v2_practice_append(
                    destination,
                    font_v2_practice_tokens +
                        FONT_PRACTICE_TOKEN_COUNT *
                            FONT_PRACTICE_TOKEN_STRIDE,
                    limit
                );
            }
            destination = font_v2_practice_append(
                destination,
                font_v2_practice_tokens +
                    (u32)token * FONT_PRACTICE_TOKEN_STRIDE,
                limit
            );
            previous_was_text = 0;
        }
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (!renderer) {
        return -1;
    }
    frame.saved_metric_callback = renderer[0x7C / sizeof(u32)];
    frame.saved_draw_callback = renderer[0x78 / sizeof(u32)];
    renderer[0x7C / sizeof(u32)] = (u32)font_v2_practice_icon_metric;
    renderer[0x78 / sizeof(u32)] = (u32)font_v2_practice_icon_draw;

    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_PRACTICE_BOX_WIDTH,
            FONT_PRACTICE_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        renderer[0x7C / sizeof(u32)] = frame.saved_metric_callback;
        renderer[0x78 / sizeof(u32)] = frame.saved_draw_callback;
        return -1;
    }

    native_y.u = native_y_bits;
    frame.session.text = frame.buffer;
    frame.session.box_x = FONT_PRACTICE_BOX_X;
    frame.session.box_y = native_y.f + FONT_PRACTICE_BOX_Y_OFFSET;
    if (frame.session.line_count == 1u) {
        frame.session.box_y += FONT_PRACTICE_SINGLE_LINE_Y_OFFSET;
    } else if (frame.session.line_count == 2u) {
        frame.session.box_y += FONT_PRACTICE_TWO_LINE_Y_OFFSET;
    }
    frame.session.box_width = FONT_PRACTICE_BOX_WIDTH;
    frame.session.box_height = FONT_PRACTICE_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_PRACTICE_LINE_LIMIT;
    frame.session.line_height = FONT_PRACTICE_LINE_ADVANCE;
    frame.session.glyph_height = FONT_PRACTICE_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_title_callback;
    frame.session.callback_arg0 = arg2;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0x0Fu;
    frame.session.callback_arg3 = (u32)&frame.session;

    result = font_v2_adapter_call(&frame.session);
    renderer[0x7C / sizeof(u32)] = frame.saved_metric_callback;
    renderer[0x78 / sizeof(u32)] = frame.saved_draw_callback;
    return result;
}
