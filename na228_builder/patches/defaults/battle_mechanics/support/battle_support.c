/* Shared field-support modes and the slim support bar; native object ownership stays in BTL. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define BATTLE_SUPPORT_SECTION(name) \
    __attribute__((section(name), noinline))

#define INLINE __attribute__((always_inline)) inline
#define SUPPORT_OFF 0u
#define SUPPORT_NERFED 1u
#define SUPPORT_NORMAL 2u
#define SUPPORT_UNLIMITED 3u

typedef void (*NativeObjectCall)(void *object);
typedef u32 (*NativePredicate)(void *object);
typedef void (*NativeSupportTransition)(void *object, u32 state);
typedef void (*NativeEvent)(u32 event, void *position);

extern u32 support_get(void);

#define NATIVE_SUPPORT_CALL ((NativeObjectCall)0x00238340u)
#define NATIVE_SUPPORT_INPUT ((NativePredicate)0x00238270u)
#define NATIVE_GAUGE_UPDATE ((NativeObjectCall)0x00238540u)
#define NATIVE_GAUGE_DRAIN ((NativeObjectCall)0x00238720u)
#define NATIVE_EVENT ((NativeEvent)0x001D87C0u)

typedef signed short s16;
typedef signed int s32;
typedef unsigned long long u64;
typedef void (*NativeSpriteCommit)(void *sprite, u32 selector, u32 enabled);
typedef void *(*NativeHud)(void *gauge);
typedef void *(*NativeItemPanel)(void *hud, u32 side);

#define NATIVE_SPRITE_COMMIT ((NativeSpriteCommit)0x001CC350u)
#define NATIVE_SPRITE_FLUSH ((NativeObjectCall)0x001CC070u)
#define NATIVE_HUD ((NativeHud)0x00376610u)
#define NATIVE_ITEM_PANEL ((NativeItemPanel)0x00375A60u)
#define NATIVE_FILL_PALETTE_ADDRESS 0x00899DD0u
#define NATIVE_FILL_RECTANGLE_ADDRESS 0x00604D30u

#define GAUGE_COLOR_STATE_OFFSET 0x0Au
#define GAUGE_READY_STATE_OFFSET 0x0Bu
#define GAUGE_FILL_OFFSET 0x0Cu
#define GAUGE_BAR_SPRITE_OFFSET 0x18u
#define GAUGE_PULSE_ALPHA_OFFSET 0x28u
#define ITEM_PANEL_WHEEL_X_OFFSET 0x50u
#define ITEM_PANEL_WHEEL_Y_OFFSET 0x54u
#define SPRITE_ALPHA_OFFSET 0x40u
#define SPRITE_OFFSET_X_OFFSET 0x44u
#define SPRITE_OFFSET_Y_OFFSET 0x48u
#define SPRITE_X_OFFSET 0x50u
#define SPRITE_Y_OFFSET 0x54u
#define SPRITE_WIDTH_OFFSET 0x58u
#define SPRITE_HEIGHT_OFFSET 0x5Cu
#define SPRITE_SOURCE_WIDTH_OFFSET 0x60u
#define SPRITE_SOURCE_HEIGHT_OFFSET 0x64u
#define SPRITE_SOURCE_X_Q4_OFFSET 0x68u
#define SPRITE_SOURCE_Y_Q4_OFFSET 0x6Cu
#define SPRITE_SOURCE_MODE_OFFSET 0x70u
#define SPRITE_COLOR_RG_OFFSET 0x90u
#define SPRITE_COLOR_BQ_OFFSET 0x98u

/* Bar centered under the item wheel origin, between the item-select badges and
 * below the item count. Colors use the 0x80-scale sprite tint. */
#define SUPPORT_BAR_HALF_WIDTH 27.0f
#define SUPPORT_BAR_Y 31.0f
#define SUPPORT_BAR_HEIGHT 6.0f
#define SUPPORT_BAR_EDGE 1.0f
/* Each round end is drawn as this many columns. */
#define SUPPORT_BAR_END_COLUMNS 6u
#define SUPPORT_TICK_WIDTH 1.0f
/* The tick's black border, on each side and beyond the bar's edge. */
#define SUPPORT_TICK_BORDER 1.0f
#define SUPPORT_EDGE_COLOR 0x00000000u
#define SUPPORT_BACKING_COLOR 0x00100C0Au
#define SUPPORT_TICK_COLOR 0x007F7F7Fu
#define SUPPORT_PULSE_ALPHA 0.6f

static INLINE void set_sprite_rgb(u8 *sprite, u32 color)
{
    u64 *rg = (u64 *)(sprite + SPRITE_COLOR_RG_OFFSET);
    u64 *bq = (u64 *)(sprite + SPRITE_COLOR_BQ_OFFSET);

    *rg = (u64)(color & 0xFFu) | ((u64)((color >> 8) & 0xFFu) << 32);
    *bq = (*bq & 0xFFFFFFFF00000000ull) | (u64)((color >> 16) & 0xFFu);
}

static INLINE void draw_piece(
    u8 *sprite,
    const s16 *rectangle,
    s32 source_x_offset,
    s32 source_width,
    float x,
    float y,
    float width,
    float height
)
{
    *(s32 *)(sprite + SPRITE_SOURCE_X_Q4_OFFSET) = ((s32)rectangle[0] + source_x_offset) * 16;
    *(s32 *)(sprite + SPRITE_SOURCE_Y_Q4_OFFSET) = (s32)rectangle[1] * 16;
    *(u32 *)(sprite + SPRITE_SOURCE_MODE_OFFSET) = 1u;
    *(s32 *)(sprite + SPRITE_SOURCE_WIDTH_OFFSET) = source_width;
    *(s32 *)(sprite + SPRITE_SOURCE_HEIGHT_OFFSET) = rectangle[3];
    *(float *)(sprite + SPRITE_X_OFFSET) = x;
    *(float *)(sprite + SPRITE_Y_OFFSET) = y;
    *(float *)(sprite + SPRITE_WIDTH_OFFSET) = width;
    *(float *)(sprite + SPRITE_HEIGHT_OFFSET) = height;
    NATIVE_SPRITE_COMMIT(sprite, 0u, 1u);
}

static INLINE u8 *active_support(u8 *fighter)
{
    u8 *manager = *(u8 * volatile *)0x00607888u;
    u32 side = fighter[0x60u] & 1u;

    return manager == (u8 *)0 ? (u8 *)0 : *(u8 **)(manager + 4u + side * 4u);
}

BATTLE_SUPPORT_SECTION(".text.battle_support_route_field_call")
void battle_support_route_field_call(void *fighter)
{
    u8 *bytes = (u8 *)fighter;
    u32 mode = support_get();
    u8 *object;

    if (mode == SUPPORT_OFF) {
        return;
    }
    if (mode == SUPPORT_UNLIMITED) {
        *(float *)(bytes + 0x74u) = 1.0f;
    }
    if (mode == SUPPORT_NERFED) {
        /* A summon is one attack; an occupied slot cannot accept another. */
        if (active_support(bytes) != (u8 *)0) {
            return;
        }
        if (*(float *)(bytes + 0x74u) < 1.0f) {
            if (NATIVE_SUPPORT_INPUT(fighter) != 0u &&
                ((*(u16 *)(bytes + 0x60u) & 0x1FFu) >> 5) == 0u) {
                NATIVE_EVENT(0x2Cu, bytes + 0x30u);
            }
            return;
        }
    }

    NATIVE_SUPPORT_CALL(fighter);
    if (mode == SUPPORT_NERFED) {
        object = active_support(bytes);
        if (object != (u8 *)0) {
            u32 *vtable = *(u32 **)(object + 0x50u);

            /* Run native summon setup, then enter the native attack directly.
             * Class transitions prepare their own animations and attack data. */
            ((NativeObjectCall)vtable[0x4Cu / 4u])(object);
            ((NativeSupportTransition)vtable[0x48u / 4u])(object, 2u);
        }
    }
}

BATTLE_SUPPORT_SECTION(".text.battle_support_route_gauge_update")
void battle_support_route_gauge_update(void *fighter)
{
    NATIVE_GAUGE_UPDATE(fighter);
    if (support_get() == SUPPORT_UNLIMITED) {
        *(float *)((u8 *)fighter + 0x74u) = 1.0f;
    }
}

BATTLE_SUPPORT_SECTION(".text.battle_support_route_gauge_drain")
void battle_support_route_gauge_drain(void *fighter)
{
    if (support_get() == SUPPORT_NERFED) {
        /* NUN6: float bits 3B839930 per update, capped at 3DCC0000.
         * The remaining tail keeps the native support lifecycle running. */
        float value = *(float *)((u8 *)fighter + 0x74u) - 0.0040160641074180603f;

        if (value < 0.0f) {
            value = 0.0f;
        } else if (value > 0.099609375f) {
            value = 0.099609375f;
        }
        *(float *)((u8 *)fighter + 0x74u) = value;
    } else {
        NATIVE_GAUGE_DRAIN(fighter);
    }
}

BATTLE_SUPPORT_SECTION(".text.battle_support_gauge_ready")
u32 battle_support_gauge_ready(void *fighter)
{
    float threshold = support_get() == SUPPORT_NERFED ? 1.0f : 0.5f;

    return *(float *)((u8 *)fighter + 0x74u) >= threshold;
}

static INLINE void draw_strip(u8 *sprite, u32 color, float x, float y, float width, float height)
{
    const s16 *rectangle = (const s16 *)NATIVE_FILL_RECTANGLE_ADDRESS;

    set_sprite_rgb(sprite, color);
    draw_piece(sprite, rectangle, 0, rectangle[2], x, y, width, height);
}

/* Half-heights of a unit semicircle at each end column's center, tip first. */
static const float support_bar_end_profile[SUPPORT_BAR_END_COLUMNS]
    __attribute__((section(".rodata.battle_support_end_profile"), used)) = {
    0.3996f, 0.6614f, 0.8122f, 0.9091f, 0.9682f, 0.9965f,
};

/* The horizontal radius of a pill's ends; a pill narrower than its height gets elliptical ends. */
static INLINE float pill_end(float magnitude, float height)
{
    return magnitude * 0.5f < height * 0.5f ? magnitude * 0.5f : height * 0.5f;
}

/*
 * A strip with semicircular ends, drawn as nested strips that each span the
 * whole pill: shorter ones reach further out. Overlap leaves no pixel gap
 * between neighbouring quads, so the pill must be opaque.
 */
static INLINE void draw_pill(u8 *sprite, u32 color, float x, float y, float width, float height)
{
    float magnitude = width < 0.0f ? -width : width;
    float dir = width < 0.0f ? -1.0f : 1.0f;
    float radius = height * 0.5f;
    float end = pill_end(magnitude, height);
    float column = end / (float)SUPPORT_BAR_END_COLUMNS;
    float center = y + radius;
    u32 index;

    if (magnitude == 0.0f) {
        return;
    }
    for (index = 0u; index < SUPPORT_BAR_END_COLUMNS; ++index) {
        float half = radius * support_bar_end_profile[index];
        float offset = (float)index * column;

        draw_strip(sprite, color, x + dir * offset, center - half,
            width - dir * 2.0f * offset, 2.0f * half);
    }
    draw_strip(sprite, color, x + dir * end, y, width - dir * 2.0f * end, height);
}

/* Blend each RGB channel of a sprite tint toward another by amount 0..1. */
static INLINE u32 blend_color(u32 color, u32 target, float amount)
{
    u32 result = 0u;
    u32 shift;

    for (shift = 0u; shift < 24u; shift += 8u) {
        float from = (float)((color >> shift) & 0xFFu);
        float to = (float)((target >> shift) & 0xFFu);

        result |= ((u32)(from + (to - from) * amount) & 0xFFu) << shift;
    }
    return result;
}

/* A support bar below the item wheel; P2 fills toward the screen center. */
BATTLE_SUPPORT_SECTION(".text.battle_support_route_gauge_draw")
void battle_support_route_gauge_draw(void *gauge)
{
    u8 *controller = (u8 *)gauge;
    u8 *bar = *(u8 **)(controller + GAUGE_BAR_SPRITE_OFFSET);
    u32 side = *(u32 *)controller;
    u32 state = controller[GAUGE_READY_STATE_OFFSET];
    const u32 *palette = (const u32 *)NATIVE_FILL_PALETTE_ADDRESS;
    float fill = *(float *)(controller + GAUGE_FILL_OFFSET);
    u32 mode = support_get();
    void *hud;
    u8 *panel;
    float dir;
    float x;
    float y;
    float width;
    float length;
    u32 fill_color;

    if (mode == SUPPORT_OFF || bar == (u8 *)0 || side >= 2u) {
        return;
    }
    hud = NATIVE_HUD(gauge);
    if (hud == (void *)0) {
        return;
    }
    panel = (u8 *)NATIVE_ITEM_PANEL(hud, side);
    if (panel == (u8 *)0) {
        return;
    }
    if (fill < 0.0f) {
        fill = 0.0f;
    } else if (fill > 1.0f) {
        fill = 1.0f;
    }

    dir = side == 0u ? 1.0f : -1.0f;
    x = *(float *)(panel + ITEM_PANEL_WHEEL_X_OFFSET) - dir * SUPPORT_BAR_HALF_WIDTH;
    y = *(float *)(panel + ITEM_PANEL_WHEEL_Y_OFFSET) + SUPPORT_BAR_Y;
    width = dir * 2.0f * SUPPORT_BAR_HALF_WIDTH;
    length = width * fill;

    *(u32 *)(bar + SPRITE_OFFSET_X_OFFSET) = 0u;
    *(u32 *)(bar + SPRITE_OFFSET_Y_OFFSET) = 0u;
    *(float *)(bar + SPRITE_ALPHA_OFFSET) = 1.0f;
    /* Each layer is flushed on its own: one sprite queues only a limited number
     * of quads before a flush. */
    draw_pill(bar, SUPPORT_EDGE_COLOR, x - dir * SUPPORT_BAR_EDGE, y - SUPPORT_BAR_EDGE,
        width + dir * 2.0f * SUPPORT_BAR_EDGE, SUPPORT_BAR_HEIGHT + 2.0f * SUPPORT_BAR_EDGE);
    NATIVE_SPRITE_FLUSH(bar);
    draw_pill(bar, SUPPORT_BACKING_COLOR, x, y, width, SUPPORT_BAR_HEIGHT);
    NATIVE_SPRITE_FLUSH(bar);
    fill_color = controller[GAUGE_COLOR_STATE_OFFSET] == 2u ? palette[3] : palette[state];
    if (state == 1u || state == 2u) {
        /* The native icon's readiness pulse brightens the whole fill. */
        fill_color = blend_color(fill_color, SUPPORT_TICK_COLOR,
            *(float *)(controller + GAUGE_PULSE_ALPHA_OFFSET) * SUPPORT_PULSE_ALPHA);
    }
    draw_pill(bar, fill_color, x, y, length, SUPPORT_BAR_HEIGHT);
    NATIVE_SPRITE_FLUSH(bar);
    if (mode == SUPPORT_NORMAL) {
        /* Normal summons from half gauge, as the native marker shows: a white
         * line in a black pin that stands out from the bar's edge. */
        float tick_x = x + width * 0.5f - SUPPORT_TICK_WIDTH * 0.5f;
        float tick_y = y - SUPPORT_BAR_EDGE;
        float tick_height = SUPPORT_BAR_HEIGHT + 2.0f * SUPPORT_BAR_EDGE;

        draw_strip(bar, SUPPORT_EDGE_COLOR, tick_x - SUPPORT_TICK_BORDER,
            tick_y - SUPPORT_TICK_BORDER, SUPPORT_TICK_WIDTH + 2.0f * SUPPORT_TICK_BORDER,
            tick_height + 2.0f * SUPPORT_TICK_BORDER);
        draw_strip(bar, SUPPORT_TICK_COLOR, tick_x, tick_y, SUPPORT_TICK_WIDTH, tick_height);
        NATIVE_SPRITE_FLUSH(bar);
    }
}
