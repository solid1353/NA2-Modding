/* Official NUN5 English Victory character-name rectangles. */

typedef unsigned short u16;
typedef unsigned int u32;

typedef struct VictoryNameWidths {
    u16 first;
    u16 second;
} VictoryNameWidths;

typedef struct VictoryRectangle {
    u16 u;
    u16 v;
    u16 width;
    u16 height;
    u32 reserved_08;
    u32 local_y_bits;
    u32 reserved_10;
    u32 reserved_14;
} VictoryRectangle;

typedef char VictoryRectangleSize[
    sizeof(VictoryRectangle) == 24u ? 1 : -1
];

#define VICTORY_SECTION(name) \
    __attribute__((section(name), noinline))
#define VICTORY_DATA_SECTION(name) \
    __attribute__((section(name), aligned(4)))

#define VICTORY_NAME_CHARACTER_COUNT 94u
#define VICTORY_NAME_FRAME_COUNT 2u
#define VICTORY_NAME_HEIGHT 62u
#define VICTORY_NAME_LOCAL_Y_BITS 0xC1F80000u

static const VictoryNameWidths victory_name_widths[
    VICTORY_NAME_CHARACTER_COUNT
] VICTORY_DATA_SECTION(".rodata.localization_ui_victory_name_widths") = {
    {  0,   0}, /* 00 */
    {156, 192}, /* 01 */
    {164, 160}, /* 02 */
    {120,  88}, /* 03 */
    {192, 204}, /* 04 */
    {236, 112}, /* 05 */
    { 92, 148}, /* 06 */
    {160, 168}, /* 07 */
    {  0,   0}, /* 08 */
    {  0,   0}, /* 09 */
    {120,   0}, /* 10 */
    {168, 204}, /* 11 */
    {148, 148}, /* 12 */
    {160,   0}, /* 13 */
    {120, 196}, /* 14 */
    { 76, 228}, /* 15 */
    {104, 176}, /* 16 */
    {132, 204}, /* 17 */
    {184,   0}, /* 18 */
    {156,   0}, /* 19 */
    {  0,   0}, /* 20 */
    {  0,   0}, /* 21 */
    {256, 200}, /* 22 */
    {  0,   0}, /* 23 */
    {  0,   0}, /* 24 */
    {  0,   0}, /* 25 */
    {  0,   0}, /* 26 */
    {  0,   0}, /* 27 */
    {  0,   0}, /* 28 */
    {  0,   0}, /* 29 */
    {  0,   0}, /* 30 */
    {  0,   0}, /* 31 */
    {  0,   0}, /* 32 */
    {  0,   0}, /* 33 */
    {236, 212}, /* 34 */
    {228, 256}, /* 35 */
    {188, 208}, /* 36 */
    {236, 196}, /* 37 */
    {208,   0}, /* 38 */
    {244, 124}, /* 39 */
    {236, 228}, /* 40 */
    {156, 148}, /* 41 */
    {204, 172}, /* 42 */
    {248, 160}, /* 43 */
    {  0,   0}, /* 44 */
    {  0,   0}, /* 45 */
    {120, 208}, /* 46 */
    {156, 192}, /* 47 */
    {164, 160}, /* 48 */
    {120,  88}, /* 49 */
    {192, 204}, /* 50 */
    {120, 196}, /* 51 */
    {236, 212}, /* 52 */
    {228, 256}, /* 53 */
    {188, 208}, /* 54 */
    {236, 196}, /* 55 */
    {208,   0}, /* 56 */
    {156, 192}, /* 57 */
    {160, 168}, /* 58 */
    {256, 180}, /* 59 */
    {184,   0}, /* 60 */
    {156,   0}, /* 61 */
    {164, 132}, /* 62 */
    {236, 188}, /* 63 */
    {176,   0}, /* 64 */
    { 92, 148}, /* 65 */
    {160,   0}, /* 66 */
    {120,  88}, /* 67 */
    {236, 112}, /* 68 */
    {132,  96}, /* 69 */
    {176, 160}, /* 70 */
    {128, 160}, /* 71 */
    {164, 220}, /* 72 */
    {156, 192}, /* 73 */
    {  0,   0}, /* 74 */
    {236, 188}, /* 75 */
    {236, 188}, /* 76 */
    {164, 132}, /* 77 */
    {104, 176}, /* 78 */
    {132, 204}, /* 79 */
    {148, 148}, /* 80 */
    {120, 196}, /* 81 */
    { 76, 228}, /* 82 */
    {152,   0}, /* 83 */
    {196,   0}, /* 84 */
    {184,   0}, /* 85 */
    {156, 192}, /* 86 */
    {172, 108}, /* 87 */
    {  0,   0}, /* 88 */
    {256,   0}, /* 89 */
    {160, 180}, /* 90 */
    {172,   0}, /* 91 */
    { 76,   0}, /* 92 */
    {164, 160}, /* 93 */
};

static VictoryRectangle victory_name_rectangles[VICTORY_NAME_FRAME_COUNT]
    VICTORY_DATA_SECTION(".bss.localization_ui_victory_name_rectangles");

VICTORY_SECTION(".text.localization_ui_victory_name_rectangle")
const VictoryRectangle *localization_ui_victory_name_rectangle(
    int character_id,
    int frame
)
{
    volatile VictoryRectangle *rectangle;
    u16 width;

    if ((u32)character_id >= VICTORY_NAME_CHARACTER_COUNT
        || (u32)frame >= VICTORY_NAME_FRAME_COUNT) {
        return (const VictoryRectangle *)0;
    }

    rectangle = &victory_name_rectangles[frame];
    width = frame == 0
        ? victory_name_widths[character_id].first
        : victory_name_widths[character_id].second;
    if (width == 0u) {
        rectangle->u = 0u;
        rectangle->v = 0u;
        rectangle->width = 0u;
        rectangle->height = 0u;
        rectangle->reserved_08 = 0u;
        rectangle->local_y_bits = 0u;
        rectangle->reserved_10 = 0u;
        rectangle->reserved_14 = 0u;
    } else {
        rectangle->u = 1u;
        rectangle->v = (u16)(frame == 0 ? 1u : 65u);
        rectangle->width = (u16)(width - 2u);
        rectangle->height = VICTORY_NAME_HEIGHT;
        rectangle->reserved_08 = 0u;
        rectangle->local_y_bits = VICTORY_NAME_LOCAL_Y_BITS;
        rectangle->reserved_10 = 0u;
        rectangle->reserved_14 = 0u;
    }
    return (const VictoryRectangle *)rectangle;
}

VICTORY_SECTION(".text.localization_ui_victory_initialize_name")
void localization_ui_victory_initialize_name(void *context, int character_id)
{
    int frame;

    /* NUN5's battle initializer passes a signed 16-bit character ID. */
    character_id = (short)character_id;
    if ((u32)character_id >= VICTORY_NAME_CHARACTER_COUNT) {
        return;
    }
    for (frame = 0; frame < 2; ++frame) {
        const VictoryRectangle *source =
            localization_ui_victory_name_rectangle(character_id, frame);
        volatile VictoryRectangle *destination = (volatile VictoryRectangle *)(
            (unsigned char *)context + 0x3C8 + frame * 24
        );
        destination->u = source->u;
        destination->v = source->v;
        destination->width = source->width;
        destination->height = source->height;
        destination->reserved_08 = source->reserved_08;
        destination->local_y_bits = source->local_y_bits;
        destination->reserved_10 = source->reserved_10;
        destination->reserved_14 = source->reserved_14;
    }
}
