/* Localized battle item-status layout for the current NA228 object ABI. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

typedef struct ItemPosition {
    float x;
    float y;
    float z;
    float w;
} ItemPosition;

typedef struct ItemRecord {
    u8 flags;
    u8 sprite_flags;
    u16 u;
    u16 v;
    u16 width;
    u16 height;
    u16 reserved;
} ItemRecord;

typedef union ItemFloatBits {
    u32 bits;
    float value;
} ItemFloatBits;

typedef u32 (*NativeItemResourceLookup)(
    u32 record,
    u32 group,
    u32 language
);
typedef void (*NativeUniformItemDraw)(
    float scale,
    float alpha,
    float rotation,
    u32 variant,
    u32 record,
    const ItemPosition *position
);
typedef void (*NativeAnisotropicItemDraw)(
    float scale_x,
    float scale_y,
    float alpha,
    float rotation,
    u32 variant,
    u32 record,
    const ItemPosition *position
);
typedef void (*NativeNumericDigitsDraw)(
    void *object,
    const ItemPosition *position
);
typedef void (*NativeItemClassDraw)(
    void *object,
    const ItemPosition *position
);

#define ITEM_STATUS_SECTION(name) \
    __attribute__((section(name), noinline))

#define ITEM_RECORD_TABLE_ADDRESS 0x005B0A60u
#define ITEM_NUMERIC_MAP_ADDRESS 0x00898BB0u
#define ITEM_SINGLE_MAP_ADDRESS 0x00898BD0u
#define ITEM_PAIRED_MAP_ADDRESS 0x00898C00u

#define ITEM_RESOURCE_LOOKUP_ADDRESS 0x00377CB0u
#define ITEM_UNIFORM_DRAW_ADDRESS 0x00377720u
#define ITEM_ANISOTROPIC_DRAW_ADDRESS 0x00377260u
#define ITEM_NUMERIC_DIGITS_DRAW_ADDRESS 0x0070E660u

#define ITEM_PAIRED_VTABLE 0x005DDEA0u
#define ITEM_SINGLE_VTABLE 0x005DDEC0u
#define ITEM_FIXED_VTABLE 0x005DDE80u

#define ITEM_QUARTER_TURN_BITS 0x3FC90FDBu
#define ITEM_BUBBLE_ROTATION_BITS 0x3FC8F5C3u

static __attribute__((always_inline)) inline u8 *
item_bytes(void *value)
{
    return (u8 *)value;
}

static __attribute__((always_inline)) inline float
item_float_from_bits(u32 bits)
{
    ItemFloatBits value;
    value.bits = bits;
    return value.value;
}

static __attribute__((always_inline)) inline const ItemRecord *
item_record(u32 record)
{
    return &((const ItemRecord *)ITEM_RECORD_TABLE_ADDRESS)[record];
}

static __attribute__((always_inline)) inline u32
item_variant(void *object, u32 record)
{
    NativeItemResourceLookup lookup =
        (NativeItemResourceLookup)ITEM_RESOURCE_LOOKUP_ADDRESS;
    u32 variant = lookup(record, 0u, 0u);

    if (*(u32 *)(item_bytes(object) + 0x18u) == 1u) {
        u32 low = variant & 0xFFu;
        if (low == 0u) {
            return 3u;
        }
        if (low == 1u) {
            return 4u;
        }
        if (low == 2u) {
            return 5u;
        }
    }
    return variant;
}

static __attribute__((always_inline)) inline u32
item_map_record(
    u32 table_address,
    u32 row_count,
    u32 row_size,
    u8 code,
    u32 fallback
)
{
    const u8 *table = (const u8 *)table_address;
    u32 row;

    for (row = 0u; row < row_count; row += 1u) {
        const u8 *entry = table + row * row_size;
        if (entry[0] == code) {
            return *(const u32 *)(entry + 4u);
        }
    }
    return fallback;
}

static __attribute__((always_inline)) inline void
item_center_x(ItemPosition *position, u32 record)
{
    position->x -= (float)(item_record(record)->width >> 1);
}

static __attribute__((always_inline)) inline float
item_paired_scale(u8 code)
{
    if (code == 4u) {
        return 1.59375f;
    }
    if (code == 5u) {
        return 1.53125f;
    }
    if (code == 6u || code == 14u) {
        return 1.90625f;
    }
    if (code == 15u) {
        return 1.09375f;
    }
    if (code == 17u) {
        return 1.15625f;
    }
    if (code < 18u) {
        return 1.0f;
    }
    return 1.25f;
}

static __attribute__((always_inline)) inline float
item_bubble_width_scale(void *object)
{
    u32 vtable = *(u32 *)object;
    u8 code = *(u8 *)(item_bytes(object) + 0x0Cu);

    if (vtable == ITEM_PAIRED_VTABLE) {
        return item_paired_scale(code);
    }
    if (vtable == ITEM_SINGLE_VTABLE) {
        return code == 9u ? 1.90625f : 1.0f;
    }
    if (vtable == ITEM_FIXED_VTABLE) {
        return 1.59375f;
    }
    return 1.25f;
}

static __attribute__((always_inline)) inline float
item_clamp(float value, float minimum, float maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

/* Byte-identical current-NA228 implementation lives in item_status_renderer.S. */
extern void localization_item_status_foreground_draw(
    float scale,
    float alpha,
    float rotation,
    u32 record,
    const ItemPosition *position,
    u32 variant
);

/*
 * The native common updater owns its state guard, source refresh, coordinate
 * transform, and per-object X/Y adjustment.  The assembly bridge enters here
 * at file offset 0x59F30 with that native stack-local position already built.
 */
ITEM_STATUS_SECTION(".text.localization_item_status_update_tail")
void localization_item_status_update_tail(
    void *object,
    ItemPosition *transformed
)
{
    NativeAnisotropicItemDraw draw_bubble =
        (NativeAnisotropicItemDraw)ITEM_ANISOTROPIC_DRAW_ADDRESS;
    ItemPosition *foreground = transformed - 1;
    volatile float x_origin = 0.0f;
    float width_scale = item_bubble_width_scale(object);
    float half_width = width_scale * 42.0f;

    transformed->x = item_clamp(
        transformed->x,
        half_width,
        512.0f - half_width
    );
    transformed->y = item_clamp(transformed->y, 42.0f, 342.0f);

    if (*(float *)(item_bytes(object) + 0x04u) != -5000.0f) {
        transformed->x =
            (*(float *)(item_bytes(object) + 0x04u) + transformed->x) * 0.5f;
        transformed->y =
            (*(float *)(item_bytes(object) + 0x08u) + transformed->y) * 0.5f;
    }
    *(float *)(item_bytes(object) + 0x04u) = transformed->x;
    *(float *)(item_bytes(object) + 0x08u) = transformed->y;

    *foreground = *transformed;
    foreground->x += x_origin;
    foreground->y -= 33.0f;
    draw_bubble(
        *(float *)(item_bytes(object) + 0x34u),
        width_scale,
        1.0f,
        item_float_from_bits(ITEM_BUBBLE_ROTATION_BITS),
        item_variant(object, 0x80u),
        0x80u,
        transformed
    );

    /* Native uses !(fade <= 0.3), which also dispatches for an unordered fade. */
    if (!(*(float *)(item_bytes(object) + 0x34u) <= 0.3f)) {
        u32 vtable = *(u32 *)object;
        NativeItemClassDraw draw =
            (NativeItemClassDraw)*(u32 *)(vtable + 8u);
        draw(object, foreground);
    }
}

ITEM_STATUS_SECTION(".text.localization_item_status_numeric_draw")
void localization_item_status_numeric_draw(
    void *object,
    const ItemPosition *input
)
{
    NativeNumericDigitsDraw draw_digits =
        (NativeNumericDigitsDraw)ITEM_NUMERIC_DIGITS_DRAW_ADDRESS;
    u8 code = *(u8 *)(item_bytes(object) + 0x0Cu);
    u32 top_record = item_map_record(
        ITEM_NUMERIC_MAP_ADDRESS,
        3u,
        8u,
        code,
        0x7Eu
    );
    u32 lower_record = code == 0x14u ? 0x95u : 0x8Du;
    ItemPosition position = *input;
    float rotation = 0.0f;

    item_center_x(&position, top_record);
    position.x += 22.0f;
    position.y += 20.0f;
    if (top_record == 0x82u) {
        position.x -= 14.0f;
        position.y -= 14.0f;
        rotation = item_float_from_bits(ITEM_QUARTER_TURN_BITS);
    }
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        rotation,
        top_record,
        &position,
        item_variant(object, top_record)
    );

    position = *input;
    item_center_x(&position, lower_record);
    if (lower_record == 0x95u) {
        position.y += 13.0f;
        rotation = item_float_from_bits(ITEM_QUARTER_TURN_BITS);
    } else {
        position.y += 35.0f;
        rotation = 0.0f;
    }
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        rotation,
        lower_record,
        &position,
        item_variant(object, lower_record)
    );

    position = *input;
    position.x -= 50.0f;
    draw_digits(object, &position);
}

ITEM_STATUS_SECTION(".text.localization_item_status_single_draw")
void localization_item_status_single_draw(
    void *object,
    const ItemPosition *input
)
{
    NativeUniformItemDraw draw =
        (NativeUniformItemDraw)ITEM_UNIFORM_DRAW_ADDRESS;
    u8 code = *(u8 *)(item_bytes(object) + 0x0Cu);
    u32 record = item_map_record(
        ITEM_SINGLE_MAP_ADDRESS,
        5u,
        8u,
        code,
        0u
    );
    ItemPosition position = *input;
    float rotation = 0.0f;

    position.y += 33.0f;
    if (record == 0x82u || record == 0x99u) {
        rotation = item_float_from_bits(ITEM_QUARTER_TURN_BITS);
    }
    draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        rotation,
        item_variant(object, record),
        record,
        &position
    );
}

ITEM_STATUS_SECTION(".text.localization_item_status_paired_draw")
void localization_item_status_paired_draw(
    void *object,
    const ItemPosition *input
)
{
    const u8 *table = (const u8 *)ITEM_PAIRED_MAP_ADDRESS;
    u8 code = *(u8 *)(item_bytes(object) + 0x0Cu);
    u32 top_record = 0u;
    u32 lower_record = 0u;
    u32 row;
    ItemPosition position;
    float rotation;

    for (row = 0u; row < 9u; row += 1u) {
        const u8 *entry = table + row * 12u;
        if (entry[0] == code) {
            top_record = *(const u32 *)(entry + 4u);
            lower_record = *(const u32 *)(entry + 8u);
            break;
        }
    }

    position = *input;
    item_center_x(&position, top_record);
    position.y += 18.0f;
    rotation = 0.0f;
    if (top_record == 0x82u) {
        position.y -= 14.0f;
        rotation = item_float_from_bits(ITEM_QUARTER_TURN_BITS);
    }
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        rotation,
        top_record,
        &position,
        item_variant(object, top_record)
    );

    position = *input;
    item_center_x(&position, lower_record);
    position.y += 20.0f;
    rotation = item_float_from_bits(ITEM_QUARTER_TURN_BITS);
    if (lower_record == 0x9Bu) {
        position.y += 14.0f;
        rotation = 0.0f;
    }
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        rotation,
        lower_record,
        &position,
        item_variant(object, lower_record)
    );
}

ITEM_STATUS_SECTION(".text.localization_item_status_fixed_draw")
void localization_item_status_fixed_draw(
    void *object,
    const ItemPosition *input
)
{
    ItemPosition position = *input;

    item_center_x(&position, 0x8Eu);
    position.y += 20.0f;
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        0.0f,
        0x8Eu,
        &position,
        item_variant(object, 0x8Eu)
    );

    position = *input;
    item_center_x(&position, 0x8Du);
    position.y += 37.0f;
    localization_item_status_foreground_draw(
        1.0f,
        *(float *)(item_bytes(object) + 0x30u),
        0.0f,
        0x8Du,
        &position,
        item_variant(object, 0x8Du)
    );
}
