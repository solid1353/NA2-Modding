/* Resident normalized substitution state and independent Battle HUD gauge. */

typedef signed int s32;
typedef signed short s16;
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;

#define SUBSTITUTION_GAUGE_SECTION(name) \
    __attribute__((section(name), noinline))
#define ALWAYS_INLINE __attribute__((always_inline)) inline

#define LIVE_MANAGER_POINTER_ADDRESS 0x00607600u
#define MANAGER_P1_FIGHTER_OFFSET 0xDE4u
#define MANAGER_P2_FIGHTER_OFFSET 0xDE8u
#define FIGHTER_HP_OFFSET 0x6Cu
#define FIGHTER_CHAKRA_OFFSET 0x70u

#define BATTLE_TIMER_ADDRESS 0x006B28D0u
#define BATTLE_TIMER_SUPPRESSION_MASK 0x05u
#define SYSTEM_CONTEXT_POINTER_ADDRESS 0x006073FCu
#define SYSTEM_CONTEXT_UPDATE_COUNTS_OFFSET 0x01u
#define SYSTEM_CONTEXT_UPDATE_ORDINAL_OFFSET 0x194u
#define NATIVE_UPDATE_COUNTS 2u

#define SUBSTITUTION_SIDE_COUNT 2u
#define SUBSTITUTION_MODE_CHAKRA 0u
#define SUBSTITUTION_MODE_GAUGE 1u
#define SUBSTITUTION_MODE_FREE 2u

#define NATIVE_SUPPORT_GAUGE_UPDATE_ADDRESS 0x0071C810u
#define NATIVE_BATTLE_HUD_PRIMARY_DRAW_ADDRESS 0x0071B720u
#define NATIVE_SPRITE_COMMIT_ADDRESS 0x001CC350u
#define NATIVE_SPRITE_FLUSH_ADDRESS 0x001CC070u
#define NATIVE_SPRITE_SCALED_DRAW_ADDRESS 0x0037BD00u

#define SUPPORT_GAUGE_SIDE_OFFSET 0x00u
#define SUPPORT_GAUGE_BAR_SPRITE_OFFSET 0x18u
#define BATTLE_HUD_LAYOUT_OFFSET 0x00u
#define BATTLE_HUD_PRIMARY_SPRITE_OFFSET 0x04u
#define BATTLE_HUD_SIDE_OFFSET 0x0Cu

#define SPRITE_FLAGS_OFFSET 0x04u
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
#define SPRITE_FLIP_X_FLAG 0x20u

#define BTL_OUTER_BAR_RECTANGLE_GP_DELTA 0x5CD8u
#define BTL_COST_MARKER_RECTANGLE_GP_DELTA 0x5CD0u
#define BTL_INNER_BAR_RECTANGLE_GP_DELTA 0x5CC0u

#define SUBSTITUTION_GAUGE_X_OFFSET 66.5f
#define SUBSTITUTION_GAUGE_Y 39.5f
#define BATTLE_HUD_CHARACTER_NAME_Y_OFFSET 11.0f
#define SUBSTITUTION_GAUGE_MIDDLE_WIDTH 60.0f
#define SUBSTITUTION_GAUGE_FILL_X 20.0f
#define SUBSTITUTION_GAUGE_FILL_Y 7.0f
#define SUBSTITUTION_GAUGE_FILL_WIDTH 64.0f
#define SUBSTITUTION_GAUGE_FILL_HEIGHT 5.0f
#define SUBSTITUTION_GAUGE_MARKER_Y 10.0f

typedef void (*NativeSupportGaugeUpdate)(void *gauge);
typedef void (*NativeBattleHudPrimaryDraw)(void *hud_child);
typedef void (*NativeSpriteCommit)(void *sprite, u32 selector);
typedef void (*NativeSpriteFlush)(void *sprite);
typedef void (*NativeSpriteScaledDraw)(
    float x,
    float y,
    float scale_x,
    float scale_y,
    void *sprite,
    const void *rectangle
);

typedef struct SpriteRectangle {
    s16 x;
    s16 y;
    s16 width;
    s16 height;
} SpriteRectangle;

typedef struct SubstitutionGaugeConfig {
    u32 stock_counts;
    u32 capacity_counts;
    u32 recovery_delay_counts;
    u32 damage_threshold_q16;
    u32 damage_recovery_enabled;
    u32 default_mode;
} SubstitutionGaugeConfig;

typedef struct SubstitutionGaugeSlot {
    void *fighter;
    u32 meter_counts;
    u32 recovery_delay_counts;
    u32 damage_recovery_remainder;
    u32 last_hp_q16;
    u32 battle_generation;
    u32 hp_valid;
    u32 active;
} SubstitutionGaugeSlot;

typedef struct SubstitutionGaugeState {
    void *manager;
    u32 battle_generation;
    u32 last_clock_ordinal;
    u32 clock_ordinal_valid;
    SubstitutionGaugeSlot player[SUBSTITUTION_SIDE_COUNT];
} SubstitutionGaugeState;

typedef struct SubstitutionGaugeRuntimeState {
    void *controller[SUBSTITUTION_SIDE_COUNT];
    u32 overlay_gp;
    u32 mode;
    u32 initialized;
} SubstitutionGaugeRuntimeState;

extern const SubstitutionGaugeConfig substitution_gauge_config;
extern float battle_logic_substitution_cost_fraction(void *fighter);
volatile float substitution_gauge_cost_fraction[SUBSTITUTION_SIDE_COUNT]
    __attribute__((section(".bss.substitution_gauge_cost_fraction")));
volatile float substitution_gauge_fill_fraction[SUBSTITUTION_SIDE_COUNT]
    __attribute__((section(".bss.substitution_gauge_fill_fraction")));
volatile SubstitutionGaugeState substitution_gauge_state
    __attribute__((section(".bss.substitution_gauge_state")));
volatile SubstitutionGaugeRuntimeState substitution_gauge_runtime_state
    __attribute__((section(".bss.substitution_gauge_runtime_state")));

const u8 substitution_gauge_mode_chakra_label[]
    __attribute__((
        section(".rodata.substitution_gauge_mode_chakra_label"),
        aligned(4),
        used
    )) = "Chakra";
const u8 substitution_gauge_mode_gauge_label[]
    __attribute__((
        section(".rodata.substitution_gauge_mode_gauge_label"),
        aligned(4),
        used
    )) = "Gauge";
const u8 substitution_gauge_mode_free_label[]
    __attribute__((
        section(".rodata.substitution_gauge_mode_free_label"),
        aligned(4),
        used
    )) = "Free";

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_mode_default")
u32 substitution_gauge_mode_default(void)
{
    return substitution_gauge_config.default_mode;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_mode_get")
u32 substitution_gauge_mode_get(void)
{
    if (substitution_gauge_runtime_state.initialized == 0u) {
        substitution_gauge_runtime_state.mode =
            substitution_gauge_mode_default();
        substitution_gauge_runtime_state.initialized = 1u;
    }
    return substitution_gauge_runtime_state.mode;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_mode_set")
void substitution_gauge_mode_set(u32 mode)
{
    u32 current = substitution_gauge_mode_get();
    u32 side;

    if (mode > SUBSTITUTION_MODE_FREE) {
        mode = substitution_gauge_mode_default();
    }
    if (mode == current) {
        return;
    }
    substitution_gauge_runtime_state.mode = mode;
    substitution_gauge_runtime_state.initialized = 1u;
    if (mode == SUBSTITUTION_MODE_CHAKRA) {
        return;
    }
    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        volatile SubstitutionGaugeSlot *slot =
            &substitution_gauge_state.player[side];

        slot->meter_counts = substitution_gauge_config.capacity_counts;
        slot->recovery_delay_counts = 0u;
        slot->damage_recovery_remainder = 0u;
    }
}

SUBSTITUTION_GAUGE_SECTION(
    ".text.substitution_gauge_adjust_battle_hud_character_name_y"
)
float substitution_gauge_adjust_battle_hud_character_name_y(float y)
{
    return substitution_gauge_mode_get() == SUBSTITUTION_MODE_GAUGE
        ? y + BATTLE_HUD_CHARACTER_NAME_Y_OFFSET
        : y;
}

static ALWAYS_INLINE void *manager_fighter(void *manager, u32 side)
{
    u32 offset = side == 0u
        ? MANAGER_P1_FIGHTER_OFFSET
        : MANAGER_P2_FIGHTER_OFFSET;

    return *(void * volatile *)((u8 *)manager + offset);
}

static ALWAYS_INLINE u32 substitution_gauge_cost_counts(void *fighter)
{
    float fraction = battle_logic_substitution_cost_fraction(fighter);
    u32 capacity = substitution_gauge_config.capacity_counts;
    u32 cost;

    if (!(fraction >= 0.0f)) {
        fraction = 0.0f;
    } else if (fraction > 1.0f) {
        fraction = 1.0f;
    }
    cost = (u32)((float)(s32)capacity * fraction + 0.5f);
    return cost < capacity ? cost : capacity;
}

static ALWAYS_INLINE void substitution_gauge_publish(
    u32 side,
    volatile SubstitutionGaugeSlot *slot
)
{
    float current;

    if (
        side >= SUBSTITUTION_SIDE_COUNT ||
        slot->fighter == (void *)0 ||
        substitution_gauge_config.capacity_counts == 0u
    ) {
        if (side < SUBSTITUTION_SIDE_COUNT) {
            substitution_gauge_fill_fraction[side] = 0.0f;
            substitution_gauge_cost_fraction[side] = 0.0f;
        }
        return;
    }
    current = (float)(s32)slot->meter_counts /
        (float)(s32)substitution_gauge_config.capacity_counts;
    substitution_gauge_fill_fraction[side] = current;
    substitution_gauge_cost_fraction[side] =
        (float)(s32)substitution_gauge_cost_counts(slot->fighter) /
        (float)(s32)substitution_gauge_config.capacity_counts;
}

static ALWAYS_INLINE void substitution_gauge_invalidate(void)
{
    u32 side;

    substitution_gauge_state.manager = (void *)0;
    substitution_gauge_state.clock_ordinal_valid = 0u;
    substitution_gauge_runtime_state.overlay_gp = 0u;
    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        substitution_gauge_runtime_state.controller[side] = (void *)0;
        substitution_gauge_state.player[side].fighter = (void *)0;
        substitution_gauge_state.player[side].hp_valid = 0u;
        substitution_gauge_state.player[side].active = 0u;
        substitution_gauge_fill_fraction[side] = 0.0f;
        substitution_gauge_cost_fraction[side] = 0.0f;
    }
}

static ALWAYS_INLINE volatile SubstitutionGaugeSlot *
substitution_gauge_slot_for_fighter(void *fighter)
{
    void *manager;
    u32 side;
    volatile SubstitutionGaugeSlot *slot;

    if (fighter == (void *)0) {
        return (volatile SubstitutionGaugeSlot *)0;
    }
    manager = *(void * volatile *)LIVE_MANAGER_POINTER_ADDRESS;
    if (
        manager == (void *)0 ||
        substitution_gauge_state.manager != manager
    ) {
        return (volatile SubstitutionGaugeSlot *)0;
    }
    if (manager_fighter(manager, 0u) == fighter) {
        side = 0u;
    } else if (manager_fighter(manager, 1u) == fighter) {
        side = 1u;
    } else {
        return (volatile SubstitutionGaugeSlot *)0;
    }

    slot = &substitution_gauge_state.player[side];
    if (slot->battle_generation != substitution_gauge_state.battle_generation) {
        return (volatile SubstitutionGaugeSlot *)0;
    }
    if (slot->fighter != fighter) {
        slot->fighter = fighter;
        slot->last_hp_q16 = 0u;
        slot->hp_valid = 0u;
    }
    slot->active = 1u;
    substitution_gauge_publish(side, slot);
    return slot;
}

static ALWAYS_INLINE u32 substitution_gauge_quantize_hp(float hp)
{
    s32 quantized;

    if (!(hp >= 0.0f)) {
        hp = 0.0f;
    } else if (hp > 1.0f) {
        hp = 1.0f;
    }
    quantized = (s32)(hp * 65536.0f + 0.5f);
    return (u32)quantized;
}

static ALWAYS_INLINE float substitution_gauge_clamp_fraction(float value)
{
    if (!(value >= 0.0f)) {
        return 0.0f;
    }
    return value > 1.0f ? 1.0f : value;
}

static ALWAYS_INLINE void substitution_gauge_set_sprite_rgb(
    volatile u8 *sprite,
    u32 red,
    u32 green,
    u32 blue
)
{
    volatile u64 *rg =
        (volatile u64 *)(sprite + SPRITE_COLOR_RG_OFFSET);
    volatile u64 *bq =
        (volatile u64 *)(sprite + SPRITE_COLOR_BQ_OFFSET);

    *rg = (u64)(red & 0xFFu) | ((u64)(green & 0xFFu) << 32);
    *bq = (*bq & 0xFFFFFFFF00000000ull) | (u64)(blue & 0xFFu);
}

static ALWAYS_INLINE void substitution_gauge_draw_piece(
    volatile u8 *sprite,
    s32 source_x,
    s32 source_y,
    s32 source_width,
    s32 source_height,
    float x,
    float y,
    float width,
    float height
)
{
    NativeSpriteCommit commit =
        (NativeSpriteCommit)NATIVE_SPRITE_COMMIT_ADDRESS;

    *(volatile s32 *)(sprite + SPRITE_SOURCE_X_Q4_OFFSET) = source_x * 16;
    *(volatile s32 *)(sprite + SPRITE_SOURCE_Y_Q4_OFFSET) = source_y * 16;
    *(volatile u32 *)(sprite + SPRITE_SOURCE_MODE_OFFSET) = 1u;
    *(volatile s32 *)(sprite + SPRITE_SOURCE_WIDTH_OFFSET) = source_width;
    *(volatile s32 *)(sprite + SPRITE_SOURCE_HEIGHT_OFFSET) = source_height;
    *(volatile float *)(sprite + SPRITE_X_OFFSET) = x;
    *(volatile float *)(sprite + SPRITE_Y_OFFSET) = y;
    *(volatile float *)(sprite + SPRITE_WIDTH_OFFSET) = width;
    *(volatile float *)(sprite + SPRITE_HEIGHT_OFFSET) = height;
    commit((void *)sprite, 0u);
}

static ALWAYS_INLINE void substitution_gauge_draw(
    void *gauge,
    u32 overlay_gp,
    const volatile u8 *hud_layout,
    const volatile u8 *hud_sprite
)
{
    NativeSpriteScaledDraw draw_marker =
        (NativeSpriteScaledDraw)NATIVE_SPRITE_SCALED_DRAW_ADDRESS;
    NativeSpriteFlush flush =
        (NativeSpriteFlush)NATIVE_SPRITE_FLUSH_ADDRESS;
    volatile u8 *controller = (volatile u8 *)gauge;
    u32 side = *(volatile u32 *)(controller + SUPPORT_GAUGE_SIDE_OFFSET);
    volatile SubstitutionGaugeSlot *slot;
    volatile u8 *sprite;
    const volatile SpriteRectangle *outer_rectangle;
    const volatile SpriteRectangle *inner_rectangle;
    const void *marker_rectangle;
    float mirror;
    float base_x;
    float base_y;
    float scale;
    float fill;
    float cost;
    u32 original_flags;
    u32 original_alpha;
    u32 original_offset_x;
    u32 original_offset_y;
    u32 original_x;
    u32 original_y;
    u32 original_width;
    u32 original_height;
    u32 original_source_width;
    u32 original_source_height;
    u32 original_source_x_q4;
    u32 original_source_y_q4;
    u32 original_source_mode;
    u64 original_color_rg;
    u64 original_color_bq;

    if (
        side >= SUBSTITUTION_SIDE_COUNT ||
        substitution_gauge_state.manager == (void *)0 ||
        substitution_gauge_config.capacity_counts == 0u
    ) {
        return;
    }
    slot = &substitution_gauge_state.player[side];
    if (
        slot->active == 0u ||
        slot->fighter == (void *)0 ||
        slot->battle_generation != substitution_gauge_state.battle_generation
    ) {
        return;
    }
    sprite = *(volatile u8 **)(
        controller + SUPPORT_GAUGE_BAR_SPRITE_OFFSET
    );
    if (sprite == (volatile u8 *)0) {
        return;
    }

    outer_rectangle = (const volatile SpriteRectangle *)(
        overlay_gp - BTL_OUTER_BAR_RECTANGLE_GP_DELTA
    );
    marker_rectangle = (const void *)(
        overlay_gp - BTL_COST_MARKER_RECTANGLE_GP_DELTA
    );
    inner_rectangle = (const volatile SpriteRectangle *)(
        overlay_gp - BTL_INNER_BAR_RECTANGLE_GP_DELTA
    );
    mirror = side == 0u ? 1.0f : -1.0f;
    fill = substitution_gauge_clamp_fraction(
        substitution_gauge_fill_fraction[side]
    );
    cost = substitution_gauge_clamp_fraction(
        substitution_gauge_cost_fraction[side]
    );

    original_flags = *(volatile u32 *)(sprite + SPRITE_FLAGS_OFFSET);
    original_alpha = *(volatile u32 *)(sprite + SPRITE_ALPHA_OFFSET);
    original_offset_x = *(volatile u32 *)(sprite + SPRITE_OFFSET_X_OFFSET);
    original_offset_y = *(volatile u32 *)(sprite + SPRITE_OFFSET_Y_OFFSET);
    original_x = *(volatile u32 *)(sprite + SPRITE_X_OFFSET);
    original_y = *(volatile u32 *)(sprite + SPRITE_Y_OFFSET);
    original_width = *(volatile u32 *)(sprite + SPRITE_WIDTH_OFFSET);
    original_height = *(volatile u32 *)(sprite + SPRITE_HEIGHT_OFFSET);
    original_source_width = *(volatile u32 *)(
        sprite + SPRITE_SOURCE_WIDTH_OFFSET
    );
    original_source_height = *(volatile u32 *)(
        sprite + SPRITE_SOURCE_HEIGHT_OFFSET
    );
    original_source_x_q4 = *(volatile u32 *)(
        sprite + SPRITE_SOURCE_X_Q4_OFFSET
    );
    original_source_y_q4 = *(volatile u32 *)(
        sprite + SPRITE_SOURCE_Y_Q4_OFFSET
    );
    original_source_mode = *(volatile u32 *)(
        sprite + SPRITE_SOURCE_MODE_OFFSET
    );
    original_color_rg = *(volatile u64 *)(sprite + SPRITE_COLOR_RG_OFFSET);
    original_color_bq = *(volatile u64 *)(sprite + SPRITE_COLOR_BQ_OFFSET);
    scale = *(const volatile float *)(hud_layout + 0x08u);
    base_x = *(const volatile float *)(hud_layout + 0x00u) +
        SUBSTITUTION_GAUGE_X_OFFSET * mirror * scale;
    base_y = *(const volatile float *)(hud_layout + 0x04u) +
        SUBSTITUTION_GAUGE_Y * scale;
    *(volatile u32 *)(sprite + SPRITE_ALPHA_OFFSET) =
        hud_sprite == (const volatile u8 *)0
            ? original_alpha
            : *(const volatile u32 *)(hud_sprite + SPRITE_ALPHA_OFFSET);
    *(volatile u32 *)(sprite + SPRITE_OFFSET_X_OFFSET) = 0u;
    *(volatile u32 *)(sprite + SPRITE_OFFSET_Y_OFFSET) = 0u;

    substitution_gauge_set_sprite_rgb(sprite, 0x7Fu, 0x7Fu, 0x7Fu);
    substitution_gauge_draw_piece(
        sprite,
        (s32)outer_rectangle->x,
        (s32)outer_rectangle->y,
        (s32)outer_rectangle->width,
        (s32)outer_rectangle->height,
        base_x,
        base_y,
        (float)outer_rectangle->width * mirror * scale,
        (float)outer_rectangle->height * scale
    );
    substitution_gauge_draw_piece(
        sprite,
        (s32)outer_rectangle->x + (s32)outer_rectangle->width,
        (s32)outer_rectangle->y,
        0,
        (s32)outer_rectangle->height,
        base_x + (float)outer_rectangle->width * mirror * scale,
        base_y,
        SUBSTITUTION_GAUGE_MIDDLE_WIDTH * mirror * scale,
        (float)outer_rectangle->height * scale
    );
    *(volatile u32 *)(sprite + SPRITE_FLAGS_OFFSET) =
        original_flags | SPRITE_FLIP_X_FLAG;
    substitution_gauge_draw_piece(
        sprite,
        (s32)outer_rectangle->x,
        (s32)outer_rectangle->y,
        (s32)outer_rectangle->width,
        (s32)outer_rectangle->height,
        base_x + (
            SUBSTITUTION_GAUGE_MIDDLE_WIDTH +
            (float)outer_rectangle->width
        ) * mirror * scale,
        base_y,
        (float)outer_rectangle->width * mirror * scale,
        (float)outer_rectangle->height * scale
    );
    *(volatile u32 *)(sprite + SPRITE_FLAGS_OFFSET) = original_flags;

    substitution_gauge_set_sprite_rgb(sprite, 0x35u, 0x16u, 0x00u);
    substitution_gauge_draw_piece(
        sprite,
        (s32)inner_rectangle->x,
        (s32)inner_rectangle->y,
        (s32)inner_rectangle->width,
        (s32)inner_rectangle->height,
        base_x + SUBSTITUTION_GAUGE_FILL_X * mirror * scale,
        base_y + SUBSTITUTION_GAUGE_FILL_Y * scale,
        SUBSTITUTION_GAUGE_FILL_WIDTH * mirror * scale,
        SUBSTITUTION_GAUGE_FILL_HEIGHT * scale
    );

    substitution_gauge_set_sprite_rgb(sprite, 0x8Bu, 0x7Fu, 0x33u);
    substitution_gauge_draw_piece(
        sprite,
        (s32)inner_rectangle->x,
        (s32)inner_rectangle->y,
        (s32)inner_rectangle->width,
        (s32)inner_rectangle->height,
        base_x + SUBSTITUTION_GAUGE_FILL_X * mirror * scale,
        base_y + SUBSTITUTION_GAUGE_FILL_Y * scale,
        SUBSTITUTION_GAUGE_FILL_WIDTH * mirror * fill * scale,
        SUBSTITUTION_GAUGE_FILL_HEIGHT * scale
    );

    substitution_gauge_set_sprite_rgb(sprite, 0x7Fu, 0x00u, 0x00u);
    draw_marker(
        base_x + (
            SUBSTITUTION_GAUGE_FILL_X +
            SUBSTITUTION_GAUGE_FILL_WIDTH * cost
        ) * mirror * scale,
        base_y + SUBSTITUTION_GAUGE_MARKER_Y * scale,
        scale,
        scale,
        (void *)sprite,
        marker_rectangle
    );
    flush((void *)sprite);

    *(volatile u32 *)(sprite + SPRITE_FLAGS_OFFSET) = original_flags;
    *(volatile u32 *)(sprite + SPRITE_ALPHA_OFFSET) = original_alpha;
    *(volatile u32 *)(sprite + SPRITE_OFFSET_X_OFFSET) = original_offset_x;
    *(volatile u32 *)(sprite + SPRITE_OFFSET_Y_OFFSET) = original_offset_y;
    *(volatile u32 *)(sprite + SPRITE_X_OFFSET) = original_x;
    *(volatile u32 *)(sprite + SPRITE_Y_OFFSET) = original_y;
    *(volatile u32 *)(sprite + SPRITE_WIDTH_OFFSET) = original_width;
    *(volatile u32 *)(sprite + SPRITE_HEIGHT_OFFSET) = original_height;
    *(volatile u32 *)(
        sprite + SPRITE_SOURCE_WIDTH_OFFSET
    ) = original_source_width;
    *(volatile u32 *)(
        sprite + SPRITE_SOURCE_HEIGHT_OFFSET
    ) = original_source_height;
    *(volatile u32 *)(
        sprite + SPRITE_SOURCE_X_Q4_OFFSET
    ) = original_source_x_q4;
    *(volatile u32 *)(
        sprite + SPRITE_SOURCE_Y_Q4_OFFSET
    ) = original_source_y_q4;
    *(volatile u32 *)(
        sprite + SPRITE_SOURCE_MODE_OFFSET
    ) = original_source_mode;
    *(volatile u64 *)(sprite + SPRITE_COLOR_RG_OFFSET) = original_color_rg;
    *(volatile u64 *)(sprite + SPRITE_COLOR_BQ_OFFSET) = original_color_bq;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_update_and_cache")
void substitution_gauge_update_and_cache(void *gauge)
{
    NativeSupportGaugeUpdate native_update =
        (NativeSupportGaugeUpdate)NATIVE_SUPPORT_GAUGE_UPDATE_ADDRESS;
    volatile u8 *controller = (volatile u8 *)gauge;
    u32 overlay_gp;
    u32 side;

    __asm__ volatile("move\t%0, $28" : "=r"(overlay_gp));
    native_update(gauge);
    if (controller == (volatile u8 *)0) {
        return;
    }
    side = *(volatile u32 *)(controller + SUPPORT_GAUGE_SIDE_OFFSET);
    if (side >= SUBSTITUTION_SIDE_COUNT) {
        return;
    }
    substitution_gauge_runtime_state.controller[side] = gauge;
    substitution_gauge_runtime_state.overlay_gp = overlay_gp;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_draw_with_battle_hud")
void substitution_gauge_draw_with_battle_hud(void *hud_child)
{
    NativeBattleHudPrimaryDraw native_draw =
        (NativeBattleHudPrimaryDraw)NATIVE_BATTLE_HUD_PRIMARY_DRAW_ADDRESS;
    volatile u8 *layout;
    volatile u8 *hud_sprite;
    void *controller;
    u32 side;
    u32 overlay_gp;

    native_draw(hud_child);
    if (substitution_gauge_mode_get() != SUBSTITUTION_MODE_GAUGE) {
        return;
    }
    if (hud_child == (void *)0) {
        return;
    }
    layout = *(volatile u8 **)(
        (volatile u8 *)hud_child + BATTLE_HUD_LAYOUT_OFFSET
    );
    if (layout == (volatile u8 *)0) {
        return;
    }
    side = layout[BATTLE_HUD_SIDE_OFFSET];
    if (side >= SUBSTITUTION_SIDE_COUNT) {
        return;
    }
    controller = substitution_gauge_runtime_state.controller[side];
    overlay_gp = substitution_gauge_runtime_state.overlay_gp;
    if (controller == (void *)0 || overlay_gp == 0u) {
        return;
    }
    hud_sprite = *(volatile u8 **)(
        (volatile u8 *)hud_child + BATTLE_HUD_PRIMARY_SPRITE_OFFSET
    );
    substitution_gauge_draw(controller, overlay_gp, layout, hud_sprite);
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_reset_battle")
void substitution_gauge_reset_battle(void *manager)
{
    u32 generation = substitution_gauge_state.battle_generation + 1u;
    u32 side;

    substitution_gauge_state.manager = manager;
    substitution_gauge_state.battle_generation = generation;
    substitution_gauge_state.last_clock_ordinal = 0u;
    substitution_gauge_state.clock_ordinal_valid = 0u;
    substitution_gauge_runtime_state.overlay_gp = 0u;
    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        volatile SubstitutionGaugeSlot *slot =
            &substitution_gauge_state.player[side];
        void *fighter = manager == (void *)0
            ? (void *)0
            : manager_fighter(manager, side);

        substitution_gauge_runtime_state.controller[side] = (void *)0;
        slot->fighter = fighter;
        slot->meter_counts = substitution_gauge_config.capacity_counts;
        slot->recovery_delay_counts = 0u;
        slot->damage_recovery_remainder = 0u;
        slot->last_hp_q16 = 0u;
        slot->battle_generation = generation;
        slot->hp_valid = 0u;
        slot->active = fighter != (void *)0;
        substitution_gauge_publish(side, slot);
    }
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_can_spend")
int substitution_gauge_can_spend(void *fighter)
{
    u32 mode = substitution_gauge_mode_get();
    volatile SubstitutionGaugeSlot *slot =
        substitution_gauge_slot_for_fighter(fighter);
    u32 cost_counts;

    if (mode == SUBSTITUTION_MODE_FREE) {
        return 1;
    }
    if (mode == SUBSTITUTION_MODE_CHAKRA) {
        return fighter != (void *)0 &&
            *(volatile float *)((u8 *)fighter + FIGHTER_CHAKRA_OFFSET) >= 1.0f;
    }
    if (slot == (volatile SubstitutionGaugeSlot *)0) {
        return 0;
    }
    cost_counts = substitution_gauge_cost_counts(fighter);
    return slot->meter_counts >= cost_counts;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_route_spend")
int substitution_gauge_route_spend(void *fighter)
{
    u32 mode = substitution_gauge_mode_get();
    volatile SubstitutionGaugeSlot *slot =
        substitution_gauge_slot_for_fighter(fighter);
    u32 cost_counts;
    u32 side;

    if (mode == SUBSTITUTION_MODE_CHAKRA) {
        return 0;
    }
    if (mode == SUBSTITUTION_MODE_FREE) {
        return 1;
    }
    if (slot == (volatile SubstitutionGaugeSlot *)0) {
        return 1;
    }
    side = slot == &substitution_gauge_state.player[0] ? 0u : 1u;
    cost_counts = substitution_gauge_cost_counts(fighter);
    if (slot->meter_counts < cost_counts) {
        return 1;
    }
    slot->meter_counts -= cost_counts;
    substitution_gauge_publish(side, slot);
    return 1;
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_note_success")
void substitution_gauge_note_success(void *fighter)
{
    volatile SubstitutionGaugeSlot *slot =
        substitution_gauge_slot_for_fighter(fighter);

    if (
        substitution_gauge_mode_get() == SUBSTITUTION_MODE_GAUGE &&
        slot != (volatile SubstitutionGaugeSlot *)0
    ) {
        slot->recovery_delay_counts =
            substitution_gauge_config.recovery_delay_counts;
    }
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_sample_hp")
void substitution_gauge_sample_hp(void *fighter)
{
    volatile SubstitutionGaugeSlot *slot =
        substitution_gauge_slot_for_fighter(fighter);
    u32 side;
    u32 current_hp_q16;
    u32 received_q16;
    u32 recovery_numerator;
    u32 recovered_counts;

    if (
        substitution_gauge_mode_get() != SUBSTITUTION_MODE_GAUGE ||
        slot == (volatile SubstitutionGaugeSlot *)0
    ) {
        return;
    }
    current_hp_q16 = substitution_gauge_quantize_hp(
        *(volatile float *)((u8 *)fighter + FIGHTER_HP_OFFSET)
    );
    if (slot->hp_valid == 0u) {
        slot->last_hp_q16 = current_hp_q16;
        slot->hp_valid = 1u;
        return;
    }

    received_q16 = slot->last_hp_q16 > current_hp_q16
        ? slot->last_hp_q16 - current_hp_q16
        : 0u;
    slot->last_hp_q16 = current_hp_q16;
    if (
        substitution_gauge_config.damage_recovery_enabled == 0u ||
        slot->meter_counts >= substitution_gauge_config.capacity_counts ||
        substitution_gauge_config.damage_threshold_q16 == 0u
    ) {
        slot->damage_recovery_remainder = 0u;
        return;
    }

    recovery_numerator = slot->damage_recovery_remainder +
        received_q16 * substitution_gauge_config.stock_counts;
    recovered_counts = recovery_numerator /
        substitution_gauge_config.damage_threshold_q16;
    slot->damage_recovery_remainder = recovery_numerator %
        substitution_gauge_config.damage_threshold_q16;
    if (recovered_counts != 0u) {
        if (
            substitution_gauge_config.capacity_counts - slot->meter_counts <=
                recovered_counts
        ) {
            slot->meter_counts = substitution_gauge_config.capacity_counts;
        } else {
            slot->meter_counts += recovered_counts;
        }
    }
    if (slot->meter_counts >= substitution_gauge_config.capacity_counts) {
        slot->meter_counts = substitution_gauge_config.capacity_counts;
        slot->damage_recovery_remainder = 0u;
    }
    side = slot == &substitution_gauge_state.player[0] ? 0u : 1u;
    substitution_gauge_publish(side, slot);
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_advance_counts")
void substitution_gauge_advance_counts(u32 advance_counts)
{
    u32 side;

    if (substitution_gauge_mode_get() != SUBSTITUTION_MODE_GAUGE) {
        return;
    }
    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        volatile SubstitutionGaugeSlot *slot =
            &substitution_gauge_state.player[side];
        u32 remaining = advance_counts;
        u32 consumed;

        if (slot->active == 0u) {
            continue;
        }
        consumed = slot->recovery_delay_counts < remaining
            ? slot->recovery_delay_counts
            : remaining;
        slot->recovery_delay_counts -= consumed;
        remaining -= consumed;
        if (
            remaining != 0u &&
            slot->meter_counts < substitution_gauge_config.capacity_counts
        ) {
            u32 available =
                substitution_gauge_config.capacity_counts - slot->meter_counts;

            slot->meter_counts += remaining < available ? remaining : available;
        }
        if (slot->meter_counts >= substitution_gauge_config.capacity_counts) {
            slot->meter_counts = substitution_gauge_config.capacity_counts;
            slot->damage_recovery_remainder = 0u;
        }
    }
}

SUBSTITUTION_GAUGE_SECTION(".text.substitution_gauge_advance_battle")
void substitution_gauge_advance_battle(void *timer)
{
    void *manager;
    volatile u8 *context;
    u32 ordinal;
    u32 side;

    if (
        timer != (void *)BATTLE_TIMER_ADDRESS ||
        (*(volatile u8 *)timer & BATTLE_TIMER_SUPPRESSION_MASK) != 0u
    ) {
        return;
    }
    manager = *(void * volatile *)LIVE_MANAGER_POINTER_ADDRESS;
    if (
        manager == (void *)0 ||
        substitution_gauge_state.manager != manager
    ) {
        substitution_gauge_invalidate();
        return;
    }
    context = *(volatile u8 **)SYSTEM_CONTEXT_POINTER_ADDRESS;
    if (
        context == (volatile u8 *)0 ||
        context[SYSTEM_CONTEXT_UPDATE_COUNTS_OFFSET] != NATIVE_UPDATE_COUNTS
    ) {
        return;
    }
    ordinal = *(volatile u32 *)(
        context + SYSTEM_CONTEXT_UPDATE_ORDINAL_OFFSET
    );
    if (
        substitution_gauge_state.clock_ordinal_valid != 0u &&
        substitution_gauge_state.last_clock_ordinal == ordinal
    ) {
        return;
    }
    substitution_gauge_state.last_clock_ordinal = ordinal;
    substitution_gauge_state.clock_ordinal_valid = 1u;

    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        volatile SubstitutionGaugeSlot *slot =
            &substitution_gauge_state.player[side];
        void *fighter = manager_fighter(manager, side);

        if (fighter == (void *)0) {
            slot->fighter = (void *)0;
            slot->hp_valid = 0u;
            slot->active = 0u;
            substitution_gauge_fill_fraction[side] = 0.0f;
            substitution_gauge_cost_fraction[side] = 0.0f;
        } else {
            if (slot->fighter != fighter) {
                slot->fighter = fighter;
                slot->last_hp_q16 = 0u;
                slot->hp_valid = 0u;
            }
            slot->active = 1u;
        }
    }
    substitution_gauge_advance_counts(NATIVE_UPDATE_COUNTS);
    for (side = 0u; side < SUBSTITUTION_SIDE_COUNT; ++side) {
        volatile SubstitutionGaugeSlot *slot =
            &substitution_gauge_state.player[side];

        if (slot->active != 0u) {
            substitution_gauge_publish(side, slot);
        }
    }
}
