/*
 * Present NA2's existing main-menu loading screen while the boot loaders run.
 * The ordinary menu path retains ownership once startup state 0 completes.
 */

typedef unsigned int u32;

#define STARTUP_STATE_POINTER_ADDRESS 0x006075C0u

#define LOADING_SYSTEM_INITIALIZE_ADDRESS 0x00203B50u
#define LOADING_RESOURCE_OPEN_ADDRESS 0x001FFC30u
#define LOADING_SCREEN_BEGIN_ADDRESS 0x002005B0u
#define LOADING_SYSTEM_UPDATE_ADDRESS 0x00203C50u
#define LOADING_PROGRESS_QUERY_ADDRESS 0x001CFAE0u

#define STARTUP_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

extern volatile u32 startup_loading_started;

STARTUP_LOADING_SECTION(".text.startup_loading_hook")
u32 startup_loading_hook(void)
{
    void (*initialize_loading_system)(void) =
        (void (*)(void))LOADING_SYSTEM_INITIALIZE_ADDRESS;
    void (*open_loading_resource)(int, int) =
        (void (*)(int, int))LOADING_RESOURCE_OPEN_ADDRESS;
    void (*begin_loading_screen)(int, int) =
        (void (*)(int, int))LOADING_SCREEN_BEGIN_ADDRESS;
    void (*update_loading_system)(void) =
        (void (*)(void))LOADING_SYSTEM_UPDATE_ADDRESS;

    if (startup_loading_started == 0u) {
        initialize_loading_system();
        open_loading_resource(-1, 0);
        begin_loading_screen(0, 1);
        startup_loading_started = 1u;
    }

    update_loading_system();
    return 1u;
}

STARTUP_LOADING_SECTION(".text.startup_loading_progress")
float startup_loading_progress(void)
{
    volatile u32 *startup_state =
        *(volatile u32 **)STARTUP_STATE_POINTER_ADDRESS;
    float (*query_native_progress)(void) =
        (float (*)(void))LOADING_PROGRESS_QUERY_ADDRESS;

    if (startup_state != (volatile u32 *)0 && startup_state[0] == 0u) {
        return 0.0f;
    }
    return query_native_progress();
}
