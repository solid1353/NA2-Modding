/* Enter a configured Practice battle directly after startup. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define PRACTICE_BOOTSTRAP_SECTION(name) \
    __attribute__((section(name), noinline))

#define BATTLE_MANAGER_POINTER_ADDRESS 0x00607600u
#define AWAKENING_CONTROLLER_GATE_POINTER_ADDRESS 0x00607834u
#define AWAKENING_TRIGGER_TABLE_ADDRESS 0x005C1B50u
#define AWAKENING_EFFECT_LIST_TABLE_ADDRESS 0x005C1D30u
#define NATIVE_CHARACTER_SELECT_UPDATE_ADDRESS 0x001ED450u
#define NATIVE_BATTLE_UPDATE_ADDRESS 0x001EDB70u
#define NATIVE_BEGIN_TRANSITION_ADDRESS 0x002005B0u
#define NATIVE_ACTIVATE_AWAKENING_ADDRESS 0x0020D910u
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

#define FIGHTER_CHARACTER_ID_OFFSET 0x68u
#define FIGHTER_ACTIVE_EFFECT_OFFSET 0x8E8u
#define AWAKENING_CONTROLLER_GATE_STATE_OFFSET 0x10u
#define AWAKENING_TRIGGER_FLAGS_OFFSET 0x02u
#define AWAKENING_TRIGGER_ENTRY_SIZE 0x04u
#define AWAKENING_EFFECT_LIST_ENTRY_SIZE 0x08u
#define AWAKENING_EFFECT_LIST_COUNT_WORD 1u
#define CONDITION_DRIVEN_AWAKENING_TRIGGER_MASK 0x003Eu

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
extern u32 character_select_no_support_is_compatible(
    u32 support_id,
    u32 character_id
);

/*
 * FUN_0020E280 routes trigger bits 1 through 5 to FUN_0020D910. Bit 0
 * represents already-active or constructor-owned forms, while bit 6 uses the
 * separate class-7 Ultimate-Jutsu path through FUN_0020D690.
 */
static __attribute__((always_inline)) inline
u32 condition_driven_awakening_effect(u32 character_id)
{
    volatile u16 *trigger_flags = (volatile u16 *)(
        AWAKENING_TRIGGER_TABLE_ADDRESS +
        character_id * AWAKENING_TRIGGER_ENTRY_SIZE +
        AWAKENING_TRIGGER_FLAGS_OFFSET
    );
    volatile u32 *effect_list = (volatile u32 *)(
        AWAKENING_EFFECT_LIST_TABLE_ADDRESS +
        character_id * AWAKENING_EFFECT_LIST_ENTRY_SIZE
    );
    volatile u16 *effect_ids;
    u32 effect_count;

    if ((*trigger_flags & CONDITION_DRIVEN_AWAKENING_TRIGGER_MASK) == 0u) {
        return NO_AWAKENING_EFFECT;
    }

    effect_count = effect_list[AWAKENING_EFFECT_LIST_COUNT_WORD];
    if (effect_count == 0u) {
        return NO_AWAKENING_EFFECT;
    }
    if (effect_count == 1u) {
        return (u16)effect_list[0];
    }

    effect_ids = (volatile u16 *)effect_list[0];
    switch (character_id) {
        case 0x50u: /* Hinata */
        case 0x55u: /* Shizune */
        case 0x57u: /* Kurenai */
        case 0x5Bu: /* Yamato */
            return effect_ids[1];
        default:
            return effect_ids[0];
    }
}

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
        practice_bootstrap_configuration.version != PRACTICE_BOOTSTRAP_VERSION ||
        character_select_no_support_is_compatible(
            practice_bootstrap_configuration.p1_support_id,
            practice_bootstrap_configuration.p1_character_id
        ) == 0u
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
    void (*activate_awakening)(void *) =
        (void (*)(void *))NATIVE_ACTIVATE_AWAKENING_ADDRESS;
    void (*apply_effect)(void *, u32, s32, u32) =
        (void (*)(void *, u32, s32, u32))NATIVE_APPLY_EFFECT_ADDRESS;
    volatile u8 *manager;
    volatile u8 *fighter;
    volatile u8 *awakening_controller_gate;
    u8 awakening_controller_gate_state;
    u32 character_id;
    u32 effect_id;
    u32 native_awakening_effect_id;

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

    character_id = *(volatile u32 *)(fighter + FIGHTER_CHARACTER_ID_OFFSET);
    native_awakening_effect_id = condition_driven_awakening_effect(character_id);
    if (effect_id == native_awakening_effect_id) {
        awakening_controller_gate =
            *(volatile u8 **)AWAKENING_CONTROLLER_GATE_POINTER_ADDRESS;
        if (awakening_controller_gate != (volatile u8 *)0) {
            awakening_controller_gate_state = awakening_controller_gate[
                AWAKENING_CONTROLLER_GATE_STATE_OFFSET
            ];
            if (
                awakening_controller_gate_state != 0u &&
                awakening_controller_gate_state != 0xFFu
            ) {
                return;
            }
        }
        activate_awakening((void *)fighter);
    } else {
        apply_effect((void *)fighter, effect_id, -1, 1u);
    }
    if (*(volatile u16 *)(fighter + FIGHTER_ACTIVE_EFFECT_OFFSET) == effect_id) {
        practice_bootstrap_state.awakening_applied = 1u;
    }
}
