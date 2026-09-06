/* Localized Ultimate Jutsu message drawing. */

typedef struct UltimateJutsuSprite {
    unsigned int flags;
    unsigned char unused_04[0x2c];
    short x;
    short y;
    short z;
    short rotation;
} UltimateJutsuSprite;

typedef void (*NativeJutsuSpriteDraw)(
    UltimateJutsuSprite *sprite,
    short record,
    const void *uv_offset
);

__attribute__((section(".text.localization_ui_ultimate_jutsu_damage_draw"), noinline))
void localization_ui_ultimate_jutsu_damage_draw(
    UltimateJutsuSprite *sprite,
    short record,
    const void *uv_offset
)
{
    NativeJutsuSpriteDraw draw = (NativeJutsuSpriteDraw)0x007664a0u;

    /* NUN5 rotates only the bubble; its English foreground stays upright. */
    sprite->flags = (sprite->flags & ~0x000f0000u)
        | (record == 0 ? 0x00040000u : 0x00010000u);
    sprite->rotation = record == 0 ? 0x4000 : 0;
    sprite->x += sprite->x < 256 ? 20 : -20;
    draw(sprite, record, uv_offset);
}

__attribute__((section(".text.localization_ui_ultimate_jutsu_input_result_draw"), noinline))
void localization_ui_ultimate_jutsu_input_result_draw(
    UltimateJutsuSprite *sprite,
    short record,
    const void *uv_offset
)
{
    NativeJutsuSpriteDraw draw = (NativeJutsuSpriteDraw)0x007664a0u;

    /* NUN5 stores Success! horizontally and Failed vertically in the atlas. */
    sprite->flags = (sprite->flags & ~0x000f0000u) | 0x00040000u;
    sprite->rotation = record == 0 ? 0 : (short)0xc000;
    draw(sprite, record, uv_offset);
}
