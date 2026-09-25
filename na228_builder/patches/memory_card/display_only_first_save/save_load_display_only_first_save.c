/* Keep only record zero in the visible native Save/Load controller. */
#include "../save_load.h"

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

SAVE_LOAD_SECTION(".text.save_load_center_empty")
void save_load_center_empty(volatile u8 *ui, SaveSlotText *label, SaveSlotText *time)
{
    volatile u8 *window = *(volatile u8 **)(ui + 0x20u);
    const u8 *text = *(const u8 *volatile *)0x0060302Cu;
    s32 (*measure)(const u8 *, s32) = (s32 (*)(const u8 *, s32))0x003798E0u;
    float width = *(volatile float *)(window + 0x0Cu) -
        2.0f * (float)*(volatile s16 *)(window + 0x30u);
    float height = *(volatile float *)(window + 0x10u) -
        2.0f * (float)*(volatile s16 *)(window + 0x32u);
    u32 occupied = 0u;
    u32 index;

    label->text = text;
    time->text = (const u8 *)0x00603038u;
    label->x = (width - (float)measure(text, 0)) * 0.5f;
    label->y = (height - 20.0f) * 0.5f;

    /* The selected row slides to -24. Anchor its resting position at the
     * center; leave the live offset to the native renderer exactly once. */
    for (index = 0u; index < 3u; index++) {
        occupied += **(volatile u8 **)(ui + 0x30u + index * 4u);
    }
    if (*(volatile u32 *)(ui + 0x10u) == 0u &&
        !(*(volatile u32 *)(ui + 8u) == 1u && occupied == 0u)) {
        label->x += 24.0f;
    }
}
