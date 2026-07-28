/*
 * Accepted ASCII numeric formatting for Font-owned dynamic fields.
 *
 * The Ninja Song caller supplies the output pointer in a3 and the padding
 * mode as the fifth integer argument in t0 under the PS2 EE EABI. Save/Load
 * and Battle Settings use typed entries so their behavior lives in C while
 * native call sites retain only argument setup and hooks. The runtime
 * injector compiles this unit into address-independent fragments during
 * normal composition.
 */

typedef unsigned int u32;
typedef signed int s32;

#define FONT_NUMERIC_SECTION(name) \
    __attribute__((section(name), noinline))

extern int font_numeric_format_decimal(char *destination, s32 value);
extern int font_numeric_format_two_decimal(char *destination, s32 value);

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

FONT_NUMERIC_SECTION(".text.font_save_load_day")
s32 font_save_load_day(const unsigned char *record, char *destination) {
    unsigned int year;

    year = (unsigned int)record[0x0e]
        | ((unsigned int)record[0x0f] << 8);
    font_numeric_format_two_decimal(destination, (s32)record[0x0c]);
    return (s32)year;
}

FONT_NUMERIC_SECTION(".text.font_save_load_two")
int font_save_load_two(s32 value, char *destination) {
    return font_numeric_format_two_decimal(destination, value);
}

FONT_NUMERIC_SECTION(".text.font_save_load_year")
int font_save_load_year(s32 value, char *destination) {
    return font_numeric_format_decimal(destination, value);
}

FONT_NUMERIC_SECTION(".text.font_save_load_hour")
int font_save_load_hour(s32 value, char *destination) {
    if (value >= 100) {
        value = 99;
    }
    return font_numeric_format_two_decimal(destination, value);
}

FONT_NUMERIC_SECTION(".text.font_battle_settings_time")
int font_battle_settings_time(s32 value, char *destination) {
    return font_numeric_format_decimal(destination, value);
}
