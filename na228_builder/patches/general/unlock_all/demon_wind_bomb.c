/* Assign the dormant Demon Wind Bomb selector only to Classic Naruto. */

typedef unsigned int u32;

#define NATIVE_JUTSU_COMPATIBILITY_ADDRESS 0x001FF8D0u
#define CLASSIC_NARUTO_CHARACTER_ID 0x01u
#define DEMON_WIND_BOMB_JUTSU_ID 0x35u

#define DEMON_WIND_BOMB_SECTION(name) \
    __attribute__((section(name), noinline))

typedef u32 (*NativeJutsuCompatibility)(u32 character_id, u32 jutsu_id);

extern const u32 unlock_all_demon_wind_bomb_enabled;

DEMON_WIND_BOMB_SECTION(".text.qol_demon_wind_bomb_compatibility")
u32 qol_demon_wind_bomb_compatibility(u32 character_id, u32 jutsu_id)
{
    NativeJutsuCompatibility native_compatibility =
        (NativeJutsuCompatibility)NATIVE_JUTSU_COMPATIBILITY_ADDRESS;

    if (unlock_all_demon_wind_bomb_enabled != 0u
        && jutsu_id == DEMON_WIND_BOMB_JUTSU_ID) {
        return character_id == CLASSIC_NARUTO_CHARACTER_ID;
    }
    return native_compatibility(character_id, jutsu_id);
}
