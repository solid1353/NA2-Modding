/* Runtime-only content availability overrides. */

typedef unsigned int u32;

#define UNLOCK_ALL_SECTION(name) \
    __attribute__((section(name), noinline))

/*
 * The fully unlocked reference save has bit 0 set for every one of the 94
 * character-status entries. Native callers retain their own metadata filters,
 * while every underlying save byte remains untouched.
 */
UNLOCK_ALL_SECTION(".text.qol_unlock_all_character")
u32 qol_unlock_all_character(void *unused_save_data, u32 character_id)
{
    (void)unused_save_data;
    return character_id < 94u;
}

UNLOCK_ALL_SECTION(".text.qol_unlock_all_secondary")
u32 qol_unlock_all_secondary(void *unused_save_data, u32 content_id)
{
    (void)unused_save_data;
    return content_id < 64u;
}

UNLOCK_ALL_SECTION(".text.qol_unlock_all_small_table")
u32 qol_unlock_all_small_table(void *unused_save_data, u32 content_id)
{
    (void)unused_save_data;
    return content_id < 32u ? 0xFFu : 0u;
}

UNLOCK_ALL_SECTION(".text.qol_unlock_all_grouped")
u32 qol_unlock_all_grouped(
    void *unused_save_data,
    u32 group_id,
    u32 content_id
)
{
    u32 count;

    (void)unused_save_data;
    if (group_id == 0u) {
        count = 0x5Du;
    } else if (group_id == 1u) {
        count = 0x29u;
    } else if (group_id == 2u) {
        count = 0x9Bu;
    } else if (group_id == 3u) {
        count = 0xA8u;
    } else if (group_id == 4u) {
        count = 7u;
    } else if (group_id == 5u) {
        count = 0x0Cu;
    } else {
        return 0u;
    }
    if (content_id >= count) {
        return 0u;
    }
    if (content_id == 0u && (group_id == 0u || group_id == 4u)) {
        return 3u;
    }
    return 0xFFu;
}

/* The native wrapper reaches this read only for metadata-valid pairs. */
UNLOCK_ALL_SECTION(".text.qol_unlock_all_jutsu")
u32 qol_unlock_all_jutsu(
    void *unused_character_record,
    u32 unused_character_id,
    u32 unused_jutsu_id
)
{
    (void)unused_character_record;
    (void)unused_character_id;
    (void)unused_jutsu_id;
    return 1u;
}
