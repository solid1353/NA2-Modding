/* Selectable pre-impact Substitution input window. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))
#define SUB_ACTIVE_FRAMES_MAX 16u

extern const u32 battle_settings_sub_active_frames_default;

volatile u32 sub_active_frames_state
    __attribute__((section(".bss.sub_active_frames_state")));
volatile u32 sub_active_frames_initialized
    __attribute__((section(".bss.sub_active_frames_initialized")));

static __attribute__((always_inline)) inline void
sub_active_frames_initialize(void)
{
    if (sub_active_frames_initialized == 0u) {
        sub_active_frames_state = battle_settings_sub_active_frames_default;
        sub_active_frames_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.sub_active_frames_get")
u32 sub_active_frames_get(void)
{
    sub_active_frames_initialize();
    return sub_active_frames_state;
}

SETTINGS_SECTION(".text.sub_active_frames_set")
void sub_active_frames_set(u32 frames)
{
    sub_active_frames_initialize();
    if (frames > SUB_ACTIVE_FRAMES_MAX) {
        frames = battle_settings_sub_active_frames_default;
    }
    sub_active_frames_state = frames;
}
