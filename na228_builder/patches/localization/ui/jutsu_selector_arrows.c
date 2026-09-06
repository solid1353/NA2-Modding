/* Localized Jutsu-selector arrow drawing. */

typedef unsigned int u32;

typedef struct JutsuSelectorArrowSprite {
    u32 unused_00;
    volatile u32 flags;
    unsigned char unused_08[0x44];
    volatile u32 rotation;
} JutsuSelectorArrowSprite;

typedef void (*NativeArrowMode)(
    JutsuSelectorArrowSprite *sprite,
    int selector,
    int enabled
);
typedef void (*NativeArrowDraw)(
    float x,
    float y,
    JutsuSelectorArrowSprite *sprite,
    const void *rectangle
);
typedef void (*NativeArrowFlush)(JutsuSelectorArrowSprite *sprite);

#define UI_JUTSU_ARROW_SECTION(name) \
    __attribute__((section(name), noinline))

#define NATIVE_ARROW_MODE_ADDRESS 0x001CBE40u
#define NATIVE_ARROW_DRAW_ADDRESS 0x0037BC40u
#define NATIVE_ARROW_FLUSH_ADDRESS 0x001CC070u
#define ARROW_MODE_SELECTOR 10
#define ARROW_FLIP_FLAG 0x40u
#define ARROW_ROTATION_PLUS_PI_OVER_2 0x3FC90FDBu
#define ARROW_ROTATION_MINUS_PI_OVER_2 0xBFC90FDBu

UI_JUTSU_ARROW_SECTION(
    ".text.localization_ui_jutsu_selector_arrow_draw_upper"
)
void localization_ui_jutsu_selector_arrow_draw_upper(
    float x,
    float y,
    JutsuSelectorArrowSprite *sprite,
    const void *rectangle
)
{
    NativeArrowMode mode = (NativeArrowMode)NATIVE_ARROW_MODE_ADDRESS;
    NativeArrowDraw draw = (NativeArrowDraw)NATIVE_ARROW_DRAW_ADDRESS;
    NativeArrowFlush flush = (NativeArrowFlush)NATIVE_ARROW_FLUSH_ADDRESS;

    mode(sprite, ARROW_MODE_SELECTOR, 1);
    sprite->rotation = ARROW_ROTATION_PLUS_PI_OVER_2;
    draw(x, y, sprite, rectangle);
    flush(sprite);
    mode(sprite, ARROW_MODE_SELECTOR, 0);
}

UI_JUTSU_ARROW_SECTION(
    ".text.localization_ui_jutsu_selector_arrow_draw_lower"
)
void localization_ui_jutsu_selector_arrow_draw_lower(
    float x,
    float y,
    JutsuSelectorArrowSprite *sprite,
    const void *rectangle
)
{
    NativeArrowMode mode = (NativeArrowMode)NATIVE_ARROW_MODE_ADDRESS;
    NativeArrowDraw draw = (NativeArrowDraw)NATIVE_ARROW_DRAW_ADDRESS;
    NativeArrowFlush flush = (NativeArrowFlush)NATIVE_ARROW_FLUSH_ADDRESS;

    mode(sprite, ARROW_MODE_SELECTOR, 1);
    sprite->rotation = ARROW_ROTATION_MINUS_PI_OVER_2;
    sprite->flags |= ARROW_FLIP_FLAG;
    draw(x, y, sprite, rectangle);
    flush(sprite);
    mode(sprite, ARROW_MODE_SELECTOR, 0);
}
