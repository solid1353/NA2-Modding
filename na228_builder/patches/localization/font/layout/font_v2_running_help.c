/* Shared horizontal menu help: identical measurement and drawing spacing. */
#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

#define HELP_APPEND_ADDRESS 0x0037F590u
#define HELP_DRAW_ADDRESS 0x0037F900u
#define FONT_SELECT_ADDRESS 0x00189740u
#define FONT_PARSE_ADDRESS 0x00185CA0u
#define FONT_DOUBLE_BYTE_ADDRESS 0x00184D90u
#define FONT_NATIVE_MEASURE_ADDRESS 0x003798E0u
#define FONT_ICON_INDEX_ADDRESS 0x00602A3Cu
#define FONT_ICON_METRIC_OFFSET 0x7Cu
#define FONT_RENDERER_WORDS (0x88u / sizeof(u32))

typedef struct HelpNode {
    u32 ownership;
    const u8 *text;
    float extent;
    struct HelpNode *next;
} HelpNode;

typedef struct HelpFrame {
    u32 renderer[FONT_RENDERER_WORDS];
    u32 scale;
    u32 icon_index;
    FontV2Session *previous;
    FontV2Session session;
} HelpFrame;

const u8 font_v2_help_font[]
    __attribute__((section(".rodata.font_v2_help_font"))) = "GF4.BIN";

static FONT_V2_SECTION(".text.font_v2_help_begin")
void font_v2_help_begin(HelpFrame *frame)
{
    volatile u32 *renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    u32 index;

    for (index = 0; index < FONT_RENDERER_WORDS; ++index) {
        frame->renderer[index] = renderer[index];
    }
    frame->scale = *(volatile u32 *)FONT_HORIZONTAL_SCALE_ADDRESS;
    frame->icon_index = *(volatile u32 *)FONT_ICON_INDEX_ADDRESS;
    frame->previous = font_v2_active_session;
    ((void (*)(volatile u32 *, const u8 *))FONT_SELECT_ADDRESS)(
        renderer, font_v2_help_font
    );
    renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
    *(volatile u8 *)((u8 *)renderer + FONT_RENDERER_FLAGS_OFFSET) |=
        FONT_RENDERER_ASCII_MODE_FLAG;
    *(volatile float *)FONT_HORIZONTAL_SCALE_ADDRESS = 1.0f;
    frame->session.scale_x = 1.0f;
    frame->session.scale_y = 1.0f;
    frame->session.flags = 0;
    font_v2_active_session = &frame->session;
}

static FONT_V2_SECTION(".text.font_v2_help_end")
void font_v2_help_end(const HelpFrame *frame)
{
    volatile u32 *renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    u32 index;

    for (index = 0; index < FONT_RENDERER_WORDS; ++index) {
        renderer[index] = frame->renderer[index];
    }
    *(volatile u32 *)FONT_HORIZONTAL_SCALE_ADDRESS = frame->scale;
    *(volatile u32 *)FONT_ICON_INDEX_ADDRESS = frame->icon_index;
    font_v2_active_session = frame->previous;
}

static FONT_V2_SECTION(".text.font_v2_help_measure")
float font_v2_help_measure(const u8 *text)
{
    float width = 0.0f;
    float maximum = 0.0f;
    u32 ruby = 0;

    while (*text) {
        s32 token[2];
        u8 glyph[3];
        u32 length;

        if (ruby && *text == '|') {
            while (*text && *text != '>') {
                ++text;
            }
            if (*text) {
                ++text;
            }
            ruby = 0;
            continue;
        }
        ((void (*)(const u8 *, s32 *))FONT_PARSE_ADDRESS)(text, token);
        if (token[0] == 1) {
            if (maximum < width) {
                maximum = width;
            }
            width = 0.0f;
            text += token[1];
        } else if (token[0] == 2) {
            text += token[1];
            ruby = 1;
        } else if (token[0] == 4) {
            /* Every native icon token fits in 16 bytes including its NUL.
             * Let the native parser select its icon ID, then use the same
             * caller-installed metric callback as the native icon renderer. */
            u8 icon[16];
            u32 count = 0;
            float advance = 0.0f;
            float height = 0.0f;
            u8 *renderer = *(u8 **)FONT_RENDERER_POINTER_ADDRESS;
            void (*metric)(float *, float *, u32) =
                *(void (**)(float *, float *, u32))(
                    renderer + FONT_ICON_METRIC_OFFSET
                );

            while (*text && *text != '>') {
                if (count < sizeof(icon) - 2u) {
                    icon[count++] = *text;
                }
                ++text;
            }
            if (*text) {
                icon[count++] = *text++;
            }
            icon[count] = 0;
            ((u32 (*)(const u8 *, s32))FONT_NATIVE_MEASURE_ADDRESS)(icon, 0);
            if (metric) {
                metric(&advance, &height, *(volatile u32 *)FONT_ICON_INDEX_ADDRESS);
            }
            width += advance;
        } else if (token[0] == 3 || token[0] == 5 || token[0] == 6) {
            /* Include the closing byte: native count/width parsing leaves it
             * behind for named color and kerning controls. */
            while (*text && *text != '>') {
                ++text;
            }
            if (*text) {
                ++text;
            }
        } else {
            length = token[0] == 0 ? (u32)token[1] :
                (1u + ((u32 (*)(const u8 *))FONT_DOUBLE_BYTE_ADDRESS)(text));
            glyph[0] = text[0];
            glyph[1] = length == 2u ? text[1] : 0;
            glyph[length] = 0;
            width += (float)((u32 (*)(const u8 *, s32))
                FONT_NATIVE_MEASURE_ADDRESS)(glyph, 0);
            if (token[0] == 0) {
                width -= 6.0f;
            }
            text += length;
        }
    }
    return maximum < width ? width : maximum;
}

FONT_V2_SECTION(".text.font_v2_help_set")
void font_v2_help_set(float unit, float *help, const u8 *text, s32 gap, s32 copy)
{
    HelpFrame frame;
    HelpNode *node;
    float extent = 0.0f;

    if (!help || !text || *((u8 *)help + 0x3C)) {
        return;
    }
    for (node = *(HelpNode **)((u8 *)help + 0x2C); node; node = node->next) {
        extent += node->extent;
    }
    if (extent > help[0x30 / sizeof(float)]) {
        return;
    }
    font_v2_help_begin(&frame);
    extent = font_v2_help_measure(text) + unit * (float)gap;
    font_v2_help_end(&frame);
    if (extent < help[0]) {
        extent = help[0] + unit;
    }
    ((void (*)(float, float *, const u8 *, s32))HELP_APPEND_ADDRESS)(
        extent, help, text, copy
    );
}

FONT_V2_SECTION(".text.font_v2_help_draw")
void font_v2_help_draw(void *help)
{
    HelpFrame frame;

    font_v2_help_begin(&frame);
    ((void (*)(void *))HELP_DRAW_ADDRESS)(help);
    font_v2_help_end(&frame);
}
