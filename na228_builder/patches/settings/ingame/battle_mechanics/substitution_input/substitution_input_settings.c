/* 0 is native timing, 1 is Hold, and 2..16 select a 1..15-frame input window. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))
#define SUBSTITUTION_INPUT_MAX 16u

extern const u32 battle_settings_substitution_input_default;

volatile u32 substitution_input_state
    __attribute__((section(".bss.substitution_input_state")));
volatile u32 substitution_input_initialized
    __attribute__((section(".bss.substitution_input_initialized")));

static __attribute__((always_inline)) inline void
substitution_input_initialize(void)
{
    if (substitution_input_initialized == 0u) {
        substitution_input_state = battle_settings_substitution_input_default;
        substitution_input_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.substitution_input_get")
u32 substitution_input_get(void)
{
    substitution_input_initialize();
    return substitution_input_state;
}

SETTINGS_SECTION(".text.substitution_input_set")
void substitution_input_set(u32 frames)
{
    substitution_input_initialize();
    if (frames > SUBSTITUTION_INPUT_MAX) {
        frames = battle_settings_substitution_input_default;
    }
    substitution_input_state = frames;
}
