/* Retain the highlighted Free Battle stage when Stage Select is cancelled. */
typedef unsigned char u8;
typedef signed int s32;

#define ENTRY(name) __attribute__((section(".text.free_battle_stage_persistence." name), noinline))
#define CALL(address, type) ((type)(address))

typedef s32 (*StageSelectorUpdate)(void *);
typedef s32 (*StageSelectorGet)(void *);

ENTRY("update")
s32 free_battle_stage_persistence_update(void *selector)
{
    u8 *process = *(u8 **)0x00607620u;
    u8 *manager = *(u8 **)0x00607600u;
    s32 result = CALL(0x00715830u, StageSelectorUpdate)(selector);

    if (result == -1 && process != (u8 *)0 && manager != (u8 *)0 &&
        *(s32 *)(process + 0x14u) == 1) {
        manager[0x114] = (u8)CALL(0x00714810u, StageSelectorGet)(selector);
    }
    return result;
}
