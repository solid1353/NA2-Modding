/* Draw a standalone boot splash with a timed loading bar. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define SPLASH_UPDATE_ADDRESS 0x001E0980u
#define SPLASH_LOAD_FILE_ADDRESS 0x00116DE0u
#define SPLASH_RESOURCE_LOOKUP_ADDRESS 0x001AA450u
#define SPLASH_TEXTURE_LOOKUP_ADDRESS 0x001A8F00u
#define RENDER_RESET_ADDRESS 0x0010D6A0u
#define RENDER_ENABLE_TEXTURE_ADDRESS 0x0010CAA0u
#define RENDER_TEXTURE_MODE_ADDRESS 0x0010C9E0u
#define RESOURCE_METADATA_LOOKUP_ADDRESS 0x001BCA00u
#define LOGO_PATH_POINTER_ADDRESS 0x00603060u
#define RESOURCE_METADATA_ROOT_ADDRESS 0x0061EA60u
#define SPLASH_TEXTURE_NAME_ADDRESS 0x00400DD0u
#define SPLASH_DECOMPRESSED_SIZE 921452u
#define RENDER_MANAGER_POINTER_ADDRESS 0x006073D4u
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
#define CONTEXT_U_OFFSET 0x130u
#define CONTEXT_V_OFFSET 0x134u
#define MANAGER_TEXTURE_OFFSET 0x128u

#define COLOR_WHITE 0xFFFFFFFFu
#define COLOR_TRACK 0xFF303030u
#define ROUNDED_BAR_STEPS 32u

#define STARTUP_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

typedef struct StartupLoadingState {
    volatile u32 start_ticks;
    volatile u32 percent;
    volatile u32 splash_textures[3];
} StartupLoadingState;

extern volatile StartupLoadingState startup_loading_state;

static const u8 startup_splash_path[]
    __attribute__((section(".rodata.startup_loading_splash_path"))) =
        "CDV:PRG/228_SPL.CCS";

static const float startup_loading_cap_profile[16]
    __attribute__((section(".rodata.startup_loading_cap_profile"))) = {
        0.5000000f, 0.3260074f, 0.2579385f, 0.2085194f,
        0.1692811f, 0.1369078f, 0.1096876f, 0.0866014f,
        0.0669873f, 0.0503908f, 0.0364876f, 0.0250411f,
        0.0158771f, 0.0088677f, 0.0039216f, 0.0009775f
    };

STARTUP_LOADING_SECTION(".text.startup_loading_load")
void startup_loading_load(void)
{
    void (*load)(const u8 *, u32) =
        (void (*)(const u8 *, u32))SPLASH_LOAD_FILE_ADDRESS;

    load(startup_splash_path, 0u);
}

STARTUP_LOADING_SECTION(".text.startup_loading_gzip_size")
u32 startup_loading_gzip_size(const u8 *path)
{
    u32 (*metadata_lookup)(u32, const u8 *) =
        (u32 (*)(u32, const u8 *))RESOURCE_METADATA_LOOKUP_ADDRESS;
    u32 entry;

    if (path == startup_splash_path) {
        return SPLASH_DECOMPRESSED_SIZE;
    }
    entry = metadata_lookup(RESOURCE_METADATA_ROOT_ADDRESS, path);
    return entry == 0u ? 0u : *(volatile u32 *)(entry + 0x24u);
}

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
    void (*reset)(void *, u32) =
        (void (*)(void *, u32))RENDER_RESET_ADDRESS;
    void (*setup)(u32, u32) = (void (*)(u32, u32))PRIMITIVE_SETUP_ADDRESS;
    void (*flush)(void) = (void (*)(void))PRIMITIVE_FLUSH_ADDRESS;
    void *manager = *(void * volatile *)RENDER_MANAGER_POINTER_ADDRESS;
    volatile u8 *context;

    if (manager == (void *)0) {
        return;
    }
    reset(manager, 0u);
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

STARTUP_LOADING_SECTION(".text.startup_loading_tile")
static void startup_loading_tile(
    u32 texture, float left, float top, float u, float v
)
{
    void (*reset)(void *, u32) =
        (void (*)(void *, u32))RENDER_RESET_ADDRESS;
    void (*enable_texture)(void *, u32) =
        (void (*)(void *, u32))RENDER_ENABLE_TEXTURE_ADDRESS;
    void (*texture_mode)(void *, u32) =
        (void (*)(void *, u32))RENDER_TEXTURE_MODE_ADDRESS;
    void (*setup)(u32, u32) = (void (*)(u32, u32))PRIMITIVE_SETUP_ADDRESS;
    void (*flush)(void) = (void (*)(void))PRIMITIVE_FLUSH_ADDRESS;
    void *manager = *(void * volatile *)RENDER_MANAGER_POINTER_ADDRESS;
    volatile u8 *context;
    /* The atlas is stored bottom-up, so its logical top tile uses high V. */
    const float texture_top = 511.5f - v;
    const float texture_bottom = 256.5f - v;

    if (manager == (void *)0) {
        return;
    }
    reset(manager, 0u);
    *(volatile u32 *)((volatile u8 *)manager + MANAGER_TEXTURE_OFFSET) = texture;
    enable_texture(manager, 1u);
    texture_mode(manager, 0u);
    setup(5u, 0u);
    context = *(volatile u8 **)RENDER_CONTEXT_POINTER_ADDRESS;
    if (context == (volatile u8 *)0) {
        return;
    }

    *(volatile float *)(context + CONTEXT_DEPTH_OFFSET) = 1.0f;
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 2u;
    startup_loading_color(context, COLOR_WHITE);
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 0x80000u;
    *(volatile float *)(context + CONTEXT_U_OFFSET) = u + 0.5f;
    *(volatile float *)(context + CONTEXT_V_OFFSET) = texture_top;
    startup_loading_vertex(context, left, top);
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 0x80000u;
    *(volatile float *)(context + CONTEXT_U_OFFSET) = u + 255.5f;
    *(volatile float *)(context + CONTEXT_V_OFFSET) = texture_top;
    startup_loading_vertex(context, left + 128.0f, top);
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 0x80000u;
    *(volatile float *)(context + CONTEXT_U_OFFSET) = u + 0.5f;
    *(volatile float *)(context + CONTEXT_V_OFFSET) = texture_bottom;
    startup_loading_vertex(context, left, top + 128.0f);
    *(volatile u32 *)(context + CONTEXT_FLAGS_OFFSET) |= 0x80000u;
    *(volatile float *)(context + CONTEXT_U_OFFSET) = u + 255.5f;
    *(volatile float *)(context + CONTEXT_V_OFFSET) = texture_bottom;
    startup_loading_vertex(context, left + 128.0f, top + 128.0f);
    flush();
}

STARTUP_LOADING_SECTION(".text.startup_loading_rounded_rect")
static void startup_loading_rounded_rect(
    float left,
    float top,
    float right,
    float bottom,
    u32 color
)
{
    const float height = bottom - top;
    const float step = height / (float)ROUNDED_BAR_STEPS;
    u32 row;

    for (row = 0u; row < ROUNDED_BAR_STEPS; ++row) {
        u32 edge = row < 16u ? row : 31u - row;
        float inset = startup_loading_cap_profile[edge] * height;

        if (right - left > inset * 2.0f) {
            startup_loading_rect(
                left + inset,
                top + (float)row * step,
                right - inset,
                row == 31u ? bottom : top + (float)(row + 1u) * step,
                color
            );
        }
    }
}

STARTUP_LOADING_SECTION(".text.startup_loading_draw")
void startup_loading_draw(void *unused_sprite)
{
    u32 (*lookup_resource)(const u8 *) =
        (u32 (*)(const u8 *))SPLASH_RESOURCE_LOOKUP_ADDRESS;
    u32 (*lookup_texture)(u32, const u8 *, u32) =
        (u32 (*)(u32, const u8 *, u32))SPLASH_TEXTURE_LOOKUP_ADDRESS;
    u32 row;
    u32 now;
    u32 start_ticks;
    u32 elapsed_ticks;
    u32 percent;

    (void)unused_sprite;
    if (startup_loading_state.splash_textures[0] == 0u) {
        u32 resource = lookup_resource(
            *(const u8 * volatile *)LOGO_PATH_POINTER_ADDRESS
        );
        if (resource != 0u) {
            for (row = 0u; row < 3u; ++row) {
                startup_loading_state.splash_textures[row] = lookup_texture(
                    resource,
                    (const u8 *)(SPLASH_TEXTURE_NAME_ADDRESS + row * 16u),
                    0u
                );
            }
        }
    }
    if (startup_loading_state.splash_textures[0] != 0u &&
        startup_loading_state.splash_textures[1] != 0u &&
        startup_loading_state.splash_textures[2] != 0u) {
        for (row = 0u; row < 3u; ++row) {
            u32 column;

            for (column = 0u; column < 4u; ++column) {
                startup_loading_tile(
                    startup_loading_state.splash_textures[row],
                    (float)(column * 128u), (float)(row * 128u),
                    (float)((column % 2u) * 256u),
                    (float)((column / 2u) * 256u)
                );
            }
        }
    }

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

    {
        /* Edit these three values to position and size the bar. */
        const float top = 242.0f;
        const float height = 9.0f;
        const float width = 95.0f;

        const float left = 256.0f - width * 0.5f;
        const float bottom = top + height;

        startup_loading_rounded_rect(
            left, top, left + width, bottom, COLOR_TRACK
        );
        if (percent != 0u) {
            const float right = left + width * (float)percent / 100.0f;

            startup_loading_rounded_rect(left, top, right, bottom, COLOR_WHITE);
        }
    }
}
