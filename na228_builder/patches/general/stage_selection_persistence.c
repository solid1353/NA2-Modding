/* Retain the highlighted Free Battle or Practice stage when Stage Select is cancelled. */
typedef unsigned char u8;
typedef signed int s32;

#define ENTRY(name) __attribute__((section(".text.stage_selection_persistence." name), noinline))
#define CALL(address, type) ((type)(address))

typedef s32 (*StageSelectorUpdate)(void *);
typedef s32 (*StageSelectorGet)(void *);
typedef void (*StageSelectorSet)(void *, s32);

ENTRY("update")
s32 stage_selection_persistence_update(void *selector)
{
    u8 *process = *(u8 **)0x00607620u;
    u8 *manager = *(u8 **)0x00607600u;
    s32 result = CALL(0x00715830u, StageSelectorUpdate)(selector);

    s32 entry_type = process == (u8 *)0 ? -1 : *(s32 *)(process + 0x14u);

    if (result == -1 && manager != (u8 *)0 &&
        (entry_type == 1 || entry_type == 2)) {
        manager[0x114] = (u8)CALL(0x00714810u, StageSelectorGet)(selector);
    }
    return result;
}

ENTRY("apply_initial")
void stage_selection_persistence_apply_initial(void *selector, s32 stage)
{
    u8 *process = *(u8 **)0x00607620u;
    u8 *manager = *(u8 **)0x00607600u;

    if (process != (u8 *)0 && manager != (u8 *)0 &&
        *(s32 *)(process + 0x14u) == 2 && manager[0x114] != 0xffu) {
        stage = manager[0x114];
    }
    CALL(0x007147C0u, StageSelectorSet)(selector, stage);
}
