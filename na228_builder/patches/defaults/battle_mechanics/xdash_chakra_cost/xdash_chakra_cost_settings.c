/* Selectable committed X-dash chakra cost. */

typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))
#define XDASH_CHAKRA_COST_MAX 100u
#define XDASH_CHAKRA_COST_STEP 5u
#define XDASH_CHAKRA_COST_OPTION_MAX \
    (XDASH_CHAKRA_COST_MAX / XDASH_CHAKRA_COST_STEP)

extern const u32 battle_settings_xdash_chakra_cost_default;

volatile u32 xdash_chakra_cost_state
    __attribute__((section(".bss.xdash_chakra_cost_state")));
volatile u32 xdash_chakra_cost_initialized
    __attribute__((section(".bss.xdash_chakra_cost_initialized")));

static __attribute__((always_inline)) inline void
xdash_chakra_cost_initialize(void)
{
    if (xdash_chakra_cost_initialized == 0u) {
        xdash_chakra_cost_state = battle_settings_xdash_chakra_cost_default;
        xdash_chakra_cost_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.xdash_chakra_cost_get")
u32 xdash_chakra_cost_get(void)
{
    xdash_chakra_cost_initialize();
    return xdash_chakra_cost_state;
}

SETTINGS_SECTION(".text.xdash_chakra_cost_option_get")
u32 xdash_chakra_cost_option_get(void)
{
    xdash_chakra_cost_initialize();
    return xdash_chakra_cost_state / XDASH_CHAKRA_COST_STEP;
}

SETTINGS_SECTION(".text.xdash_chakra_cost_option_set")
void xdash_chakra_cost_option_set(u32 option)
{
    xdash_chakra_cost_initialize();
    if (option > XDASH_CHAKRA_COST_OPTION_MAX) {
        option = battle_settings_xdash_chakra_cost_default /
            XDASH_CHAKRA_COST_STEP;
    }
    xdash_chakra_cost_state = option * XDASH_CHAKRA_COST_STEP;
}
