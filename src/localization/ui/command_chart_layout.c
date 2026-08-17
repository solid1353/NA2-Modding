typedef signed short s16;

typedef struct UiRectangle {
    s16 x;
    s16 y;
    s16 width;
    s16 height;
} UiRectangle;

typedef void (*NativeScaledRectangleDraw)(
    float x,
    float y,
    float width,
    float height,
    void *context,
    const UiRectangle *rectangle
);

#define NATIVE_SCALED_RECTANGLE_DRAW_ADDRESS 0x0037BBD0u
#define COMMAND_CHART_NAME_CENTER_X 150.0f
#define COMMAND_CHART_NAME_MAX_WIDTH 172.0f

#define COMMAND_CHART_LAYOUT_SECTION(name) \
    __attribute__((section(name), noinline))

COMMAND_CHART_LAYOUT_SECTION(
    ".text.localization_command_chart_name_draw"
)
void localization_command_chart_name_draw(
    float unused_x,
    float y,
    void *context,
    const UiRectangle *rectangle
)
{
    NativeScaledRectangleDraw draw =
        (NativeScaledRectangleDraw)
            NATIVE_SCALED_RECTANGLE_DRAW_ADDRESS;
    float width = (float)rectangle->width;
    float display_width = width;

    (void)unused_x;
    if (display_width > COMMAND_CHART_NAME_MAX_WIDTH) {
        display_width = COMMAND_CHART_NAME_MAX_WIDTH;
    }
    draw(
        COMMAND_CHART_NAME_CENTER_X - display_width * 0.5f,
        y,
        display_width,
        (float)rectangle->height,
        context,
        rectangle
    );
}
