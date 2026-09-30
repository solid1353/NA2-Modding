/* Extended Items toggle and the five-slot inventory. */
typedef unsigned char u8;
typedef signed char s8;
typedef signed short s16;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

#define EXTENDED_ITEMS_SECTION(name) __attribute__((section(name), noinline))
#define EXTENDED_ITEMS_OPTION_MAX 1u
#define NATIVE_SLOTS 3u
#define MAX_SLOTS 5u
#define EXTRA_SLOTS (MAX_SLOTS - NATIVE_SLOTS)
#define SIDES 2u
#define STACK_LIMIT 9
#define NATIVE_CACHE 0x008D6A60u

typedef struct ItemSlot {
    u8 code;
    u8 padding[3];
    s32 count;
} ItemSlot;

typedef struct CacheEntry {
    u8 code;
    s8 count;
} CacheEntry;

typedef struct WheelHistory {
    u32 ready;
    s32 selected;
    float blend;
    float native_offset;
    float span, origin_span, drawn_span;
    u8 code[MAX_SLOTS];
    u8 present[MAX_SLOTS];
    float rest[MAX_SLOTS];
    float target[MAX_SLOTS];
    float origin[MAX_SLOTS];
    float drawn[MAX_SLOTS];
    float origin_visibility[MAX_SLOTS];
    float drawn_visibility[MAX_SLOTS];
} WheelHistory;

typedef u32 (*CodeQuery)(u32);
typedef void *(*FighterGet)(u32);
typedef u32 (*FighterCode)(void *);
typedef u32 (*PanelCodeQuery)(void *, u32);
typedef u32 (*PanelQuery)(void *);
typedef void (*SoundPlay)(u32);
typedef void (*SpriteDraw)(float, float, float, u32, void *);
typedef void (*ItemDraw)(void *, s32, void *, float, float);
typedef void (*ItemDetailDraw)(void *, void *, s32, void *, float);
typedef void (*NumberDraw)(float, float, u32, u32, u32, s32, void *, u32, u32, u32);

typedef struct WheelVector {
    float x, y, z, w;
} __attribute__((aligned(16))) WheelVector;

#define ITEM_SPECIAL ((CodeQuery)0x00376480u)
#define ITEM_KNOWN ((CodeQuery)0x003763D0u)
#define ITEM_CATEGORY ((CodeQuery)0x003765B0u)
#define ITEM_USE_READY ((CodeQuery)0x003764B0u)
#define SIDE_FIGHTER ((FighterGet)0x003769C0u)
#define FIGHTER_ITEM_CODE ((FighterCode)0x00373980u)
#define PANEL_ITEM_USABLE ((PanelCodeQuery)0x00710EB0u)
#define PANEL_ADVANCE ((PanelQuery)0x00711990u)
#define PANEL_ADVANCE_WRAPPER ((PanelQuery)0x00711970u)
#define SOUND_PLAY ((SoundPlay)0x001D7E20u)
#define SPRITE_DRAW ((SpriteDraw)0x00377750u)
#define SPRITE_LAYER_DRAW ((SpriteDraw)0x003777E0u)
#define WHEEL_ITEM_DRAW ((ItemDraw)0x00711C30u)
#define WHEEL_ITEM_DETAIL_DRAW ((ItemDetailDraw)0x00712C20u)
#define NUMBER_DRAW ((NumberDraw)0x00376CF0u)
#define COUNT_OFFSET_X (*(const float *)0x008C3AD8u)
#define COUNT_FRAME_OFFSET_X (*(const float *)0x008C3AE0u)

extern const u32 extended_items_default;

volatile u32 extended_items_state
    __attribute__((section(".bss.extended_items_state")));
volatile u32 extended_items_initialized
    __attribute__((section(".bss.extended_items_initialized")));
/* Extended inventory enabled for the current battle panels. */
volatile u32 extended_items_active
    __attribute__((section(".bss.extended_items_active")));
static ItemSlot extra_slots[SIDES][EXTRA_SLOTS]
    __attribute__((section(".bss.extended_items_extra")));
static CacheEntry practice_cache[SIDES][MAX_SLOTS]
    __attribute__((section(".bss.extended_items_cache")));
/* Slot identities stay fixed; this permutation owns their cyclic order. */
static u8 item_order[SIDES][MAX_SLOTS]
    __attribute__((section(".bss.extended_items_order")));
static WheelHistory wheel_history[SIDES]
    __attribute__((section(".bss.extended_items_history")));

static __attribute__((always_inline)) inline void extended_items_initialize(void)
{
    if (extended_items_initialized == 0u) {
        extended_items_state = extended_items_default;
        extended_items_initialized = 1u;
    }
}

EXTENDED_ITEMS_SECTION(".text.extended_items_option_get")
u32 extended_items_option_get(u32 argument)
{
    (void)argument;
    extended_items_initialize();
    return extended_items_state;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_option_set")
void extended_items_option_set(u32 argument, u32 value)
{
    (void)argument;
    extended_items_initialize();
    if (value > EXTENDED_ITEMS_OPTION_MAX) value = extended_items_default;
    extended_items_state = value;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") u32 slot_total(void)
{
    return extended_items_active != 0u ? MAX_SLOTS : NATIVE_SLOTS;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") u32 panel_side(void *panel)
{
    u32 side = *(u32 *)((u8 *)panel + 0x20u);
    return side < SIDES ? side : 0u;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") s32 *panel_selected(void *panel)
{
    return (s32 *)((u8 *)panel + 0x24u);
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") float *panel_offset(void *panel)
{
    return (float *)((u8 *)panel + 0x28u);
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") ItemSlot *slot_at(void *panel, u32 index)
{
    if (index < NATIVE_SLOTS) return ((ItemSlot **)panel)[index];
    return &extra_slots[panel_side(panel)][index - NATIVE_SLOTS];
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") u32 occupied(const ItemSlot *slot)
{
    return slot->code != 0u && slot->count != 0;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
u32 order_index(void *panel, u32 slot)
{
    const u8 *order = item_order[panel_side(panel)];
    u32 index = 0u;
    while (order[index] != slot) ++index;
    return index;
}

/* Latch Extended Items before the constructor seeds starting items. */
EXTENDED_ITEMS_SECTION(".text.extended_items_begin_panel")
void extended_items_begin_panel(void *panel, u32 side)
{
    u32 index;
    (void)panel;
    extended_items_initialize();
    extended_items_active = extended_items_state;
    if (side >= SIDES) return;
    for (index = 0u; index < MAX_SLOTS; ++index) item_order[side][index] = (u8)index;
    wheel_history[side].ready = 0u;
    for (index = 0u; index < EXTRA_SLOTS; ++index) {
        extra_slots[side][index].code = 0u;
        extra_slots[side][index].count = 0;
    }
}

EXTENDED_ITEMS_SECTION(".text.extended_items_count")
u32 extended_items_count(void *panel)
{
    u32 total = slot_total(), index, count = 0u;
    for (index = 0u; index < total; ++index)
        if (occupied(slot_at(panel, index))) ++count;
    return count;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_full")
u32 extended_items_full(void *panel)
{
    return extended_items_count(panel) >= slot_total();
}

EXTENDED_ITEMS_SECTION(".text.extended_items_has_two")
u32 extended_items_has_two(void *panel)
{
    return extended_items_count(panel) >= 2u;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
s32 step_slots(void *panel, s32 step, u32 want_occupied)
{
    u32 total = slot_total();
    u32 count = extended_items_count(panel);
    u32 ordered = want_occupied && extended_items_active != 0u;
    const u8 *order = item_order[panel_side(panel)];
    s32 index, direction, remaining, slot;
    if (want_occupied ? count == 0u : count >= total) return -1;
    index = ordered ? (s32)order_index(panel, (u32)*panel_selected(panel))
        : *panel_selected(panel);
    direction = step < 0 ? -1 : 1;
    remaining = (step < 0 ? -step : step) + 1;
    index -= direction;
    while (remaining > 0) {
        index += direction;
        if (index >= (s32)total) index = 0;
        else if (index < 0) index = (s32)total - 1;
        slot = ordered ? (s32)order[index] : index;
        if ((occupied(slot_at(panel, (u32)slot)) != 0u) == (want_occupied != 0u))
            --remaining;
    }
    return slot;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_step_occupied")
s32 extended_items_step_occupied(void *panel, s32 step)
{
    return step_slots(panel, step, 1u);
}

EXTENDED_ITEMS_SECTION(".text.extended_items_step_empty")
s32 extended_items_step_empty(void *panel, s32 step)
{
    return step_slots(panel, step, 0u);
}

EXTENDED_ITEMS_SECTION(".text.extended_items_slot_of")
ItemSlot *extended_items_slot_of(void *panel, s32 index)
{
    if (index < 0 || (u32)index >= slot_total()) return (ItemSlot *)0;
    return slot_at(panel, (u32)index);
}

EXTENDED_ITEMS_SECTION(".text.extended_items_selected_slot")
ItemSlot *extended_items_selected_slot(void *panel)
{
    return slot_at(panel, (u32)*panel_selected(panel));
}

EXTENDED_ITEMS_SECTION(".text.extended_items_code_of")
s32 extended_items_code_of(void *panel, s32 index)
{
    ItemSlot *slot = extended_items_slot_of(panel, index);
    return slot != (ItemSlot *)0 ? (s32)(s8)slot->code : 0;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_selected_count")
s32 extended_items_selected_count(void *panel, s32 step)
{
    ItemSlot *slot = extended_items_slot_of(panel, extended_items_step_occupied(panel, step));
    return slot != (ItemSlot *)0 ? slot->count : 0;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_code_at")
s32 extended_items_code_at(void *panel, s32 step)
{
    return extended_items_code_of(panel, extended_items_step_occupied(panel, step));
}

EXTENDED_ITEMS_SECTION(".text.extended_items_selected_code")
s32 extended_items_selected_code(void *panel)
{
    return extended_items_code_at(panel, 0);
}

EXTENDED_ITEMS_SECTION(".text.extended_items_find")
ItemSlot *extended_items_find(void *panel, u32 code)
{
    u32 total = slot_total(), index;
    code &= 0xFFu;
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if (slot->code == code) return slot;
    }
    return (ItemSlot *)0;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_room")
s32 extended_items_room(void *panel, u32 code)
{
    ItemSlot *slot;
    s32 count;
    if ((ITEM_KNOWN(code & 0xFFu) & 0xFFu) == 0u) return 0;
    slot = extended_items_find(panel, code);
    count = slot != (ItemSlot *)0 ? slot->count : 0;
    if (count >= 1) return STACK_LIMIT - count;
    return extended_items_count(panel) < slot_total() ? STACK_LIMIT : 0;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void insert_order(void *panel, u32 slot, u32 count)
{
    u8 *order = item_order[panel_side(panel)];
    u8 remaining[MAX_SLOTS - 1u];
    u32 start, index, written = 0u, seen = 0u, insertion = MAX_SLOTS - 1u;
    u32 rank = (count + 2u) / 2u;
    if (count == 0u) return;
    start = order_index(panel, (u32)*panel_selected(panel));
    for (index = 0u; index < MAX_SLOTS; ++index) {
        u8 current = order[(start + index) % MAX_SLOTS];
        if (current != slot) remaining[written++] = current;
    }
    /* Insert at the next alternating arm without moving any slot's contents. */
    for (index = 0u; index < MAX_SLOTS - 1u; ++index) {
        if (!occupied(slot_at(panel, remaining[index]))) continue;
        if (seen == rank) {
            insertion = index;
            break;
        }
        ++seen;
        if (seen == rank) insertion = index + 1u;
    }
    written = 0u;
    for (index = 0u; index < MAX_SLOTS; ++index)
        order[index] = index == insertion ? (u8)slot : remaining[written++];
}

EXTENDED_ITEMS_SECTION(".text.extended_items_add")
u32 extended_items_add(void *panel, u32 code, s32 amount)
{
    u32 total = slot_total(), index;
    ItemSlot *target = (ItemSlot *)0;
    code &= 0xFFu;
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if (slot->code == code) {
            if (occupied(slot) && slot->count < STACK_LIMIT) target = slot;
            break;
        }
    }
    if (target != (ItemSlot *)0) {
        if (target->count != -1) {
            s32 count = target->count + amount;
            if (count < 0) count = 0;
            else if (count > STACK_LIMIT) count = STACK_LIMIT;
            target->count = count;
        }
        return 1u;
    }
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if (slot->code == code) {
            if (occupied(slot)) return 0u;
            break;
        }
    }
    {
        u32 count = extended_items_count(panel);
        if (count >= total) return 0u;
        index = (u32)extended_items_step_empty(panel, 0);
        insert_order(panel, index, count);
    }
    target = slot_at(panel, index);
    target->code = (u8)code;
    target->count = amount;
    return 1u;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
u32 consume(void *panel, ItemSlot *slot, s32 amount)
{
    s32 count;
    if ((ITEM_SPECIAL(slot->code) & 0xFFu) != 0u) return 0u;
    count = slot->count;
    if (amount < count && amount != -1) {
        if (count != -1) {
            count -= amount;
            if (count < 0) count = 0;
            else if (count > STACK_LIMIT) count = STACK_LIMIT;
            slot->count = count;
        }
        return 0u;
    }
    slot->count = 0;
    slot->code = 0u;
    if (occupied(extended_items_selected_slot(panel))) return 0u;
    *panel_selected(panel) = extended_items_step_occupied(panel, 0);
    if (*panel_selected(panel) < 0) *panel_selected(panel) = 0;
    return 1u;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_consume_code")
void extended_items_consume_code(void *panel, u32 code, s32 amount)
{
    u32 total = slot_total(), index;
    code &= 0xFFu;
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if (slot->code == code) {
            if (occupied(slot)) consume(panel, slot, amount);
            return;
        }
    }
}

EXTENDED_ITEMS_SECTION(".text.extended_items_consume_selected")
void extended_items_consume_selected(void *panel, s32 step, s32 amount)
{
    ItemSlot *slot = extended_items_slot_of(panel, extended_items_step_occupied(panel, step));
    if (slot != (ItemSlot *)0 && consume(panel, slot, amount) != 0u)
        *panel_offset(panel) += 1.0f;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_clear")
void extended_items_clear(void *panel)
{
    u32 total = slot_total(), index;
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if ((ITEM_SPECIAL(slot->code) & 0xFFu) == 0u) {
            slot->code = 0u;
            slot->count = 0;
        }
    }
}

EXTENDED_ITEMS_SECTION(".text.extended_items_relation")
u32 extended_items_relation(void *panel, s32 index)
{
    ItemSlot *slot = extended_items_slot_of(panel, index);
    if (slot == (ItemSlot *)0 || !occupied(slot)) return 0u;
    if (index == *panel_selected(panel)) return 1u;
    if (index == extended_items_step_occupied(panel, 1)) return 2u;
    if (index == extended_items_step_occupied(panel, -1)) return 3u;
    return 0u;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_category")
u32 extended_items_category(void *panel, s32 index)
{
    ItemSlot *slot = extended_items_slot_of(panel, index);
    if (slot == (ItemSlot *)0 || !occupied(slot)) return 0u;
    return ITEM_CATEGORY(slot->code);
}

/* Selected code for the fighter's use input, including native auto-advance. */
EXTENDED_ITEMS_SECTION(".text.extended_items_use_code")
s32 extended_items_use_code(void *panel)
{
    s32 code = (s32)(s8)extended_items_selected_slot(panel)->code;
    u32 ready = 0u, relation, pass;
    u8 *fighter;
    if ((ITEM_USE_READY((u32)code & 0xFFu) & 0xFFu) != 0u) {
        ready = 1u;
    } else {
        fighter = (u8 *)SIDE_FIGHTER(0u);
        ready = *(s16 *)(fighter + 0x9F6u) == *(s16 *)(fighter + 0x324u);
    }
    if (ready && PANEL_ITEM_USABLE(panel, (u32)code) != 0u) return code;
    fighter = (u8 *)SIDE_FIGHTER(panel_side(panel));
    if (((*(u16 *)(fighter + 0x60u) >> 5) & 0xFu) == 0u) {
        SOUND_PLAY(44u);
        return 0;
    }
    relation = extended_items_relation(panel, 0) & 0xFFu;
    for (pass = 0u; pass < 2u; ++pass) {
        if ((ITEM_SPECIAL(extended_items_selected_slot(panel)->code) & 0xFFu) != 0u) break;
        if (relation == 2u) PANEL_ADVANCE(panel);
        else PANEL_ADVANCE_WRAPPER(panel);
    }
    return (s32)(s8)extended_items_selected_slot(panel)->code;
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") CacheEntry *cache_side(void *panel)
{
    return practice_cache[panel_side(panel)];
}

EXTENDED_ITEMS_SECTION(".text.extended_items_cache_build")
void extended_items_cache_build(void *panel, void *destination)
{
    CacheEntry *cache = cache_side(panel);
    const u8 *order = item_order[panel_side(panel)];
    u8 slots[MAX_SLOTS];
    u32 index, start = order_index(panel, 0u), count = 0u, written = 0u;
    (void)destination;
    for (index = 0u; index < MAX_SLOTS; ++index) {
        cache[index].code = 0u;
        cache[index].count = 0;
    }
    for (index = 0u; index < MAX_SLOTS; ++index) {
        u8 slot = order[(start + index) % MAX_SLOTS];
        if (occupied(slot_at(panel, slot))) slots[count++] = slot;
    }
    /* Replay alternating insertion in the same order when Practice restores. */
    for (index = 0u; index < count; ++index) {
        u32 rank = index == 0u ? 0u : (index & 1u) != 0u
            ? (index + 1u) / 2u : count - index / 2u;
        ItemSlot *slot = slot_at(panel, slots[rank]);
        u8 code = slot->code;
        s8 slot_count = (s8)slot->count;
        if ((ITEM_SPECIAL(code) & 0xFFu) != 1u) {
            cache[written].code = code;
            cache[written].count = slot_count;
            ++written;
        }
    }
}

EXTENDED_ITEMS_SECTION(".text.extended_items_cache_restore")
void extended_items_cache_restore(void *panel, void *source)
{
    CacheEntry *cache = cache_side(panel);
    u32 total = slot_total(), index;
    void *fighter;
    (void)source;
    *panel_selected(panel) = 0;
    for (index = 0u; index < total; ++index) {
        ItemSlot *slot = slot_at(panel, index);
        if ((ITEM_SPECIAL(slot->code) & 0xFFu) != 1u) {
            slot->code = 0u;
            slot->count = 0;
        }
    }
    fighter = SIDE_FIGHTER(panel_side(panel));
    for (index = 0u; index < total; ++index) {
        CacheEntry *entry = &cache[index];
        if (entry->count == 0 || entry->code == 0u) continue;
        if (entry->code >= 0x51u && entry->code < 0x74u) {
            u8 normalized = (u8)FIGHTER_ITEM_CODE(fighter);
            if (normalized != entry->code) entry->code = normalized;
        }
        extended_items_add(panel, (u32)(s32)(s8)entry->code, entry->count);
    }
    wheel_history[panel_side(panel)].ready = 0u;
}

EXTENDED_ITEMS_SECTION(".text.extended_items_cache_clear")
void extended_items_cache_clear(void)
{
    u8 *native = (u8 *)NATIVE_CACHE;
    u32 side, index;
    for (index = 0u; index < SIDES * NATIVE_SLOTS * 2u; ++index) native[index] = 0u;
    for (side = 0u; side < SIDES; ++side) {
        for (index = 0u; index < MAX_SLOTS; ++index) {
            practice_cache[side][index].code = 0u;
            practice_cache[side][index].count = 0;
        }
    }
}

/* NUN4's directional sweep: later items rise, earlier items extend below. */
static const float wheel_later_x[4] = {0.0f, 42.0f, 60.0f, 85.0f};
static const float wheel_later_y[4] = {0.0f, -9.0f, -25.0f, -25.0f};
static const float wheel_earlier_x[4] = {0.0f, 43.0f, 70.0f, 100.0f};
static const float wheel_earlier_y[4] = {0.0f, 8.0f, 7.0f, 7.0f};
static const float wheel_origin_x[SIDES] = {77.4f, 434.6f};
#define WHEEL_VERTICAL_LIFT 6.0f
/* Both selection badges sit below the sweep, with the count between them. */
#define WHEEL_BADGE_X (-50.0f)
#define WHEEL_BADGE_Y 30.0f

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void wheel_position(void *panel, float position, WheelVector *out)
{
    const WheelVector *origin = (const WheelVector *)((u8 *)panel + 0x50u);
    float distance = position < 0.0f ? -position : position;
    u32 step = distance >= 2.0f ? 2u : distance >= 1.0f ? 1u : 0u;
    float blend = distance - (float)step;
    const float *steps_x = position > 0.0f ? wheel_later_x : wheel_earlier_x;
    const float *steps_y = position > 0.0f ? wheel_later_y : wheel_earlier_y;
    float x = steps_x[step] + (steps_x[step + 1u] - steps_x[step]) * blend;
    float y = steps_y[step] + (steps_y[step + 1u] - steps_y[step]) * blend;
    /* Later items take negative x on side 0 and positive x on side 1, like retail. */
    if ((position > 0.0f) == (panel_side(panel) == 0u)) x = -x;
    out->x = origin->x + x;
    out->y = origin->y + y - WHEEL_VERTICAL_LIFT;
    out->z = origin->z;
    out->w = origin->w;
}

/* Move the wheel and the Item Select L badge, then finish construction natively. */
EXTENDED_ITEMS_SECTION(".text.extended_items_finish_panel")
void extended_items_finish_panel(void *panel)
{
    if (slot_total() > NATIVE_SLOTS) {
        float *badge = (float *)(*(u8 **)((u8 *)panel + 0x10u) + 0x10u);
        *(float *)((u8 *)panel + 0x30u) = wheel_origin_x[panel_side(panel)];
        badge[0] = WHEEL_BADGE_X;
        badge[1] = WHEEL_BADGE_Y;
    }
    ((void (*)(void *))0x007109D0u)(panel);
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers") float positive(float value)
{
    return value > 0.0f ? value : 0.0f;
}

/* NUN4 items use their own step spacing, independently of the frame points. */
static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
float wheel_item_distance(float position)
{
    float distance = position < 0.0f ? -position : position;
    return distance <= 1.0f ? 35.2f * distance : 35.2f + 28.8f * (distance - 1.0f);
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void wheel_item_position(void *panel, float position, float distance, WheelVector *out)
{
    const WheelVector *origin = (const WheelVector *)((u8 *)panel + 0x50u);
    const float *steps_x = position > 0.0f ? wheel_later_x : wheel_earlier_x;
    const float *steps_y = position > 0.0f ? wheel_later_y : wheel_earlier_y;
    u32 side = panel_side(panel);
    u32 step = distance >= steps_x[2] ? 2u : distance >= steps_x[1] ? 1u : 0u;
    float blend = (distance - steps_x[step]) / (steps_x[step + 1u] - steps_x[step]);
    float next_y = position > 0.0f && side == 1u && step == 2u
        ? -50.0f : steps_y[step + 1u];
    float x = distance;
    if ((position > 0.0f) == (side == 0u)) x = -x;
    out->x = origin->x + x;
    out->y = origin->y + steps_y[step] + (next_y - steps_y[step]) * blend
        - WHEEL_VERTICAL_LIFT;
    out->z = origin->z;
    out->w = origin->w;
}

/* NUN4's signed-x fade bands, indexed by occupied count. */
static const float wheel_negative_fade[6][2] = {
    {0.0f, 35.2f}, {0.0f, 35.2f}, {10.0f, 35.0f},
    {35.0f, 60.0f}, {40.0f, 65.0f}, {45.0f, 75.0f}
};
static const float wheel_positive_fade[6][2] = {
    {0.0f, 35.2f}, {0.0f, 35.2f}, {35.0f, 60.0f},
    {35.0f, 60.0f}, {47.0f, 75.0f}, {47.0f, 75.0f}
};

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
const float *wheel_fade_band(void *panel, float position, u32 count)
{
    u32 positive_x = (position > 0.0f) != (panel_side(panel) == 0u);
    /* The alternating population puts the even-count extra item on the forward arm. */
    if (count == 2u || count == 4u) positive_x = position > 0.0f;
    return positive_x ? wheel_positive_fade[count] : wheel_negative_fade[count];
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
float wheel_item_alpha(void *panel, float position, float distance, float span)
{
    u32 count = span >= 5.0f ? 5u : (u32)span;
    const float *band = wheel_fade_band(panel, position, count);
    float inner = band[0], outer = band[1];
    if (count < 5u) {
        const float *next_band = wheel_fade_band(panel, position, count + 1u);
        float blend = span - (float)count;
        inner += (next_band[0] - inner) * blend;
        outer += (next_band[1] - outer) * blend;
    }
    /* NUN4's 35-unit band edges round its 35.2 step; keep resting neighbors opaque. */
    if (distance <= inner + 0.5f) return 1.0f;
    return positive((outer - distance) / (outer - inner));
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void wheel_draw_item(void *panel, s32 code, float position, float visibility, float span)
{
    float distance = wheel_item_distance(position);
    float scale = positive(1.2f - 0.6f * (distance / 96.0f));
    float alpha = wheel_item_alpha(panel, position, distance, span) * visibility;
    WheelVector at;
    if (alpha <= 0.0f) return;
    wheel_item_position(panel, position, distance, &at);
    WHEEL_ITEM_DRAW(panel, code, &at, scale, alpha);
    /* This native model draw has no opacity argument; keep it off fading copies. */
    if (alpha >= 1.0f)
        WHEEL_ITEM_DETAIL_DRAW(panel, (u8 *)panel + 0x64u, code, &at, scale);
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void wheel_capture_positions(void *panel, u32 count, WheelHistory *history, s32 steps)
{
    float positions[MAX_SLOTS];
    u8 codes[MAX_SLOTS], present[MAX_SLOTS];
    float span = count != 0u ? (float)count : 1.0f;
    u32 index, rank, changed = !history->ready || steps != 0
        || history->selected != *panel_selected(panel);
    for (index = 0u; index < MAX_SLOTS; ++index) {
        positions[index] = 0.0f;
        codes[index] = 0u;
        present[index] = 0u;
    }
    for (rank = 0u; rank < count; ++rank) {
        index = (u32)extended_items_step_occupied(panel, (s32)rank);
        positions[index] = rank <= count / 2u ? (float)rank
            : (float)((s32)rank - (s32)count);
        codes[index] = slot_at(panel, index)->code;
        present[index] = 1u;
    }
    for (index = 0u; index < MAX_SLOTS; ++index)
        if (history->present[index] != present[index] || history->code[index] != codes[index]
            || history->rest[index] != positions[index]) changed = 1u;
    if (changed) {
        for (index = 0u; index < MAX_SLOTS; ++index) {
            u32 surviving = history->ready && history->present[index]
                && history->code[index] == codes[index] && present[index];
            float target = positions[index];
            if (surviving) {
                float expected = history->target[index] - (float)steps;
                /* Keep the chosen direction through the wrap, including a full turn. */
                while (target - expected > span * 0.5f) target -= span;
                while (expected - target > span * 0.5f) target += span;
            }
            history->origin[index] = surviving ? history->drawn[index] : target;
            history->origin_visibility[index] = surviving ? history->drawn_visibility[index]
                : history->ready ? 0.0f : 1.0f;
            history->rest[index] = positions[index];
            history->target[index] = target;
            history->code[index] = codes[index];
            history->present[index] = present[index];
        }
        /* Blending the span preserves wrap positions and count-dependent fading on removal. */
        history->origin_span = history->ready ? history->drawn_span : span;
        history->span = span;
        history->blend = history->ready ? 1.0f : 0.0f;
        history->selected = *panel_selected(panel);
        history->ready = 1u;
    }
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
s32 wheel_selection_steps(void *panel, WheelHistory *history)
{
    float offset = *panel_offset(panel);
    float delta = history->ready ? offset - history->native_offset : 0.0f;
    history->native_offset = offset;
    return (s32)(delta + (delta < 0.0f ? -0.5f : 0.5f));
}

static EXTENDED_ITEMS_SECTION(".text.extended_items_helpers")
void wheel_blend_positions(WheelHistory *history)
{
    float blend = history->blend;
    u32 index;
    history->drawn_span = history->span + (history->origin_span - history->span) * blend;
    for (index = 0u; index < MAX_SLOTS; ++index) {
        /* At rest, discard completed turns without changing their visible positions. */
        if (blend == 0.0f) history->target[index] = history->rest[index];
        history->drawn[index] = history->target[index]
            + (history->origin[index] - history->target[index]) * blend;
        history->drawn_visibility[index] = 1.0f
            + (history->origin_visibility[index] - 1.0f) * blend;
    }
}

/* Capture presses before native clamping can discard their signed displacement. */
EXTENDED_ITEMS_SECTION(".text.extended_items_update_count")
u32 extended_items_update_count(void *panel)
{
    u32 count = extended_items_count(panel);
    float *offset = panel_offset(panel);
    if (extended_items_active != 0u) {
        WheelHistory *history = &wheel_history[panel_side(panel)];
        s32 steps = wheel_selection_steps(panel, history);
        wheel_capture_positions(panel, count, history, steps);
        history->blend = positive(history->blend - 0.2f);
        wheel_blend_positions(history);
    }
    /* Preserve the native panel offset and its update when the toggle is off. */
    if (*offset < -1.0f) *offset = -1.0f;
    else if (*offset > 1.0f) *offset = 1.0f;
    ((void (*)(float, float, float *))0x006C12A0u)(0.0f, 0.2f, offset);
    if (extended_items_active != 0u)
        wheel_history[panel_side(panel)].native_offset = *offset;
    return count;
}

/* Five-slot wheel with the selection at the center of the mirrored sweep. */
EXTENDED_ITEMS_SECTION(".text.extended_items_draw")
void extended_items_draw(void *panel)
{
    float *animation = *(float **)((u8 *)panel + 0x0Cu);
    WheelHistory *history = &wheel_history[panel_side(panel)];
    s32 position;
    u32 index;
    WheelVector center = *(const WheelVector *)((u8 *)panel + 0x50u);
    WheelVector at;
    s32 count;
    u32 occupied_count = extended_items_count(panel);
    s32 next = (s32)(occupied_count / 2u);
    s32 previous = (s32)occupied_count - 1 - next;

    wheel_capture_positions(panel, occupied_count, history, wheel_selection_steps(panel, history));
    wheel_blend_positions(history);
    center.y -= WHEEL_VERTICAL_LIFT;
    SPRITE_DRAW(animation[2], 1.0f, animation[5], 124u, &center);
    for (position = -2; position <= 2; ++position) {
        float distance = (float)(position < 0 ? -position : position);
        if (position == 0 || (occupied_count > 0u
            && position >= -previous && position <= next)) continue;
        wheel_position(panel, (float)position, &at);
        SPRITE_DRAW(positive(1.0f - 0.1f * distance),
            positive(1.0f - 0.15f * distance), 0.0f, 126u, &at);
    }
    /* A wrapped item retains both copies; interrupted blends keep their full phase. */
    for (index = 0u; index < MAX_SLOTS; ++index) {
        float at_position = history->drawn[index];
        float span = history->drawn_span;
        s32 code = (s32)(s8)history->code[index];
        if (!history->present[index]) continue;
        while (at_position < -3.0f) at_position += span;
        while (at_position >= -3.0f + span) at_position -= span;
        for (; at_position < 3.0f; at_position += span)
            wheel_draw_item(panel, code, at_position, history->drawn_visibility[index], span);
    }
    SPRITE_LAYER_DRAW(animation[2], animation[1], animation[3], 121u, &center);
    SPRITE_LAYER_DRAW(1.0f, animation[1], 0.0f, 120u, &center);
    count = extended_items_selected_count(panel, 0);
    if (count == 0) return;
    at = center;
    at.x += COUNT_OFFSET_X;
    at.y += 27.0f;
    if (count == -1) SPRITE_DRAW(1.0f, 1.0f, 0.0f, 162u, &at);
    else NUMBER_DRAW(1.0f, 1.0f, 0u, 0u, 0x005B1204u, count, &at, 0u, 0u, 0u);
    at = center;
    at.x += COUNT_FRAME_OFFSET_X;
    at.y += 27.0f;
    SPRITE_DRAW(1.0f, 1.0f, 0.0f, 161u, &at);
}
