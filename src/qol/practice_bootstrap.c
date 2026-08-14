/* Enter a configured Practice battle directly after startup. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define PRACTICE_BOOTSTRAP_SECTION(name) \
    __attribute__((section(name), noinline))

#define BATTLE_MANAGER_POINTER_ADDRESS 0x00607600u
#define NATIVE_CHARACTER_SELECT_UPDATE_ADDRESS 0x001ED450u
#define NATIVE_BATTLE_UPDATE_ADDRESS 0x001EDB70u
#define NATIVE_BEGIN_TRANSITION_ADDRESS 0x002005B0u
#define NATIVE_APPLY_EFFECT_ADDRESS 0x00305C30u

#define PRACTICE_BOOTSTRAP_VERSION 1u
#define NO_AWAKENING_EFFECT 0xFFFFFFFFu

#define CONTROLLER_STATE_WORD 0u
#define CONTROLLER_COUNTDOWN_WORD 1u
#define PRACTICE_BATTLE_LOADING_STATE 10u
#define PRACTICE_TRANSITION_COUNTDOWN 3u

#define MANAGER_P1_CHARACTER_OFFSET 0x4Cu
#define MANAGER_P1_SUPPORT_OFFSET 0x68u
#define MANAGER_P2_CHARACTER_OFFSET 0x74u
#define MANAGER_P2_SUPPORT_OFFSET 0x90u
#define MANAGER_STAGE_OFFSET 0x98u
#define MANAGER_P1_SELECTED_CHARACTER_OFFSET 0xC8u
#define MANAGER_P1_SELECTED_SUPPORT_OFFSET 0xE4u
#define MANAGER_P2_SELECTED_CHARACTER_OFFSET 0xF0u
#define MANAGER_P2_SELECTED_SUPPORT_OFFSET 0x10Cu
#define MANAGER_P1_FIGHTER_OFFSET 0xDE4u

#define FIGHTER_ACTIVE_EFFECT_OFFSET 0x8E8u

#define FIXED_P2_CHARACTER_ID 0x39u
#define FIXED_P2_SUPPORT_ID 0x01u
#define FIXED_PRACTICE_STAGE_ID 0x06u

typedef struct PracticeBootstrapConfiguration {
    u32 version;
    u32 p1_character_id;
    u32 p1_support_id;
    u32 awakening_effect_id;
} PracticeBootstrapConfiguration;

typedef struct PracticeBootstrapState {
    volatile u32 awakening_applied;
} PracticeBootstrapState;

extern const PracticeBootstrapConfiguration practice_bootstrap_configuration;
extern volatile PracticeBootstrapState practice_bootstrap_state;

PRACTICE_BOOTSTRAP_SECTION(".text.qol_practice_bootstrap_select")
void qol_practice_bootstrap_select(u32 *controller)
{
    void (*native_character_select_update)(u32 *) =
        (void (*)(u32 *))NATIVE_CHARACTER_SELECT_UPDATE_ADDRESS;
    void (*begin_transition)(u32, u32) =
        (void (*)(u32, u32))NATIVE_BEGIN_TRANSITION_ADDRESS;
    volatile u8 *manager =
        *(volatile u8 **)BATTLE_MANAGER_POINTER_ADDRESS;

    if (
        manager == (volatile u8 *)0 ||
        practice_bootstrap_configuration.version != PRACTICE_BOOTSTRAP_VERSION
    ) {
        native_character_select_update(controller);
        return;
    }

    *(volatile u32 *)(manager + MANAGER_P1_CHARACTER_OFFSET) =
        practice_bootstrap_configuration.p1_character_id;
    *(volatile u32 *)(manager + MANAGER_P1_SUPPORT_OFFSET) =
        practice_bootstrap_configuration.p1_support_id;
    *(volatile u32 *)(manager + MANAGER_P2_CHARACTER_OFFSET) =
        FIXED_P2_CHARACTER_ID;
    *(volatile u32 *)(manager + MANAGER_P2_SUPPORT_OFFSET) =
        FIXED_P2_SUPPORT_ID;
    *(volatile u8 *)(manager + MANAGER_STAGE_OFFSET) =
        FIXED_PRACTICE_STAGE_ID;

    *(volatile u32 *)(manager + MANAGER_P1_SELECTED_CHARACTER_OFFSET) =
        practice_bootstrap_configuration.p1_character_id;
    *(volatile u32 *)(manager + MANAGER_P1_SELECTED_SUPPORT_OFFSET) =
        practice_bootstrap_configuration.p1_support_id;
    *(volatile u32 *)(manager + MANAGER_P2_SELECTED_CHARACTER_OFFSET) =
        FIXED_P2_CHARACTER_ID;
    *(volatile u32 *)(manager + MANAGER_P2_SELECTED_SUPPORT_OFFSET) =
        FIXED_P2_SUPPORT_ID;

    practice_bootstrap_state.awakening_applied = 0u;
    controller[CONTROLLER_COUNTDOWN_WORD] = PRACTICE_TRANSITION_COUNTDOWN;
    begin_transition(1u, 0u);
    controller[CONTROLLER_STATE_WORD] = PRACTICE_BATTLE_LOADING_STATE;
}

PRACTICE_BOOTSTRAP_SECTION(".text.qol_practice_bootstrap_battle")
void qol_practice_bootstrap_battle(u32 *controller)
{
    void (*native_battle_update)(u32 *) =
        (void (*)(u32 *))NATIVE_BATTLE_UPDATE_ADDRESS;
    void (*apply_effect)(void *, u32, s32, u32) =
        (void (*)(void *, u32, s32, u32))NATIVE_APPLY_EFFECT_ADDRESS;
    volatile u8 *manager;
    volatile u8 *fighter;
    u32 effect_id;

    native_battle_update(controller);

    effect_id = practice_bootstrap_configuration.awakening_effect_id;
    if (
        practice_bootstrap_state.awakening_applied != 0u ||
        effect_id == NO_AWAKENING_EFFECT
    ) {
        return;
    }

    manager = *(volatile u8 **)BATTLE_MANAGER_POINTER_ADDRESS;
    if (manager == (volatile u8 *)0) {
        return;
    }
    fighter = *(volatile u8 **)(manager + MANAGER_P1_FIGHTER_OFFSET);
    if (fighter == (volatile u8 *)0) {
        return;
    }

    apply_effect((void *)fighter, effect_id, -1, 1u);
    if (*(volatile u16 *)(fighter + FIGHTER_ACTIVE_EFFECT_OFFSET) == effect_id) {
        practice_bootstrap_state.awakening_applied = 1u;
    }
}
