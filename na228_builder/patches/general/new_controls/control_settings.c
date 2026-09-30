/* Extended Control Settings actions and their battle bindings. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef signed int s32;
typedef unsigned int u32;

#define SECTION(name) __attribute__((section(name), noinline))
#define FIELD(object, offset) ((s32 *)((u8 *)(object) + (offset)))
#define NATIVE_ACTIONS 8
#define GUARD 8
#define SUBSTITUTION 9
#define ITEM_SELECT_L 10
#define ITEM_SELECT_R 11
#define UNBOUND 12
#define ACTIONS 13
#define EXTRA_BINDINGS 8
#define NATIVE_ITEM_SELECT_BIT 0x02000000u
#define REVERSE_ITEM_SELECT_BIT 0x04000000u
#define SIDES 2

typedef s16 *(*BindingsGet)(u32);
typedef u32 (*VibrationGet)(u32);
typedef void (*BindingsSet)(u32, const u16 *);
typedef void (*VibrationSet)(u32, u32);
typedef s32 (*HistoryMatch)(void *, u32, u32, u32, u32, u32, s32);
typedef void (*HelpQueue)(float, void *, const u8 *, s32, s32);
typedef s32 (*PanelStep)(void *, s32);
typedef u32 (*PanelQuery)(void *);
typedef void (*SoundPlay)(u32);

extern const u8 mod_text_settings__substitution__label[];
extern const u8 mod_text_controls__guard_sub_1__label[];
extern const u8 mod_text_controls__guard_sub_2__label[];
extern const u8 mod_text_controls__item_select_l__label[];
extern const u8 mod_text_controls__item_select_r__label[];
extern const u8 mod_text_controls__unbound__label[];
/* Substitution Input getter, or null when that setting is not built. */
extern u32 (*const control_settings_substitution_input_get)(void);
#define SUBSTITUTION_INPUT_HOLD 1u

const u8 *control_settings_labels[ACTIONS]
    __attribute__((section(".data.control_settings_labels"))) = {
        (const u8 *)0x005B2540u, (const u8 *)0x00604638u,
        (const u8 *)0x005B2550u, (const u8 *)0x005B2560u,
        (const u8 *)0x005B2570u, (const u8 *)0x005B2580u,
        mod_text_controls__guard_sub_1__label,
        mod_text_controls__guard_sub_2__label,
        (const u8 *)0x00604640u, mod_text_settings__substitution__label,
        mod_text_controls__item_select_l__label,
        mod_text_controls__item_select_r__label,
        mod_text_controls__unbound__label,
    };

/* Guard, Substitution, Item Select L, and Item Select R for P1, then P2; the
   builder initializes them from resources/default_controls.tsv. */
extern volatile u16 control_settings_extra_bindings[EXTRA_BINDINGS];
/* Item Select R badge press animation per side, kept apart from the native badge's. */
typedef struct ItemBadgeState {
    float scale[SIDES];
    u8 pressed[SIDES];
} ItemBadgeState;

volatile ItemBadgeState control_settings_item_badge_state
    __attribute__((section(".data.control_settings_item_badge_state"))) = {
        {1.0f, 1.0f}, {0u, 0u},
    };

static const u16 physical_masks[8] = {
    0x20u, 0x10u, 0x80u, 0x40u, 0x04u, 0x08u, 0x01u, 0x02u,
};
static const u16 shoulder_masks[5] = {0u, 0x01u, 0x02u, 0x04u, 0x08u};
/* Selector orders: Unbound, then Attack, Ultimate Jutsu Prep, Item Use, and Jump
   as the rows appear, or Substitution, Guard, Item Select L, Item Select R, and
   Linked Attack. */
static const s32 face_order[5] = {UNBOUND, 1, 0, 3, 2};
static const s32 shoulder_order[6] = {UNBOUND, SUBSTITUTION, GUARD, ITEM_SELECT_L, ITEM_SELECT_R, 5};

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

static SECTION(".text.control_settings_helpers") u32 extra_index(u32 side, u32 action)
{
    return side * 4u + action - GUARD;
}

SECTION(".text.control_settings_extra_get")
u32 control_settings_extra_get(u32 argument)
{
    u32 index;
    if (argument >= EXTRA_BINDINGS) return 0u;
    for (index = 0u; index < 5u; ++index) {
        if (control_settings_extra_bindings[argument] == shoulder_masks[index])
            return index;
    }
    return 0u;
}

SECTION(".text.control_settings_extra_set")
void control_settings_extra_set(u32 argument, u32 value)
{
    if (argument < EXTRA_BINDINGS && value < 5u)
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
    u32 substitution = control_settings_extra_bindings[extra_index(side, SUBSTITUTION)];
    return history_match(input, first, frames) ||
        history_match(input, second, frames) ||
        history_match(input, substitution, frames);
}

/*
 * Accept the added Substitution button before the held-Guard age limit: a held
 * button with Substitution Input set to Hold, otherwise a fresh press in the window.
 */
SECTION(".text.control_settings_substitution_accepted")
u32 control_settings_substitution_accepted(void *input, u32 frames)
{
    u8 *records = *(u8 **)((u8 *)input + 0x94u);
    u32 index = *(u32 *)((u8 *)input + 0x9cu);
    u32 held = *(u32 *)(records + index * 0x18u);
    u32 side = input_side(input);
    u32 substitution = control_settings_extra_bindings[extra_index(side, SUBSTITUTION)];
    if (substitution == 0u) return 0u;
    if (
        control_settings_substitution_input_get != (u32 (*)(void))0 &&
        control_settings_substitution_input_get() == SUBSTITUTION_INPUT_HOLD
    ) {
        return (held & substitution) == substitution;
    }
    return history_match(input, substitution, frames);
}

SECTION(".text.control_settings_guard_pressed")
u32 control_settings_guard_pressed(void *input, u32 held)
{
    u32 side = input_side(input);
    u32 second = (u16)*(s16 *)((u8 *)input + 0x76u);
    u32 guard = control_settings_extra_bindings[extra_index(side, GUARD)];
    return (second != 0u && (held & second) != 0u) ||
        (guard != 0u && (held & guard) != 0u);
}

/* Step a row through its fixed action order; Left goes back, Right forward. */
SECTION(".text.control_settings_action_step")
void control_settings_action_step(void *controller, u32 side, u32 row, u32 pressed)
{
    const s32 *order = row < 4u ? face_order : shoulder_order;
    u32 count = row < 4u ? 5u : 6u;
    s32 *value;
    u32 index;
    if (controller == (void *)0 || side >= SIDES || row >= NATIVE_ACTIONS) return;
    value = FIELD(controller, 0x14u + side * 0x24u + row * 4u);
    for (index = 0u; index < count && order[index] != *value; ++index) {}
    if (index == count) index = 0u;
    else if ((pressed & 0x8000u) != 0u) index = index == 0u ? count - 1u : index - 1u;
    else if ((pressed & 0x2000u) != 0u) index = index == count - 1u ? 0u : index + 1u;
    *value = order[index];
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
        rows[row] = UNBOUND;
        for (action = 0; action < NATIVE_ACTIONS; ++action) {
            if ((u16)native[action] == physical_masks[row]) {
                rows[row] = action;
                break;
            }
        }
        if (action == NATIVE_ACTIONS) {
            for (action = NATIVE_ACTIONS; action < UNBOUND; ++action) {
                if (control_settings_extra_bindings[extra_index((u32)side, (u32)action)] ==
                    physical_masks[row]) {
                    rows[row] = action;
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
    u16 extra[EXTRA_BINDINGS];
    u32 side, row, action, seen;
    if (controller == (void *)0) return;
    for (row = 0u; row < EXTRA_BINDINGS; ++row) extra[row] = 0u;
    for (side = 0u; side < SIDES; ++side) {
        s32 *rows = FIELD(controller, 0x14u + side * 0x24u);
        seen = 0u;
        for (action = 0u; action < NATIVE_ACTIONS; ++action)
            native[side][action] = 0u;
        for (row = 0u; row < NATIVE_ACTIONS; ++row) {
            action = (u32)rows[row];
            if (action == UNBOUND) continue;
            if (action >= UNBOUND || (seen & (1u << action)) != 0u) return;
            seen |= 1u << action;
            if (action < NATIVE_ACTIONS)
                native[side][action] = physical_masks[row];
            else
                extra[extra_index(side, action)] = physical_masks[row];
        }
    }
    if (*(void **)0x00607600u == (void *)0) return;
    for (row = 0u; row < EXTRA_BINDINGS; ++row)
        control_settings_extra_bindings[row] = extra[row];
    for (side = 0u; side < SIDES; ++side) {
        ((BindingsSet)0x001F3DC0u)(side + 1u, native[side]);
        ((VibrationSet)0x001F4120u)(side + 1u,
            *FIELD(controller, 0x34u + side * 0x24u) != 0);
    }
}

SECTION(".text.control_settings_assign_action")
void control_settings_assign_action(void *controller, s32 side)
{
    s32 *rows, selected, chosen, row;
    if (controller == (void *)0 || side < 0 || side >= SIDES) return;
    *FIELD(controller, 0x04u + (u32)side * 4u) = 1;
    selected = *FIELD(controller, 0x0cu + (u32)side * 4u);
    if (selected < 0 || selected >= NATIVE_ACTIONS) return;
    rows = FIELD(controller, 0x14u + (u32)side * 0x24u);
    chosen = rows[selected];
    if (chosen < 0 || chosen >= UNBOUND) return;
    /* The button that held the chosen action becomes Unbound. */
    for (row = 0; row < NATIVE_ACTIONS; ++row) {
        if (row != selected && rows[row] == chosen) {
            rows[row] = UNBOUND;
            return;
        }
    }
}

/* Item Select L and R use the pressed-button mask, like the native Item Select. */
SECTION(".text.control_settings_item_select_bits")
u32 control_settings_item_select_bits(void *input, u32 pressed)
{
    u32 side = input_side(input);
    u32 left = control_settings_extra_bindings[extra_index(side, ITEM_SELECT_L)];
    u32 right = control_settings_extra_bindings[extra_index(side, ITEM_SELECT_R)];
    u32 bits = 0u;
    if (left != 0u && (pressed & left) != 0u) bits |= NATIVE_ITEM_SELECT_BIT;
    if (right != 0u && (pressed & right) != 0u) bits |= REVERSE_ITEM_SELECT_BIT;
    return bits;
}

/* Step the selection backward with the same gates, animation, and sound as advance. */
SECTION(".text.control_settings_item_select_reverse")
u32 control_settings_item_select_reverse(void *manager, u32 side)
{
    void *panel;
    if (side == 0u) panel = *(void **)((u8 *)manager + 0x6Cu);
    else if (side == 1u) panel = *(void **)((u8 *)manager + 0x70u);
    else return 0xFFFFFFFFu;
    if (((PanelQuery)0x00711AA0u)(panel) != 0u) return 0u;
    if (((PanelQuery)0x00711AC0u)(panel) == 0u) return 0u;
    control_settings_item_badge_state.pressed[side] = 1u;
    *(float *)((u8 *)panel + 0x28u) -= 1.0f;
    *(s32 *)((u8 *)panel + 0x24u) = ((PanelStep)0x007106D0u)(panel, -1);
    ((SoundPlay)0x001D7E20u)(42u);
    return 1u;
}

typedef void (*SpriteDraw)(float, float, float, u32, void *);
typedef void (*PanelDraw)(void *);
typedef u32 (*BindingSprite)(u32, u32);

typedef struct BadgeVector {
    float x, y, z, w;
} __attribute__((aligned(16))) BadgeVector;

/* Map a binding through the native (button mask, sprite) table; unbound gives none. */
static SECTION(".text.control_settings_helpers") u32 badge_sprite(u32 binding)
{
    const u32 *badges = (const u32 *)0x005B00B0u;
    u32 index;
    for (index = 0u; binding != 0u && index < 6u; ++index)
        if (badges[index * 2u] == binding) return badges[index * 2u + 1u];
    return 0xFFFFFFFFu;
}

/* Draw both item-select badges for the panel's own side, skipping unbound actions, then the wheel. */
SECTION(".text.control_settings_item_badges")
void control_settings_item_badges(void *panel)
{
    u8 *badge = *(u8 **)((u8 *)panel + 0x10u);
    const BadgeVector *offset = (const BadgeVector *)(badge + 0x10u);
    const BadgeVector *origin = (const BadgeVector *)((u8 *)panel + 0x50u);
    u32 side = *(u32 *)((u8 *)panel + 0x20u) < SIDES ? *(u32 *)((u8 *)panel + 0x20u) : 0u;
    /* As in NUN4, both badges turn translucent while fewer than two items are held. */
    float alpha = ((PanelQuery)0x00711AC0u)(panel) != 0u ? 1.0f : 0.2f;
    u32 sprite;
    BadgeVector at;
    float scale = control_settings_item_badge_state.scale[side];
    /* Retail reads the side from badge +0, which stays 0 for both panels. Byte +0x28
       selects Item Select, now the owned Item Select L binding, over Linked Attack. */
    sprite = badge[0x28u] != 0u
        ? badge_sprite(control_settings_extra_bindings[extra_index(side, ITEM_SELECT_L)])
        : ((BindingSprite)0x00376F10u)(side, 5u);
    if (sprite != 0xFFFFFFFFu) {
        at.x = origin->x + offset->x;
        at.y = origin->y + offset->y;
        at.z = origin->z + offset->z;
        at.w = origin->w + offset->w;
        ((SpriteDraw)0x00377750u)(1.0f, alpha, 0.0f, 123u, &at);
        ((SpriteDraw)0x00377750u)(*(float *)(badge + 0x20u), alpha, 0.0f, sprite, &at);
    }
    /* Same shrink and recovery as the native badge: 0.1 per frame between 0.8 and 1.0. */
    scale += control_settings_item_badge_state.pressed[side] != 0u ? -0.1f : 0.1f;
    if (scale > 1.0f) scale = 1.0f;
    else if (scale < 0.8f) scale = 0.8f;
    control_settings_item_badge_state.scale[side] = scale;
    control_settings_item_badge_state.pressed[side] = 0u;
    sprite = badge_sprite(control_settings_extra_bindings[extra_index(side, ITEM_SELECT_R)]);
    if (sprite != 0xFFFFFFFFu) {
        at.x = origin->x - offset->x;
        at.y = origin->y + offset->y;
        at.z = origin->z + offset->z;
        at.w = origin->w + offset->w;
        ((SpriteDraw)0x00377750u)(1.0f, alpha, 0.0f, 123u, &at);
        ((SpriteDraw)0x00377750u)(scale, alpha, 0.0f, sprite, &at);
    }
    ((PanelDraw)0x00711E50u)(panel);
}
