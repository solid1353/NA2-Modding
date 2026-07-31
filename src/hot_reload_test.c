typedef unsigned char u8;
typedef unsigned int u32;
typedef void (*NativeTextDraw)(float x, float y, const u8 *text, u32 highlighted);

#define NATIVE_TEXT_DRAW_ADDRESS 0x00379040u
#define HOT_RELOAD_VISIBLE_FRAMES 120u

static volatile u32 visible_frames;

void hotReloadTest(void) {
    NativeTextDraw draw = (NativeTextDraw)NATIVE_TEXT_DRAW_ADDRESS;

    if (visible_frames >= HOT_RELOAD_VISIBLE_FRAMES) {
        return;
    }

    draw(16.0f, 16.0f, (const u8 *)"HOT RELOAD 12C2", 1u);
    visible_frames += 1u;
}
