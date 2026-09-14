/* Mode Select host and session-wide state for the shared Mod Settings menu. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef signed int s32;
typedef unsigned int u32;

#define MOD_SETTINGS_SECTION(name) __attribute__((section(name), noinline))

#define RESIDENT_ALLOCATE_ADDRESS 0x00117150u
#define RESIDENT_FREE_ADDRESS 0x00117000u
#define MODE_SELECT_CONSTRUCT_ADDRESS 0x00383DB0u
#define MODE_SELECT_DRAW_ADDRESS 0x00385C00u
#define MODE_SELECT_CLEANUP_ADDRESS 0x00383AA0u
#define SPRITE_DRAW_RECT_ADDRESS 0x0037BC40u
#define SPRITE_CREATE_ADDRESS 0x0037B670u
#define SPRITE_FINALIZE_ADDRESS 0x001CC070u
#define SPRITE_DESTROY_ADDRESS 0x001CBDF0u
#define PRACTICE_CHILD_INITIALIZE_ADDRESS 0x008809E0u
#define PRACTICE_CHILD_DESTROY_ADDRESS 0x00880A20u
#define PRACTICE_CHILD_CONSTRUCT_ADDRESS 0x00880BE0u
#define PRACTICE_CHILD_RESET_ADDRESS 0x00880F30u
#define PRACTICE_CHILD_UPDATE_ADDRESS 0x00881AB0u
#define PRACTICE_CHILD_DRAW_ADDRESS 0x00882250u
#define INPUT_CONTEXT_POINTER_ADDRESS 0x006073FCu
#define MANAGER_POINTER_ADDRESS 0x00607600u
#define NATIVE_SOUND_ADDRESS 0x001D7E20u
#define CCS_FIND_OBJECT_ADDRESS 0x001A8F00u
#define TEXTURE_UPLOAD_ADDRESS 0x0010F860u
#define OPTIONS_ARCHIVE_LOAD_ADDRESS 0x0037E1A0u
#define ARCHIVE_FIND_ADDRESS 0x001AA4B0u
#define OPTIONS_CONTEXT_INITIALIZE_ADDRESS 0x00110340u
#define OPTIONS_CONTEXT_LOAD_ADDRESS 0x0010A1D0u
#define OPTIONS_ANIMATION_LOAD_ADDRESS 0x0037D5B0u
#define OPTIONS_ANIMATION_DESTROY_ADDRESS 0x001B7570u
#define OPTIONS_CONTEXT_DESTROY_ADDRESS 0x0010A0F0u
#define OPTIONS_ARCHIVE_DESTROY_ADDRESS 0x001A9790u
#define OPTIONS_RENDER_ENABLE_ADDRESS 0x00186510u
#define OPTIONS_ANIMATION_PREPARE_ADDRESS 0x001BB210u
#define OPTIONS_ANIMATION_ADVANCE_ADDRESS 0x001BB6F0u
#define OPTIONS_ANIMATION_DRAW_ADDRESS 0x001BB790u
#define OPTIONS_CAMERA_BIND_ADDRESS 0x0010E220u
#define RENDER_MANAGER_POINTER_ADDRESS 0x00607470u
#define CURRENT_RENDER_CONTEXT_ADDRESS 0x006073F4u

#define MODE_SELECT_NEW_INPUT_OFFSET 0x30u
#define MODE_SELECT_HELD_INPUT_OFFSET 0x38u
#define MODE_SELECT_P0_INPUT_OFFSET 0x3Cu
#define MODE_SELECT_P1_INPUT_OFFSET 0x40u
#define MODE_SELECT_ARCHIVE_OFFSET 0x64u
#define MODE_SELECT_PROMPT_CONTEXT_OFFSET 0x6Cu
#define INPUT_RECORD_STRIDE 0x78u
#define INPUT_RECORD_HELD_OFFSET 0x80u
#define INPUT_RECORD_NEW_OFFSET 0x84u
#define MANAGER_ACTIVE_SIDE_OFFSET 0x18u
#define PRACTICE_CHILD_SIZE 0xB8u
#define INPUT_SQUARE 0x0080u
#define PRACTICE_CHILD_PHASE_OFFSET 0x38u
#define OPTIONS_CONTEXT_SIZE 0x40u
#define OPTIONS_CONTEXT_OBJECT_OFFSET 0x08u
#define OPTIONS_CONTEXT_ZERO_0_OFFSET 0x28u
#define OPTIONS_CONTEXT_ZERO_1_OFFSET 0x2Cu
#define OPTIONS_CONTEXT_CAMERA_OFFSET 0x3Cu
#define OPTIONS_ANIMATION_FRAME_OFFSET 0x94u
#define OPTIONS_ANIMATION_ACTIVE_OFFSET 0xFCu
#define OPTIONS_ANIMATION_CAMERA_OFFSET 0x10Cu

#define SIMPLE_DISPLAY_BIT 0x02u
#define MANAGER_SETTINGS_PACK_0 0x9F4u
#define MANAGER_SETTINGS_PACK_1 0xA00u
#define MANAGER_SETTINGS_PACK_2 0xA0Cu
#define PRACTICE_ARCHIVE_OFFSET 0x04u
#define PRACTICE_BACKDROP_ENABLED_OFFSET 0x48u
#define PRACTICE_CHILD_REVEAL_DELAY_OFFSET 0x56u
#define PRACTICE_CHILD_PHASE_INTERACTIVE 2u
#define PRACTICE_CHILD_REVEAL_READY 3u
#define MOD_SETTINGS_INACTIVE 0u
#define MOD_SETTINGS_OPENING 1u
#define MOD_SETTINGS_ACTIVE 2u
#define TEXTURE_MIPMAPS_OFFSET 0x28u
#define TEXTURE_WIDTH_LOG2_OFFSET 0x36u
#define TEXTURE_HEIGHT_LOG2_OFFSET 0x37u
#define MIPMAP_PIXELS_OFFSET 0x04u
#define MIPMAP_QWORD_COUNT_OFFSET 0x08u
#define MOD_SETTINGS_TITLE_WIDTH 128u
#define MOD_SETTINGS_TITLE_HEIGHT 32u
#define MOD_SETTINGS_TITLE_BYTES \
    (MOD_SETTINGS_TITLE_WIDTH * MOD_SETTINGS_TITLE_HEIGHT)
#define MOD_SETTINGS_PROMPT_LABEL_WIDTH 48u
#define MOD_SETTINGS_PROMPT_LABEL_HEIGHT 24u
#define MOD_SETTINGS_PROMPT_LABEL_BYTES \
    (MOD_SETTINGS_PROMPT_LABEL_WIDTH * MOD_SETTINGS_PROMPT_LABEL_HEIGHT)
#define PRACTICE_TEXTURE_WIDTH 128u
#define PRACTICE_TEXTURE_HEIGHT 128u
#define PRACTICE_TEXTURE_BYTES \
    (PRACTICE_TEXTURE_WIDTH * PRACTICE_TEXTURE_HEIGHT)
#define PRACTICE_TITLE_OFFSET \
    (PRACTICE_TEXTURE_BYTES - MOD_SETTINGS_TITLE_BYTES)
#define MODE_SELECT_TEXTURE_WIDTH 256u
#define MODE_SELECT_TEXTURE_HEIGHT 512u
#define MODE_SELECT_TEXTURE_BYTES \
    (MODE_SELECT_TEXTURE_WIDTH * MODE_SELECT_TEXTURE_HEIGHT)
#define MODE_SELECT_PROMPT_LABEL_X 0u
#define MODE_SELECT_PROMPT_LABEL_RAW_Y 64u
#define MODE_SELECT_PROMPT_LABEL_V \
    (MODE_SELECT_TEXTURE_HEIGHT - MODE_SELECT_PROMPT_LABEL_RAW_Y - \
        MOD_SETTINGS_PROMPT_LABEL_HEIGHT)

typedef void *(*Allocate)(u32 size);
typedef void (*Free)(void *value);
typedef void (*ObjectCall)(void *object);
typedef void (*ObjectConstruct)(void *object, u32 variant);
typedef s32 (*ObjectUpdate)(void *object);
typedef void (*Sound)(u32 sound_id);
typedef void *(*FindObject)(void *archive, const u8 *name, u32 optional);
typedef void (*ArchiveLoad)(const u8 *name, u8 *owned);
typedef void *(*FindArchive)(const u8 *name);
typedef void (*InitializeContext)(void *object);
typedef void (*LoadContext)(void *context, u32 kind, void *source);
typedef void *(*LoadAnimation)(void *archive, const u8 *name);
typedef void (*DestroyResource)(void *resource, u32 release);
typedef void (*RenderEnable)(void *manager, u32 enabled);
typedef void (*PrepareAnimation)(void *animation, u16 frame, u32 flags);
typedef void (*BindCamera)(void *context, void *camera, u32 flags);
typedef void *(*CreateSprite)(
    void *archive,
    const u8 *texture_name,
    u32 argument_2,
    u32 argument_3,
    void *context
);
typedef void (*DrawSpriteRect)(
    float x,
    float y,
    void *sprite,
    const u16 *rectangle
);
typedef struct ModSettingsState {
    u32 control_scheme;
    u32 simple_display;
    u32 character_balance;
    u32 balance_overlay;
    u32 support_selection;
    u32 defaults[5];
} ModSettingsState;

typedef struct ModSettingsBackdrop {
    void *archive;
    void *context;
    void *camera;
    void *background;
    void *footer_archive;
    void *footer_sprite;
    u32 state;
    u8 archive_owned;
    u8 footer_archive_owned;
} ModSettingsBackdrop;

extern volatile ModSettingsState mod_settings_state;
extern const u8 mod_settings_title_pixels[MOD_SETTINGS_TITLE_BYTES];
extern const u8 mod_settings_prompt_label_pixels[MOD_SETTINGS_PROMPT_LABEL_BYTES];

volatile u32 mod_settings_child
    __attribute__((section(".bss.mod_settings_child")));

static ModSettingsBackdrop mod_settings_backdrop
    __attribute__((section(".bss.mod_settings_backdrop")));

static const u8 mod_settings_options_archive_name[]
    __attribute__((section(".rodata"))) = "option.ccs";
static const u8 mod_settings_options_camera_name[]
    __attribute__((section(".rodata"))) = "ANM_option_ca";
static const u8 mod_settings_options_background_name[]
    __attribute__((section(".rodata"))) = "ANM_option_back";
static const u8 mod_settings_footer_archive_name[]
    __attribute__((section(".rodata"))) = "vs.ccs";
static const u8 mod_settings_footer_texture_name[]
    __attribute__((section(".rodata"))) = "TEX_vs_t01";
static const u8 mod_settings_mode_select_texture_name[]
    __attribute__((section(".rodata"))) = "TEX_modesel02";
static const u8 mod_settings_practice_texture_name[]
    __attribute__((section(".rodata"))) = "TEX_prac_t01";
static const u16 mod_settings_prompt_label_rectangle[4]
    __attribute__((section(".rodata"))) = {
        MODE_SELECT_PROMPT_LABEL_X,
        MODE_SELECT_PROMPT_LABEL_V,
        MOD_SETTINGS_PROMPT_LABEL_WIDTH,
        MOD_SETTINGS_PROMPT_LABEL_HEIGHT,
    };
static const u16 mod_settings_square_rectangle[4]
    __attribute__((section(".rodata"))) = {
        5u,
        281u,
        22u,
        22u,
    };

static u32 *mod_settings_field(u32 argument)
{
    if (argument >= 5u) {
        return (u32 *)0;
    }
    return &((u32 *)&mod_settings_state)[argument];
}

static u32 mod_settings_maximum(u32 argument)
{
    return argument == 4u ? 2u : 1u;
}

MOD_SETTINGS_SECTION(".text.mod_settings_option_get")
u32 mod_settings_option_get(u32 argument)
{
    u32 *field = mod_settings_field(argument);
    u32 value;

    if (field == (u32 *)0) {
        return 0u;
    }
    value = *field;
    return value <= mod_settings_maximum(argument)
        ? value : mod_settings_state.defaults[argument];
}

static u8 *mod_settings_texture_pixels(
    void *archive,
    const u8 *texture_name,
    u8 width_log2,
    u8 height_log2,
    u32 required_bytes,
    void **mipmap_out
)
{
    u8 *texture;
    u8 *mipmap;

    if (archive == (void *)0) {
        return (u8 *)0;
    }
    texture = ((FindObject)CCS_FIND_OBJECT_ADDRESS)(
        archive,
        texture_name,
        1u
    );
    if (
        texture == (u8 *)0 ||
        texture[TEXTURE_WIDTH_LOG2_OFFSET] != width_log2 ||
        texture[TEXTURE_HEIGHT_LOG2_OFFSET] != height_log2
    ) {
        return (u8 *)0;
    }
    mipmap = *(u8 **)(texture + TEXTURE_MIPMAPS_OFFSET);
    if (
        mipmap == (u8 *)0 ||
        *(u32 *)(mipmap + MIPMAP_QWORD_COUNT_OFFSET) * 16u < required_bytes
    ) {
        return (u8 *)0;
    }
    *mipmap_out = mipmap;
    return *(u8 **)(mipmap + MIPMAP_PIXELS_OFFSET);
}

static void mod_settings_copy_rows(
    u8 *destination,
    u32 destination_stride,
    u32 destination_x,
    u32 destination_y,
    const u8 *source,
    u32 source_width,
    u32 source_height
)
{
    u32 x;
    u32 y;

    for (y = 0u; y < source_height; ++y) {
        for (x = 0u; x < source_width; ++x) {
            destination[
                (destination_y + y) * destination_stride +
                destination_x + x
            ] = source[y * source_width + x];
        }
    }
}

static void mod_settings_install_graphics(void *child, void *controller)
{
    void *practice_archive = *(void **)(
        (u8 *)child + PRACTICE_ARCHIVE_OFFSET
    );
    void *mode_select_archive = *(void **)(
        (u8 *)controller + MODE_SELECT_ARCHIVE_OFFSET
    );
    void *mipmap;
    u8 *pixels;

    pixels = mod_settings_texture_pixels(
        practice_archive,
        mod_settings_practice_texture_name,
        7u,
        7u,
        PRACTICE_TEXTURE_BYTES,
        &mipmap
    );
    if (pixels != (u8 *)0) {
        mod_settings_copy_rows(
            pixels,
            PRACTICE_TEXTURE_WIDTH,
            0u,
            PRACTICE_TITLE_OFFSET / PRACTICE_TEXTURE_WIDTH,
            mod_settings_title_pixels,
            PRACTICE_TEXTURE_WIDTH,
            MOD_SETTINGS_TITLE_HEIGHT
        );
        ((ObjectCall)TEXTURE_UPLOAD_ADDRESS)(mipmap);
    }

    pixels = mod_settings_texture_pixels(
        mode_select_archive,
        mod_settings_mode_select_texture_name,
        8u,
        9u,
        MODE_SELECT_TEXTURE_BYTES,
        &mipmap
    );
    if (pixels == (u8 *)0) {
        return;
    }
    mod_settings_copy_rows(
        pixels,
        MODE_SELECT_TEXTURE_WIDTH,
        MODE_SELECT_PROMPT_LABEL_X,
        MODE_SELECT_PROMPT_LABEL_RAW_Y,
        mod_settings_prompt_label_pixels,
        MOD_SETTINGS_PROMPT_LABEL_WIDTH,
        MOD_SETTINGS_PROMPT_LABEL_HEIGHT
    );
    ((ObjectCall)TEXTURE_UPLOAD_ADDRESS)(mipmap);
}

static void mod_settings_apply_simple_display(u32 enabled)
{
    static const u32 offsets[3] = {
        MANAGER_SETTINGS_PACK_0,
        MANAGER_SETTINGS_PACK_1,
        MANAGER_SETTINGS_PACK_2,
    };
    u8 *manager = *(u8 **)MANAGER_POINTER_ADDRESS;
    u32 index;

    if (manager == (u8 *)0) {
        return;
    }
    for (index = 0u; index < 3u; ++index) {
        volatile u8 *flags = manager + offsets[index];
        *flags = enabled != 0u
            ? (u8)(*flags | SIMPLE_DISPLAY_BIT)
            : (u8)(*flags & (u8)~SIMPLE_DISPLAY_BIT);
    }
}

static void mod_settings_destroy_backdrop(void)
{
    mod_settings_backdrop.state = MOD_SETTINGS_INACTIVE;
    if (mod_settings_backdrop.footer_sprite != (void *)0) {
        ((DestroyResource)SPRITE_DESTROY_ADDRESS)(
            mod_settings_backdrop.footer_sprite,
            1u
        );
        mod_settings_backdrop.footer_sprite = (void *)0;
    }
    if (mod_settings_backdrop.footer_archive != (void *)0) {
        if (mod_settings_backdrop.footer_archive_owned != 0u) {
            ((DestroyResource)OPTIONS_ARCHIVE_DESTROY_ADDRESS)(
                mod_settings_backdrop.footer_archive,
                1u
            );
        }
        mod_settings_backdrop.footer_archive = (void *)0;
    }
    mod_settings_backdrop.footer_archive_owned = 0u;
    if (mod_settings_backdrop.background != (void *)0) {
        ((DestroyResource)OPTIONS_ANIMATION_DESTROY_ADDRESS)(
            mod_settings_backdrop.background,
            1u
        );
        mod_settings_backdrop.background = (void *)0;
    }
    if (mod_settings_backdrop.camera != (void *)0) {
        ((DestroyResource)OPTIONS_ANIMATION_DESTROY_ADDRESS)(
            mod_settings_backdrop.camera,
            1u
        );
        mod_settings_backdrop.camera = (void *)0;
    }
    if (mod_settings_backdrop.context != (void *)0) {
        ((DestroyResource)OPTIONS_CONTEXT_DESTROY_ADDRESS)(
            mod_settings_backdrop.context,
            1u
        );
        mod_settings_backdrop.context = (void *)0;
    }
    if (mod_settings_backdrop.archive != (void *)0) {
        if (mod_settings_backdrop.archive_owned != 0u) {
            ((DestroyResource)OPTIONS_ARCHIVE_DESTROY_ADDRESS)(
                mod_settings_backdrop.archive,
                1u
            );
        }
        mod_settings_backdrop.archive = (void *)0;
    }
    mod_settings_backdrop.archive_owned = 0u;
}

static s32 mod_settings_create_backdrop(void *controller)
{
    void *context;
    void *mode_select_context;

    mod_settings_destroy_backdrop();
    ((ArchiveLoad)OPTIONS_ARCHIVE_LOAD_ADDRESS)(
        mod_settings_options_archive_name,
        &mod_settings_backdrop.archive_owned
    );
    mod_settings_backdrop.archive =
        ((FindArchive)ARCHIVE_FIND_ADDRESS)(
            mod_settings_options_archive_name
        );
    if (mod_settings_backdrop.archive == (void *)0) {
        return 0;
    }
    context = ((Allocate)RESIDENT_ALLOCATE_ADDRESS)(OPTIONS_CONTEXT_SIZE);
    if (context == (void *)0) {
        mod_settings_destroy_backdrop();
        return 0;
    }
    ((InitializeContext)OPTIONS_CONTEXT_INITIALIZE_ADDRESS)(
        (u8 *)context + OPTIONS_CONTEXT_OBJECT_OFFSET
    );
    *(u32 *)((u8 *)context + OPTIONS_CONTEXT_ZERO_0_OFFSET) = 0u;
    *(u32 *)((u8 *)context + OPTIONS_CONTEXT_ZERO_1_OFFSET) = 0u;
    ((LoadContext)OPTIONS_CONTEXT_LOAD_ADDRESS)(context, 0x50u, (void *)0);
    mod_settings_backdrop.context = context;
    mod_settings_backdrop.camera =
        ((LoadAnimation)OPTIONS_ANIMATION_LOAD_ADDRESS)(
            mod_settings_backdrop.archive,
            mod_settings_options_camera_name
        );
    mod_settings_backdrop.background =
        ((LoadAnimation)OPTIONS_ANIMATION_LOAD_ADDRESS)(
            mod_settings_backdrop.archive,
            mod_settings_options_background_name
        );
    if (
        mod_settings_backdrop.camera == (void *)0 ||
        mod_settings_backdrop.background == (void *)0
    ) {
        mod_settings_destroy_backdrop();
        return 0;
    }
    mode_select_context = *(void **)(
        (u8 *)controller + MODE_SELECT_PROMPT_CONTEXT_OFFSET
    );
    if (mode_select_context == (void *)0) {
        mod_settings_destroy_backdrop();
        return 0;
    }
    ((ArchiveLoad)OPTIONS_ARCHIVE_LOAD_ADDRESS)(
        mod_settings_footer_archive_name,
        &mod_settings_backdrop.footer_archive_owned
    );
    mod_settings_backdrop.footer_archive =
        ((FindArchive)ARCHIVE_FIND_ADDRESS)(
            mod_settings_footer_archive_name
        );
    if (mod_settings_backdrop.footer_archive == (void *)0) {
        mod_settings_destroy_backdrop();
        return 0;
    }
    mod_settings_backdrop.footer_sprite =
        ((CreateSprite)SPRITE_CREATE_ADDRESS)(
            mod_settings_backdrop.footer_archive,
            mod_settings_footer_texture_name,
            10u,
            1u,
            mode_select_context
        );
    if (mod_settings_backdrop.footer_sprite == (void *)0) {
        mod_settings_destroy_backdrop();
        return 0;
    }
    return 1;
}

static void mod_settings_draw_backdrop(void)
{
    void *camera = mod_settings_backdrop.camera;
    void *context = mod_settings_backdrop.context;
    void *saved_context;
    void *render_manager;

    if (
        camera == (void *)0 ||
        context == (void *)0 ||
        mod_settings_backdrop.background == (void *)0
    ) {
        return;
    }
    render_manager = *(void **)RENDER_MANAGER_POINTER_ADDRESS;
    saved_context = *(void **)CURRENT_RENDER_CONTEXT_ADDRESS;
    ((RenderEnable)OPTIONS_RENDER_ENABLE_ADDRESS)(render_manager, 1u);
    *(void **)CURRENT_RENDER_CONTEXT_ADDRESS = context;
    if (*(u32 *)((u8 *)camera + OPTIONS_ANIMATION_ACTIVE_OFFSET) != 0u) {
        ((PrepareAnimation)OPTIONS_ANIMATION_PREPARE_ADDRESS)(
            camera,
            *(u16 *)((u8 *)camera + OPTIONS_ANIMATION_FRAME_OFFSET),
            0u
        );
        ((ObjectCall)OPTIONS_ANIMATION_ADVANCE_ADDRESS)(camera);
    }
    ((ObjectCall)OPTIONS_ANIMATION_DRAW_ADDRESS)(camera);
    ((BindCamera)OPTIONS_CAMERA_BIND_ADDRESS)(
        *(void **)((u8 *)context + OPTIONS_CONTEXT_CAMERA_OFFSET),
        *(void **)((u8 *)camera + OPTIONS_ANIMATION_CAMERA_OFFSET),
        0u
    );
    ((ObjectCall)OPTIONS_ANIMATION_DRAW_ADDRESS)(
        mod_settings_backdrop.background
    );
    *(void **)CURRENT_RENDER_CONTEXT_ADDRESS = saved_context;
    ((RenderEnable)OPTIONS_RENDER_ENABLE_ADDRESS)(render_manager, 0u);
}

MOD_SETTINGS_SECTION(".text.mod_settings_option_set")
void mod_settings_option_set(u32 argument, u32 value)
{
    u32 *field = mod_settings_field(argument);

    if (field == (u32 *)0 || value > mod_settings_maximum(argument)) {
        return;
    }
    *field = value;
    if (argument == 1u) {
        mod_settings_apply_simple_display(value);
    }
}

static void mod_settings_destroy_child(void)
{
    void *child = (void *)mod_settings_child;

    mod_settings_backdrop.state = MOD_SETTINGS_INACTIVE;
    if (child != (void *)0) {
        ((ObjectCall)PRACTICE_CHILD_DESTROY_ADDRESS)(child);
        ((Free)RESIDENT_FREE_ADDRESS)(child);
        mod_settings_child = 0u;
    }
    mod_settings_destroy_backdrop();
}

static s32 mod_settings_create_child(void *controller)
{
    void *child;

    if (mod_settings_child != 0u) {
        return 1;
    }
    if (
        (
            mod_settings_backdrop.archive == (void *)0 ||
            mod_settings_backdrop.context == (void *)0 ||
            mod_settings_backdrop.camera == (void *)0 ||
            mod_settings_backdrop.background == (void *)0 ||
            mod_settings_backdrop.footer_archive == (void *)0 ||
            mod_settings_backdrop.footer_sprite == (void *)0
        ) &&
        mod_settings_create_backdrop(controller) == 0
    ) {
        return 0;
    }
    child = ((Allocate)RESIDENT_ALLOCATE_ADDRESS)(PRACTICE_CHILD_SIZE);
    if (child == (void *)0) {
        return 0;
    }
    ((ObjectCall)PRACTICE_CHILD_INITIALIZE_ADDRESS)(child);
    mod_settings_child = (u32)child;
    ((ObjectConstruct)PRACTICE_CHILD_CONSTRUCT_ADDRESS)(child, 1u);
    *((u8 *)child + PRACTICE_BACKDROP_ENABLED_OFFSET) = 0u;
    mod_settings_install_graphics(child, controller);
    return 1;
}

static s32 mod_settings_open_child(void)
{
    void *child = (void *)mod_settings_child;

    if (child == (void *)0) {
        return 0;
    }
    ((ObjectCall)PRACTICE_CHILD_RESET_ADDRESS)(child);
    mod_settings_backdrop.state = MOD_SETTINGS_OPENING;
    return 1;
}

MOD_SETTINGS_SECTION(".text.mod_settings_mode_select_construct")
void mod_settings_mode_select_construct(void *controller)
{
    ((ObjectCall)MODE_SELECT_CONSTRUCT_ADDRESS)(controller);
    if (mod_settings_create_child(controller) == 0) {
        mod_settings_destroy_child();
    }
}

MOD_SETTINGS_SECTION(".text.mod_settings_draw_mode_select_footer")
void mod_settings_draw_mode_select_footer(
    float x,
    float y,
    void *mode_select_sprite,
    const u16 *rectangle
)
{
    void *footer_sprite = mod_settings_backdrop.footer_sprite;

    ((DrawSpriteRect)SPRITE_DRAW_RECT_ADDRESS)(
        x,
        y,
        mode_select_sprite,
        rectangle
    );
    if (mod_settings_child != 0u && footer_sprite != (void *)0) {
        ((DrawSpriteRect)SPRITE_DRAW_RECT_ADDRESS)(
            294.0f,
            362.0f,
            footer_sprite,
            mod_settings_square_rectangle
        );
        ((ObjectCall)SPRITE_FINALIZE_ADDRESS)(footer_sprite);
        ((DrawSpriteRect)SPRITE_DRAW_RECT_ADDRESS)(
            327.0f,
            362.0f,
            mode_select_sprite,
            mod_settings_prompt_label_rectangle
        );
    }
}

static void mod_settings_clear_mode_select_input(void *controller)
{
    *(volatile u32 *)((u8 *)controller + MODE_SELECT_NEW_INPUT_OFFSET) = 0u;
    *(volatile u32 *)((u8 *)controller + MODE_SELECT_HELD_INPUT_OFFSET) = 0u;
    *(volatile u32 *)((u8 *)controller + MODE_SELECT_P0_INPUT_OFFSET) = 0u;
    *(volatile u32 *)((u8 *)controller + MODE_SELECT_P1_INPUT_OFFSET) = 0u;
}

static s32 mod_settings_update_child(void *child, void *controller)
{
    u8 *input_context = *(u8 **)INPUT_CONTEXT_POINTER_ADDRESS;
    u8 *manager = *(u8 **)MANAGER_POINTER_ADDRESS;
    volatile u32 *held;
    volatile u32 *pressed;
    u32 saved_held;
    u32 saved_pressed;
    s32 result;

    if (input_context == (u8 *)0) {
        return ((ObjectUpdate)PRACTICE_CHILD_UPDATE_ADDRESS)(child);
    }
    if (manager != (u8 *)0) {
        input_context +=
            *(volatile u32 *)(manager + MANAGER_ACTIVE_SIDE_OFFSET) *
            INPUT_RECORD_STRIDE;
    }
    held = (volatile u32 *)(input_context + INPUT_RECORD_HELD_OFFSET);
    pressed = (volatile u32 *)(input_context + INPUT_RECORD_NEW_OFFSET);
    saved_held = *held;
    saved_pressed = *pressed;
    *held = *(volatile u32 *)(
        (u8 *)controller + MODE_SELECT_HELD_INPUT_OFFSET
    );
    *pressed = *(volatile u32 *)(
        (u8 *)controller + MODE_SELECT_NEW_INPUT_OFFSET
    );
    result = ((ObjectUpdate)PRACTICE_CHILD_UPDATE_ADDRESS)(child);
    *held = saved_held;
    *pressed = saved_pressed;
    return result;
}

MOD_SETTINGS_SECTION(".text.mod_settings_mode_select_update")
void mod_settings_mode_select_update(void *controller)
{
    void *child = (void *)mod_settings_child;
    u32 state = mod_settings_backdrop.state;
    u32 suppress_input = state != MOD_SETTINGS_INACTIVE;
    u32 input = *(volatile u32 *)(
        (u8 *)controller + MODE_SELECT_NEW_INPUT_OFFSET
    );

    if (state == MOD_SETTINGS_INACTIVE) {
        if (
            (input & INPUT_SQUARE) != 0u &&
            mod_settings_open_child() != 0
        ) {
            suppress_input = 1u;
        }
    } else if (child != (void *)0) {
        if (mod_settings_update_child(child, controller) != 0) {
            mod_settings_backdrop.state = MOD_SETTINGS_INACTIVE;
        } else if (
            state == MOD_SETTINGS_OPENING &&
            *(u32 *)((u8 *)child + PRACTICE_CHILD_PHASE_OFFSET) ==
                PRACTICE_CHILD_PHASE_INTERACTIVE
        ) {
            *(u16 *)((u8 *)child + PRACTICE_CHILD_REVEAL_DELAY_OFFSET) =
                PRACTICE_CHILD_REVEAL_READY;
            mod_settings_backdrop.state = MOD_SETTINGS_ACTIVE;
            ((Sound)NATIVE_SOUND_ADDRESS)(0x34u);
        }
    } else {
        mod_settings_backdrop.state = MOD_SETTINGS_INACTIVE;
    }
    if (suppress_input != 0u) {
        mod_settings_clear_mode_select_input(controller);
    }
}

MOD_SETTINGS_SECTION(".text.mod_settings_mode_select_draw")
void mod_settings_mode_select_draw(void *controller)
{
    if (mod_settings_backdrop.state == MOD_SETTINGS_ACTIVE) {
        mod_settings_draw_backdrop();
        ((ObjectCall)PRACTICE_CHILD_DRAW_ADDRESS)((void *)mod_settings_child);
    } else {
        ((ObjectCall)MODE_SELECT_DRAW_ADDRESS)(controller);
    }
}

MOD_SETTINGS_SECTION(".text.mod_settings_mode_select_cleanup")
void mod_settings_mode_select_cleanup(void *controller)
{
    mod_settings_destroy_child();
    ((ObjectCall)MODE_SELECT_CLEANUP_ADDRESS)(controller);
}
