/*
 * Accepted native secondary-font metric lookup and draw adjustment.
 *
 * The packed 14x20 metric rows live in empty primary-map value slots. These
 * entries decode the same four nibbles for both measurement and drawing while
 * leaving final placement and hooks to the runtime injector/payload builder.
 */

typedef unsigned char u8;
typedef signed short s16;
typedef unsigned short u16;
typedef unsigned int u32;

#define FONT_GLYPH_SECTION(name) \
    __attribute__((section(name), noinline))

#define FONT_PRIMARY_RESOURCE_OFFSET 0x64u
#define FONT_PRIMARY_MAP_OFFSET 0x14u
#define FONT_VERTICAL_MODE_OFFSET 0x54u
#define FONT_HORIZONTAL_POSITION_OFFSET 0x1Cu
#define FONT_VERTICAL_POSITION_OFFSET 0x20u
#define FONT_TRAILING_TRIM_OFFSET 0x38u
#define FONT_HORIZONTAL_SCALE_ADDRESS 0x0060737Cu
#define FONT_SECONDARY_CELL_COUNT 123u

static __attribute__((always_inline)) inline u8 *
font_glyph_bytes(void *value)
{
    return (u8 *)value;
}

static __attribute__((always_inline)) inline u16
font_glyph_packed_metric(void *context, u32 cell, u32 *available)
{
    u8 *resource = *(u8 **)(font_glyph_bytes(context) +
                            FONT_PRIMARY_RESOURCE_OFFSET);
    u8 *cursor;

    if (resource == (u8 *)0) {
        *available = 0u;
        return 0u;
    }
    cursor = *(u8 **)(resource + FONT_PRIMARY_MAP_OFFSET);
    if (cursor == (u8 *)0) {
        *available = 0u;
        return 0u;
    }

    for (;;) {
        while (*(s16 *)cursor != (s16)-1) {
            cursor += 4;
        }
        if (cell == 0u) {
            *available = 1u;
            return *(u16 *)(cursor + 2);
        }
        cell -= 1u;
        cursor += 4;
    }
}

FONT_GLYPH_SECTION(".text.font.glyph.metric.lookup")
u32 font_glyph_metric_lookup(void *context, u32 value)
{
    u32 available;
    u32 cell = value < 0xA0u ? value - 0x20u : value - 0x23u;
    u16 packed;

    if (cell >= FONT_SECONDARY_CELL_COUNT) {
        cell = 0u;
    }
    packed = font_glyph_packed_metric(context, cell, &available);
    if (available == 0u) {
        return 0u;
    }
    return ((u32)(packed & 0x000Fu)) |
           ((u32)(packed & 0x00F0u) << 4) |
           ((u32)(packed & 0x0F00u) << 8) |
           ((u32)(packed & 0xF000u) << 12);
}

FONT_GLYPH_SECTION(".text.font.glyph.metric.apply")
void font_glyph_metric_apply(void *context, u32 cell, u32 flags)
{
    u32 available;
    u16 packed = font_glyph_packed_metric(context, cell, &available);
    u32 leading;
    u32 trailing;
    float *position;
    float amount;

    if (available == 0u) {
        *(u32 *)(font_glyph_bytes(context) +
                 FONT_TRAILING_TRIM_OFFSET) = 0u;
        return;
    }

    leading = packed & 0x000Fu;
    trailing = (packed >> 8) & 0x000Fu;
    if ((flags & 4u) != 0u) {
        position = (float *)(font_glyph_bytes(context) +
                             FONT_VERTICAL_POSITION_OFFSET);
        if (*(u8 *)(font_glyph_bytes(context) +
                    FONT_VERTICAL_MODE_OFFSET) == 0u) {
            leading = (packed >> 4) & 0x000Fu;
            trailing = (packed >> 12) & 0x000Fu;
        }
        amount = (float)leading;
    } else {
        position = (float *)(font_glyph_bytes(context) +
                             FONT_HORIZONTAL_POSITION_OFFSET);
        amount = (float)leading *
                 *(volatile float *)FONT_HORIZONTAL_SCALE_ADDRESS;
    }

    *position -= amount;
    *(u32 *)(font_glyph_bytes(context) +
             FONT_TRAILING_TRIM_OFFSET) = trailing;
}
