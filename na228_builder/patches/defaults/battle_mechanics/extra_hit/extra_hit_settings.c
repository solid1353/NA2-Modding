/* Selectable Extra Hit behavior and initiation penalty. */

typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int s32;

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))
#define EXTRA_HIT_ON 1u
#define EXTRA_HIT_LAST_OPTION 21u
#define FIGHTER_CHAKRA_OFFSET 0x70u
#define LIVE_MANAGER_POINTER_ADDRESS 0x00607600u
#define MANAGER_P1_FIGHTER_OFFSET 0xDE4u
#define MANAGER_P2_FIGHTER_OFFSET 0xDE8u

extern const u32 battle_settings_extra_hit_default;

volatile u32 extra_hit_state
    __attribute__((section(".bss.extra_hit_state")));
volatile u32 extra_hit_initialized
    __attribute__((section(".bss.extra_hit_initialized")));
volatile u32 extra_hit_charged[2]
    __attribute__((section(".bss.extra_hit_charged")));

static __attribute__((always_inline)) inline void extra_hit_initialize(void)
{
    if (extra_hit_initialized == 0u) {
        extra_hit_state = battle_settings_extra_hit_default;
        extra_hit_initialized = 1u;
    }
}

static __attribute__((always_inline)) inline s32 extra_hit_side(void *fighter)
{
    u8 *manager = *(u8 * volatile *)LIVE_MANAGER_POINTER_ADDRESS;
    if (manager != (void *)0) {
        if (*(void * volatile *)(manager + MANAGER_P1_FIGHTER_OFFSET) == fighter) {
            return 0;
        }
        if (*(void * volatile *)(manager + MANAGER_P2_FIGHTER_OFFSET) == fighter) {
            return 1;
        }
    }
    return -1;
}

SETTINGS_SECTION(".text.extra_hit_get")
u32 extra_hit_get(void)
{
    extra_hit_initialize();
    return extra_hit_state;
}

SETTINGS_SECTION(".text.extra_hit_set")
void extra_hit_set(u32 value)
{
    extra_hit_initialize();
    if (value > EXTRA_HIT_LAST_OPTION) {
        value = battle_settings_extra_hit_default;
    }
    extra_hit_state = value;
}

SETTINGS_SECTION(".text.extra_hit_begin_attack")
void extra_hit_begin_attack(void *fighter, s32 attack_index)
{
    s32 side = extra_hit_side(fighter);
    if (side >= 0) {
        extra_hit_charged[side] = 0u;
    }
    ((void (*)(void *, s32))0x00238A70u)(fighter, attack_index);
}

SETTINGS_SECTION(".text.extra_hit_check")
s32 extra_hit_check(void *fighter, s32 attack_index)
{
    s32 result = ((s32 (*)(void *, s32))0x00241A50u)(fighter, attack_index);
    u32 mode;
    s32 side;

    if (result != 1) {
        return result;
    }
    mode = extra_hit_get();
    if (mode == EXTRA_HIT_ON) {
        return result;
    }
    side = extra_hit_side(fighter);
    if (mode > EXTRA_HIT_ON && side >= 0 && extra_hit_charged[side] == 0u) {
        float *chakra = (float *)((u8 *)fighter + FIGHTER_CHAKRA_OFFSET);
        float cost = (float)((mode - 1u) * 5u) * 15.0f / 100.0f;
        float remaining = *chakra - cost;
        *chakra = remaining > 0.0f ? remaining : 0.0f;
        extra_hit_charged[side] = 1u;
    }
    /* Rejection continues through the native action-exit path at 0x23B6DC. */
    return -1;
}
