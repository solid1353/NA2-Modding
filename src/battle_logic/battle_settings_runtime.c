/* Shared selectable Battle Settings state and runtime behavior. */

typedef unsigned char u8;
typedef unsigned int u32;

#define BATTLE_SETTINGS_RUNTIME_SECTION(name) \
    __attribute__((section(name), noinline))
#define BATTLE_SETTINGS_RUNTIME_USED_SECTION(name) \
    __attribute__((section(name), aligned(4), used))

#define NATIVE_INPUT_STATE_ADDRESS 0x001D99B0u
#define NATIVE_CONTEST_RENDER_ADDRESS 0x0036BFF0u

#define ULTIMATE_JUTSU_MODE_NO_CONTEST 6u
#define ULTIMATE_JUTSU_MODE_NO_HUD 7u
#define SUB_ACTIVE_FRAMES_MAX 16u
#define XDASH_CHAKRA_COST_MAX 100u
#define XDASH_CHAKRA_COST_STEP 5u
#define XDASH_CHAKRA_COST_OPTION_MAX \
    (XDASH_CHAKRA_COST_MAX / XDASH_CHAKRA_COST_STEP)

typedef u32 (*NativeInputState)(u32 bank, u32 slot);
typedef void (*NativeContestRender)(void *contest);

typedef struct BattleSettingsRuntimeConfig {
    u32 default_ultimate_jutsu_mode;
    u32 default_shadowblur;
    u32 default_extra_hit;
    u32 default_sub_active_frames;
    u32 default_xdash_chakra_cost;
    u32 default_support;
} BattleSettingsRuntimeConfig;

typedef struct BattleSettingsRuntimeState {
    u32 ultimate_jutsu_mode;
    u32 shadowblur;
    u32 extra_hit;
    u32 sub_active_frames;
    u32 xdash_chakra_cost;
    u32 support;
    u32 initialized;
} BattleSettingsRuntimeState;

extern const BattleSettingsRuntimeConfig battle_settings_runtime_config;

volatile BattleSettingsRuntimeState battle_settings_runtime_state
    __attribute__((section(".bss.battle_settings_runtime_state")));

const u8 ultimate_jutsu_no_contest_label[]
    BATTLE_SETTINGS_RUNTIME_USED_SECTION(
        ".rodata.ultimate_jutsu_no_contest_label"
    ) = "No Contest";

const u8 ultimate_jutsu_no_hud_label[]
    BATTLE_SETTINGS_RUNTIME_USED_SECTION(
        ".rodata.ultimate_jutsu_no_hud_label"
    ) = "No HUD";

BATTLE_SETTINGS_RUNTIME_SECTION(".text.battle_settings_runtime_initialize")
void battle_settings_runtime_initialize(void)
{
    if (battle_settings_runtime_state.initialized != 0u) {
        return;
    }
    battle_settings_runtime_state.ultimate_jutsu_mode =
        battle_settings_runtime_config.default_ultimate_jutsu_mode;
    battle_settings_runtime_state.shadowblur =
        battle_settings_runtime_config.default_shadowblur != 0u;
    battle_settings_runtime_state.extra_hit =
        battle_settings_runtime_config.default_extra_hit != 0u;
    battle_settings_runtime_state.sub_active_frames =
        battle_settings_runtime_config.default_sub_active_frames;
    battle_settings_runtime_state.xdash_chakra_cost =
        battle_settings_runtime_config.default_xdash_chakra_cost;
    battle_settings_runtime_state.support =
        battle_settings_runtime_config.default_support != 0u;
    battle_settings_runtime_state.initialized = 1u;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.ultimate_jutsu_mode_default")
u32 ultimate_jutsu_mode_default(void)
{
    return battle_settings_runtime_config.default_ultimate_jutsu_mode;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.ultimate_jutsu_mode_get")
u32 ultimate_jutsu_mode_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.ultimate_jutsu_mode;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.ultimate_jutsu_mode_set")
void ultimate_jutsu_mode_set(u32 mode)
{
    battle_settings_runtime_initialize();
    if (mode > ULTIMATE_JUTSU_MODE_NO_HUD) {
        mode = ultimate_jutsu_mode_default();
    }
    battle_settings_runtime_state.ultimate_jutsu_mode = mode;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.shadowblur_get")
u32 shadowblur_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.shadowblur;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.shadowblur_set")
void shadowblur_set(u32 enabled)
{
    battle_settings_runtime_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_runtime_config.default_shadowblur != 0u;
    }
    battle_settings_runtime_state.shadowblur = enabled;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.extra_hit_get")
u32 extra_hit_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.extra_hit;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.extra_hit_set")
void extra_hit_set(u32 enabled)
{
    battle_settings_runtime_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_runtime_config.default_extra_hit != 0u;
    }
    battle_settings_runtime_state.extra_hit = enabled;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.sub_active_frames_get")
u32 sub_active_frames_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.sub_active_frames;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.sub_active_frames_set")
void sub_active_frames_set(u32 frames)
{
    battle_settings_runtime_initialize();
    if (frames > SUB_ACTIVE_FRAMES_MAX) {
        frames = battle_settings_runtime_config.default_sub_active_frames;
    }
    battle_settings_runtime_state.sub_active_frames = frames;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.xdash_chakra_cost_get")
u32 xdash_chakra_cost_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.xdash_chakra_cost;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.xdash_chakra_cost_option_get")
u32 xdash_chakra_cost_option_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.xdash_chakra_cost /
        XDASH_CHAKRA_COST_STEP;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.xdash_chakra_cost_option_set")
void xdash_chakra_cost_option_set(u32 option)
{
    battle_settings_runtime_initialize();
    if (option > XDASH_CHAKRA_COST_OPTION_MAX) {
        option = battle_settings_runtime_config.default_xdash_chakra_cost /
            XDASH_CHAKRA_COST_STEP;
    }
    battle_settings_runtime_state.xdash_chakra_cost =
        option * XDASH_CHAKRA_COST_STEP;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.support_get")
u32 support_get(void)
{
    battle_settings_runtime_initialize();
    return battle_settings_runtime_state.support;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.support_set")
void support_set(u32 enabled)
{
    battle_settings_runtime_initialize();
    if (enabled > 1u) {
        enabled = battle_settings_runtime_config.default_support != 0u;
    }
    battle_settings_runtime_state.support = enabled;
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.ultimate_jutsu_contest_input_state")
u32 ultimate_jutsu_contest_input_state(u32 bank, u32 slot)
{
    NativeInputState native_input =
        (NativeInputState)NATIVE_INPUT_STATE_ADDRESS;

    if (ultimate_jutsu_mode_get() >= ULTIMATE_JUTSU_MODE_NO_CONTEST) {
        return 0u;
    }
    return native_input(bank, slot);
}

BATTLE_SETTINGS_RUNTIME_SECTION(".text.ultimate_jutsu_contest_render")
void ultimate_jutsu_contest_render(void *contest)
{
    NativeContestRender native_render =
        (NativeContestRender)NATIVE_CONTEST_RENDER_ADDRESS;

    if (ultimate_jutsu_mode_get() < ULTIMATE_JUTSU_MODE_NO_CONTEST) {
        native_render(contest);
    }
}
