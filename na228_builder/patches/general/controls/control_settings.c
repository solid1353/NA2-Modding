/* Extended Control Settings actions and their battle bindings. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef signed int s32;
typedef unsigned int u32;
typedef unsigned long long u64;

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
typedef void (*Rumble)(void *, u32, u32, u32);
typedef void (*RectDraw)(float, float, void *, const void *);
typedef void (*TextDraw)(float, float, const u8 *, s32);
typedef void (*CursorDraw)(float, float, void *);
typedef void (*RowFrameDraw)(void *, s32, s32);
typedef void (*HelpSet)(float, void *, const u8 *, s32, s32);
typedef void (*SpriteSubmit)(void *, u32, u32);
typedef float (*Sine)(float);
typedef void *(*ArchiveFind)(const u8 *);
typedef void *(*ObjectFind)(void *, const u8 *, u32);
typedef void (*ObjectCall)(void *);
typedef s32 (*PanelStep)(void *, s32);
typedef u32 (*PanelQuery)(void *);
typedef void (*SoundPlay)(u32);

extern const u8 mod_text_settings__substitution__label[];
extern const u8 mod_text_controls__guard_sub_1__label[];
extern const u8 mod_text_controls__guard_sub_2__label[];
extern const u8 mod_text_controls__item_select_l__label[];
extern const u8 mod_text_controls__item_select_r__label[];
extern const u8 mod_text_controls__unbound__label[];
extern u32 substitution_input_get(void);
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
   builder initializes them from the controls setting's layout. */
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

/* Control Settings rows in display order: Circle, Triangle, Square, Cross, Select,
   L1, R1, L2, R2, L3, R3, then vibration. The native child stores eight button rows
   and vibration; L3, R3, and Select live here. The nine native slots scroll over
   all twelve rows. */
#define NATIVE_ROWS 8u
#define EXTRA_ROWS 3u
#define ACTION_ROWS 11u
#define VIBRATION_ROW 11u
#define ROWS 12u
#define VISIBLE_ROWS 9
#define ROW_PITCH 26.8f
/* Text color scales the white glyphs by color / 128: 0x48 is a mid grey. */
#define UNBOUND_LABEL_COLOR 0xFF484848u
#define LABEL_Y 48.0f
#define CELL_Y 57.0f
#define CELL_X 256.0f
/* First button row in the top slot, shared by both panels and their center icons. */
s32 control_settings_scroll __attribute__((section(".data.control_settings_scroll"))) = 0;
static const u16 row_masks[ACTION_ROWS] = {
    0x20u, 0x10u, 0x80u, 0x40u, 0x100u, 0x04u, 0x08u, 0x01u, 0x02u, 0x200u, 0x400u,
};
/* Storage of each button row: the native rows 0..7, then L3, R3, and Select. */
static const u8 row_storage[ACTION_ROWS] = {0u, 1u, 2u, 3u, 10u, 4u, 5u, 6u, 7u, 8u, 9u};
s32 control_settings_extra_rows[SIDES][EXTRA_ROWS]
    __attribute__((section(".data.control_settings_extra_rows"))) = {
        {UNBOUND, UNBOUND, UNBOUND}, {UNBOUND, UNBOUND, UNBOUND},
    };
/* Generated defaults for the Select reset: every row, then vibration. */
extern const s32 control_default_reset_actions[ROWS];
/* Action-label draw: the localized boxed-label adapter, or the native text draw. */
extern void (*const control_settings_label_draw)(float, float, const u8 *, s32);
/* Running-help setter: the localized one, or the native setter. */
extern const HelpSet control_settings_help_set;
/* L3, R3, and Select cells, 30x16 TEX_xcommand02 palette indices each, top row first. */
extern const u8 control_settings_button_icons[3][16][30];
/* Saved button choices for the added actions; matches save_appendix.tsv. */
#define SAVED_BUTTONS 12u
static const u16 saved_button_masks[SAVED_BUTTONS] = {
    0u, 0x01u, 0x02u, 0x04u, 0x08u, 0x10u, 0x20u, 0x40u, 0x80u, 0x100u, 0x200u, 0x400u,
};
/* Selector order for every row: Unbound, Attack, Ultimate Jutsu Prep, Item Use,
   Jump, Substitution, Guard, Item Select L, Item Select R, and Linked Attack. */
#define ACTION_ORDER_COUNT 10u
static const s32 action_order[ACTION_ORDER_COUNT] = {
    UNBOUND, 1, 0, 3, 2, SUBSTITUTION, GUARD, ITEM_SELECT_L, ITEM_SELECT_R, 5,
};
/* Free texels of TEX_xcommand02 below the L1, R1, L2, and R2 cells. */
static const s16 shoulder3_rects[2][4] = {{1, 42, 30, 16}, {33, 42, 30, 16}};
/* Free texels of TEX_xmenu, right of the player chevrons, for the Select cell. */
static const s16 select_rect[4] = {224, 28, 30, 16};
static const u8 gauge_archive_name[] = "gauge";
static const u8 face_texture_name[] = "TEX_xcommand";
static const u8 shoulder_texture_name[] = "TEX_xcommand02";
static const u8 menu_texture_name[] = "TEX_xmenu";
/* Red TEX_xmenu chevron, tinted orange and drawn at half size as the scroll indicators. */
static const s16 scroll_arrow_rect[4] = {130, 29, 20, 22};
#define ARROW_WIDTH 10.0f
#define ARROW_HEIGHT 11.0f
#define ARROW_X 27.0f
/* Accept and back buttons, read from the native checks that regional input rewrites. */
#define NAVIGATE_ACCEPT (*(const u16 *)0x00387E44u)
#define NAVIGATE_BACK (*(const u16 *)0x00387EC8u)
#define EDIT_ACCEPT (*(const u16 *)0x00388230u)
#define EDIT_CANCEL (*(const u16 *)0x00388260u)
#define HELP_MESSAGES ((const u8 *const *)0x005B2520u)

static SECTION(".text.control_settings_helpers") s32 *row_slot(void *controller, u32 side, u32 row)
{
    u32 storage;
    if (row >= ACTION_ROWS) return FIELD(controller, 0x34u + side * 0x24u);
    storage = row_storage[row];
    if (storage < NATIVE_ROWS) return FIELD(controller, 0x14u + side * 0x24u + storage * 4u);
    return &control_settings_extra_rows[side][storage - NATIVE_ROWS];
}

/* A button row's icon texture (0 face, 1 shoulder, 2 menu) and rectangle. */
static SECTION(".text.control_settings_helpers") u32 row_icon(u32 row, const s16 **rect)
{
    const s16 *rects = (const s16 *)0x005D5280u;
    u32 storage = row_storage[row];
    if (storage < 4u) {
        *rect = rects + storage * 4u;
        return 0u;
    }
    if (storage < NATIVE_ROWS) {
        *rect = rects + storage * 4u;
        return 1u;
    }
    if (storage < NATIVE_ROWS + 2u) {
        *rect = shoulder3_rects[storage - NATIVE_ROWS];
        return 1u;
    }
    *rect = select_rect;
    return 2u;
}


static SECTION(".text.control_settings_helpers") void show_help(void *controller, const u8 *message)
{
    void *help = *(void **)((u8 *)controller + 0x90u);
    ((ObjectCall)0x0037EEE0u)(help);
    control_settings_help_set(20.0f, help, message, 8, 0);
}

static SECTION(".text.control_settings_helpers") u8 *pad_state(s32 side)
{
    return *(u8 **)0x006073FCu + (u32)side * 0x78u;
}

static SECTION(".text.control_settings_helpers") void play_sound(u32 sound)
{
    ((SoundPlay)0x001D7E20u)(sound);
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
    for (index = 0u; index < SAVED_BUTTONS; ++index) {
        if (control_settings_extra_bindings[argument] == saved_button_masks[index])
            return index;
    }
    return 0u;
}

SECTION(".text.control_settings_extra_set")
void control_settings_extra_set(u32 argument, u32 value)
{
    if (argument < EXTRA_BINDINGS && value < SAVED_BUTTONS)
        control_settings_extra_bindings[argument] = saved_button_masks[value];
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
    if (substitution_input_get() == SUBSTITUTION_INPUT_HOLD) {
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

/* Step a row through the action order; Left goes back, Right forward. */
SECTION(".text.control_settings_action_step")
void control_settings_action_step(void *controller, u32 side, u32 row, u32 pressed)
{
    const s32 *order = action_order;
    u32 count = ACTION_ORDER_COUNT;
    s32 *value;
    u32 index;
    if (controller == (void *)0 || side >= SIDES || row >= ACTION_ROWS) return;
    value = row_slot(controller, side, row);
    for (index = 0u; index < count && order[index] != *value; ++index) {}
    if (index == count) index = 0u;
    else if ((pressed & 0x8000u) != 0u) index = index == 0u ? count - 1u : index - 1u;
    else if ((pressed & 0x2000u) != 0u) index = index == count - 1u ? 0u : index + 1u;
    *value = order[index];
}

/* Pixels of a texture with the given size, or null. Rows are stored bottom-up. */
static SECTION(".text.control_settings_helpers") u8 *texture_pixels(
    void *archive, const u8 *name, u32 width_log2, u32 height_log2, u32 bytes)
{
    u8 *texture = ((ObjectFind)0x001A8F00u)(archive, name, 1u);
    u8 *mipmap;
    if (texture == (u8 *)0 || texture[0x36u] != width_log2 || texture[0x37u] != height_log2) return (u8 *)0;
    mipmap = *(u8 **)(texture + 0x28u);
    if (mipmap == (u8 *)0 || *(u32 *)(mipmap + 0x08u) * 16u < bytes) return (u8 *)0;
    return *(u8 **)(mipmap + 0x04u);
}

/* A texture's palette: 16 or 256 RGBA entries, the 256-entry ones in GS storage order. */
static SECTION(".text.control_settings_helpers") const u8 *texture_palette(void *archive, const u8 *name)
{
    u8 *texture = ((ObjectFind)0x001A8F00u)(archive, name, 1u);
    u8 *palette;
    if (texture == (u8 *)0 || (palette = *(u8 **)(texture + 0x3cu)) == (u8 *)0) return (const u8 *)0;
    palette = *(u8 **)(palette + 0x10u);
    return palette == (u8 *)0 ? (const u8 *)0 : *(const u8 **)(palette + 0x04u);
}

/* The 256-entry palette index whose RGBA is closest to a color. */
static SECTION(".text.control_settings_helpers") u8 closest_entry(const u8 *palette, const u8 *color)
{
    u32 best = 0xFFFFFFFFu, entry;
    u8 closest = 0u;
    for (entry = 0u; entry < 256u; ++entry) {
        /* The 256-entry palette swaps bits 3 and 4 of the index in storage. */
        const u8 *candidate = palette +
            ((entry & 0xE7u) | ((entry & 0x08u) << 1) | ((entry & 0x10u) >> 1)) * 4u;
        u32 distance = 0u, channel;
        for (channel = 0u; channel < 4u; ++channel) {
            s32 delta = (s32)candidate[channel] - (s32)color[channel];
            distance += (u32)(delta * delta);
        }
        if (distance < best) {
            best = distance;
            closest = (u8)entry;
        }
    }
    return closest;
}

/* Write the L3 and R3 cells into the free rows of the shoulder texture, and the Select
   cell into free TEX_xmenu texels, mapped to that texture's closest palette entries. */
static SECTION(".text.control_settings_helpers") void install_button_icons(void *archive)
{
    u8 *pixels = texture_pixels(archive, shoulder_texture_name, 6u, 6u, 64u * 64u / 2u);
    u8 *menu = texture_pixels(archive, menu_texture_name, 8u, 7u, 256u * 128u);
    const u8 *source = texture_palette(archive, shoulder_texture_name);
    const u8 *target = texture_palette(archive, menu_texture_name);
    u8 map[16];
    u32 icon, x, y, color;
    if (pixels != (u8 *)0) {
        for (icon = 0u; icon < 2u; ++icon) {
            for (y = 0u; y < 16u; ++y) {
                /* PSMT4 stores two texels per byte, low nibble first. */
                u32 row = 63u - ((u32)shoulder3_rects[icon][1] + y);
                for (x = 0u; x < 30u; ++x) {
                    u32 texel = row * 64u + (u32)shoulder3_rects[icon][0] + x;
                    u8 *byte = pixels + texel / 2u;
                    u8 index = control_settings_button_icons[icon][y][x] & 0x0Fu;
                    *byte = (texel & 1u) != 0u
                        ? (u8)((*byte & 0x0Fu) | (index << 4))
                        : (u8)((*byte & 0xF0u) | index);
                }
            }
        }
    }
    if (menu != (u8 *)0 && source != (const u8 *)0 && target != (const u8 *)0) {
        for (color = 0u; color < 16u; ++color) map[color] = closest_entry(target, source + color * 4u);
        for (y = 0u; y < 16u; ++y)
            for (x = 0u; x < 30u; ++x)
                menu[(127u - ((u32)select_rect[1] + y)) * 256u + (u32)select_rect[0] + x] =
                    map[control_settings_button_icons[2][y][x] & 0x0Fu];
    }
    /* The sprites upload texels from memory, so write the data cache back. */
    ((ObjectCall)0x0015DF60u)((void *)0);
}

SECTION(".text.control_settings_open")
void control_settings_open(void *controller, s32 side)
{
    s16 *native;
    u32 row;
    s32 action;
    if (controller == (void *)0 || side < 0 || side >= SIDES) return;
    control_settings_labels[0] = *(const u8 **)0x005B2590u;
    if (side == 0) {
        void *archive = ((ArchiveFind)0x001AA4B0u)(gauge_archive_name);
        control_settings_scroll = 0;
        if (archive != (void *)0) install_button_icons(archive);
    }
    native = ((BindingsGet)0x001F3F10u)((u32)side + 1u);
    for (row = 0u; row < ACTION_ROWS; ++row) {
        s32 *slot = row_slot(controller, (u32)side, row);
        *slot = UNBOUND;
        for (action = 0; action < NATIVE_ACTIONS; ++action) {
            if ((u16)native[action] == row_masks[row]) {
                *slot = action;
                break;
            }
        }
        if (action == NATIVE_ACTIONS) {
            for (action = NATIVE_ACTIONS; action < UNBOUND; ++action) {
                if (control_settings_extra_bindings[extra_index((u32)side, (u32)action)] ==
                    row_masks[row]) {
                    *slot = action;
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
    for (side = 0u; side < SIDES; ++side) {
        seen = 0u;
        for (row = 0u; row < ACTION_ROWS; ++row) {
            action = (u32)*row_slot(controller, side, row);
            if (action == UNBOUND) continue;
            if (action >= UNBOUND || (seen & (1u << action)) != 0u) return;
            seen |= 1u << action;
        }
        for (action = 0u; action < NATIVE_ACTIONS; ++action) native[side][action] = 0u;
        for (action = GUARD; action < UNBOUND; ++action) extra[extra_index(side, action)] = 0u;
        for (row = 0u; row < ACTION_ROWS; ++row) {
            action = (u32)*row_slot(controller, side, row);
            if (action == UNBOUND) continue;
            if (action < NATIVE_ACTIONS)
                native[side][action] = row_masks[row];
            else
                extra[extra_index(side, action)] = row_masks[row];
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
    s32 selected, chosen;
    u32 row;
    if (controller == (void *)0 || side < 0 || side >= SIDES) return;
    *FIELD(controller, 0x04u + (u32)side * 4u) = 1;
    selected = *FIELD(controller, 0x0cu + (u32)side * 4u);
    if (selected < 0 || selected >= (s32)ACTION_ROWS) return;
    chosen = *row_slot(controller, (u32)side, (u32)selected);
    if (chosen < 0 || chosen >= UNBOUND) return;
    /* The button that held the chosen action becomes Unbound. */
    for (row = 0u; row < ACTION_ROWS; ++row) {
        s32 *slot = row_slot(controller, (u32)side, row);
        if ((s32)row != selected && *slot == chosen) {
            *slot = UNBOUND;
            return;
        }
    }
}

/* Queue the Controls instruction during the shared reset, before the first draw. */
SECTION(".text.control_settings_reset_with_help")
void control_settings_reset_with_help(void *controller)
{
    *(u32 *)controller = 0u;
    control_settings_help_set(20.0f, *(void **)((u8 *)controller + 0x90u), HELP_MESSAGES[0], 8, 0);
}

static SECTION(".text.control_settings_helpers") s32 row_visible(s32 row)
{
    return row >= control_settings_scroll && row < control_settings_scroll + VISIBLE_ROWS;
}

/* Move the shared window to show a row. The other panel's cursor keeps its row,
   hidden while scrolled out; the window never leaves a row being edited. */
static SECTION(".text.control_settings_helpers") s32 scroll_to(void *controller, s32 side, s32 row)
{
    s32 top = control_settings_scroll;
    s32 other = *FIELD(controller, 0x0cu + (u32)(1 - side) * 4u);
    if (row < top) top = row;
    else if (row >= top + VISIBLE_ROWS) top = row - VISIBLE_ROWS + 1;
    if (*FIELD(controller, 0x04u + (u32)(1 - side) * 4u) == 2 &&
        (other < top || other >= top + VISIBLE_ROWS))
        return 0;
    control_settings_scroll = top;
    return 1;
}

/* Row navigation, replacing FUN_00387e10: accept edits a row, back confirms both
   players, Select restores the defaults, and Up/Down wrap across every row. */
SECTION(".text.control_settings_navigate")
void control_settings_navigate(void *controller, s32 side)
{
    u8 *pad = pad_state(side);
    u32 pressed = *(u32 *)(pad + 0x84u);
    u32 repeat = *(u32 *)(pad + 0x8cu);
    s32 *selected = FIELD(controller, 0x0cu + (u32)side * 4u);
    s32 next;
    u32 row;
    /* With the cursor scrolled out, accept or a row move only brings it back. */
    if (!row_visible(*selected) && ((pressed & NAVIGATE_ACCEPT) != 0u || (repeat & 0x5000u) != 0u)) {
        if (scroll_to(controller, side, *selected)) play_sound(0x35u);
        else play_sound(0x3fu);
        return;
    }
    if ((pressed & NAVIGATE_ACCEPT) != 0u) {
        play_sound(0x34u);
        *FIELD(controller, 0x04u + (u32)side * 4u) = 2;
        *FIELD(controller, 0x5cu + (u32)side * 4u) = *row_slot(controller, (u32)side, (u32)*selected);
        return;
    }
    if ((pressed & NAVIGATE_BACK) != 0u) {
        for (row = 0u; row < SIDES; ++row) {
            s32 mode = *FIELD(controller, 0x04u + row * 4u);
            if (mode != 0 && mode != 1) {
                play_sound(0x3fu);
                show_help(controller, HELP_MESSAGES[7 - side]);
                return;
            }
        }
        play_sound(0x33u);
        *FIELD(controller, 0u) = 1;
        *FIELD(controller, 0x9cu) = 2;
        control_settings_commit(controller);
        return;
    }
    if ((pressed & 0x100u) != 0u) {
        play_sound(0x33u);
        for (row = 0u; row < ROWS; ++row)
            *row_slot(controller, (u32)side, row) = control_default_reset_actions[row];
        show_help(controller, HELP_MESSAGES[1 + side]);
        return;
    }
    if ((repeat & 0x4000u) != 0u) next = *selected + 1;
    else if ((repeat & 0x1000u) != 0u) next = *selected - 1;
    else return;
    if (next < 0) next = (s32)ROWS - 1;
    else if (next >= (s32)ROWS) next = 0;
    if (!scroll_to(controller, side, next)) {
        play_sound(0x3fu);
        return;
    }
    play_sound(0x35u);
    *selected = next;
}

/* Row editing, replacing FUN_003881f0: accept assigns, cancel restores the
   staged value, and Left/Right step the action or toggle vibration. */
SECTION(".text.control_settings_edit")
void control_settings_edit(void *controller, s32 side)
{
    u8 *pad = pad_state(side);
    u32 pressed = *(u32 *)(pad + 0x84u);
    u32 repeat = *(u32 *)(pad + 0x8cu);
    s32 selected = *FIELD(controller, 0x0cu + (u32)side * 4u);
    u8 *cooldown = (u8 *)controller + 0x64u + (u32)side;
    s32 *slot;
    if ((pressed & EDIT_ACCEPT) != 0u) {
        play_sound(0x34u);
        control_settings_assign_action(controller, side);
        return;
    }
    if ((pressed & EDIT_CANCEL) != 0u) {
        play_sound(0x33u);
        *FIELD(controller, 0x04u + (u32)side * 4u) = 1;
        *row_slot(controller, (u32)side, (u32)selected) = *FIELD(controller, 0x5cu + (u32)side * 4u);
        return;
    }
    if ((repeat & 0xa000u) == 0u) return;
    if (selected < (s32)ACTION_ROWS) {
        control_settings_action_step(controller, (u32)side, (u32)selected, repeat);
        play_sound(0x35u);
        return;
    }
    if ((pressed & 0xa000u) == 0u || *cooldown != 0u) return;
    slot = row_slot(controller, (u32)side, VIBRATION_ROW);
    *slot = *slot != 0 ? 0 : 1;
    play_sound(0x35u);
    if (*slot != 0) {
        ((Rumble)0x00113C70u)(pad + 0x1cu, 1u, 200u, 200u);
        *cooldown = 4u;
    }
}

/* Draw a sprite rectangle at a chosen size, like FUN_0037bc40 at the rectangle's size. */
static SECTION(".text.control_settings_helpers") void draw_scaled(
    float x, float y, u8 *sprite, const s16 *rect, float width, float height)
{
    *(s32 *)(sprite + 0x68u) = rect[0] << 4;
    *(s32 *)(sprite + 0x6cu) = rect[1] << 4;
    *(s32 *)(sprite + 0x70u) = 1;
    *(float *)(sprite + 0x58u) = width;
    *(s32 *)(sprite + 0x60u) = rect[2];
    *(float *)(sprite + 0x5cu) = height;
    *(s32 *)(sprite + 0x64u) = rect[3];
    *(float *)(sprite + 0x50u) = x;
    *(float *)(sprite + 0x54u) = y;
    *(float *)(sprite + 0x44u) = width * -0.5f;
    *(float *)(sprite + 0x48u) = height * -0.5f;
    ((SpriteSubmit)0x001CC350u)(sprite, 0u, 1u);
}

/* Pulsing chevrons on both sides of the top or bottom icon while rows are hidden. */
static SECTION(".text.control_settings_helpers") void draw_scroll_arrows(void *controller)
{
    u8 *sprite = *(u8 **)((u8 *)controller + 0x68u);
    float pulse = ((Sine)0x0016F2E8u)(*(float *)((u8 *)controller + 0x98u) * 3.1415927f) * 1.5f;
    float top = CELL_Y - pulse;
    float bottom = CELL_Y + ROW_PITCH * (float)(VISIBLE_ROWS - 1) + pulse;
    volatile u64 *rg = (volatile u64 *)(sprite + 0x90u);
    volatile u64 *bq = (volatile u64 *)(sprite + 0x98u);
    u64 saved_rg = *rg, saved_bq = *bq;
    /* The sprite color scales texels by color / 128: red 0x80, green 0xFF, and blue 0
       turn the red chevron orange. */
    *rg = 0x80ull | (0xFFull << 32);
    *bq = saved_bq & 0xFFFFFFFF00000000ull;
    if (control_settings_scroll > 0) {
        /* Flag 0x40 mirrors the down-pointing chevron vertically. */
        *(u32 *)(sprite + 4u) |= 0x40u;
        draw_scaled(CELL_X - ARROW_X, top, sprite, scroll_arrow_rect, ARROW_WIDTH, ARROW_HEIGHT);
        draw_scaled(CELL_X + ARROW_X, top, sprite, scroll_arrow_rect, ARROW_WIDTH, ARROW_HEIGHT);
        *(u32 *)(sprite + 4u) &= ~0x40u;
    }
    if (control_settings_scroll + VISIBLE_ROWS < (s32)ROWS) {
        draw_scaled(CELL_X - ARROW_X, bottom, sprite, scroll_arrow_rect, ARROW_WIDTH, ARROW_HEIGHT);
        draw_scaled(CELL_X + ARROW_X, bottom, sprite, scroll_arrow_rect, ARROW_WIDTH, ARROW_HEIGHT);
    }
    ((ObjectCall)0x001CC070u)(sprite);
    *rg = saved_rg;
    *bq = saved_bq;
}

/* Center cells, replacing FUN_00388460: the visible rows. */
SECTION(".text.control_settings_draw_cells")
void control_settings_draw_cells(void *controller)
{
    /* Face, shoulder, and menu sprites, indexed like the row_icon textures. */
    static const u8 sprite_fields[3] = {0x6cu, 0x70u, 0x68u};
    s32 slot;
    for (slot = 0; slot < VISIBLE_ROWS; ++slot) {
        u32 row = (u32)(control_settings_scroll + slot);
        u32 texture = 2u;
        void *sprite;
        const s16 *rect = (const s16 *)0x005D5280u + 8u * 4u;
        if (row < ACTION_ROWS) texture = row_icon(row, &rect);
        sprite = *(void **)((u8 *)controller + sprite_fields[texture]);
        ((RectDraw)0x0037BC40u)(CELL_X, CELL_Y + ROW_PITCH * (float)slot, sprite, rect);
        /* The shoulder sprite holds the four native quads; submit each one. */
        if (texture == 1u) ((ObjectCall)0x001CC070u)(sprite);
    }
    draw_scroll_arrows(controller);
}

/* Row labels, cursor, and row frame, replacing FUN_003885b0. */
SECTION(".text.control_settings_draw_rows")
void control_settings_draw_rows(void *controller)
{
    const u8 **vibration_labels = (const u8 **)0x00604658u;
    s32 side;
    for (side = 0; side < SIDES; ++side) {
        float x = side == 0 ? 124.0f : 388.0f;
        s32 mode = *FIELD(controller, 0x04u + (u32)side * 4u);
        s32 selected = *FIELD(controller, 0x0cu + (u32)side * 4u);
        u32 editing = mode == 2;
        s32 slot;
        if (pad_state(side)[0x5fu] != '@') continue;
        if (mode != 0 && row_visible(selected)) {
            s32 cursor = selected - control_settings_scroll;
            if (editing)
                ((CursorDraw)0x00388900u)(x, CELL_Y + ROW_PITCH * (float)cursor, controller);
            ((RowFrameDraw)0x00388820u)(controller, side, cursor);
        }
        for (slot = 0; slot < VISIBLE_ROWS; ++slot) {
            u32 row = (u32)(control_settings_scroll + slot);
            s32 value = *row_slot(controller, (u32)side, row);
            /* The row being edited keeps the native highlight; Unbound is grey. */
            s32 color = editing && (s32)row == selected ? (s32)0xFF0000D4u
                : row != VIBRATION_ROW && value == UNBOUND ? (s32)UNBOUND_LABEL_COLOR
                : (s32)0xFF000000u;
            if (row == VIBRATION_ROW)
                ((TextDraw)0x00379240u)(x, LABEL_Y + ROW_PITCH * (float)slot,
                    vibration_labels[value], color);
            else
                control_settings_label_draw(x, LABEL_Y + ROW_PITCH * (float)slot,
                    control_settings_labels[value], color);
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
typedef u8 *(*SpriteCreate)(void *, const u8 *, u32, u32, void *);
typedef void (*SpriteRelease)(void *, u32);
typedef void *(*SpriteManager)(void);
typedef u8 *(*ManagerSprite)(void *, u32);
typedef u16 (*ActionBinding)(void *, u32);

typedef struct BadgeVector {
    float x, y, z, w;
} __attribute__((aligned(16))) BadgeVector;

/* Battle sprites for the face, shoulder, and menu textures of the resident gauge
   archive; created once and kept, since that archive stays loaded. */
typedef struct BadgeSprites {
    void *archive;
    u8 *sprite[3];
} BadgeSprites;

BadgeSprites control_settings_badge_sprites
    __attribute__((section(".data.control_settings_badge_sprites"))) = {(void *)0, {(u8 *)0, (u8 *)0, (u8 *)0}};

#define BADGE_FRAME 123u
#define BADGE_FRAME_LAYER 16u
#define FACE_BADGE_SIZE 20.0f

static SECTION(".text.control_settings_helpers") u32 badge_sprites_ready(void *layer)
{
    BadgeSprites *state = &control_settings_badge_sprites;
    void *archive = ((ArchiveFind)0x001AA4B0u)(gauge_archive_name);
    u32 index;
    if (archive == (void *)0) return 0u;
    if (archive != state->archive) {
        for (index = 0u; index < 3u; ++index)
            if (state->sprite[index] != (u8 *)0) ((SpriteRelease)0x001CBDF0u)(state->sprite[index], 1u);
        /* Same textures and quad modes as the Control Settings child. */
        state->sprite[0] = ((SpriteCreate)0x0037B670u)(archive, face_texture_name, 4u, 0u, layer);
        state->sprite[1] = ((SpriteCreate)0x0037B670u)(archive, shoulder_texture_name, 4u, 0u, layer);
        state->sprite[2] = ((SpriteCreate)0x0037B670u)(archive, menu_texture_name, 4u, 1u, layer);
        install_button_icons(archive);
        state->archive = archive;
    }
    return state->sprite[0] != (u8 *)0 && state->sprite[1] != (u8 *)0 && state->sprite[2] != (u8 *)0;
}

/* Draw the badge frame, then the Control Settings icon of the binding's first button
   in row order; a binding with no button draws nothing. */
static SECTION(".text.control_settings_helpers") void draw_badge(
    u32 mask, float scale, float alpha, BadgeVector *at)
{
    void *manager = ((SpriteManager)0x00376610u)();
    u8 *frame;
    u8 *sprite;
    const s16 *rect;
    float width = 30.0f, height = 16.0f;
    u32 row, texture;
    for (row = 0u; row < ACTION_ROWS && (mask & row_masks[row]) == 0u; ++row) {}
    if (row == ACTION_ROWS || manager == (void *)0) return;
    texture = row_icon(row, &rect);
    if (texture == 0u) width = height = FACE_BADGE_SIZE;
    frame = ((ManagerSprite)0x00375180u)(manager, BADGE_FRAME_LAYER);
    if (!badge_sprites_ready(*(void **)(frame + 0xd0u))) return;
    ((SpriteDraw)0x00377750u)(1.0f, alpha, 0.0f, BADGE_FRAME, at);
    /* Submit the frame first so the icon draws over it. */
    ((ObjectCall)0x001CC070u)(frame);
    sprite = control_settings_badge_sprites.sprite[texture];
    *(void **)(sprite + 0xd0u) = *(void **)(frame + 0xd0u);
    *(s32 *)(sprite + 0x68u) = rect[0] << 4;
    *(s32 *)(sprite + 0x6cu) = rect[1] << 4;
    *(s32 *)(sprite + 0x70u) = 1;
    *(s32 *)(sprite + 0x60u) = rect[2];
    *(s32 *)(sprite + 0x64u) = rect[3];
    *(float *)(sprite + 0x58u) = width * scale;
    *(float *)(sprite + 0x5cu) = height * scale;
    *(float *)(sprite + 0x44u) = width * scale * -0.5f;
    *(float *)(sprite + 0x48u) = height * scale * -0.5f;
    *(float *)(sprite + 0x50u) = at->x;
    *(float *)(sprite + 0x54u) = at->y;
    *(float *)(sprite + 0x4cu) = 0.0f;
    *(float *)(sprite + 0x40u) = alpha;
    ((SpriteSubmit)0x001CC350u)(sprite, 0u, 1u);
    ((ObjectCall)0x001CC070u)(sprite);
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
    u32 mask;
    BadgeVector at;
    float scale = control_settings_item_badge_state.scale[side];
    /* Retail reads the side from badge +0, which stays 0 for both panels. Byte +0x28
       selects Item Select, now the owned Item Select L binding, over Linked Attack. */
    mask = badge[0x28u] != 0u
        ? control_settings_extra_bindings[extra_index(side, ITEM_SELECT_L)]
        : ((ActionBinding)0x006EF7F0u)(*(void **)(*(u8 **)0x00607600u + 0xdf0u + side * 4u), 5u);
    at.x = origin->x + offset->x;
    at.y = origin->y + offset->y;
    at.z = origin->z + offset->z;
    at.w = origin->w + offset->w;
    draw_badge(mask, *(float *)(badge + 0x20u), alpha, &at);
    /* Same shrink and recovery as the native badge: 0.1 per frame between 0.8 and 1.0. */
    scale += control_settings_item_badge_state.pressed[side] != 0u ? -0.1f : 0.1f;
    if (scale > 1.0f) scale = 1.0f;
    else if (scale < 0.8f) scale = 0.8f;
    control_settings_item_badge_state.scale[side] = scale;
    control_settings_item_badge_state.pressed[side] = 0u;
    at.x = origin->x - offset->x;
    draw_badge(control_settings_extra_bindings[extra_index(side, ITEM_SELECT_R)], scale, alpha, &at);
    ((PanelDraw)0x00711E50u)(panel);
}
