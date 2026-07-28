/*
 * Accepted Ninja Song ASCII number formatter.
 *
 * The native caller ABI supplies the output pointer in a3 and the padding
 * mode as the fifth integer argument in t0 under the PS2 EE EABI.
 */

typedef unsigned int u32;
typedef signed int s32;

#define FONT_NUMERIC_SECTION(name) \
    __attribute__((section(name), noinline))

extern int font_numeric_format_decimal(char *destination, s32 value);

FONT_NUMERIC_SECTION(".text.font_ninja_song_ascii_number")
int font_ninja_song_ascii_number(
    u32 unused,
    s32 value,
    s32 width,
    char *destination,
    s32 mode
) {
    char temporary[16];
    int length;
    int padding;
    char fill = ' ';
    int index;

    (void)unused;
    length = font_numeric_format_decimal(temporary, value);
    padding = width - length;
    if (mode != 1 && padding > 0) {
        if (mode == 2) {
            fill = '0';
        }
        while (padding > 0) {
            *destination = fill;
            destination += 1;
            padding -= 1;
        }
    }

    for (index = 0; index <= length; index += 1) {
        destination[index] = temporary[index];
    }
    return length;
}
