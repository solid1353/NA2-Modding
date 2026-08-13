#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

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

/* === Battle/Practice quit-confirmation body === */

/* Quit prompt body left edge; increase to move the body right. */
#define FONT_QUIT_BODY_BOX_X 25.4f

/* Quit prompt body top edge; increase to move the body down. */
#define FONT_QUIT_BODY_BOX_Y 12.0f

/* Quit prompt width; larger values wrap later. */
#define FONT_QUIT_BODY_BOX_WIDTH 420u

/* Quit prompt box height used to place its wrapped block. */
#define FONT_QUIT_BODY_BOX_HEIGHT 40u

/* Vertical distance between quit-prompt lines. */
#define FONT_QUIT_BODY_LINE_HEIGHT 20.0f

/* Maximum quit-prompt line count. */
#define FONT_QUIT_BODY_LINE_LIMIT 2u

/* === Character Select return-confirmation body === */

/* Return prompt left edge; increase to move the body right. */
#define FONT_CHARACTER_BODY_BOX_X 8.0f

/* Return prompt top edge; increase to move the body down. */
#define FONT_CHARACTER_BODY_BOX_Y 8.0f

/* Return prompt width; larger values wrap later or shrink less. */
#define FONT_CHARACTER_BODY_BOX_WIDTH 368u

/* Return prompt box height used for vertical centering. */
#define FONT_CHARACTER_BODY_BOX_HEIGHT 24u

/* Return prompt line height. */
#define FONT_CHARACTER_BODY_LINE_HEIGHT 20.0f

/* Keeps the Character Select return prompt on one line. */
#define FONT_CHARACTER_BODY_LINE_LIMIT 1u

/* === Special Controls explanatory body === */

/* Special Controls body left edge; increase to move it right. */
#define FONT_SPECIAL_BODY_BOX_X 26.0f

/* Special Controls body top edge; increase to move it down. */
#define FONT_SPECIAL_BODY_BOX_Y 12.0f

/* Special Controls body width; larger values wrap later. */
#define FONT_SPECIAL_BODY_BOX_WIDTH 400u

/* Special Controls body height used for vertical placement. */
#define FONT_SPECIAL_BODY_BOX_HEIGHT 60u

/* Vertical distance between Special Controls body lines. */
#define FONT_SPECIAL_BODY_LINE_HEIGHT 20.0f

/* Maximum Special Controls body line count. */
#define FONT_SPECIAL_BODY_LINE_LIMIT 2u

/* === Collection exit-confirmation body === */

/* Collection exit body left edge; increase to move it right. */
#define FONT_COLLECTION_BODY_BOX_X 24.8f

/* Collection exit body top edge; increase to move it down. */
#define FONT_COLLECTION_BODY_BOX_Y 12.0f

/* Collection exit body width; larger values wrap later. */
#define FONT_COLLECTION_BODY_BOX_WIDTH 400u

/* Collection exit body height used for vertical placement. */
#define FONT_COLLECTION_BODY_BOX_HEIGHT 60u

/* Collection exit body glyph width; larger values widen visible letters. */
#define FONT_COLLECTION_BODY_SCALE_X 1.0f

/* Vertical distance between Collection exit body lines. */
#define FONT_COLLECTION_BODY_LINE_HEIGHT 20.0f

/* Maximum Collection exit body line count. */
#define FONT_COLLECTION_BODY_LINE_LIMIT 2u

/* === Shared temporary body storage: internal capacity === */

/* Maximum copied body/list text bytes including the terminator; not geometry. */
#define FONT_BODY_BUFFER_SIZE 0x100u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

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
    u32 callback,
    float fixed_scale_x
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
    if (fixed_scale_x > 0.0f) {
        frame.session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        frame.session.scale_x = fixed_scale_x;
    }
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
        (u32)font_v2_collection_body_callback,
        0.0f
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
        (u32)font_v2_collection_body_callback,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_collection_body_callback")
int font_v2_collection_body_callback(
    u32 object,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    volatile u8 *object_bytes = (volatile u8 *)object;
    volatile u32 *object_words = (volatile u32 *)object;
    FontV2NativeUiDraw draw = (FontV2NativeUiDraw)0x00379A20u;
    FontV2UiDrawRecord record;

    if (!object_bytes || !text || !session || object_bytes[0x62] == 0) {
        return 0;
    }

    record.draw_x = session->draw_x;
    record.draw_y = session->draw_y;
    record.text = text;
    record.arg2 = arg2;
    return draw(
        object_words[0x78u / sizeof(u32)],
        &record,
        object_words[0x74u / sizeof(u32)],
        -1
    );
}

FONT_V2_SECTION(".text.font_v2_collection_body_adapter")
int font_v2_collection_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    int result;

    if (font_v2_is_mode_select_body(text)) {
        return font_v2_wrapped_body_common(
            arg0,
            text,
            arg2,
            FONT_MODE_SELECT_BODY_BOX_X,
            FONT_MODE_SELECT_BODY_BOX_Y,
            FONT_MODE_SELECT_BODY_BOX_WIDTH,
            FONT_MODE_SELECT_BODY_BOX_HEIGHT,
            FONT_MODE_SELECT_BODY_LINE_HEIGHT,
            FONT_MODE_SELECT_BODY_LINE_LIMIT,
            (u32)font_v2_collection_body_callback,
            0.0f
        );
    }

    result = font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_COLLECTION_BODY_BOX_X,
        FONT_COLLECTION_BODY_BOX_Y,
        FONT_COLLECTION_BODY_BOX_WIDTH,
        FONT_COLLECTION_BODY_BOX_HEIGHT,
        FONT_COLLECTION_BODY_LINE_HEIGHT,
        FONT_COLLECTION_BODY_LINE_LIMIT,
        (u32)font_v2_collection_body_callback,
        FONT_COLLECTION_BODY_SCALE_X
    );
    if (result >= 0) {
        font_v2_quit_active = FONT_COLLECTION_CHOICE_SCOPE;
    }
    return result;
}
