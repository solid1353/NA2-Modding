/* Selectable Ultimate Jutsu mode and contest behavior. */

typedef unsigned char u8;
typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))
#define SETTINGS_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define NATIVE_INPUT_STATE_ADDRESS 0x001D99B0u
#define NATIVE_CONTEST_RENDER_ADDRESS 0x0036BFF0u
#define ULTIMATE_JUTSU_MODE_NO_CONTEST 6u
#define ULTIMATE_JUTSU_MODE_NO_HUD 7u

typedef u32 (*NativeInputState)(u32 bank, u32 slot);
typedef void (*NativeContestRender)(void *contest);

extern const u32 battle_settings_ultimate_jutsu_default;

volatile u32 ultimate_jutsu_mode_state
    __attribute__((section(".bss.ultimate_jutsu_mode_state")));
volatile u32 ultimate_jutsu_mode_initialized
    __attribute__((section(".bss.ultimate_jutsu_mode_initialized")));

const u8 ultimate_jutsu_no_contest_label[]
    SETTINGS_USED_SECTION(".rodata.ultimate_jutsu_no_contest_label") =
        "No Contest";
const u8 ultimate_jutsu_no_hud_label[]
    SETTINGS_USED_SECTION(".rodata.ultimate_jutsu_no_hud_label") = "No HUD";

static __attribute__((always_inline)) inline void
ultimate_jutsu_mode_initialize(void)
{
    if (ultimate_jutsu_mode_initialized == 0u) {
        ultimate_jutsu_mode_state = battle_settings_ultimate_jutsu_default;
        ultimate_jutsu_mode_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.ultimate_jutsu_mode_default")
u32 ultimate_jutsu_mode_default(void)
{
    return battle_settings_ultimate_jutsu_default;
}

SETTINGS_SECTION(".text.ultimate_jutsu_mode_get")
u32 ultimate_jutsu_mode_get(void)
{
    ultimate_jutsu_mode_initialize();
    return ultimate_jutsu_mode_state;
}

SETTINGS_SECTION(".text.ultimate_jutsu_mode_set")
void ultimate_jutsu_mode_set(u32 mode)
{
    ultimate_jutsu_mode_initialize();
    if (mode > ULTIMATE_JUTSU_MODE_NO_HUD) {
        mode = ultimate_jutsu_mode_default();
    }
    ultimate_jutsu_mode_state = mode;
}

SETTINGS_SECTION(".text.ultimate_jutsu_contest_input_state")
u32 ultimate_jutsu_contest_input_state(u32 bank, u32 slot)
{
    NativeInputState native_input = (NativeInputState)NATIVE_INPUT_STATE_ADDRESS;

    if (ultimate_jutsu_mode_get() >= ULTIMATE_JUTSU_MODE_NO_CONTEST) {
        return 0u;
    }
    return native_input(bank, slot);
}

SETTINGS_SECTION(".text.ultimate_jutsu_contest_render")
void ultimate_jutsu_contest_render(void *contest)
{
    NativeContestRender native_render =
        (NativeContestRender)NATIVE_CONTEST_RENDER_ADDRESS;

    if (ultimate_jutsu_mode_get() < ULTIMATE_JUTSU_MODE_NO_CONTEST) {
        native_render(contest);
    }
}
