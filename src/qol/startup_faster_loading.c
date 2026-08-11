/* Defer RPG and player voice indexes until their first playback. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define AUDIO_MANAGER_POINTER_ADDRESS 0x00607558u

#define INITIALIZE_AUDIO_ARCHIVES_ADDRESS 0x001D6550u
#define LOAD_AUDIO_INDEX_ADDRESS 0x001D6C70u
#define PLAY_AUDIO_CLIP_ADDRESS 0x001D97D0u

#define CREATE_SEMAPHORE_ADDRESS 0x0015DCE0u
#define SIGNAL_SEMAPHORE_ADDRESS 0x0015DD00u
#define WAIT_SEMAPHORE_ADDRESS 0x0015DD20u

#define RPG_TABLE_ADDRESS 0x003FDD50u
#define PLAYER_TABLE_ADDRESS 0x003FDFF0u
#define RPG_ARCHIVE_HANDLE_ADDRESS 0x00602C4Cu
#define PLAYER_ARCHIVE_HANDLE_ADDRESS 0x00602C4Eu

#define RPG_COUNT_OFFSET 0x704u
#define PLAYER_COUNT_OFFSET 0x708u
#define RPG_BUFFER_POINTERS_OFFSET 0x17Cu
#define PLAYER_BUFFER_POINTERS_OFFSET 0x40Cu
#define BANK_RECORD_SIZE 8u
#define BANK_BITSET_WORDS 3u

#define AUDIO_CATEGORY_RPG 2u
#define AUDIO_CATEGORY_PLAYER 3u

#define SEMAPHORE_EAGER_FALLBACK (-2)

#define STARTUP_FASTER_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))

typedef struct SemaphoreParameters {
    s32 count;
    s32 maximum_count;
    s32 initial_count;
    s32 wait_threads;
    u32 attributes;
    u32 option;
} SemaphoreParameters;

typedef struct StartupVoiceLoadingState {
    volatile s32 semaphore_id;
    volatile u32 rpg_loaded[BANK_BITSET_WORDS];
    volatile u32 player_loaded[BANK_BITSET_WORDS];
} StartupVoiceLoadingState;

extern volatile StartupVoiceLoadingState startup_voice_loading_state;

STARTUP_FASTER_LOADING_SECTION(".text.startup_voice_loading_initialize")
void startup_voice_loading_initialize(void)
{
    void (*initialize_archives)(void) =
        (void (*)(void))INITIALIZE_AUDIO_ARCHIVES_ADDRESS;
    s32 (*create_semaphore)(SemaphoreParameters *) =
        (s32 (*)(SemaphoreParameters *))CREATE_SEMAPHORE_ADDRESS;
    volatile u8 *manager =
        *(volatile u8 **)AUDIO_MANAGER_POINTER_ADDRESS;
    SemaphoreParameters parameters;
    u32 rpg_count;
    u32 player_count;
    s32 semaphore_id;

    parameters.count = 0;
    parameters.maximum_count = 1;
    parameters.initial_count = 1;
    parameters.wait_threads = 0;
    parameters.attributes = 0u;
    parameters.option = 0u;

    if (manager == (volatile u8 *)0) {
        initialize_archives();
        startup_voice_loading_state.semaphore_id = SEMAPHORE_EAGER_FALLBACK;
        return;
    }

    semaphore_id = create_semaphore(&parameters);
    if (semaphore_id < 0) {
        initialize_archives();
        startup_voice_loading_state.semaphore_id = SEMAPHORE_EAGER_FALLBACK;
        return;
    }

    rpg_count = *(volatile u32 *)(manager + RPG_COUNT_OFFSET);
    player_count = *(volatile u32 *)(manager + PLAYER_COUNT_OFFSET);
    *(volatile u32 *)(manager + RPG_COUNT_OFFSET) = 0u;
    *(volatile u32 *)(manager + PLAYER_COUNT_OFFSET) = 0u;

    initialize_archives();

    *(volatile u32 *)(manager + RPG_COUNT_OFFSET) = rpg_count;
    *(volatile u32 *)(manager + PLAYER_COUNT_OFFSET) = player_count;
    startup_voice_loading_state.semaphore_id = semaphore_id;
}

STARTUP_FASTER_LOADING_SECTION(".text.startup_voice_loading_ensure")
static u32 startup_voice_loading_ensure(u32 category, u32 bank)
{
    void (*load_index)(void *, u32, u32, u32, void *) =
        (void (*)(void *, u32, u32, u32, void *))LOAD_AUDIO_INDEX_ADDRESS;
    s32 (*wait_semaphore)(s32) =
        (s32 (*)(s32))WAIT_SEMAPHORE_ADDRESS;
    s32 (*signal_semaphore)(s32) =
        (s32 (*)(s32))SIGNAL_SEMAPHORE_ADDRESS;
    volatile u8 *manager =
        *(volatile u8 **)AUDIO_MANAGER_POINTER_ADDRESS;
    volatile u32 *loaded;
    volatile u8 *table;
    u32 count;
    u32 archive_handle;
    u32 buffer_offset;
    u32 word;
    u32 mask;
    void *buffer;
    s32 semaphore_id;

    semaphore_id = startup_voice_loading_state.semaphore_id;
    if (semaphore_id == SEMAPHORE_EAGER_FALLBACK) {
        return 1u;
    }
    if (semaphore_id < 0 || manager == (volatile u8 *)0) {
        return 0u;
    }

    if (category == AUDIO_CATEGORY_RPG) {
        loaded = startup_voice_loading_state.rpg_loaded;
        table = (volatile u8 *)RPG_TABLE_ADDRESS;
        count = *(volatile u32 *)(manager + RPG_COUNT_OFFSET);
        archive_handle = *(volatile u16 *)RPG_ARCHIVE_HANDLE_ADDRESS;
        buffer_offset = RPG_BUFFER_POINTERS_OFFSET;
    } else if (category == AUDIO_CATEGORY_PLAYER) {
        loaded = startup_voice_loading_state.player_loaded;
        table = (volatile u8 *)PLAYER_TABLE_ADDRESS;
        count = *(volatile u32 *)(manager + PLAYER_COUNT_OFFSET);
        archive_handle = *(volatile u16 *)PLAYER_ARCHIVE_HANDLE_ADDRESS;
        buffer_offset = PLAYER_BUFFER_POINTERS_OFFSET;
    } else {
        return 0u;
    }

    if (bank >= count || bank >= BANK_BITSET_WORDS * 32u) {
        return 0u;
    }
    word = bank >> 5;
    mask = 1u << (bank & 31u);
    if ((loaded[word] & mask) != 0u) {
        return 1u;
    }
    if (wait_semaphore(semaphore_id) < 0) {
        return 0u;
    }

    if ((loaded[word] & mask) == 0u) {
        buffer = *(void * volatile *)(
            manager + buffer_offset + bank * BANK_RECORD_SIZE
        );
        load_index(
            (void *)manager,
            *(volatile u16 *)(table + bank * BANK_RECORD_SIZE),
            archive_handle,
            bank,
            buffer
        );
        loaded[word] |= mask;
    }
    signal_semaphore(semaphore_id);
    return 1u;
}

STARTUP_FASTER_LOADING_SECTION(".text.startup_voice_loading_rpg")
u32 startup_voice_loading_rpg(
    u32 bank,
    u32 clip,
    u32 channel,
    u32 category
)
{
    u32 (*play_clip)(u32, u32, u32, u32) =
        (u32 (*)(u32, u32, u32, u32))PLAY_AUDIO_CLIP_ADDRESS;

    if (category == AUDIO_CATEGORY_RPG &&
        startup_voice_loading_ensure(category, bank) == 0u) {
        return 0xFFFFFFFFu;
    }
    return play_clip(bank, clip, channel, category);
}

STARTUP_FASTER_LOADING_SECTION(".text.startup_voice_loading_player")
u32 startup_voice_loading_player(
    u32 bank,
    u32 clip,
    u32 channel,
    u32 category
)
{
    u32 (*play_clip)(u32, u32, u32, u32) =
        (u32 (*)(u32, u32, u32, u32))PLAY_AUDIO_CLIP_ADDRESS;

    if (category == AUDIO_CATEGORY_PLAYER &&
        startup_voice_loading_ensure(category, bank) == 0u) {
        return 0xFFFFFFFFu;
    }
    return play_clip(bank, clip, channel, category);
}
