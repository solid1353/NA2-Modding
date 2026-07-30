/*
 * Address-independent C form of the accepted Font v2 measurement and
 * preparation algorithms. The runtime injector compiles this source through
 * the generic EE C fragment extractor during composition; the payload builder
 * owns final 228.BIN placement, and this unit owns no hooks or addresses.
 */

typedef unsigned char u8;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;

#define FONT_V2_FLAG_SHRINK_X 0x01u
#define FONT_V2_FLAG_BR_TAGS 0x02u
#define FONT_V2_FLAG_NEWLINE_BYTES 0x04u
#define FONT_V2_FLAG_SEPARATE_LINE_ADVANCE 0x08u
#define FONT_V2_FLAG_SCALE_LINE_ADVANCE 0x20u
#define FONT_V2_NATIVE_LINE_ADVANCE 40.0f
#define FONT_V2_FLAG_PREMEASURED 0x10u

#define FONT_V2_ALIGN_START 0u
#define FONT_V2_ALIGN_CENTER 1u
#define FONT_V2_ALIGN_END 2u
#define FONT_RENDERER_POINTER_ADDRESS 0x00607470u
#define FONT_HORIZONTAL_SCALE_ADDRESS 0x0060737Cu
#define FONT_RENDERER_TRACKING_OFFSET 0x3Cu
#define FONT_RENDERER_DRAW_X_OFFSET 0x28u
#define FONT_RENDERER_DRAW_Y_OFFSET 0x2Cu
#define FONT_RENDERER_CONTEXT_OFFSET 0x6Cu
#define FONT_INITIALIZE_ADDRESS 0x00186510u
#define FONT_SET_CONTEXT_ADDRESS 0x001866D0u
#define FONT_DRAW_ADDRESS 0x00379040u
#define FONT_CHARACTER_SELECTED_DRAW_ADDRESS 0x00382610u
#define FONT_CONTROLS_BOX_WIDTH 128u
#define FONT_CONTROLS_BOX_HEIGHT 20u
#define FONT_CONTROLS_LINE_HEIGHT 20.0f
#define FONT_COMMAND_TITLE_BOX_X 27.2f
#define FONT_COMMAND_TITLE_BOX_WIDTH 288u
#define FONT_COMMAND_TITLE_Y_OFFSET -3.8f
#define FONT_COMMAND_TEXT_TABLE_ADDRESS 0x008BD1D0u
#define FONT_COMMAND_RELATION_BOX_X 43.2f
#define FONT_COMMAND_RELATION_Y_OFFSET -11.5f
#define FONT_COMMAND_RELATION_SINGLE_LINE_Y_OFFSET -8.0f
#define FONT_COMMAND_RELATION_BOX_WIDTH 226u
#define FONT_COMMAND_RELATION_BOX_HEIGHT 32u
#define FONT_COMMAND_RELATION_LINE_HEIGHT 30.0f
#define FONT_COMMAND_RELATION_GLYPH_HEIGHT 14.0f
#define FONT_COMMAND_RELATION_LINE_LIMIT 2u
#define FONT_COMMAND_ICON_RELATION_OFFSET 16.0f
#define FONT_COMMAND_ICON_PLAIN_OFFSET 38.0f
#define FONT_PRACTICE_TITLE_BOX_X 31.2f
#define FONT_PRACTICE_TITLE_BOX_WIDTH 352u
#define FONT_PRACTICE_TITLE_Y_OFFSET -6.8f
#define FONT_TITLE_BOX_HEIGHT 20u
#define FONT_TITLE_LINE_HEIGHT 20.0f
#define FONT_PAUSE_LIST_BOX_WIDTH 216u
#define FONT_PAUSE_LIST_BOX_HEIGHT 20u
#define FONT_PAUSE_LIST_Y_OFFSET -4.0f
#define FONT_PAUSE_LIST_SELECTED_X_OFFSET 2.0f
#define FONT_PAUSE_LIST_LINE_HEIGHT 20.0f
#define FONT_CHARACTER_LIST_BOX_WIDTH 240u
#define FONT_CHARACTER_LIST_BOX_HEIGHT 20u
#define FONT_CHARACTER_LIST_SELECTED_X_OFFSET 5.0f
#define FONT_CHARACTER_LIST_LINE_HEIGHT 20.0f
#define FONT_QUIT_YES_SOURCE_BITS 0x41C00000u
#define FONT_QUIT_NO_SOURCE_BITS 0x42600000u
#define FONT_QUIT_YES_X 64.5f
#define FONT_QUIT_YES_Y 31.5f
#define FONT_QUIT_NO_X 68.5f
#define FONT_QUIT_NO_Y 49.0f
#define FONT_SPECIAL_ON_TEXT 0x006059F0u
#define FONT_SPECIAL_OFF_TEXT 0x006059F8u
#define FONT_SPECIAL_ON_X 66.0f
#define FONT_SPECIAL_ON_Y 31.0f
#define FONT_SPECIAL_OFF_X 59.0f
#define FONT_SPECIAL_OFF_Y 49.0f
#define FONT_QUIT_BODY_BOX_X 19.0f
#define FONT_QUIT_BODY_BOX_Y 12.0f
#define FONT_QUIT_BODY_BOX_WIDTH 420u
#define FONT_QUIT_BODY_BOX_HEIGHT 40u
#define FONT_QUIT_BODY_LINE_HEIGHT 20.0f
#define FONT_QUIT_BODY_LINE_LIMIT 2u
#define FONT_CHARACTER_BODY_BOX_X 8.0f
#define FONT_CHARACTER_BODY_BOX_Y 8.0f
#define FONT_CHARACTER_BODY_BOX_WIDTH 368u
#define FONT_CHARACTER_BODY_BOX_HEIGHT 24u
#define FONT_CHARACTER_BODY_LINE_HEIGHT 20.0f
#define FONT_CHARACTER_BODY_LINE_LIMIT 1u
#define FONT_SPECIAL_BODY_BOX_X 24.0f
#define FONT_SPECIAL_BODY_BOX_Y 12.0f
#define FONT_SPECIAL_BODY_BOX_WIDTH 400u
#define FONT_SPECIAL_BODY_BOX_HEIGHT 60u
#define FONT_SPECIAL_BODY_LINE_HEIGHT 20.0f
#define FONT_SPECIAL_BODY_LINE_LIMIT 2u
#define FONT_BODY_BUFFER_SIZE 0x100u
#define FONT_PRACTICE_ICON_TABLE_ADDRESS 0x008D14C0u
#define FONT_PRACTICE_TEXT_TABLE_ADDRESS 0x008BD510u
#define FONT_PRACTICE_BOX_X 39.2f
#define FONT_PRACTICE_BOX_Y_OFFSET 21.2f
#define FONT_PRACTICE_BOX_WIDTH 364u
#define FONT_PRACTICE_BOX_HEIGHT 48u
#define FONT_PRACTICE_GLYPH_HEIGHT 28.0f
#define FONT_PRACTICE_LINE_ADVANCE 14.0f
#define FONT_PRACTICE_LINE_LIMIT 0u
#define FONT_PRACTICE_TOKEN_COUNT 13u
#define FONT_PRACTICE_TOKEN_STRIDE 16u
#define FONT_PRACTICE_ICON_MAP_COUNT 18u
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

typedef int (*FontV2Callback)(u32 arg0, u32 arg1, u32 arg2, u32 arg3);
typedef void (*FontV2NativeInitialize)(u32 renderer, u32 mode);
typedef void (*FontV2NativeSetContext)(u32 renderer, u32 context);
typedef void (*FontV2NativeDraw)(
    float draw_x,
    float draw_y,
    const u8 *text,
    u32 highlighted
);

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
    if (session->flags & FONT_V2_FLAG_SCALE_LINE_ADVANCE) {
        session->scale_y =
            session->line_height / FONT_V2_NATIVE_LINE_ADVANCE;
    }
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

FONT_V2_SECTION(".text.font_v2_controls_adapter")
int font_v2_controls_adapter(
    const u8 *text,
    u32 style,
    float center_x,
    float draw_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = center_x - (float)(FONT_CONTROLS_BOX_WIDTH / 2u);
    session.box_y = draw_y;
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
    session.flags = FONT_V2_FLAG_SHRINK_X;
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
    (void)native_x;
    return font_v2_title_adapter_common(
        arg0,
        text,
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
    session.box_x = native_x;
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
    session.box_x = (float)native_x + FONT_PAUSE_LIST_SELECTED_X_OFFSET;
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

FONT_V2_SECTION(".text.font_v2_character_selected_adapter")
int font_v2_character_selected_adapter(
    u32 object,
    s32 draw_x,
    s32 draw_y,
    const u8 *text
) {
    FontV2Session session;

    session.text = text;
    session.box_x =
        (float)draw_x + FONT_CHARACTER_LIST_SELECTED_X_OFFSET;
    session.box_y = (float)draw_y;
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
        (u32)(draw_x + (s32)FONT_CHARACTER_LIST_SELECTED_X_OFFSET);
    session.callback_arg2 = (u32)draw_y;
    session.callback_arg3 = (u32)text;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_quit_scope_enter")
u32 font_v2_quit_scope_enter(void) {
    u32 previous = font_v2_quit_active;
    font_v2_quit_active = 1;
    return previous;
}

FONT_V2_SECTION(".text.font_v2_quit_scope_leave")
void font_v2_quit_scope_leave(u32 previous) {
    font_v2_quit_active = previous;
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

    if (font_v2_quit_active) {
        if (source_y == FONT_QUIT_YES_SOURCE_BITS) {
            x.f = FONT_QUIT_YES_X;
            y.f = FONT_QUIT_YES_Y;
        } else if (source_y == FONT_QUIT_NO_SOURCE_BITS) {
            x.f = FONT_QUIT_NO_X;
            y.f = FONT_QUIT_NO_Y;
        } else {
            return 0;
        }
    } else if (text == FONT_SPECIAL_ON_TEXT) {
        x.f = FONT_SPECIAL_ON_X;
        y.f = FONT_SPECIAL_ON_Y;
    } else if (text == FONT_SPECIAL_OFF_TEXT) {
        x.f = FONT_SPECIAL_OFF_X;
        y.f = FONT_SPECIAL_OFF_Y;
    } else {
        return 0;
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

    font_v2_map_choice(text, source_y, &target_x, &mapped_y);
    *target_y = mapped_y;
    return target_x;
}

FONT_V2_SECTION(".text.font_v2_quit_unselected_adapter")
int font_v2_quit_unselected_adapter(
    u32 arg0,
    u32 *record,
    u32 arg2,
    u32 arg3
) {
    u32 original_x;
    u32 original_y;
    u32 target_x;
    u32 target_y;
    u32 text;
    int result;

    original_x = record[0];
    original_y = record[1];
    text = record[2];
    target_x = original_x;
    target_y = original_y;
    if (!font_v2_map_choice(text, original_y, &target_x, &target_y)) {
        return font_v2_quit_unselected_callback(
            arg0, (u32)record, arg2, arg3
        );
    }

    record[0] = target_x;
    record[1] = target_y;
    result = font_v2_quit_unselected_callback(
        arg0, (u32)record, arg2, arg3
    );
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

static FONT_V2_SECTION(".text.font_v2_wrapped_body_common")
int font_v2_wrapped_body_common(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float box_x,
    float box_y,
    u32 box_width,
    u32 box_height,
    float line_height,
    u32 line_limit,
    u32 callback
) {
    FontV2BodyFrame frame;
    u32 index = 0;

    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        frame.buffer[index] = text[index];
        index += 1;
    }
    frame.buffer[index] = 0;

    if (
        font_v2_wrap_native(
            frame.buffer,
            box_width,
            line_limit,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x = box_x;
    frame.session.box_y = box_y;
    frame.session.box_width = box_width;
    frame.session.box_height = box_height;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_START;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES | FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = line_limit;
    frame.session.line_height = line_height;
    frame.session.callback = callback;
    frame.session.callback_arg0 = arg0;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_quit_body_adapter")
int font_v2_quit_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    return font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_QUIT_BODY_BOX_X,
        FONT_QUIT_BODY_BOX_Y,
        FONT_QUIT_BODY_BOX_WIDTH,
        FONT_QUIT_BODY_BOX_HEIGHT,
        FONT_QUIT_BODY_LINE_HEIGHT,
        FONT_QUIT_BODY_LINE_LIMIT,
        (u32)font_v2_quit_body_callback
    );
}

static FONT_V2_SECTION(
    ".text.font_v2_character_confirmation_body_callback"
)
int font_v2_character_confirmation_body_callback(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;

    (void)arg0;
    (void)arg2;
    draw(
        session->draw_x,
        session->draw_y,
        text,
        0u
    );
    return 0;
}

FONT_V2_SECTION(".text.font_v2_character_confirmation_body_adapter")
int font_v2_character_confirmation_body_adapter(
    u32 object,
    const u8 *text,
    u32 arg2
) {
    volatile u32 *renderer =
        *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    volatile u32 *object_words = (volatile u32 *)object;
    FontV2NativeInitialize initialize =
        (FontV2NativeInitialize)FONT_INITIALIZE_ADDRESS;
    FontV2NativeSetContext set_context =
        (FontV2NativeSetContext)FONT_SET_CONTEXT_ADDRESS;
    FontV2Session session;
    u32 saved_draw_x;
    u32 saved_draw_y;
    u32 saved_context;
    int result;

    if (!renderer || !object_words || !text) {
        return -1;
    }

    saved_draw_x =
        renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(u32)];
    saved_draw_y =
        renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(u32)];
    saved_context =
        renderer[FONT_RENDERER_CONTEXT_OFFSET / sizeof(u32)];

    initialize((u32)renderer, 1u);
    renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(u32)] = saved_draw_x;
    renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(u32)] = saved_draw_y;
    set_context(
        (u32)renderer,
        object_words[0x74u / sizeof(u32)]
    );

    session.text = text;
    session.box_x = FONT_CHARACTER_BODY_BOX_X;
    session.box_y = FONT_CHARACTER_BODY_BOX_Y;
    session.box_width = FONT_CHARACTER_BODY_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_BODY_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = FONT_CHARACTER_BODY_LINE_LIMIT;
    session.line_height = FONT_CHARACTER_BODY_LINE_HEIGHT;
    session.callback =
        (u32)font_v2_character_confirmation_body_callback;
    session.callback_arg0 = object;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    result = font_v2_adapter_call(&session);
    renderer[FONT_RENDERER_CONTEXT_OFFSET / sizeof(u32)] = saved_context;
    return result;
}

FONT_V2_SECTION(".text.font_v2_special_controls_body_adapter")
int font_v2_special_controls_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    return font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_SPECIAL_BODY_BOX_X,
        FONT_SPECIAL_BODY_BOX_Y,
        FONT_SPECIAL_BODY_BOX_WIDTH,
        FONT_SPECIAL_BODY_BOX_HEIGHT,
        FONT_SPECIAL_BODY_LINE_HEIGHT,
        FONT_SPECIAL_BODY_LINE_LIMIT,
        (u32)font_v2_special_controls_body_callback
    );
}

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
    font_v2_practice_icon_draw_callback(
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
    frame.session.callback = (u32)font_v2_practice_callback;
    frame.session.callback_arg0 = arg2;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0x0Fu;
    frame.session.callback_arg3 = (u32)&frame.session;

    result = font_v2_adapter_call(&frame.session);
    renderer[0x7C / sizeof(u32)] = frame.saved_metric_callback;
    renderer[0x78 / sizeof(u32)] = frame.saved_draw_callback;
    return result;
}
