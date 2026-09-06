/* Generated per-character battle overrides for the native battle routine. */

typedef unsigned char u8;
typedef unsigned int u32;

#define SUBSTITUTION_COST_SECTION(name) \
    __attribute__((section(name), noinline))

typedef union FloatBits {
    u32 bits;
    float value;
} FloatBits;

typedef struct CharacterOverrideRow {
    u32 flags;
    u8 tier[4];
    float substitution_cost;
    float hp;
    float damage_multiplier;
    float health_recovery_multiplier;
    float chakra_recovery_multiplier;
} CharacterOverrideRow;

typedef struct CharacterOverrideTable {
    u32 version;
    u32 character_count;
    u32 field_count;
    u32 reserved;
    CharacterOverrideRow base;
    CharacterOverrideRow characters[1];
} CharacterOverrideTable;

extern const CharacterOverrideTable battle_logic_character_overrides;

#define BATTLE_MANAGER_POINTER_ADDRESS 0x00607600u
#define BATTLE_MANAGER_P1_SELECTED_ID_OFFSET 0xC8u
#define BATTLE_MANAGER_P2_SELECTED_ID_OFFSET 0xF0u
#define BATTLE_MANAGER_P1_FIGHTER_OFFSET 0xDE4u
#define BATTLE_MANAGER_P2_FIGHTER_OFFSET 0xDE8u
#define FIGHTER_LIVE_CHARACTER_ID_OFFSET 0x68u

#define CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT (1u << 0)
#define CHARACTER_OVERRIDE_SUBSTITUTION_COST_DELTA (1u << 16)
#define NORMALIZED_COST_CAPACITY 100.0f
#define NATIVE_CHAKRA_CAPACITY 15.0f

static __attribute__((always_inline)) inline u32 match_start_character_id(
    void *fighter
)
{
    u8 *manager = *(u8 **)BATTLE_MANAGER_POINTER_ADDRESS;
    if (manager != (u8 *)0) {
        void *p1_fighter = *(void **)(
            manager + BATTLE_MANAGER_P1_FIGHTER_OFFSET
        );
        void *p2_fighter = *(void **)(
            manager + BATTLE_MANAGER_P2_FIGHTER_OFFSET
        );

        if (fighter == p1_fighter) {
            return *(u32 *)(manager + BATTLE_MANAGER_P1_SELECTED_ID_OFFSET);
        }
        if (fighter == p2_fighter) {
            return *(u32 *)(manager + BATTLE_MANAGER_P2_SELECTED_ID_OFFSET);
        }
    }
    return *(u32 *)((u8 *)fighter + FIGHTER_LIVE_CHARACTER_ID_OFFSET);
}

static __attribute__((always_inline)) inline float resolved_substitution_cost_percent(
    void *fighter,
    float default_cost_percent
)
{
    u32 character_id = match_start_character_id(fighter);
    const CharacterOverrideRow *character = 0;
    float base_cost;

    base_cost = default_cost_percent;
    if ((battle_logic_character_overrides.base.flags &
         CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT) != 0u) {
        base_cost = battle_logic_character_overrides.base.substitution_cost;
    }

    if (character_id < battle_logic_character_overrides.character_count) {
        character = &battle_logic_character_overrides.characters[character_id];
        if ((character->flags &
             CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT) != 0u) {
            if ((character->flags &
                 CHARACTER_OVERRIDE_SUBSTITUTION_COST_DELTA) != 0u) {
                return base_cost + character->substitution_cost;
            }
            return character->substitution_cost;
        }
    }
    return base_cost;
}

SUBSTITUTION_COST_SECTION(".text.battle_logic_substitution_cost")
float battle_logic_substitution_cost(void *fighter, u32 default_cost_bits)
{
    FloatBits default_cost;
    float cost_percent;

    default_cost.bits = default_cost_bits;
    cost_percent = resolved_substitution_cost_percent(
        fighter,
        default_cost.value * NORMALIZED_COST_CAPACITY / NATIVE_CHAKRA_CAPACITY
    );
    return cost_percent * NATIVE_CHAKRA_CAPACITY / NORMALIZED_COST_CAPACITY;
}

SUBSTITUTION_COST_SECTION(".text.battle_logic_substitution_cost_fraction")
float battle_logic_substitution_cost_fraction(void *fighter)
{
    float cost_percent = resolved_substitution_cost_percent(
        fighter,
        NORMALIZED_COST_CAPACITY / NATIVE_CHAKRA_CAPACITY
    );

    if (!(cost_percent >= 0.0f)) {
        cost_percent = 0.0f;
    } else if (cost_percent > NORMALIZED_COST_CAPACITY) {
        cost_percent = NORMALIZED_COST_CAPACITY;
    }
    return cost_percent / NORMALIZED_COST_CAPACITY;
}
