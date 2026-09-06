/* Localized Battle HUD name-width fitting. */

#define UI_BATTLE_HUD_SECTION(name) \
    __attribute__((section(name), noinline))

#define BATTLE_HUD_NAME_MAX_WIDTH 160.0f

UI_BATTLE_HUD_SECTION(
    ".text.localization_ui_battle_hud_fit_width"
)
float localization_ui_battle_hud_fit_width(
    float source_width,
    float scale
)
{
    if (source_width > BATTLE_HUD_NAME_MAX_WIDTH) {
        source_width = BATTLE_HUD_NAME_MAX_WIDTH;
    }
    return source_width * scale;
}
