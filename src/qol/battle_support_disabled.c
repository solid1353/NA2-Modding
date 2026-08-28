/* Disable field support calls and the native support gauge. */

#define BATTLE_SUPPORT_DISABLED_SECTION(name) \
    __attribute__((section(name), noinline))

/* This hook replaces only the native support-button acceptance call. */
BATTLE_SUPPORT_DISABLED_SECTION(".text.battle_support_disabled_suppress_field_call")
void battle_support_disabled_suppress_field_call(void *fighter)
{
    (void)fighter;
}

/* This hook replaces only the dedicated TEX_xgauge draw call. */
BATTLE_SUPPORT_DISABLED_SECTION(".text.battle_support_disabled_hide_gauge")
void battle_support_disabled_hide_gauge(void *gauge)
{
    (void)gauge;
}
