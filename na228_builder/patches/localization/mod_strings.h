#ifndef NA228_MOD_STRINGS_H
#define NA228_MOD_STRINGS_H

extern const unsigned short mod_number_glyphs[128];

/* The builder encodes {0} as byte 1; native dialogs use NUL-separated lines. */
static __attribute__((always_inline)) inline unsigned char *mod_string_format(
    unsigned char *output, unsigned int capacity,
    const unsigned char *text, const unsigned char *value
)
{
    unsigned char *end = output + (capacity != 0u ? capacity - 1u : 0u);
    if (capacity == 0u) return output;
    while (*text != 0u && output < end) {
        if (*text == 1u) {
            const unsigned char *insert = value;
            unsigned int numeric = 0u;
            while (*insert != 0u) {
                if (*insert >= '0' && *insert <= '9') numeric = 1u;
                ++insert;
            }
            insert = value;
            while (*insert != 0u && output < end) {
                unsigned int glyph = *insert++;
                if (numeric != 0u && glyph < 128u) glyph = mod_number_glyphs[glyph];
                if (glyph > 255u) {
                    if (end - output < 2) break;
                    *output++ = (unsigned char)(glyph >> 8);
                }
                *output++ = (unsigned char)glyph;
            }
            ++text;
        } else {
            *output++ = *text == '\n' ? 0u : *text;
            ++text;
        }
    }
    *output = 0u;
    return output;
}

#endif
