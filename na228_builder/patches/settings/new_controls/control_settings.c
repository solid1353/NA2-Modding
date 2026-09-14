/* Own Control Settings action assignment without native Guard-pair coupling. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define CONTROL_SETTINGS_PLAYER_COUNT 2
#define CONTROL_SETTINGS_ACTION_COUNT 8
#define CONTROL_SETTINGS_VIBRATION_ROW 8

#define CONTROL_SETTINGS_ACTIVE_OFFSET 0x04
#define CONTROL_SETTINGS_SELECTED_ROW_OFFSET 0x0C
#define CONTROL_SETTINGS_ASSIGNMENTS_OFFSET 0x14
#define CONTROL_SETTINGS_PLAYER_ASSIGNMENTS_SIZE 0x24
#define CONTROL_SETTINGS_ORIGINAL_ACTION_OFFSET 0x5C

#define BATTLE_INPUT_HISTORY_RECORDS_OFFSET 0x94
#define BATTLE_INPUT_HISTORY_CURRENT_INDEX_OFFSET 0x9C
#define BATTLE_INPUT_HISTORY_RECORD_SIZE 0x18

#define CONTROL_SETTINGS_SECTION(name) \
    __attribute__((section(name), noinline))
#define CONTROL_SETTINGS_S32(controller, offset) \
    ((s32 *)((u8 *)(controller) + (offset)))

extern u32 mod_settings_option_get(u32 argument);

typedef s32 (*InputBindingGet)(void *input, s32 action);

static __attribute__((always_inline)) inline s32
control_settings_binding_get(void *input, s32 action)
{
    InputBindingGet get_binding = (InputBindingGet)0x006EF7F0u;
    return get_binding(input, action);
}

CONTROL_SETTINGS_SECTION(".text.control_settings_history_action")
s32 control_settings_history_action(void *input)
{
    return control_settings_binding_get(
        input,
        mod_settings_option_get(0u) != 0u ? 7 : 6
    );
}

CONTROL_SETTINGS_SECTION(".text.control_settings_substitution_held")
u32 control_settings_substitution_held(void *input)
{
    u8 *records;
    u32 current_index;
    u32 binding;
    u32 held;

    records = *(u8 **)((u8 *)input + BATTLE_INPUT_HISTORY_RECORDS_OFFSET);
    current_index = *(u32 *)(
        (u8 *)input + BATTLE_INPUT_HISTORY_CURRENT_INDEX_OFFSET
    );
    binding = (u32)control_settings_binding_get(input, 7);
    held = *(u32 *)(
        records + current_index * BATTLE_INPUT_HISTORY_RECORD_SIZE
    );
    return binding != 0u && (held & binding) == binding;
}

CONTROL_SETTINGS_SECTION(".text.control_settings_assign_action")
void control_settings_assign_action(void *controller, s32 side)
{
    s32 *assignments;
    s32 selected_row;
    s32 original_action;
    s32 selected_action;
    s32 row;

    if (controller == (void *)0 || side < 0 ||
        side >= CONTROL_SETTINGS_PLAYER_COUNT) {
        return;
    }

    *CONTROL_SETTINGS_S32(
        controller,
        CONTROL_SETTINGS_ACTIVE_OFFSET + (unsigned int)side * 4u
    ) = 1;
    selected_row = *CONTROL_SETTINGS_S32(
        controller,
        CONTROL_SETTINGS_SELECTED_ROW_OFFSET + (unsigned int)side * 4u
    );
    if (selected_row == CONTROL_SETTINGS_VIBRATION_ROW) {
        return;
    }
    original_action = *CONTROL_SETTINGS_S32(
        controller,
        CONTROL_SETTINGS_ORIGINAL_ACTION_OFFSET + (unsigned int)side * 4u
    );
    if (selected_row < 0 || selected_row >= CONTROL_SETTINGS_ACTION_COUNT ||
        original_action < 0 ||
        original_action >= CONTROL_SETTINGS_ACTION_COUNT) {
        return;
    }

    assignments = CONTROL_SETTINGS_S32(
        controller,
        CONTROL_SETTINGS_ASSIGNMENTS_OFFSET +
            (unsigned int)side * CONTROL_SETTINGS_PLAYER_ASSIGNMENTS_SIZE
    );
    selected_action = assignments[selected_row];
    if (selected_action < 0 ||
        selected_action >= CONTROL_SETTINGS_ACTION_COUNT) {
        return;
    }

    for (row = 0; row < CONTROL_SETTINGS_ACTION_COUNT; row += 1) {
        if (row != selected_row && assignments[row] == selected_action) {
            assignments[row] = original_action;
            return;
        }
    }
}
