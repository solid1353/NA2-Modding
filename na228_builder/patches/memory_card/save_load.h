/* Shared native Save/Load controller interface. */
#ifndef MEMORY_CARD_SAVE_LOAD_H
#define MEMORY_CARD_SAVE_LOAD_H

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed short s16;

#define MEMORY_CARD_WORKER_POINTER_ADDRESS 0x006075F4u
#define INPUT_SELECTOR_ADDRESS 0x006075FCu
#define FRAME_POINTER_ADDRESS 0x006073FCu

#define NATIVE_SAVE_LOAD_UPDATE_ADDRESS 0x001E3F20u
#define WORKER_PREAMBLE_ADDRESS 0x001E1D80u
#define LOAD_MODE_PREAMBLE_ADDRESS 0x001E1DF0u
#define SCAN_MEMORY_CARD_ADDRESS 0x001E1DA0u
#define REQUEST_RECORD_LOAD_ADDRESS 0x001E1E10u
#define REQUEST_RECORD_SAVE_ADDRESS 0x001E1E50u
#define RESOLVE_WORKER_RESULT_ADDRESS 0x001E3120u
#define PLAY_MENU_SOUND_ADDRESS 0x001D7E20u
#define DISPLAY_WORKER_STATUS_ADDRESS 0x001E5B20u
#define PREPARE_RECORD_OPERATION_ADDRESS 0x001E5B60u
#define INITIALIZE_UI_ADDRESS 0x001E5D10u
#define UPDATE_ACKNOWLEDGMENT_ADDRESS 0x001E5DC0u
#define UPDATE_CONFIRMATION_ADDRESS 0x001E6CE0u
#define UPDATE_UNFORMATTED_CONFIRMATION_ADDRESS 0x001E6FB0u

#define STATE_TWO_ACCEPT_INSTRUCTION_ADDRESS 0x001E451Cu

#define CONTROLLER_PORT_WORD 0u
#define CONTROLLER_RECORD_WORD 1u
#define CONTROLLER_STATE_WORD 2u
#define CONTROLLER_FRAME_WORD 3u
#define CONTROLLER_SUBSTATE_WORD 4u
#define CONTROLLER_REMEMBERED_STATUS_WORD 5u
#define CONTROLLER_UI_WORD 9u

#define UI_MODE_OFFSET 0x08u
#define UI_PORT_OFFSET 0x0Cu
#define UI_RECORD_OFFSET 0x10u
#define UI_MODAL_FLAG_OFFSET 0x14u
#define UI_MESSAGE_OFFSET 0x40u

#define WORKER_STATUS_OFFSET 0x4Cu
#define WORKER_RESULT_OFFSET 0x50u

#define CONTROLLER_STATE_SCAN 2u
#define CONTROLLER_STATE_OPERATION_RESULT 3u
#define CONTROLLER_STATE_RECORD_LIST 4u
#define CONTROLLER_STATE_SAVE 5u
#define CONTROLLER_STATE_LOAD 6u
#define CONTROLLER_STATE_ACKNOWLEDGMENT 7u
#define CONTROLLER_STATE_COMPLETE 8u
#define CONTROLLER_STATE_CLOSING 9u

#define WORKER_STATUS_SCAN_COMPLETE 0x01u
#define WORKER_STATUS_UNFORMATTED_INFO 0x0Au
#define WORKER_STATUS_UNFORMATTED_CONFIRMATION 0x0Bu
#define WORKER_STATUS_NO_DATA_CONFIRMATION 0x0Cu
#define WORKER_STATUS_LOAD_CONFIRMATION 0x10u
#define WORKER_STATUS_SAVE_CONFIRMATION_A 0x1Au
#define WORKER_STATUS_SAVE_CONFIRMATION_B 0x1Bu

#define WORKER_RESULT_SUCCESS 1u
#define WORKER_RESULT_FAILURE 2u
#define WORKER_RESULT_CONFIRMATION 3u

#define SAVE_LOAD_MODE_LOAD 1u
#define SOUND_ACCEPT 0x34u
#define FRAME_COUNTER_MAX 0x1C2

#define SAVE_LOAD_SECTION(name) __attribute__((section(name), noinline))
#define ALWAYS_INLINE static inline __attribute__((always_inline))

typedef struct SaveSlotText {
    float x;
    float y;
    const u8 *text;
} SaveSlotText;

typedef u32 (*UpdateFunction)(void *, u32);
typedef void (*OnePointerFunction)(void *);
typedef void (*PointerValueFunction)(void *, u32);
typedef u32 (*PointerResultFunction)(void *);
typedef u32 (*PointerValueResultFunction)(void *, u32);
typedef void (*ValueFunction)(u32);

ALWAYS_INLINE u32 read_word(const volatile u8 *base, u32 offset)
{
    return *(const volatile u32 *)(base + offset);
}

ALWAYS_INLINE void write_word(volatile u8 *base, u32 offset, u32 value)
{
    *(volatile u32 *)(base + offset) = value;
}

ALWAYS_INLINE volatile u8 *memory_card_worker(void)
{
    return *(volatile u8 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
}

ALWAYS_INLINE u32 current_input(void)
{
    volatile u8 *frame = *(volatile u8 **)FRAME_POINTER_ADDRESS;
    s32 selector = *(volatile s32 *)INPUT_SELECTOR_ADDRESS;

    if (selector == 1) {
        return read_word(frame, 0xFCu);
    }
    if (selector == 0) {
        return read_word(frame, 0x84u);
    }
    return read_word(frame, 0x84u) | read_word(frame, 0xFCu);
}

ALWAYS_INLINE u32 live_state_two_accept_mask(void)
{
    return
        *(const volatile u32 *)STATE_TWO_ACCEPT_INSTRUCTION_ADDRESS &
        0xFFFFu;
}

ALWAYS_INLINE void display_worker_status(volatile u8 *ui, u32 status)
{
    ((PointerValueFunction)DISPLAY_WORKER_STATUS_ADDRESS)((void *)ui, status);
}

ALWAYS_INLINE void resolve_worker(volatile u8 *worker, u32 result)
{
    ((PointerValueFunction)RESOLVE_WORKER_RESULT_ADDRESS)(
        (void *)worker,
        result
    );
}

ALWAYS_INLINE u32 finish(volatile u32 *controller, u32 result)
{
    s32 frame = (s32)controller[CONTROLLER_FRAME_WORD] + 1;

    controller[CONTROLLER_FRAME_WORD] = (u32)frame;
    if (frame > FRAME_COUNTER_MAX) {
        controller[CONTROLLER_FRAME_WORD] = FRAME_COUNTER_MAX;
    }
    return result;
}

#endif
