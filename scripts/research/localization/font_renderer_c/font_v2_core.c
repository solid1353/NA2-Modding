/*
 * Address-independent C form of the accepted Font v2 measurement and
 * preparation algorithms. This source is compiled by ee_c_fragments.py and
 * does not own final 228.BIN placement or any game hook.
 */

typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int s32;

#define FONT_V2_FLAG_SHRINK_X 0x01u
#define FONT_V2_FLAG_BR_TAGS 0x02u
#define FONT_V2_FLAG_NEWLINE_BYTES 0x04u
#define FONT_V2_FLAG_SEPARATE_LINE_ADVANCE 0x08u
#define FONT_V2_FLAG_PREMEASURED 0x10u

#define FONT_V2_ALIGN_START 0u
#define FONT_V2_ALIGN_CENTER 1u
#define FONT_V2_ALIGN_END 2u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

typedef struct FontV2Session {
    u32 previous;
    const u8 *text;
    float box_x;
    float box_y;
    u32 box_width;
    u32 box_height;
    u32 horizontal_alignment;
    u32 vertical_alignment;
    u32 flags;
    u32 line_limit;
    float line_height;
    u32 callback;
    u32 measured_width;
    u32 line_count;
    float scale_x;
    float scale_y;
    float rendered_width;
    float rendered_height;
    float draw_x;
    float draw_y;
    u32 callback_arg0;
    u32 callback_arg1;
    u32 callback_arg2;
    u32 callback_arg3;
    u32 saved_tracking;
    u32 saved_scale;
    float glyph_height;
} FontV2Session;

#define FONT_V2_OFFSET(type, member) ((u32)&(((type *)0)->member))
#define FONT_V2_ASSERT(name, expression) \
    typedef char font_v2_assert_##name[(expression) ? 1 : -1]

FONT_V2_ASSERT(text_offset, FONT_V2_OFFSET(FontV2Session, text) == 0x04);
FONT_V2_ASSERT(flags_offset, FONT_V2_OFFSET(FontV2Session, flags) == 0x20);
FONT_V2_ASSERT(callback_offset, FONT_V2_OFFSET(FontV2Session, callback) == 0x2C);
FONT_V2_ASSERT(measured_width_offset,
               FONT_V2_OFFSET(FontV2Session, measured_width) == 0x30);
FONT_V2_ASSERT(scale_x_offset,
               FONT_V2_OFFSET(FontV2Session, scale_x) == 0x38);
FONT_V2_ASSERT(draw_x_offset, FONT_V2_OFFSET(FontV2Session, draw_x) == 0x48);
FONT_V2_ASSERT(saved_scale_offset,
               FONT_V2_OFFSET(FontV2Session, saved_scale) == 0x64);
FONT_V2_ASSERT(glyph_height_offset,
               FONT_V2_OFFSET(FontV2Session, glyph_height) == 0x68);
FONT_V2_ASSERT(session_size, sizeof(FontV2Session) == 0x6C);

extern const u8 font_v2_ascii_widths[95];

static u32 font_v2_is_br(const u8 *text) {
    return text[0] == (u8)'<' &&
           text[1] == (u8)'b' &&
           text[2] == (u8)'r' &&
           text[3] == (u8)'>';
}

FONT_V2_SECTION(".text.font_v2_measure")
int font_v2_measure(
    const u8 *text,
    u32 flags,
    u32 *measured_width,
    u32 *line_count
) {
    u32 current_width = 0;
    u32 maximum_width = 0;
    u32 lines = 1;

    if (!text || !measured_width || !line_count) {
        return -1;
    }

    while (*text) {
        u32 character = *text;
        if ((flags & FONT_V2_FLAG_BR_TAGS) && font_v2_is_br(text)) {
            text += 4;
        } else if (
            (flags & FONT_V2_FLAG_NEWLINE_BYTES) &&
            character == 0x0Au
        ) {
            text += 1;
        } else {
            if (character < 0x20u || character > 0x7Eu) {
                return -1;
            }
            current_width += font_v2_ascii_widths[character - 0x20u];
            text += 1;
            continue;
        }

        if (current_width > maximum_width) {
            maximum_width = current_width;
        }
        current_width = 0;
        lines += 1;
    }

    if (current_width > maximum_width) {
        maximum_width = current_width;
    }
    *measured_width = maximum_width;
    *line_count = lines;
    return 0;
}

FONT_V2_SECTION(".text.font_v2_prepare")
int font_v2_prepare(FontV2Session *session) {
    u32 measured_width;
    u32 line_count;
    float box_width;
    float box_height;

    if (!session || !session->text) {
        return -1;
    }

    if (session->flags & FONT_V2_FLAG_PREMEASURED) {
        measured_width = session->measured_width;
        line_count = session->line_count;
    } else {
        if (font_v2_measure(
                session->text,
                session->flags,
                &measured_width,
                &line_count
            ) != 0) {
            return -1;
        }
        session->measured_width = measured_width;
        session->line_count = line_count;
    }

    if ((s32)measured_width < 0 || line_count == 0) {
        return -1;
    }
    if (session->line_limit && line_count > session->line_limit) {
        return -1;
    }
    if (!session->box_width || !session->box_height) {
        return -1;
    }

    session->scale_x = 1.0f;
    session->scale_y = 1.0f;
    if (
        (session->flags & FONT_V2_FLAG_SHRINK_X) &&
        measured_width > session->box_width
    ) {
        session->scale_x =
            (float)(s32)session->box_width / (float)(s32)measured_width;
    }
    session->rendered_width =
        (float)(s32)measured_width * session->scale_x;

    if (session->flags & FONT_V2_FLAG_SEPARATE_LINE_ADVANCE) {
        session->rendered_height =
            (float)(s32)(line_count - 1u) * session->line_height +
            session->glyph_height;
    } else {
        session->rendered_height =
            (float)(s32)line_count * session->line_height;
    }

    box_width = (float)(s32)session->box_width;
    if (session->horizontal_alignment == FONT_V2_ALIGN_START) {
        session->draw_x = session->box_x;
    } else if (session->horizontal_alignment == FONT_V2_ALIGN_CENTER) {
        session->draw_x =
            session->box_x +
            (box_width - session->rendered_width) * 0.5f;
    } else if (session->horizontal_alignment == FONT_V2_ALIGN_END) {
        session->draw_x =
            session->box_x + box_width - session->rendered_width;
    } else {
        return -1;
    }

    box_height = (float)(s32)session->box_height;
    if (session->vertical_alignment == FONT_V2_ALIGN_START) {
        session->draw_y = session->box_y;
    } else if (session->vertical_alignment == FONT_V2_ALIGN_CENTER) {
        session->draw_y =
            session->box_y +
            (box_height - session->rendered_height) * 0.5f;
    } else if (session->vertical_alignment == FONT_V2_ALIGN_END) {
        session->draw_y =
            session->box_y + box_height - session->rendered_height;
    } else {
        return -1;
    }

    return 0;
}
