/* Development Character Select overlay for per-character balance values. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define CHARACTER_ID_OVERLAY_SECTION(name) \
    __attribute__((section(name), noinline))

#define CHARACTER_SELECT_DRAW_ADDRESS 0x003B9160u
#define CHARACTER_SELECT_ID_ADDRESS 0x003B4A90u
#define FONT_BODY_DRAW_ADDRESS 0x00378F50u

typedef void (*CharacterSelectDraw)(u32 selector);
typedef u32 (*CharacterSelectId)(u32 selector);
typedef void (*FontBodyDraw)(float x, float y, const u8 *text, u32 color);

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

#define CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT (1u << 0)
#define CHARACTER_OVERRIDE_SUBSTITUTION_COST_DELTA (1u << 16)

static __attribute__((always_inline)) inline u32 append_u32(
    u8 *text,
    u32 cursor,
    u32 value
)
{
    u8 reversed[10];
    u32 count = 0u;

    do {
        reversed[count++] = (u8)('0' + value % 10u);
        value /= 10u;
    } while (value != 0u);
    while (count != 0u) {
        text[cursor++] = reversed[--count];
    }
    return cursor;
}

static __attribute__((always_inline)) inline void format_tier(
    u8 *text,
    const CharacterOverrideRow *character
)
{
    u32 cursor = 0u;
    u32 index;

    text[cursor++] = (u8)'T';
    text[cursor++] = (u8)'I';
    text[cursor++] = (u8)'E';
    text[cursor++] = (u8)'R';
    text[cursor++] = (u8)' ';
    if (character == 0 || character->tier[0] == 0u) {
        text[cursor++] = (u8)'-';
    } else {
        for (index = 0u; index < 4u && character->tier[index] != 0u; index += 1u) {
            text[cursor++] = character->tier[index];
        }
    }
    text[cursor] = 0u;
}

static __attribute__((always_inline)) inline void format_substitution_cost(
    u8 *text,
    u32 present,
    float cost
)
{
    u32 cursor = 0u;
    u32 magnitude;
    u32 fractional;
    s32 scaled;

    text[cursor++] = (u8)'S';
    text[cursor++] = (u8)'U';
    text[cursor++] = (u8)'B';
    text[cursor++] = (u8)' ';
    if (present == 0u || cost < -21474836.0f || cost > 21474836.0f) {
        text[cursor++] = (u8)'-';
        text[cursor] = 0u;
        return;
    }

    scaled = (s32)(cost * 100.0f + (cost < 0.0f ? -0.5f : 0.5f));
    if (scaled < 0) {
        text[cursor++] = (u8)'-';
        magnitude = (u32)(-(scaled + 1)) + 1u;
    } else {
        magnitude = (u32)scaled;
    }
    cursor = append_u32(text, cursor, magnitude / 100u);
    fractional = magnitude % 100u;
    text[cursor++] = (u8)'.';
    text[cursor++] = (u8)('0' + fractional / 10u);
    if (fractional % 10u != 0u) {
        text[cursor++] = (u8)('0' + fractional % 10u);
    }
    text[cursor] = 0u;
}

static __attribute__((always_inline)) inline u32 resolved_substitution_cost(
    u32 character_id,
    const CharacterOverrideRow **character_out,
    float *cost_out
)
{
    const CharacterOverrideRow *base = &battle_logic_character_overrides.base;
    const CharacterOverrideRow *character = 0;
    u32 base_present =
        base->flags & CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT;

    if (character_id < battle_logic_character_overrides.character_count) {
        character = &battle_logic_character_overrides.characters[character_id];
    }
    *character_out = character;
    if (character != 0 &&
        (character->flags & CHARACTER_OVERRIDE_SUBSTITUTION_COST_PRESENT) != 0u) {
        if ((character->flags & CHARACTER_OVERRIDE_SUBSTITUTION_COST_DELTA) != 0u) {
            if (base_present == 0u) {
                return 0u;
            }
            *cost_out = base->substitution_cost + character->substitution_cost;
        } else {
            *cost_out = character->substitution_cost;
        }
        return 1u;
    }
    if (base_present != 0u) {
        *cost_out = base->substitution_cost;
        return 1u;
    }
    return 0u;
}

CHARACTER_ID_OVERLAY_SECTION(".text.battle_logic_character_id_overlay")
void battle_logic_character_id_overlay(u32 selector)
{
    CharacterSelectDraw draw_character_select =
        (CharacterSelectDraw)CHARACTER_SELECT_DRAW_ADDRESS;
    CharacterSelectId selected_id =
        (CharacterSelectId)CHARACTER_SELECT_ID_ADDRESS;
    FontBodyDraw draw_text = (FontBodyDraw)FONT_BODY_DRAW_ADDRESS;
    u32 side = *(u32 *)(selector + 0x0Cu) != 0u;
    u32 character_id;
    u32 cost_present;
    float cost = 0.0f;
    float x = side ? 332.0f : 166.0f;
    const CharacterOverrideRow *character;
    u8 text[24];

    draw_character_select(selector);
    character_id = selected_id(selector);
    cost_present = resolved_substitution_cost(character_id, &character, &cost);
    format_tier(text, character);
    draw_text(x, 8.0f, text, 0xFF000000u);
    format_substitution_cost(text, cost_present, cost);
    draw_text(x, 28.0f, text, 0xFF000000u);
}
