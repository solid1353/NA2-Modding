/* Shared field-support modes; native object ownership and rendering stay in BTL. */

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
typedef void (*NativeMarkerDraw)(float x, float y, void *sprite, const void *rectangle);

extern u32 support_get(void);

#define NATIVE_SUPPORT_CALL ((NativeObjectCall)0x00238340u)
#define NATIVE_SUPPORT_INPUT ((NativePredicate)0x00238270u)
#define NATIVE_GAUGE_UPDATE ((NativeObjectCall)0x00238540u)
#define NATIVE_GAUGE_DRAIN ((NativeObjectCall)0x00238720u)
#define NATIVE_GAUGE_DRAW ((NativeObjectCall)0x0071CAF0u)
#define NATIVE_EVENT ((NativeEvent)0x001D87C0u)
#define NATIVE_MARKER_DRAW ((NativeMarkerDraw)0x0037BC40u)

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

BATTLE_SUPPORT_SECTION(".text.battle_support_draw_marker")
void battle_support_draw_marker(float x, float y, void *sprite, const void *rectangle)
{
    if (support_get() == SUPPORT_NORMAL) {
        NATIVE_MARKER_DRAW(x, y, sprite, rectangle);
    }
}

/* This hook replaces only the dedicated TEX_xgauge draw call. */
BATTLE_SUPPORT_SECTION(".text.battle_support_route_gauge_draw")
void battle_support_route_gauge_draw(void *gauge)
{
    if (support_get() != SUPPORT_OFF) {
        NATIVE_GAUGE_DRAW(gauge);
    }
}
