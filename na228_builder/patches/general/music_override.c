/* Select existing streamed-music tracks for front-end menus. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned int u32;

#define AUDIO_CONTROL_POINTER_ADDRESS 0x0060755Cu
#define AUDIO_CURRENT_TRACK_OFFSET 0xC0u
#define AUDIO_STOP_ADDRESS 0x001D9760u
#define AUDIO_SELECT_ADDRESS 0x001D95D0u

#define MUSIC_OVERRIDE_SECTION(name) \
    __attribute__((section(name), noinline))

typedef void (*AudioStop)(u32 channel);
typedef void (*AudioSelect)(u32 track, u32 channel);

MUSIC_OVERRIDE_SECTION(".text.general_music_override_select")
void general_music_override_select(u32 track, u32 channel)
{
    volatile u8 *control =
        *(volatile u8 **)AUDIO_CONTROL_POINTER_ADDRESS;

    if (*(volatile s32 *)(control + AUDIO_CURRENT_TRACK_OFFSET) !=
        (s32)track) {
        ((AudioStop)AUDIO_STOP_ADDRESS)(channel);
    }
    ((AudioSelect)AUDIO_SELECT_ADDRESS)(track, channel);
}
