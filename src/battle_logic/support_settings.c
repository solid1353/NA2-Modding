/* Selectable battle support behavior. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))

extern const u32 battle_settings_support_default;

volatile u32 support_state
    __attribute__((section(".bss.support_state")));
volatile u32 support_initialized
    __attribute__((section(".bss.support_initialized")));

static __attribute__((always_inline)) inline void support_initialize(void)
{
    if (support_initialized == 0u) {
        support_state = battle_settings_support_default != 0u;
        support_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.support_get")
u32 support_get(void)
{
    support_initialize();
    return support_state;
}

SETTINGS_SECTION(".text.support_set")
void support_set(u32 enabled)
{
    support_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_support_default != 0u;
    }
    support_state = enabled;
}
