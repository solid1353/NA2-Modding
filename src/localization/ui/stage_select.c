/* Localized Stage Select name fitting without repurposing preview indices. */

typedef signed short s16;

typedef struct StageNameRectangle {
    s16 u;
    s16 v;
    s16 width;
    s16 height;
} StageNameRectangle;

typedef void (*NativeStageNameDraw)(
    float x,
    float y,
    float scale_x,
    float scale_y,
    void *context,
    const StageNameRectangle *rectangle
);

#define UI_STAGE_SELECT_SECTION(name) \
    __attribute__((section(name), noinline))

#define NATIVE_STAGE_NAME_DRAW_ADDRESS 0x0037BD00u
#define STAGE_NAME_MAX_WIDTH 214.0f

UI_STAGE_SELECT_SECTION(
    ".text.localization_ui_stage_select_name_draw"
)
void localization_ui_stage_select_name_draw(
    float x,
    float y,
    float unused_scale_x,
    float scale_y,
    void *context,
    const StageNameRectangle *rectangle
)
{
    NativeStageNameDraw draw =
        (NativeStageNameDraw)NATIVE_STAGE_NAME_DRAW_ADDRESS;
    float width = (float)rectangle->width;
    float scale_x = 1.0f;

    (void)unused_scale_x;
    if (width > STAGE_NAME_MAX_WIDTH) {
        scale_x = STAGE_NAME_MAX_WIDTH / width;
    }
    draw(x, y, scale_x, scale_y, context, rectangle);
}
