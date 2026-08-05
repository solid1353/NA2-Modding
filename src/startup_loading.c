/* Display a boot-safe timed loading counter through the splash draw phase. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define SPLASH_UPDATE_ADDRESS 0x001E0980u
#define NATIVE_TEXT_DRAW_ADDRESS 0x00379040u
#define FRAMES_PER_PERCENT 60u
#define MAX_DISPLAY_PERCENT 99u

#define STARTUP_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

typedef struct StartupLoadingState {
    volatile u32 frames;
    volatile u32 percent;
    volatile u8 text[20];
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

STARTUP_LOADING_SECTION(".text.startup_loading_draw")
void startup_loading_draw(void *unused_sprite)
{
    void (*draw_text)(float, float, const u8 *, u32) =
        (void (*)(float, float, const u8 *, u32))NATIVE_TEXT_DRAW_ADDRESS;
    u32 frames;
    u32 percent;

    (void)unused_sprite;
    frames = startup_loading_state.frames + 1u;
    startup_loading_state.frames = frames;
    percent = frames / FRAMES_PER_PERCENT;
    if (percent > MAX_DISPLAY_PERCENT) {
        percent = MAX_DISPLAY_PERCENT;
    }
    startup_loading_state.percent = percent;
    startup_loading_state.text[15] =
        percent < 10u ? (u8)' ' : (u8)('0' + percent / 10u);
    startup_loading_state.text[16] = (u8)('0' + percent % 10u);
    draw_text(220.0f, 210.0f, (const u8 *)startup_loading_state.text, 0u);
}
