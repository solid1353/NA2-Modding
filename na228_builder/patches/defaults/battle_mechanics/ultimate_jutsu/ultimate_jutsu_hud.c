/* Keep the native HP damage trail until the No HUD presentation returns. */

typedef unsigned char u8;
typedef unsigned int u32;

#define HUD_SECTION(name) __attribute__((section(name), noinline))
#define ULTIMATE_JUTSU_MODE_NO_HUD 7u
#define CONTEST_POINTER_ADDRESS 0x00607750u
#define NATIVE_HUD_HIDE_ADDRESS 0x001F1820u
#define NATIVE_HUD_SHOW_ADDRESS 0x001F1A20u
#define HUD_SIDE_OFFSET 0x0Cu
#define HUD_FIGHTER_OFFSET 0x14u
#define HUD_HP_BAR_OFFSET 0x24u
#define HUD_SLIDE_Y_OFFSET 0x3Cu
#define HUD_HIDDEN_OFFSET 0x54u
#define HP_BAR_CURRENT_OFFSET 0x08u
#define HP_BAR_TRAILING_OFFSET 0x0Cu
#define HP_BAR_DELAY_OFFSET 0x10u
#define HP_BAR_NATIVE_DELAY 100u

typedef void (*NativeHudTransition)(u32 mask);

typedef struct DamageTrailHold {
    void *bar;
    void *fighter;
    u32 holding;
} DamageTrailHold;

typedef struct UltimateJutsuHudState {
    u32 active;
    DamageTrailHold sides[2];
} UltimateJutsuHudState;

UltimateJutsuHudState ultimate_jutsu_hud_state
    __attribute__((section(".bss.ultimate_jutsu_hud_state")));

extern u32 ultimate_jutsu_mode_get(void);

HUD_SECTION(".text.ultimate_jutsu_hud_update")
void ultimate_jutsu_hud_update(void *hud)
{
    u8 *parent = (u8 *)hud;
    u32 no_hud = ultimate_jutsu_mode_get() == ULTIMATE_JUTSU_MODE_NO_HUD;
    u32 active = no_hud && *(volatile u32 *)CONTEST_POINTER_ADDRESS != 0u;
    u32 side = *(u8 *)(parent + HUD_SIDE_OFFSET);
    u8 *bar = *(u8 **)(parent + HUD_HP_BAR_OFFSET);
    void *fighter = *(void **)(parent + HUD_FIGHTER_OFFSET);
    DamageTrailHold *hold;

    if (active != ultimate_jutsu_hud_state.active) {
        ultimate_jutsu_hud_state.active = active;
        if (active) {
            ((NativeHudTransition)NATIVE_HUD_HIDE_ADDRESS)(~0u);
        } else {
            ((NativeHudTransition)NATIVE_HUD_SHOW_ADDRESS)(~0u);
        }
    }

    if (side >= 2u) {
        return;
    }
    hold = &ultimate_jutsu_hud_state.sides[side];
    if (hold->bar != bar || hold->fighter != fighter) {
        hold->bar = bar;
        hold->fighter = fighter;
        hold->holding = 0u;
    }
    if (bar == (u8 *)0 || fighter == (void *)0) {
        hold->holding = 0u;
        return;
    }

    if (active) {
        float current = *(float *)(bar + HP_BAR_CURRENT_OFFSET);
        float *trailing = (float *)(bar + HP_BAR_TRAILING_OFFSET);

        /* The cached HP precedes this update's damage sample. Preserve any
         * existing damage trail, and catch up if HP has recovered instead. */
        if (*trailing < current) {
            *trailing = current;
        }
        hold->holding = 1u;
    } else if (!no_hud ||
               (*(u8 *)(parent + HUD_HIDDEN_OFFSET) != 1u &&
                *(float *)(parent + HUD_SLIDE_Y_OFFSET) >= -2.0f)) {
        hold->holding = 0u;
    }

    if (hold->holding) {
        /* Native sampling still updates current HP. Only the trailing bar's
         * countdown is held, including while the parent slides back in. */
        *(u32 *)(bar + HP_BAR_DELAY_OFFSET) = HP_BAR_NATIVE_DELAY;
    }
}
