/* Route a Mode Select exit through a repeating opening movie. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define FRONT_END_MANAGER_POINTER_ADDRESS 0x00607600u
#define MOVIE_PLAYER_POINTER_ADDRESS 0x0060743Cu
#define OPENING_SEQUENCE_PLAYED_ADDRESS 0x006075C8u
#define OPENING_SEQUENCE_STATE_ADDRESS 0x006075CCu
#define SYSTEM_CONTEXT_POINTER_ADDRESS 0x006073FCu
#define TITLE_CONTROLLER_POINTER_ADDRESS 0x006075C4u

#define FRONT_END_UPDATE_ADDRESS 0x001E9980u
#define MOVIE_INPUT_UPDATE_ADDRESS 0x001056E0u
#define OPENING_UPDATE_ADDRESS 0x001DE6F0u
#define RESIDENT_ALLOCATE_ADDRESS 0x00117150u
#define TITLE_CONSTRUCT_ADDRESS 0x001DE900u
#define TITLE_CONTROLLER_UPDATE_ADDRESS 0x001DF690u
#define TITLE_DESTROY_ADDRESS 0x001DE970u
#define TRANSITION_CREATE_ADDRESS 0x001EB700u

#define MANAGER_PHASE_OFFSET 0x08u
#define MANAGER_CALLBACK_OFFSET 0x0Cu
#define MOVIE_STOP_REQUEST_OFFSET 0x34u
#define SYSTEM_NEW_INPUT_OFFSET 0x84u
#define TITLE_STATE_OFFSET 0x00u
#define TITLE_RESULT_OFFSET 0x08u
#define TITLE_TRANSITION_OFFSET 0x10u

#define MANAGER_PHASE_EXIT 5u
#define MODE_SELECT_CALLBACK 1u
#define FRONT_END_RESULT_TITLE 1
#define TITLE_RESULT_CONTINUE 2
#define TITLE_RESULT_OPENING -1
#define TITLE_CONTROLLER_SIZE 0x48u
#define TITLE_STATE_IDLE_TRANSITION 5u
#define TITLE_TRANSITION_KIND 0u
#define TITLE_TRANSITION_FRAMES 20u
#define OPENING_SEQUENCE_MOVIE 8u
#define OPENING_SEQUENCE_FINISHED 9u

#define STARTUP_SECTION(name) __attribute__((section(name), noinline))

typedef struct StartupOpeningReplayState {
    volatile u32 active;
    volatile u32 input_exit;
    volatile u32 title_handoff_started;
} StartupOpeningReplayState;

extern volatile StartupOpeningReplayState startup_opening_replay_state;

STARTUP_SECTION(".text.startup_manager_update")
s32 startup_manager_update(void)
{
    s32 (*update_front_end)(void) =
        (s32 (*)(void))FRONT_END_UPDATE_ADDRESS;
    volatile u8 *manager =
        *(volatile u8 **)FRONT_END_MANAGER_POINTER_ADDRESS;
    u32 mode_select_exit = 0u;
    s32 result;

    if (manager != (void *)0 &&
        *(volatile u32 *)(manager + MANAGER_PHASE_OFFSET) ==
            MANAGER_PHASE_EXIT &&
        *(volatile u32 *)(manager + MANAGER_CALLBACK_OFFSET) ==
            MODE_SELECT_CALLBACK) {
        mode_select_exit = 1u;
    }

    result = update_front_end();
    if (mode_select_exit != 0u && result == FRONT_END_RESULT_TITLE) {
        startup_opening_replay_state.active = 1u;
        startup_opening_replay_state.input_exit = 0u;
        startup_opening_replay_state.title_handoff_started = 0u;
    }

    return result;
}

STARTUP_SECTION(".text.startup_title_update")
s32 startup_title_update(void)
{
    void *(*allocate)(u32) =
        (void *(*)(u32))RESIDENT_ALLOCATE_ADDRESS;
    void *(*construct_title)(void *) =
        (void *(*)(void *))TITLE_CONSTRUCT_ADDRESS;
    s32 (*update_title_controller)(void *) =
        (s32 (*)(void *))TITLE_CONTROLLER_UPDATE_ADDRESS;
    void (*destroy_title)(void *, s32) =
        (void (*)(void *, s32))TITLE_DESTROY_ADDRESS;
    u32 (*create_transition)(u32, u32) =
        (u32 (*)(u32, u32))TRANSITION_CREATE_ADDRESS;
    volatile u8 **title_slot =
        (volatile u8 **)TITLE_CONTROLLER_POINTER_ADDRESS;
    volatile u8 *title = *title_slot;
    volatile u8 *system;
    u32 saved_input = 0u;
    s32 result = 0;

    if (startup_opening_replay_state.active == 0u) {
        return TITLE_RESULT_CONTINUE;
    }

    if (title == (void *)0) {
        title = (volatile u8 *)allocate(TITLE_CONTROLLER_SIZE);
        if (title != (void *)0) {
            title = (volatile u8 *)construct_title((void *)title);
        }
        *title_slot = title;
    }

    if (title == (void *)0) {
        return 0;
    }

    if (startup_opening_replay_state.title_handoff_started == 0u) {
        *(volatile u32 *)(title + TITLE_TRANSITION_OFFSET) =
            create_transition(
                TITLE_TRANSITION_KIND,
                TITLE_TRANSITION_FRAMES
            );
        *(volatile u32 *)(title + TITLE_STATE_OFFSET) =
            TITLE_STATE_IDLE_TRANSITION;
        startup_opening_replay_state.title_handoff_started = 1u;
    }

    system = *(volatile u8 **)SYSTEM_CONTEXT_POINTER_ADDRESS;
    if (system != (void *)0) {
        saved_input = *(volatile u32 *)(system + SYSTEM_NEW_INPUT_OFFSET);
        *(volatile u32 *)(system + SYSTEM_NEW_INPUT_OFFSET) = 0u;
    }

    result = update_title_controller((void *)title);

    if (system != (void *)0) {
        *(volatile u32 *)(system + SYSTEM_NEW_INPUT_OFFSET) = saved_input;
    }

    if (result != 0) {
        destroy_title((void *)title, 1);
        *title_slot = (volatile u8 *)0;
        if (result == TITLE_RESULT_OPENING) {
            *(volatile u16 *)OPENING_SEQUENCE_PLAYED_ADDRESS = 1u;
            *(volatile u16 *)OPENING_SEQUENCE_STATE_ADDRESS =
                OPENING_SEQUENCE_MOVIE;
        }
    }

    return result;
}

STARTUP_SECTION(".text.startup_movie_input")
void startup_movie_input(void)
{
    void (*update_movie_input)(void) =
        (void (*)(void))MOVIE_INPUT_UPDATE_ADDRESS;
    volatile u8 *player =
        *(volatile u8 **)MOVIE_PLAYER_POINTER_ADDRESS;
    u8 stop_requested = 0u;

    if (player != (void *)0) {
        stop_requested = player[MOVIE_STOP_REQUEST_OFFSET];
    }

    update_movie_input();

    player = *(volatile u8 **)MOVIE_PLAYER_POINTER_ADDRESS;
    if (startup_opening_replay_state.active != 0u &&
        player != (void *)0 &&
        stop_requested == 0u &&
        player[MOVIE_STOP_REQUEST_OFFSET] != 0u) {
        startup_opening_replay_state.input_exit = 1u;
    }
}

STARTUP_SECTION(".text.startup_opening_update")
s32 startup_opening_update(void)
{
    s32 (*update_opening)(void) =
        (s32 (*)(void))OPENING_UPDATE_ADDRESS;
    volatile u16 *sequence_state =
        (volatile u16 *)OPENING_SEQUENCE_STATE_ADDRESS;
    s32 result = update_opening();

    if (startup_opening_replay_state.active == 0u) {
        return result;
    }

    if (startup_opening_replay_state.input_exit != 0u) {
        if (result == 1) {
            startup_opening_replay_state.active = 0u;
            startup_opening_replay_state.input_exit = 0u;
            startup_opening_replay_state.title_handoff_started = 0u;
        }
        return result;
    }

    if (*sequence_state == OPENING_SEQUENCE_FINISHED || result == 1) {
        *sequence_state = OPENING_SEQUENCE_MOVIE;
        return 0;
    }

    return result;
}
