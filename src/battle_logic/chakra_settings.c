/* Selectable shared Battle and Practice chakra behavior. */

typedef unsigned char u8;
typedef unsigned int u32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))

#define LIVE_MANAGER_POINTER_ADDRESS 0x00607600u
#define MANAGER_P1_FIGHTER_OFFSET 0xDE4u
#define MANAGER_P2_FIGHTER_OFFSET 0xDE8u
#define FIGHTER_CHAKRA_OFFSET 0x70u

#define CHAKRA_MODE_NORMAL 0u
#define CHAKRA_MODE_UNLIMITED 1u
#define CHAKRA_REGEN_OPTION_OFFSET 1u
#define CHAKRA_OPTION_MAX 101u
#define CHAKRA_CAPACITY 15.0f
#define CHAKRA_REGEN_TENTHS_PER_UPDATE_DIVISOR 2000.0f

extern const u32 battle_settings_chakra_default;

volatile u32 chakra_mode_state
    __attribute__((section(".bss.chakra_mode_state")));
volatile u32 chakra_mode_initialized
    __attribute__((section(".bss.chakra_mode_initialized")));

const u8 chakra_normal_label[]
    __attribute__((section(".rodata.chakra_normal_label"), used)) =
        "Normal";

const u8 chakra_unlimited_label[]
    __attribute__((section(".rodata.chakra_unlimited_label"), used)) =
        "Unlimited";

static __attribute__((always_inline)) inline void chakra_mode_initialize(void)
{
    if (chakra_mode_initialized == 0u) {
        chakra_mode_state = battle_settings_chakra_default;
        chakra_mode_initialized = 1u;
    }
}

SETTINGS_SECTION(".text.chakra_mode_get")
u32 chakra_mode_get(void)
{
    chakra_mode_initialize();
    return chakra_mode_state;
}

SETTINGS_SECTION(".text.chakra_mode_set")
void chakra_mode_set(u32 mode)
{
    chakra_mode_initialize();
    if (mode > CHAKRA_OPTION_MAX) {
        mode = battle_settings_chakra_default;
    }
    chakra_mode_state = mode;
}

SETTINGS_SECTION(".text.chakra_mode_apply")
void chakra_mode_apply(void *fighter)
{
    u8 *manager;
    volatile float *chakra;
    float value;
    u32 mode = chakra_mode_get();

    if (fighter == (void *)0 || mode == CHAKRA_MODE_NORMAL) {
        return;
    }
    manager = *(u8 * volatile *)LIVE_MANAGER_POINTER_ADDRESS;
    if (
        manager == (void *)0 ||
        (
            *(void * volatile *)(manager + MANAGER_P1_FIGHTER_OFFSET) !=
                fighter &&
            *(void * volatile *)(manager + MANAGER_P2_FIGHTER_OFFSET) != fighter
        )
    ) {
        return;
    }

    chakra = (volatile float *)((u8 *)fighter + FIGHTER_CHAKRA_OFFSET);
    if (mode == CHAKRA_MODE_UNLIMITED) {
        *chakra = CHAKRA_CAPACITY;
        return;
    }
    value = *chakra +
        (float)(mode - CHAKRA_REGEN_OPTION_OFFSET) /
            CHAKRA_REGEN_TENTHS_PER_UPDATE_DIVISOR;
    *chakra = value < CHAKRA_CAPACITY ? value : CHAKRA_CAPACITY;
}
