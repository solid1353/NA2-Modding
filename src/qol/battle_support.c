/* Runtime-selectable field support calls and native support-gauge drawing. */

typedef unsigned int u32;

#define BATTLE_SUPPORT_SECTION(name) \
    __attribute__((section(name), noinline))

typedef void (*NativeSupportCall)(void *fighter);
typedef void (*NativeGaugeDraw)(void *gauge);

extern u32 support_get(void);

#define NATIVE_SUPPORT_CALL ((NativeSupportCall)0x00238340u)
#define NATIVE_GAUGE_DRAW ((NativeGaugeDraw)0x0071CAF0u)

/* This hook replaces only the native support-button acceptance call. */
BATTLE_SUPPORT_SECTION(".text.battle_support_route_field_call")
void battle_support_route_field_call(void *fighter)
{
    if (support_get() != 0u) {
        NATIVE_SUPPORT_CALL(fighter);
    }
}

/* This hook replaces only the dedicated TEX_xgauge draw call. */
BATTLE_SUPPORT_SECTION(".text.battle_support_route_gauge_draw")
void battle_support_route_gauge_draw(void *gauge)
{
    if (support_get() != 0u) {
        NATIVE_GAUGE_DRAW(gauge);
    }
}
