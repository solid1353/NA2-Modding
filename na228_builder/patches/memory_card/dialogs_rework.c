/* Shared memory-card confirmation flow, independent of slot count. */
#include "save_load.h"

extern const UpdateFunction dialogs_rework_next_update;

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
        write_word(ui, UI_MESSAGE_OFFSET, 0u);
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
                controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_CLOSING;
                return finish(controller, 0u);
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
                    controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_CLOSING;
                    return finish(controller, 0u);
                }
            }
        }
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
        controller[CONTROLLER_STATE_WORD] = CONTROLLER_STATE_CLOSING;
        return finish(controller, 0u);
    }
    if (confirmation == 1u) {
        resolve_worker(worker, 1u);
        controller[CONTROLLER_STATE_WORD] =
            CONTROLLER_STATE_OPERATION_RESULT;
    }
    return finish(controller, 0u);
}

SAVE_LOAD_SECTION(".text.dialogs_rework_update")
u32 dialogs_rework_update(void *controller_pointer, u32 mode)
{
    volatile u32 *controller = (volatile u32 *)controller_pointer;
    volatile u8 *ui = (volatile u8 *)controller[CONTROLLER_UI_WORD];
    volatile u8 *worker;
    u32 state = controller[CONTROLLER_STATE_WORD];
    u32 status;

    if (state != CONTROLLER_STATE_SCAN && state != CONTROLLER_STATE_SAVE) {
        return dialogs_rework_next_update(controller_pointer, mode);
    }
    worker = memory_card_worker();
    status = read_word(worker, WORKER_STATUS_OFFSET);

    if (state == CONTROLLER_STATE_SCAN &&
        (status == WORKER_STATUS_UNFORMATTED_INFO ||
         status == WORKER_STATUS_UNFORMATTED_CONFIRMATION ||
         status == WORKER_STATUS_NO_DATA_CONFIRMATION)) {
        return update_special_state_two(
            controller, ui, worker, mode, status, current_input());
    }
    if (state == CONTROLLER_STATE_SAVE &&
        (status == WORKER_STATUS_SAVE_CONFIRMATION_A ||
         status == WORKER_STATUS_SAVE_CONFIRMATION_B)) {
        return update_save_confirmation(controller, ui, worker, mode, status);
    }
    return dialogs_rework_next_update(controller_pointer, mode);
}
