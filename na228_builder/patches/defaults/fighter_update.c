/* Shared additions around the native per-fighter update. */

#define SETTINGS_SECTION(name) __attribute__((section(name), noinline))

typedef void (*NativeFighterUpdate)(void *fighter);

extern void battle_logic_xdash_pre_fighter_update(void *fighter);
extern void chakra_mode_apply(void *fighter);

#define NATIVE_PRE_FIGHTER_UPDATE ((NativeFighterUpdate)0x0020E280u)

SETTINGS_SECTION(".text.settings_fighter_update_shim")
void settings_fighter_update_shim(void *fighter)
{
    battle_logic_xdash_pre_fighter_update(fighter);
    NATIVE_PRE_FIGHTER_UPDATE(fighter);
    chakra_mode_apply(fighter);
}
