/* Keep selected supports for linked Jutsu while disabling field assists. */

#define QOL_BATTLE_SUPPORT_SECTION(name) \
    __attribute__((section(name), noinline))

/* This hook replaces only the native support-button acceptance call. */
QOL_BATTLE_SUPPORT_SECTION(".text.qol_battle_support_suppress_field_call")
void qol_battle_support_suppress_field_call(void *fighter)
{
    (void)fighter;
}

/* This hook replaces only the dedicated TEX_xgauge draw call. */
QOL_BATTLE_SUPPORT_SECTION(".text.qol_battle_support_hide_gauge")
void qol_battle_support_hide_gauge(void *gauge)
{
    (void)gauge;
}
