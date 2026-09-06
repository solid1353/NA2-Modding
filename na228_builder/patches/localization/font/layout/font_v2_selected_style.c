#define FONT_V2_DECLARATIONS_ONLY
#include "font_v2_core.c"

/* Fixed native selected-style state; these addresses are ABI, not tuning. */
#define FONT_V2_GLOBAL_CHOICE_RECORDS_ADDRESS 0x005B1280u
#define FONT_V2_NATIVE_CONTEXT_ADDRESS 0x00607474u
#define FONT_V2_ORDINARY_COLOR 0xFF000000u
#define FONT_V2_SELECTED_COLOR 0xFF0000D4u
#define FONT_V2_ORDINARY_DRAW_ADDRESS 0x00378F50u
#define FONT_V2_SELECTED_DRAW_ADDRESS 0x00379150u

typedef struct FontV2GlobalChoiceRecord {
    float draw_x;
    float draw_y;
    const u8 *text;
    u32 unused;
} FontV2GlobalChoiceRecord;

typedef int (*FontV2GlobalSetContext)(u32 renderer, u32 context);
typedef void (*FontV2GlobalChoiceDraw)(
    const u8 *text,
    u32 color,
    float draw_x,
    float draw_y
);

FONT_V2_SECTION(".text.font_v2_global_two_choice_draw")
int font_v2_global_two_choice_draw(u32 object, u32 selected) {
    const volatile FontV2GlobalChoiceRecord *records =
        (const volatile FontV2GlobalChoiceRecord *)
            FONT_V2_GLOBAL_CHOICE_RECORDS_ADDRESS;
    FontV2GlobalSetContext set_context =
        (FontV2GlobalSetContext)FONT_SET_CONTEXT_ADDRESS;
    volatile u32 *object_words = (volatile u32 *)object;

    set_context(
        *(volatile u32 *)FONT_RENDERER_POINTER_ADDRESS,
        object_words[7]
    );
    if (selected == 1u) {
        ((FontV2GlobalChoiceDraw)FONT_V2_SELECTED_DRAW_ADDRESS)(
            records[1].text,
            FONT_V2_SELECTED_COLOR,
            records[1].draw_x,
            records[1].draw_y
        );
    } else {
        ((FontV2GlobalChoiceDraw)FONT_V2_ORDINARY_DRAW_ADDRESS)(
            records[1].text,
            FONT_V2_ORDINARY_COLOR,
            records[1].draw_x,
            records[1].draw_y
        );
    }
    if (selected == 0u) {
        ((FontV2GlobalChoiceDraw)FONT_V2_SELECTED_DRAW_ADDRESS)(
            records[0].text,
            FONT_V2_SELECTED_COLOR,
            records[0].draw_x,
            records[0].draw_y
        );
    } else {
        ((FontV2GlobalChoiceDraw)FONT_V2_ORDINARY_DRAW_ADDRESS)(
            records[0].text,
            FONT_V2_ORDINARY_COLOR,
            records[0].draw_x,
            records[0].draw_y
        );
    }
    return set_context(
        *(volatile u32 *)FONT_RENDERER_POINTER_ADDRESS,
        *(volatile u32 *)FONT_V2_NATIVE_CONTEXT_ADDRESS
    );
}
