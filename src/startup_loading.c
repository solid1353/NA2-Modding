/* Display a boot-safe timed loading counter through solid GS primitives. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define SPLASH_UPDATE_ADDRESS 0x001E0980u
#define RENDER_CONTEXT_POINTER_ADDRESS 0x0060745Cu
#define PRIMITIVE_SETUP_ADDRESS 0x001830A0u
#define COLOR_SETUP_ADDRESS 0x00182A20u
#define VERTEX_SUBMIT_ADDRESS 0x001822B0u
#define PRIMITIVE_FLUSH_ADDRESS 0x00182F50u
#define EE_COUNT_TICKS_PER_SECOND 147456000u
#define LOAD_TICKS_PER_PERCENT \
    ((EE_COUNT_TICKS_PER_SECOND / 200u) * 13u)
#define MAX_DISPLAY_PERCENT 99u

#define CONTEXT_COLOR_OFFSET 0x100u
#define CONTEXT_X_OFFSET 0xE0u
#define CONTEXT_Y_OFFSET 0xE4u
#define CONTEXT_DEPTH_OFFSET 0xE8u
#define CONTEXT_FLAGS_OFFSET 0x170u

#define COLOR_WHITE 0xFFFFFFFFu
#define COLOR_TRACK 0xFF303030u

#define STARTUP_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

typedef struct StartupLoadingState {
    volatile u32 start_ticks;
    volatile u32 percent;
} StartupLoadingState;

extern volatile StartupLoadingState startup_loading_state;

STARTUP_LOADING_SECTION(".text.startup_loading_hook")
u32 startup_loading_hook(void *controller)
{
    u32 (*update_splash)(void *) =
        (u32 (*)(void *))SPLASH_UPDATE_ADDRESS;
    volatile u16 *halfwords = (volatile u16 *)controller;
    volatile u32 *words = (volatile u32 *)controller;

    if (controller != (void *)0 && words[2] == 0u) {
        update_splash(controller);
    }

    if (controller != (void *)0 && words[2] != 0u) {
        halfwords[0] = 1u;
        halfwords[8] = 0u;
    }

    return 1u;
}

STARTUP_LOADING_SECTION(".text.startup_loading_vertex")
static void startup_loading_vertex(volatile u8 *context, float x, float y)
{
    void (*submit)(u32) = (void (*)(u32))VERTEX_SUBMIT_ADDRESS;

    *(volatile float *)(context + CONTEXT_X_OFFSET) = x;
    *(volatile float *)(context + CONTEXT_Y_OFFSET) = y;
    submit(0u);
}

STARTUP_LOADING_SECTION(".text.startup_loading_color")
static void startup_loading_color(volatile u8 *context, u32 color)
{
    void (*set_color)(float *, u32) =
        (void (*)(float *, u32))COLOR_SETUP_ADDRESS;

    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 0x20000u;
    set_color((float *)(context + CONTEXT_COLOR_OFFSET), color);
}

STARTUP_LOADING_SECTION(".text.startup_loading_rect")
static void startup_loading_rect(
    float left,
    float top,
    float right,
    float bottom,
    u32 color
)
{
    void (*setup)(u32, u32) = (void (*)(u32, u32))PRIMITIVE_SETUP_ADDRESS;
    void (*flush)(void) = (void (*)(void))PRIMITIVE_FLUSH_ADDRESS;
    volatile u8 *context;

    setup(5u, 0u);
    context = *(volatile u8 **)RENDER_CONTEXT_POINTER_ADDRESS;
    if (context == (volatile u8 *)0) {
        return;
    }

    *(volatile float *)(context + CONTEXT_DEPTH_OFFSET) = 0.0f;
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 2u;
    startup_loading_color(context, color);
    startup_loading_vertex(context, left, top);
    startup_loading_vertex(context, right, top);
    startup_loading_vertex(context, left, bottom);
    startup_loading_vertex(context, right, bottom);
    flush();
}

STARTUP_LOADING_SECTION(".text.startup_loading_digit_mask")
static u32 startup_loading_digit_mask(u32 digit)
{
    switch (digit) {
    case 0u: return 0x3Fu;
    case 1u: return 0x06u;
    case 2u: return 0x5Bu;
    case 3u: return 0x4Fu;
    case 4u: return 0x66u;
    case 5u: return 0x6Du;
    case 6u: return 0x7Du;
    case 7u: return 0x07u;
    case 8u: return 0x7Fu;
    default: return 0x6Fu;
    }
}

STARTUP_LOADING_SECTION(".text.startup_loading_digit")
static void startup_loading_digit(
    float x,
    float y,
    u32 digit
)
{
    const float width = 40.0f;
    const float height = 72.0f;
    const float thickness = 7.0f;
    const float middle = y + height * 0.5f;
    const u32 mask = startup_loading_digit_mask(digit);

    if ((mask & 0x01u) != 0u)
        startup_loading_rect(x + thickness, y, x + width - thickness, y + thickness, COLOR_WHITE);
    if ((mask & 0x02u) != 0u)
        startup_loading_rect(x + width - thickness, y + thickness, x + width, middle, COLOR_WHITE);
    if ((mask & 0x04u) != 0u)
        startup_loading_rect(x + width - thickness, middle, x + width, y + height - thickness, COLOR_WHITE);
    if ((mask & 0x08u) != 0u)
        startup_loading_rect(x + thickness, y + height - thickness, x + width - thickness, y + height, COLOR_WHITE);
    if ((mask & 0x10u) != 0u)
        startup_loading_rect(x, middle, x + thickness, y + height - thickness, COLOR_WHITE);
    if ((mask & 0x20u) != 0u)
        startup_loading_rect(x, y + thickness, x + thickness, middle, COLOR_WHITE);
    if ((mask & 0x40u) != 0u)
        startup_loading_rect(x + thickness, middle - thickness * 0.5f, x + width - thickness, middle + thickness * 0.5f, COLOR_WHITE);
}

STARTUP_LOADING_SECTION(".text.startup_loading_percent_sign")
static void startup_loading_percent_sign(
    float x,
    float y
)
{
    u32 step;

    startup_loading_rect(x, y, x + 8.0f, y + 8.0f, COLOR_WHITE);
    startup_loading_rect(x + 28.0f, y + 52.0f, x + 36.0f, y + 60.0f, COLOR_WHITE);
    for (step = 0u; step < 6u; ++step) {
        float dx = (float)step * 5.0f;
        startup_loading_rect(x + 25.0f - dx, y + 8.0f + dx * 1.6f,
                             x + 31.0f - dx, y + 14.0f + dx * 1.6f,
                             COLOR_WHITE);
    }
}

STARTUP_LOADING_SECTION(".text.startup_loading_draw")
void startup_loading_draw(void *unused_sprite)
{
    u32 now;
    u32 start_ticks;
    u32 elapsed_ticks;
    u32 percent;

    (void)unused_sprite;
    percent = startup_loading_state.percent;
    if (percent < MAX_DISPLAY_PERCENT) {
        __asm__ volatile("mfc0\t%0, $9\n" : "=r"(now));
        start_ticks = startup_loading_state.start_ticks;
        if (start_ticks == 0u) {
            start_ticks = now == 0u ? 1u : now;
            startup_loading_state.start_ticks = start_ticks;
            elapsed_ticks = 0u;
        } else {
            elapsed_ticks = now - start_ticks;
        }

        percent = elapsed_ticks / LOAD_TICKS_PER_PERCENT;
        if (percent > MAX_DISPLAY_PERCENT) {
            percent = MAX_DISPLAY_PERCENT;
        }
        startup_loading_state.percent = percent;
    }

    startup_loading_digit(196.0f, 142.0f, percent / 10u);
    startup_loading_digit(246.0f, 142.0f, percent % 10u);
    startup_loading_percent_sign(298.0f, 148.0f);

    startup_loading_rect(96.0f, 260.0f, 416.0f, 272.0f, COLOR_TRACK);
    if (percent != 0u) {
        startup_loading_rect(
            96.0f,
            260.0f,
            96.0f + (float)percent * 3.2f,
            272.0f,
            COLOR_WHITE
        );
    }
}
