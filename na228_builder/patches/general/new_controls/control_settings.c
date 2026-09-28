/* Extended Control Settings actions and their battle bindings. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef signed int s32;
typedef unsigned int u32;

#define SECTION(name) __attribute__((section(name), noinline))
#define FIELD(object, offset) ((s32 *)((u8 *)(object) + (offset)))
#define NATIVE_ACTIONS 8
#define ACTIONS 10
#define SIDES 2

typedef s16 *(*BindingsGet)(u32);
typedef u32 (*VibrationGet)(u32);
typedef void (*BindingsSet)(u32, const u16 *);
typedef void (*VibrationSet)(u32, u32);
typedef s32 (*HistoryMatch)(void *, u32, u32, u32, u32, u32, s32);
typedef void (*HelpQueue)(float, void *, const u8 *, s32, s32);

extern const u8 mod_text_settings__substitution__label[];
extern const u8 mod_text_controls__guard_sub_1__label[];
extern const u8 mod_text_controls__guard_sub_2__label[];

const u8 *control_settings_labels[ACTIONS]
    __attribute__((section(".data.control_settings_labels"))) = {
        (const u8 *)0x005B2540u, (const u8 *)0x00604638u,
        (const u8 *)0x005B2550u, (const u8 *)0x005B2560u,
        (const u8 *)0x005B2570u, (const u8 *)0x005B2580u,
        mod_text_controls__guard_sub_1__label,
        mod_text_controls__guard_sub_2__label,
        (const u8 *)0x00604640u, mod_text_settings__substitution__label,
    };

/* P1 Guard/Substitution, then P2 Guard/Substitution. */
volatile u16 control_settings_extra_bindings[4]
    __attribute__((section(".data.control_settings_extra_bindings"))) = {
        0x08u, 0x04u, 0x08u, 0x04u,
    };
static const u16 physical_masks[8] = {
    0x20u, 0x10u, 0x80u, 0x40u, 0x04u, 0x08u, 0x01u, 0x02u,
};
static const u16 shoulder_masks[5] = {0u, 0x01u, 0x02u, 0x04u, 0x08u};
static const s32 reset_actions[8] = {1, 0, 3, 2, 9, 8, 4, 5};

SECTION(".text.control_settings_reset_with_help")
void control_settings_reset_with_help(void *controls)
{
    void *help = *(void **)((u8 *)controls + 0x90u);
    const u8 *message = *(const u8 **)0x005B2520u;

    *(u32 *)controls = 0u;
    ((HelpQueue)0x0037F760u)(20.0f, help, message, 8, 0);
}

static SECTION(".text.control_settings_helpers") u32 input_side(void *input)
{
    u32 side = *(u32 *)((u8 *)input + 0x60u);
    return side < SIDES ? side : 0u;
}

SECTION(".text.control_settings_extra_get")
u32 control_settings_extra_get(u32 argument)
{
    u32 index;
    if (argument >= 4u) return 0u;
    for (index = 0u; index < 5u; ++index) {
        if (control_settings_extra_bindings[argument] == shoulder_masks[index])
            return index;
    }
    return 0u;
}

SECTION(".text.control_settings_extra_set")
void control_settings_extra_set(u32 argument, u32 value)
{
    if (argument < 4u && value < 5u)
        control_settings_extra_bindings[argument] = shoulder_masks[value];
}

/* A zero native binding must never satisfy the subset-based history matcher. */
SECTION(".text.control_settings_binding_nonzero")
u32 control_settings_binding_nonzero(void *input, s32 action)
{
    u32 binding;
    if (action < 0 || action >= NATIVE_ACTIONS) return 0x10000u;
    binding = (u16)*(s16 *)((u8 *)input + 0x68u + (u32)action * 2u);
    return binding != 0u ? binding : 0x10000u;
}

static SECTION(".text.control_settings_helpers") s32 history_match(void *input, u32 binding, u32 frames)
{
    return binding != 0u &&
        ((HistoryMatch)0x006EFAC0u)(input, binding, 1u, frames, 0u, 0u, -1);
}

SECTION(".text.control_settings_history_any")
s32 control_settings_history_any(void *input, u32 frames)
{
    u32 side = input_side(input);
    u32 first = (u16)*(s16 *)((u8 *)input + 0x74u);
    u32 second = (u16)*(s16 *)((u8 *)input + 0x76u);
    u32 substitution = control_settings_extra_bindings[side * 2u + 1u];
    return history_match(input, first, frames) ||
        history_match(input, second, frames) ||
        history_match(input, substitution, frames);
}

SECTION(".text.control_settings_substitution_held")
u32 control_settings_substitution_held(void *input)
{
    u8 *records = *(u8 **)((u8 *)input + 0x94u);
    u32 index = *(u32 *)((u8 *)input + 0x9cu);
    u32 held = *(u32 *)(records + index * 0x18u);
    u32 side = input_side(input);
    u32 substitution = control_settings_extra_bindings[side * 2u + 1u];
    return substitution != 0u && (held & substitution) == substitution;
}

SECTION(".text.control_settings_guard_pressed")
u32 control_settings_guard_pressed(void *input, u32 held)
{
    u32 side = input_side(input);
    u32 second = (u16)*(s16 *)((u8 *)input + 0x76u);
    u32 guard = control_settings_extra_bindings[side * 2u];
    return (second != 0u && (held & second) != 0u) ||
        (guard != 0u && (held & guard) != 0u);
}

SECTION(".text.control_settings_open")
void control_settings_open(void *controller, s32 side)
{
    s16 *native;
    s32 *rows;
    s32 row;
    s32 action;
    if (controller == (void *)0 || side < 0 || side >= SIDES) return;
    control_settings_labels[0] = *(const u8 **)0x005B2590u;
    native = ((BindingsGet)0x001F3F10u)((u32)side + 1u);
    rows = FIELD(controller, 0x14u + (u32)side * 0x24u);
    for (row = 0; row < NATIVE_ACTIONS; ++row) {
        rows[row] = reset_actions[row];
        for (action = 0; action < NATIVE_ACTIONS; ++action) {
            if ((u16)native[action] == physical_masks[row]) {
                rows[row] = action;
                break;
            }
        }
        if (action == NATIVE_ACTIONS) {
            for (action = 0; action < 2; ++action) {
                if (control_settings_extra_bindings[side * 2 + action] ==
                    physical_masks[row]) {
                    rows[row] = NATIVE_ACTIONS + action;
                    break;
                }
            }
        }
    }
    *FIELD(controller, 0x34u + (u32)side * 0x24u) =
        ((VibrationGet)0x001F41A0u)((u32)side + 1u) & 0xffu;
}

SECTION(".text.control_settings_commit")
void control_settings_commit(void *controller)
{
    u16 native[SIDES][NATIVE_ACTIONS];
    u16 extra[4] = {0u, 0u, 0u, 0u};
    u32 side, row, action, seen;
    if (controller == (void *)0) return;
    for (side = 0u; side < SIDES; ++side) {
        s32 *rows = FIELD(controller, 0x14u + side * 0x24u);
        seen = 0u;
        for (action = 0u; action < NATIVE_ACTIONS; ++action)
            native[side][action] = 0u;
        for (row = 0u; row < NATIVE_ACTIONS; ++row) {
            action = (u32)rows[row];
            if (action >= ACTIONS || (seen & (1u << action)) != 0u) return;
            seen |= 1u << action;
            if (action < NATIVE_ACTIONS)
                native[side][action] = physical_masks[row];
            else
                extra[side * 2u + action - NATIVE_ACTIONS] = physical_masks[row];
        }
    }
    if (*(void **)0x00607600u == (void *)0) return;
    for (side = 0u; side < SIDES; ++side) {
        control_settings_extra_bindings[side * 2u] = extra[side * 2u];
        control_settings_extra_bindings[side * 2u + 1u] = extra[side * 2u + 1u];
        ((BindingsSet)0x001F3DC0u)(side + 1u, native[side]);
        ((VibrationSet)0x001F4120u)(side + 1u,
            *FIELD(controller, 0x34u + side * 0x24u) != 0);
    }
}

SECTION(".text.control_settings_assign_action")
void control_settings_assign_action(void *controller, s32 side)
{
    s32 *rows, selected, original, chosen, row;
    if (controller == (void *)0 || side < 0 || side >= SIDES) return;
    *FIELD(controller, 0x04u + (u32)side * 4u) = 1;
    selected = *FIELD(controller, 0x0cu + (u32)side * 4u);
    if (selected == 8) return;
    original = *FIELD(controller, 0x5cu + (u32)side * 4u);
    if (selected < 0 || selected >= NATIVE_ACTIONS ||
        original < 0 || original >= ACTIONS) return;
    rows = FIELD(controller, 0x14u + (u32)side * 0x24u);
    chosen = rows[selected];
    if (chosen < 0 || chosen >= ACTIONS) return;
    for (row = 0; row < NATIVE_ACTIONS; ++row) {
        if (row != selected && rows[row] == chosen) {
            rows[row] = original;
            return;
        }
    }
}
