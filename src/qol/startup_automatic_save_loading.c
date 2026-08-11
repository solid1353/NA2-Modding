/* Silently drive the native first-record load before the main-menu loader. */

typedef unsigned char u8;
typedef unsigned int u32;

#define MEMORY_CARD_WORKER_POINTER_ADDRESS 0x006075F4u

#define LOAD_MODE_PREAMBLE_ADDRESS 0x001E1D80u
#define LOAD_MODE_PREPARE_ADDRESS 0x001D9600u
#define SCAN_MEMORY_CARD_ADDRESS 0x001E1DA0u
#define REQUEST_RECORD_LOAD_ADDRESS 0x001E1E10u
#define RESOLVE_WORKER_RESULT_ADDRESS 0x001E3120u

#define CONTROLLER_PHASE_WORD 2u

#define WORKER_RECORD_ZERO_PRESENT_OFFSET 0x00u
#define WORKER_STATUS_OFFSET 0x4Cu
#define WORKER_RESULT_OFFSET 0x50u
#define WORKER_MODE_OFFSET 0x54u

#define WORKER_STATUS_BUSY 0x04u
#define WORKER_STATUS_SCAN_COMPLETE 0x01u
#define WORKER_STATUS_LOAD_CONFIRMATION 0x10u
#define WORKER_STATUS_READING_PORT_ZERO 0x11u
#define WORKER_STATUS_READING_PORT_ONE 0x12u
#define WORKER_STATUS_LOAD_COMPLETE 0x13u

#define WORKER_RESULT_NONE 0u
#define WORKER_RESULT_SUCCESS 1u
#define WORKER_RESULT_CONFIRMATION 3u

#define CONTINUE_PENDING 0u
#define CONTINUE_LOADED 1u
#define CONTINUE_WITHOUT_LOAD 2u

#define AUTOMATIC_SAVE_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

AUTOMATIC_SAVE_LOADING_SECTION(".text.startup_automatic_save_loading")
u32 startup_automatic_save_loading(void *controller, u32 mode)
{
    void (*load_mode_preamble)(void *) =
        (void (*)(void *))LOAD_MODE_PREAMBLE_ADDRESS;
    void (*prepare_load_mode)(u32) =
        (void (*)(u32))LOAD_MODE_PREPARE_ADDRESS;
    void (*scan_memory_card)(void *, u32) =
        (void (*)(void *, u32))SCAN_MEMORY_CARD_ADDRESS;
    void (*request_record_load)(void *, u32) =
        (void (*)(void *, u32))REQUEST_RECORD_LOAD_ADDRESS;
    void (*resolve_worker_result)(void *, u32) =
        (void (*)(void *, u32))RESOLVE_WORKER_RESULT_ADDRESS;
    volatile u32 *controller_words = (volatile u32 *)controller;
    volatile u8 *worker =
        *(volatile u8 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
    u32 phase;
    u32 status;
    u32 result;

    if (controller == (void *)0 || mode != 1u || worker == (volatile u8 *)0) {
        return CONTINUE_WITHOUT_LOAD;
    }

    phase = controller_words[CONTROLLER_PHASE_WORD];
    if (phase == 0u) {
        *(volatile u32 *)(worker + WORKER_MODE_OFFSET) = 1u;
        load_mode_preamble((void *)worker);
        prepare_load_mode(0u);
        scan_memory_card((void *)worker, 0u);
        controller_words[CONTROLLER_PHASE_WORD] = 1u;
        return CONTINUE_PENDING;
    }

    status = *(volatile u32 *)(worker + WORKER_STATUS_OFFSET);
    result = *(volatile u32 *)(worker + WORKER_RESULT_OFFSET);

    if (phase == 1u) {
        if (status == WORKER_STATUS_BUSY) {
            return CONTINUE_PENDING;
        }
        if (status != WORKER_STATUS_SCAN_COMPLETE ||
            result != WORKER_RESULT_NONE ||
            worker[WORKER_RECORD_ZERO_PRESENT_OFFSET] == 0u) {
            return CONTINUE_WITHOUT_LOAD;
        }

        request_record_load((void *)worker, 0u);
        controller_words[CONTROLLER_PHASE_WORD] = 2u;
        return CONTINUE_PENDING;
    }

    if (phase == 2u) {
        if (status == WORKER_STATUS_BUSY) {
            return CONTINUE_PENDING;
        }
        if (status == WORKER_STATUS_LOAD_CONFIRMATION &&
            result != WORKER_RESULT_CONFIRMATION) {
            return CONTINUE_PENDING;
        }
        if (status != WORKER_STATUS_LOAD_CONFIRMATION) {
            return CONTINUE_WITHOUT_LOAD;
        }

        resolve_worker_result((void *)worker, 1u);
        controller_words[CONTROLLER_PHASE_WORD] = 3u;
        return CONTINUE_PENDING;
    }

    if (phase == 3u) {
        if (status == WORKER_STATUS_BUSY ||
            status == WORKER_STATUS_READING_PORT_ZERO ||
            status == WORKER_STATUS_READING_PORT_ONE) {
            return CONTINUE_PENDING;
        }
        if (status == WORKER_STATUS_LOAD_COMPLETE) {
            if (result == WORKER_RESULT_SUCCESS) {
                return CONTINUE_LOADED;
            }
            return CONTINUE_PENDING;
        }
    }

    return CONTINUE_WITHOUT_LOAD;
}
