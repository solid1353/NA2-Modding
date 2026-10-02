/* Selectable Shadowblur Extra Hit behavior. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))

extern const u32 battle_settings_shadowblur_default;

volatile u32 shadowblur_state
    __attribute__((section(".bss.shadowblur_state")));
volatile u32 shadowblur_initialized
    __attribute__((section(".bss.shadowblur_initialized")));

static __attribute__((always_inline)) inline void shadowblur_initialize(void)
{
    if (shadowblur_initialized == 0u) {
        shadowblur_state = battle_settings_shadowblur_default != 0u;
        shadowblur_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.shadowblur_get")
u32 shadowblur_get(void)
{
    shadowblur_initialize();
    return shadowblur_state;
}

SETTINGS_SECTION(".text.shadowblur_set")
void shadowblur_set(u32 enabled)
{
    shadowblur_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_shadowblur_default != 0u;
    }
    shadowblur_state = enabled;
}
