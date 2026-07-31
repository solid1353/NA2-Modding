typedef unsigned char u8;
typedef unsigned int u32;
typedef void (*NativeTextDraw)(float x, float y, const u8 *text, u32 highlighted);

#define NATIVE_TEXT_DRAW_ADDRESS 0x00379040u
#define HOT_RELOAD_VISIBLE_FRAMES 300u

#ifndef HOT_RELOAD_LABEL
#define HOT_RELOAD_LABEL "HOT RELOAD"
#endif

static volatile u32 visible_frames;

void hotReloadTest(void) {
    NativeTextDraw draw = (NativeTextDraw)NATIVE_TEXT_DRAW_ADDRESS;

    if (visible_frames >= HOT_RELOAD_VISIBLE_FRAMES) {
        return;
    }

    draw(1.0f, 1.0f, (const u8 *)HOT_RELOAD_LABEL, 0u);
    visible_frames += 1u;
}
