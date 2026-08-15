/* Spend chakra on the first update after X-dash becomes non-cancellable. */

typedef signed short s16;
typedef unsigned int u32;
typedef unsigned char u8;

#define XDASH_CHAKRA_COST_SECTION(name) \
    __attribute__((section(name), noinline))

#define FIGHTER_CHAKRA_OFFSET 0x70u
#define FIGHTER_MAJOR_ACTION_OFFSET 0x18Eu
#define FIGHTER_ACTION_INDEX_OFFSET 0x190u
#define FIGHTER_ACTION_PHASE_OFFSET 0x192u
#define FIGHTER_XDASH_SUBSTATE_OFFSET 0x9BAu
#define LIVE_MANAGER_POINTER_ADDRESS 0x00607600u
#define MANAGER_P1_FIGHTER_OFFSET 0xDE4u
#define MANAGER_P2_FIGHTER_OFFSET 0xDE8u

#define MAJOR_ACTION_GENERIC 8
#define XDASH_ACTION_INDEX 0x13
#define XDASH_MOVEMENT_PHASE 1
#define XDASH_MOVEMENT_SUBSTATE 2

typedef struct XdashChargeState {
    volatile u32 charged[2];
} XdashChargeState;

extern const float battle_logic_xdash_chakra_cost;
extern volatile XdashChargeState battle_logic_xdash_charge_state;

XDASH_CHAKRA_COST_SECTION(".text.battle_logic_xdash_pre_fighter_update")
void battle_logic_xdash_pre_fighter_update(void *fighter)
{
    u8 *bytes = (u8 *)fighter;
    u8 *manager;
    int side;
    volatile u32 *charged;

    if (fighter == (void *)0) {
        return;
    }
    manager = *(u8 * volatile *)LIVE_MANAGER_POINTER_ADDRESS;
    if (manager == (void *)0) {
        return;
    }
    if (*(void * volatile *)(manager + MANAGER_P1_FIGHTER_OFFSET) == fighter) {
        side = 0;
    } else if (
        *(void * volatile *)(manager + MANAGER_P2_FIGHTER_OFFSET) == fighter
    ) {
        side = 1;
    } else {
        return;
    }
    charged = &battle_logic_xdash_charge_state.charged[side];
    if (
        *(s16 *)(bytes + FIGHTER_MAJOR_ACTION_OFFSET) != MAJOR_ACTION_GENERIC ||
        *(s16 *)(bytes + FIGHTER_ACTION_INDEX_OFFSET) != XDASH_ACTION_INDEX ||
        *(s16 *)(bytes + FIGHTER_ACTION_PHASE_OFFSET) != XDASH_MOVEMENT_PHASE ||
        *(s16 *)(bytes + FIGHTER_XDASH_SUBSTATE_OFFSET) !=
            XDASH_MOVEMENT_SUBSTATE
    ) {
        *charged = 0u;
        return;
    }
    if (*charged == 0u) {
        float *chakra = (float *)(bytes + FIGHTER_CHAKRA_OFFSET);
        float remaining = *chakra - battle_logic_xdash_chakra_cost;

        *chakra = remaining > 0.0f ? remaining : 0.0f;
        *charged = 1u;
    }
}
