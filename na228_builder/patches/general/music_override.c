/* Select existing streamed-music tracks for front-end menus. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned int u32;

#define AUDIO_CONTROL_POINTER_ADDRESS 0x0060755Cu
#define AUDIO_MASTER_VOLUME_OFFSET 0x00u
#define AUDIO_CURRENT_TRACK_OFFSET 0xC0u
#define AUDIO_STOP_ADDRESS 0x001D9760u
#define AUDIO_SELECT_ADDRESS 0x001D95D0u
#define AUDIO_VOLUME_ADDRESS 0x001D9D40u

#define AUDIO_GAIN_REFERENCE 300
#define AUDIO_GAIN_LINEAR_MINIMUM -299
#define AUDIO_GAIN_SILENCE -960
#define CHARACTER_SELECT_TRACK 68u
#define CHARACTER_SELECT_GAIN -40

#define MUSIC_OVERRIDE_SECTION(name) \
    __attribute__((section(name), noinline))

typedef void (*AudioStop)(u32 channel);
typedef void (*AudioSelect)(u32 track, u32 channel);
typedef void (*AudioVolume)(u32 channel, s32 gain);

MUSIC_OVERRIDE_SECTION(".text.general_music_override_select")
void general_music_override_select(u32 track, u32 channel)
{
    volatile u8 *control =
        *(volatile u8 **)AUDIO_CONTROL_POINTER_ADDRESS;
    s32 gain;

    if (*(volatile s32 *)(control + AUDIO_CURRENT_TRACK_OFFSET) !=
        (s32)track) {
        ((AudioStop)AUDIO_STOP_ADDRESS)(channel);
    }
    ((AudioSelect)AUDIO_SELECT_ADDRESS)(track, channel);

    if (track == CHARACTER_SELECT_TRACK) {
        gain = ((CHARACTER_SELECT_GAIN + AUDIO_GAIN_REFERENCE) *
                *(volatile s32 *)(control + AUDIO_MASTER_VOLUME_OFFSET)) >> 8;
        gain -= AUDIO_GAIN_REFERENCE;
        if (gain < AUDIO_GAIN_LINEAR_MINIMUM) {
            gain = AUDIO_GAIN_SILENCE;
        }
        ((AudioVolume)AUDIO_VOLUME_ADDRESS)(channel, gain);
    }
}
