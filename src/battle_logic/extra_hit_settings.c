/* Selectable Extra Hit behavior. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))

extern const u32 battle_settings_extra_hit_default;

volatile u32 extra_hit_state
    __attribute__((section(".bss.extra_hit_state")));
volatile u32 extra_hit_initialized
    __attribute__((section(".bss.extra_hit_initialized")));

static __attribute__((always_inline)) inline void extra_hit_initialize(void)
{
    if (extra_hit_initialized == 0u) {
        extra_hit_state = battle_settings_extra_hit_default != 0u;
        extra_hit_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.extra_hit_get")
u32 extra_hit_get(void)
{
    extra_hit_initialize();
    return extra_hit_state;
}

SETTINGS_SECTION(".text.extra_hit_set")
void extra_hit_set(u32 enabled)
{
    extra_hit_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_extra_hit_default != 0u;
    }
    extra_hit_state = enabled;
}
