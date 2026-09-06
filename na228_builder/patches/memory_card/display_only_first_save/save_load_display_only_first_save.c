/* Keep only record zero in the visible native Save/Load controller. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned int u32;

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
#define UI_TRANSITION_OFFSET 0x40u

#define WORKER_STATUS_OFFSET 0x4Cu
#define WORKER_RESULT_OFFSET 0x50u

#define CONTROLLER_STATE_SCAN 2u
#define CONTROLLER_STATE_OPERATION_RESULT 3u
#define CONTROLLER_STATE_RECORD_LIST 4u
#define CONTROLLER_STATE_SAVE 5u
#define CONTROLLER_STATE_LOAD 6u
#define CONTROLLER_STATE_ACKNOWLEDGMENT 7u
#define CONTROLLER_STATE_COMPLETE 8u

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

ALWAYS_INLINE void update_state_two_prefix(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 result
)
{
    u32 substate = controller[CONTROLLER_SUBSTATE_WORD];

    if (substate == 4u) {
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_COMPLETE;
    } else if (substate == 1u) {
        controller[CONTROLLER_PORT_WORD] = read_word(ui, UI_PORT_OFFSET);
        ((PointerValueFunction)SCAN_MEMORY_CARD_ADDRESS)(
            (void *)worker,
            controller[CONTROLLER_PORT_WORD]
        );
        controller[CONTROLLER_SUBSTATE_WORD] = 2u;
        ui[4] = 0u;
        if ((s32)result > 0) {
            controller[CONTROLLER_SUBSTATE_WORD] = 3u;
        }
    } else if (substate == 0u) {
        ((PointerValueFunction)INITIALIZE_UI_ADDRESS)((void *)ui, 1u);
        ui[1] = 1u;
        write_word(ui, UI_TRANSITION_OFFSET, 0u);
        controller[CONTROLLER_SUBSTATE_WORD] = 1u;
    }
}

ALWAYS_INLINE u32 update_special_state_two(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 mode,
    u32 status,
    u32 input
)
{
    u32 result;

    write_word(ui, UI_MODE_OFFSET, mode);
    if (status == WORKER_STATUS_UNFORMATTED_INFO) {
        write_word(ui, UI_MODAL_FLAG_OFFSET, 1u);
    } else {
        display_worker_status(ui, status);
    }

    result = read_word(worker, WORKER_RESULT_OFFSET);
    update_state_two_prefix(controller, ui, worker, result);

    if (result == WORKER_RESULT_SUCCESS) {
        controller[CONTROLLER_REMEMBERED_STATUS_WORD] = 0xFFFFFFFFu;
        if (status == WORKER_STATUS_UNFORMATTED_INFO) {
            u32 complete = mode == 0u ? 1u :
                ((PointerValueResultFunction)UPDATE_ACKNOWLEDGMENT_ADDRESS)(
                    (void *)ui,
                    0u
                );
            if (complete != 0u) {
                resolve_worker(worker, 0u);
                write_word(ui, UI_MODAL_FLAG_OFFSET, 1u);
            }
        } else if (
            status == WORKER_STATUS_UNFORMATTED_CONFIRMATION &&
            (input & live_state_two_accept_mask()) != 0u
        ) {
            ((ValueFunction)PLAY_MENU_SOUND_ADDRESS)(SOUND_ACCEPT);
            resolve_worker(worker, 0u);
        }
    } else if (result == WORKER_RESULT_CONFIRMATION) {
        controller[CONTROLLER_REMEMBERED_STATUS_WORD] = 0xFFFFFFFFu;
        if (status == WORKER_STATUS_UNFORMATTED_CONFIRMATION) {
            if (
                ((PointerResultFunction)
                    UPDATE_UNFORMATTED_CONFIRMATION_ADDRESS)((void *)ui) > 1u
            ) {
                resolve_worker(worker, 0u);
                return finish(controller, 1u);
            }
        } else if (status == WORKER_STATUS_NO_DATA_CONFIRMATION) {
            ui[2] = 1u;
            if ((input & live_state_two_accept_mask()) != 0u) {
                ((ValueFunction)PLAY_MENU_SOUND_ADDRESS)(SOUND_ACCEPT);
                if (read_word(ui, UI_MODAL_FLAG_OFFSET) == 0u) {
                    resolve_worker(worker, 1u);
                    ui[2] = 0u;
                } else {
                    resolve_worker(worker, 0u);
                    return finish(controller, 1u);
                }
            }
        }
    }

    return finish(controller, 0u);
}

ALWAYS_INLINE u32 enter_first_save_operation(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 mode
)
{
    write_word(ui, UI_MODE_OFFSET, mode);
    display_worker_status(ui, WORKER_STATUS_SCAN_COMPLETE);
    (void)read_word(worker, WORKER_RESULT_OFFSET);
    controller[CONTROLLER_SUBSTATE_WORD] = 3u;
    ((OnePointerFunction)PREPARE_RECORD_OPERATION_ADDRESS)((void *)ui);
    ui[4] = 1u;
    write_word(ui, UI_RECORD_OFFSET, 0u);
    controller[CONTROLLER_RECORD_WORD] = 0u;
    ((PointerValueFunction)REQUEST_RECORD_SAVE_ADDRESS)((void *)worker, 0u);
    write_word(ui, UI_MODAL_FLAG_OFFSET, 0u);
    controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_SAVE;
    return finish(controller, 0u);
}

ALWAYS_INLINE u32 is_state_four_error_status(u32 status)
{
    return
        status == 0x2Bu ||
        status == 0x19u ||
        status == 0x2Au ||
        status == 0x06u ||
        status == 0x05u;
}

ALWAYS_INLINE u32 update_state_four(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 mode
)
{
    u32 status;
    u32 result;

    write_word(ui, UI_MODE_OFFSET, mode);
    status = read_word(worker, WORKER_STATUS_OFFSET);
    if (status == 0u) {
        ((PointerValueFunction)REQUEST_RECORD_SAVE_ADDRESS)(
            (void *)worker,
            controller[CONTROLLER_RECORD_WORD]
        );
        return finish(controller, 0u);
    }
    if (status == 1u) {
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_ACKNOWLEDGMENT;
        return finish(controller, 0u);
    }

    display_worker_status(ui, status);
    result = read_word(worker, WORKER_RESULT_OFFSET);
    if (result == WORKER_RESULT_SUCCESS || result == WORKER_RESULT_FAILURE) {
        ui[4] = 0u;
        controller[CONTROLLER_REMEMBERED_STATUS_WORD] = 0xFFFFFFFFu;
        if (
            is_state_four_error_status(status) != 0u &&
            ((PointerValueResultFunction)UPDATE_ACKNOWLEDGMENT_ADDRESS)(
                (void *)ui,
                0u
            ) != 0u
        ) {
            resolve_worker(worker, 0u);
            ((OnePointerFunction)WORKER_PREAMBLE_ADDRESS)((void *)worker);
            controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_SCAN;
            controller[CONTROLLER_SUBSTATE_WORD] = 1u;
            controller[CONTROLLER_REMEMBERED_STATUS_WORD] = status;
        }
        return 0u;
    }

    display_worker_status(
        ui,
        mode == SAVE_LOAD_MODE_LOAD ? 0x0Fu : 0x15u
    );
    write_word(ui, UI_RECORD_OFFSET, 0u);
    if (mode == SAVE_LOAD_MODE_LOAD) {
        ((PointerValueFunction)REQUEST_RECORD_LOAD_ADDRESS)((void *)worker, 0u);
        write_word(ui, UI_MODAL_FLAG_OFFSET, 0u);
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_LOAD;
    } else {
        controller[CONTROLLER_RECORD_WORD] = 0u;
        ((PointerValueFunction)REQUEST_RECORD_SAVE_ADDRESS)((void *)worker, 0u);
        write_word(ui, UI_MODAL_FLAG_OFFSET, 0u);
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_SAVE;
    }
    return finish(controller, 0u);
}

ALWAYS_INLINE u32 update_save_confirmation(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 mode,
    u32 status
)
{
    u32 result;
    u32 confirmation;

    write_word(ui, UI_MODE_OFFSET, mode);
    display_worker_status(ui, status);
    result = read_word(worker, WORKER_RESULT_OFFSET);
    if (result != WORKER_RESULT_CONFIRMATION) {
        return finish(controller, 0u);
    }

    confirmation =
        ((PointerResultFunction)UPDATE_CONFIRMATION_ADDRESS)((void *)ui);
    if (confirmation == 2u) {
        resolve_worker(worker, 0u);
        return finish(controller, 1u);
    }
    if (confirmation == 1u) {
        resolve_worker(worker, 1u);
        controller[CONTROLLER_STATE_WORD] =
            CONTROLLER_STATE_OPERATION_RESULT;
    }
    return finish(controller, 0u);
}

ALWAYS_INLINE u32 update_load_confirmation(
    volatile u32 *controller,
    volatile u8 *ui,
    volatile u8 *worker,
    u32 mode
)
{
    u32 result;
    u32 confirmation;

    write_word(ui, UI_MODE_OFFSET, mode);
    display_worker_status(ui, WORKER_STATUS_LOAD_CONFIRMATION);
    result = read_word(worker, WORKER_RESULT_OFFSET);
    if (result != WORKER_RESULT_CONFIRMATION) {
        return finish(controller, 0u);
    }

    confirmation =
        ((PointerResultFunction)UPDATE_CONFIRMATION_ADDRESS)((void *)ui);
    if (confirmation == 2u) {
        resolve_worker(worker, 0u);
        ((OnePointerFunction)LOAD_MODE_PREAMBLE_ADDRESS)((void *)worker);
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_COMPLETE;
        write_word(ui, UI_MODAL_FLAG_OFFSET, 0u);
    } else if (confirmation == 1u) {
        resolve_worker(worker, 1u);
        controller[CONTROLLER_STATE_WORD] =
            CONTROLLER_STATE_OPERATION_RESULT;
    }
    return finish(controller, 0u);
}

SAVE_LOAD_SECTION(".text.save_load_display_only_first_save_update")
u32 display_only_first_save_update(void *controller_pointer, u32 mode)
{
    volatile u32 *controller = (volatile u32 *)controller_pointer;
    volatile u8 *ui =
        (volatile u8 *)controller[CONTROLLER_UI_WORD];
    volatile u8 *worker;
    u32 state = controller[CONTROLLER_STATE_WORD];
    u32 status;

    if (state == CONTROLLER_STATE_SCAN) {
        worker = memory_card_worker();
        status = read_word(worker, WORKER_STATUS_OFFSET);
        if (
            status == WORKER_STATUS_UNFORMATTED_INFO ||
            status == WORKER_STATUS_UNFORMATTED_CONFIRMATION ||
            status == WORKER_STATUS_NO_DATA_CONFIRMATION
        ) {
            return update_special_state_two(
                controller,
                ui,
                worker,
                mode,
                status,
                current_input()
            );
        }
        if (
            status == WORKER_STATUS_SCAN_COMPLETE &&
            controller[CONTROLLER_SUBSTATE_WORD] == 2u &&
            mode != SAVE_LOAD_MODE_LOAD
        ) {
            return enter_first_save_operation(
                controller,
                ui,
                worker,
                mode
            );
        }
    } else if (state == CONTROLLER_STATE_RECORD_LIST) {
        return update_state_four(
            controller,
            ui,
            memory_card_worker(),
            mode
        );
    } else if (state == CONTROLLER_STATE_SAVE) {
        worker = memory_card_worker();
        status = read_word(worker, WORKER_STATUS_OFFSET);
        if (
            status == WORKER_STATUS_SAVE_CONFIRMATION_A ||
            status == WORKER_STATUS_SAVE_CONFIRMATION_B
        ) {
            return update_save_confirmation(
                controller,
                ui,
                worker,
                mode,
                status
            );
        }
    } else if (state == CONTROLLER_STATE_LOAD) {
        worker = memory_card_worker();
        if (
            read_word(worker, WORKER_STATUS_OFFSET) ==
            WORKER_STATUS_LOAD_CONFIRMATION
        ) {
            return update_load_confirmation(controller, ui, worker, mode);
        }
    }

    return ((UpdateFunction)NATIVE_SAVE_LOAD_UPDATE_ADDRESS)(
        controller_pointer,
        mode
    );
}
