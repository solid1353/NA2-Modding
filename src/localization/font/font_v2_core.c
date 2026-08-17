/*
 * Shared Font v2 ABI declarations and the layout-engine implementation.
 * Responsibility-owned units compile the exact declaration and constant
 * prefix below with FONT_V2_DECLARATIONS_ONLY, while this file alone emits the
 * shared layout engine. The catalog fingerprints every responsibility unit
 * directly without adding a separate source-dependency mechanism.
 */

#ifndef NA228_FONT_V2_DECLARATIONS
#define NA228_FONT_V2_DECLARATIONS

/*
 * Address-independent C form of the accepted Font v2 measurement and
 * preparation algorithms. The runtime injector compiles this source through
 * the generic EE C fragment extractor during composition; the payload builder
 * owns final 228.BIN placement, and this unit owns no hooks or addresses.
 */

typedef unsigned char u8;
typedef signed char s8;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;

/*
 * Screen geometry uses the game's local coordinates, not capture pixels.
 * Larger X moves right; smaller X moves left. Larger Y moves down; smaller Y
 * moves up. Larger widths wrap later. Address, offset, flag, count, and buffer
 * constants are internal contracts, not visual tuning controls.
 */

/* === Shared layout engine: internal flags and alignment modes === */

/* Allows horizontal shrinking when measured text exceeds its box width. */
#define FONT_V2_FLAG_SHRINK_X 0x01u

/* Makes measurement treat the four-byte <br> tag as a line break. */
#define FONT_V2_FLAG_BR_TAGS 0x02u

/* Makes measurement treat an actual '\n' byte as a line break. */
#define FONT_V2_FLAG_NEWLINE_BYTES 0x04u

/* Uses line_height as row spacing instead of the glyph's native advance. */
#define FONT_V2_FLAG_SEPARATE_LINE_ADVANCE 0x08u

/* Scales row spacing together with vertical text scale when enabled. */
#define FONT_V2_FLAG_SCALE_LINE_ADVANCE 0x20u

/* Overrides drawn glyph-quad height; misuse visibly squeezes or stretches text. */
#define FONT_V2_FLAG_GLYPH_HEIGHT 0x40u

/* Uses the caller-supplied horizontal scale instead of deriving an overflow fit. */
#define FONT_V2_FLAG_FIXED_SCALE_X 0x80u

/* Measures visible quotes with NUN5's original @-delimiter advance. */
#define FONT_V2_FLAG_NUN5_QUOTE_WIDTH 0x100u

/* Excludes renderer-consumed color tags from visible-width measurement. */
#define FONT_V2_FLAG_COLOR_TAGS 0x200u

/* Native fallback row advance when no separate line spacing is requested. */
#define FONT_V2_NATIVE_LINE_ADVANCE 40.0f

/* Trusts caller-supplied measured_width and line_count instead of remeasuring. */
#define FONT_V2_FLAG_PREMEASURED 0x10u

/* Anchors content at the box's left or top edge. */
#define FONT_V2_ALIGN_START 0u

/* Centers content within the box on the selected axis. */
#define FONT_V2_ALIGN_CENTER 1u

/* Anchors content at the box's right or bottom edge. */
#define FONT_V2_ALIGN_END 2u

/* === Native renderer ABI: fixed addresses and structure offsets === */

/* Fixed EE address containing NA2's live renderer pointer; do not tune. */
#define FONT_RENDERER_POINTER_ADDRESS 0x00607470u

/* Fixed EE address of NA2's live horizontal text scale; do not tune. */
#define FONT_HORIZONTAL_SCALE_ADDRESS 0x0060737Cu

/* Fixed renderer-field offset for extra inter-character tracking. */
#define FONT_RENDERER_TRACKING_OFFSET 0x3Cu

/* Fixed renderer-field offset and bit for the ordinary ASCII glyph mode. */
#define FONT_RENDERER_FLAGS_OFFSET 0x70u
#define FONT_RENDERER_ASCII_MODE_FLAG 0x08u

/* Fixed renderer-field offset for the caller's logical X position. */
#define FONT_RENDERER_POSITION_X_OFFSET 0x14u

/* Fixed renderer-field offset for the caller's logical Y position. */
#define FONT_RENDERER_POSITION_Y_OFFSET 0x18u

/* Fixed renderer-field offset for the current draw-origin X. */
#define FONT_RENDERER_DRAW_X_OFFSET 0x28u

/* Fixed renderer-field offset for the current draw-origin Y. */
#define FONT_RENDERER_DRAW_Y_OFFSET 0x2Cu

/* Fixed renderer-field offset for the active native drawing context. */
#define FONT_RENDERER_CONTEXT_OFFSET 0x6Cu

/* Fixed native renderer-initialization function address; do not tune. */
#define FONT_INITIALIZE_ADDRESS 0x00186510u

/* Fixed native renderer-context setter address; do not tune. */
#define FONT_SET_CONTEXT_ADDRESS 0x001866D0u

/* Fixed native renderer-position setter address; do not tune. */
#define FONT_SET_POSITION_ADDRESS 0x00186700u

/* Native palette-index selector used by page code that passes colors 0..15. */
#define FONT_SET_INDEXED_COLOR_ADDRESS 0x00186AC0u

/* Native raw-color selector used by code that passes packed RGBA values. */
#define FONT_SET_RGBA_COLOR_ADDRESS 0x00186B30u

/* Fixed ordinary native text-draw function address; do not tune. */
#define FONT_DRAW_ADDRESS 0x00379040u

/* Fixed unselected section-heading draw function address; do not tune. */
#define FONT_HEADING_DRAW_ADDRESS 0x00378FD0u

/* Fixed ordinary colored text-draw function address; do not tune. */
#define FONT_BODY_DRAW_ADDRESS 0x00378F50u

/* Fixed Battle Settings/Jutsu native draw function address; do not tune. */
#define FONT_JUTSU_DRAW_ADDRESS 0x00188140u

/* Fixed selected Character Select row draw function address; do not tune. */
#define FONT_CHARACTER_SELECTED_DRAW_ADDRESS 0x00382610u

#define FONT_BODY_BUFFER_SIZE 0x100u
#define FONT_PRACTICE_BUFFER_SIZE 0x200u

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

typedef union FontV2Bits {
    u32 u;
    s32 s;
    float f;
} FontV2Bits;

typedef struct FontV2BodyFrame {
    FontV2Session session;
    u8 padding[0x14];
    u8 buffer[FONT_BODY_BUFFER_SIZE];
} FontV2BodyFrame;

typedef struct FontV2PracticeFrame {
    FontV2Session session;
    u32 object_primary;
    u32 object_secondary;
    u32 saved_metric_callback;
    u32 saved_draw_callback;
    u32 padding;
    u8 buffer[FONT_PRACTICE_BUFFER_SIZE];
} FontV2PracticeFrame;

typedef struct FontV2IconRecord {
    u32 unknown;
    s16 width;
    s16 height;
} FontV2IconRecord;

typedef struct FontV2UiDrawRecord {
    float draw_x;
    float draw_y;
    const u8 *text;
    u32 arg2;
} FontV2UiDrawRecord;

typedef struct FontV2SpecialChoiceFrame {
    FontV2Session session;
    u32 native_arg3;
} FontV2SpecialChoiceFrame;

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
FONT_V2_ASSERT(special_choice_arg3_offset,
               FONT_V2_OFFSET(FontV2SpecialChoiceFrame, native_arg3) ==
                   0x6C);
FONT_V2_ASSERT(body_buffer_offset,
               FONT_V2_OFFSET(FontV2BodyFrame, buffer) == 0x80);
FONT_V2_ASSERT(practice_primary_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, object_primary) == 0x6C);
FONT_V2_ASSERT(practice_secondary_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, object_secondary) == 0x70);
FONT_V2_ASSERT(practice_metric_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, saved_metric_callback) ==
                   0x74);
FONT_V2_ASSERT(practice_draw_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, saved_draw_callback) ==
                   0x78);
FONT_V2_ASSERT(practice_buffer_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, buffer) == 0x80);

extern const u8 font_v2_ascii_widths[95];
extern FontV2Session *font_v2_active_session;
extern volatile u32 font_v2_quit_active;
extern const u8 font_v2_practice_tokens[];
extern const u8 font_v2_practice_icon_map[];
extern int font_v2_controls_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_title_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_pause_list_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_pause_list_selected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_quit_unselected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_special_choice_selected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_quit_body_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_special_controls_body_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
static int font_v2_collection_body_callback(
    u32 object,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
);
extern u32 font_v2_native_measure_callback(const u8 *text);
extern void font_v2_practice_icon_draw_callback(
    u32 object,
    u32 record,
    float draw_x,
    float draw_y
);
extern int font_v2_practice_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_ninja_song_ascii_number(
    u32 unused,
    s32 value,
    s32 width,
    u8 *destination,
    s32 mode
);

typedef int (*FontV2Callback)(u32 arg0, u32 arg1, u32 arg2, u32 arg3);
typedef void (*FontV2NativeInitialize)(u32 renderer, u32 mode);
typedef void (*FontV2NativeSetContext)(u32 renderer, u32 context);
typedef void (*FontV2NativeSetPosition)(
    float draw_x,
    float draw_y,
    u32 renderer
);
typedef void (*FontV2NativeSetColor)(u32 renderer, u32 color, u32 mode);
typedef void (*FontV2NativeTextDraw)(u32 renderer, const u8 *text);
typedef void (*FontV2NativeDraw)(
    float draw_x,
    float draw_y,
    const u8 *text,
    u32 highlighted
);
typedef int (*FontV2NativeUiDraw)(
    u32 context,
    const FontV2UiDrawRecord *record,
    u32 state,
    s32 index
);

#ifdef FONT_V2_DECLARATIONS_ONLY
int font_v2_is_mode_select_body(const u8 *text);
#else
static int font_v2_is_mode_select_body(const u8 *text);
#endif
int font_v2_measure(const u8 *, u32, u32 *, u32 *);
int font_v2_prepare(FontV2Session *session);
int font_v2_adapter_call(FontV2Session *session);
u32 font_v2_native_measure(const u8 *text);
int font_v2_wrap_native(u8 *, u32, u32, u32 *, u32 *);
int font_v2_wrap_retry(u8 *, const u8 *, u32, u32, u32 *, u32 *);
u8 *font_v2_practice_append(u8 *, const u8 *, u8 *);

#endif

#ifndef FONT_V2_DECLARATIONS_ONLY

static u32 font_v2_is_br(const u8 *text) {
    return text[0] == (u8)'<' &&
           text[1] == (u8)'b' &&
           text[2] == (u8)'r' &&
           text[3] == (u8)'>';
}

static u32 font_v2_is_hex_digit(u8 character) {
    return
        (character >= (u8)'0' && character <= (u8)'9') ||
        (character >= (u8)'A' && character <= (u8)'F') ||
        (character >= (u8)'a' && character <= (u8)'f');
}

static u32 font_v2_color_tag_length(const u8 *text) {
    u32 index;

    if (text[0] != (u8)'<') {
        return 0;
    }
    if (
        text[1] == (u8)'B' &&
        text[2] == (u8)'L' &&
        text[3] == (u8)'A' &&
        text[4] == (u8)'C' &&
        text[5] == (u8)'K' &&
        text[6] == (u8)'>'
    ) {
        return 7;
    }
    if (
        text[1] == (u8)'W' &&
        text[2] == (u8)'H' &&
        text[3] == (u8)'I' &&
        text[4] == (u8)'T' &&
        text[5] == (u8)'E' &&
        text[6] == (u8)'>'
    ) {
        return 7;
    }
    if (
        text[1] == (u8)'R' &&
        text[2] == (u8)'E' &&
        text[3] == (u8)'D' &&
        text[4] == (u8)'>'
    ) {
        return 5;
    }
    if (
        text[1] != (u8)'c' ||
        text[2] != (u8)'o' ||
        text[3] != (u8)'l' ||
        text[4] != (u8)'o' ||
        text[5] != (u8)'r'
    ) {
        return 0;
    }
    for (index = 6; index < 12; index += 1) {
        if (!font_v2_is_hex_digit(text[index])) {
            return 0;
        }
    }
    return text[12] == (u8)'>' ? 13u : 0u;
}

static int font_v2_is_mode_select_body(const u8 *text) {
    return text &&
           text[0] == (u8)'R' &&
           text[1] == (u8)'e' &&
           text[2] == (u8)'t' &&
           text[3] == (u8)'u' &&
           text[4] == (u8)'r' &&
           text[5] == (u8)'n' &&
           text[6] == (u8)' ' &&
           text[7] == (u8)'t' &&
           text[8] == (u8)'o' &&
           text[9] == (u8)' ' &&
           text[10] == (u8)'T' &&
           text[11] == (u8)'i' &&
           text[12] == (u8)'t' &&
           text[13] == (u8)'l' &&
           text[14] == (u8)'e' &&
           text[15] == (u8)' ' &&
           text[16] == (u8)'S' &&
           text[17] == (u8)'c' &&
           text[18] == (u8)'r' &&
           text[19] == (u8)'e' &&
           text[20] == (u8)'e' &&
           text[21] == (u8)'n' &&
           text[22] == (u8)'?' &&
           text[23] == 0;
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
        u32 color_tag_length = 0;
        if (
            (flags & FONT_V2_FLAG_COLOR_TAGS) &&
            (color_tag_length = font_v2_color_tag_length(text)) != 0
        ) {
            text += color_tag_length;
            continue;
        }
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
            if (
                (flags & FONT_V2_FLAG_NUN5_QUOTE_WIDTH) &&
                character == (u32)'"'
            ) {
                character = (u32)'@';
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

    if (session->flags & FONT_V2_FLAG_FIXED_SCALE_X) {
        if (session->scale_x <= 0.0f) {
            return -1;
        }
    } else {
        session->scale_x = 1.0f;
    }
    session->scale_y = 1.0f;
    if (session->flags & FONT_V2_FLAG_SCALE_LINE_ADVANCE) {
        session->scale_y =
            session->line_height / FONT_V2_NATIVE_LINE_ADVANCE;
    }
    if (
        !(session->flags & FONT_V2_FLAG_FIXED_SCALE_X) &&
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

FONT_V2_SECTION(".text.font_v2_adapter_call")
int font_v2_adapter_call(FontV2Session *session) {
    volatile u32 *renderer;
    volatile u32 *scale_bits =
        (volatile u32 *)FONT_HORIZONTAL_SCALE_ADDRESS;
    FontV2Callback callback;
    int result;

    if (!session || !session->callback) {
        return -1;
    }
    if (font_v2_prepare(session) != 0) {
        return -1;
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (!renderer) {
        return -1;
    }

    session->previous = (u32)font_v2_active_session;
    session->saved_tracking =
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)];
    session->saved_scale = *scale_bits;

    renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
    *(volatile float *)FONT_HORIZONTAL_SCALE_ADDRESS = session->scale_x;
    font_v2_active_session = session;

    callback = (FontV2Callback)session->callback;
    result = callback(
        session->callback_arg0,
        session->callback_arg1,
        session->callback_arg2,
        session->callback_arg3
    );

    *scale_bits = session->saved_scale;
    renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] =
        session->saved_tracking;
    font_v2_active_session = (FontV2Session *)session->previous;
    return result;
}

#endif
