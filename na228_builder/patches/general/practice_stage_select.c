/* Native Stage Select for Practice while retaining its default stage. */
typedef unsigned char u8;
typedef signed int s32;

#define ENTRY(name) __attribute__((section(".text.practice_stage_select." name), noinline))
#define CALL(address, type) ((type)(address))

typedef void (*StageSelectorInitialize)(void *, s32);
typedef void (*ControllerModeSet)(void *, s32);
typedef void (*PreparationReset)(void *);

ENTRY("initialize")
void practice_stage_select_initialize(void *selector, s32 stage)
{
    u8 *process = *(u8 **)0x00607620u;

    if (process != (u8 *)0 && *(s32 *)(process + 0x14u) == 2) {
        stage = -1;
    }
    CALL(0x00713DC0u, StageSelectorInitialize)(selector, stage);
}

ENTRY("reset_preparation")
void practice_stage_select_reset_preparation(void *preparation)
{
    u8 *process = *(u8 **)0x00607620u;
    u8 *manager = *(u8 **)0x00607600u;

    if (process != (u8 *)0 && manager != (u8 *)0 &&
        *(s32 *)(process + 0x14u) == 2) {
        /* Manual applies when preparation closes; entry needs only Player 1. */
        CALL(0x001F48F0u, ControllerModeSet)(manager, 1);
    }
    CALL(0x006C0380u, PreparationReset)(preparation);
}
