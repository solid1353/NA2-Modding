/* Add configurable entries ahead of Character Select's native support list. */

typedef unsigned char u8;
typedef unsigned int u32;

#define CHARACTER_SELECT_SUPPORT_COUNT_OFFSET 0x21Cu
#define CHARACTER_SELECT_SUPPORT_IDS_OFFSET 0x220u
#define CHARACTER_SELECT_SUPPORT_STATES_OFFSET 0x248u
#define CHARACTER_SELECT_SUPPORT_CAPACITY 40u

#define SUPPORT_STATE_AVAILABLE 4u

#define NATIVE_POPULATE_SUPPORT_LIST_ADDRESS 0x003BB210u
#define NATIVE_SUPPORT_COMPATIBILITY_ADDRESS 0x008858C0u
#define NATIVE_SUPPORT_DISPLAY_ID_ADDRESS 0x008859A0u
#define NATIVE_SELECTED_SUPPORT_ID_ADDRESS 0x003B4D30u
#define NATIVE_SELECTED_SUPPORT_NAME_DRAW_ADDRESS 0x003B8A90u

#define FRAME_POINTER_ADDRESS 0x006073FCu
#define FONT_RENDERER_POINTER_ADDRESS 0x00607470u
#define FONT_SET_CONTEXT_ADDRESS 0x001866D0u
#define TEXT_DRAW_ADDRESS 0x00378F50u

#define FRAME_SCREEN_CONTEXT_OFFSET 0x150u
#define FONT_RENDERER_CONTEXT_OFFSET 0x6Cu
#define FONT_RENDERER_FLAGS_OFFSET 0x70u
#define FONT_RENDERER_ASCII_MODE_FLAG 0x08u

#define FONT_V2_FLAG_SHRINK_X 0x01u
#define FONT_V2_ALIGN_START 0u
#define FONT_V2_ALIGN_CENTER 1u

#define CHARACTER_SELECT_PHASE_OFFSET 0x08u
#define CHARACTER_SELECT_SIDE_OFFSET 0x0Cu
#define CHARACTER_SELECT_STATE_OFFSET 0x00u

#define CHARACTER_SELECT_PHASE_HIDDEN 2u
#define CHARACTER_SELECT_STATE_HIDDEN 4u
#define CHARACTER_SELECT_STATE_EXITING 7u

#define LEFT_NAME_CENTER_X 131.5f
#define RIGHT_NAME_CENTER_X 380.5f
#define NAME_TEXT_Y 254.0f
#define NAME_TEXT_BOX_HEIGHT 40u
#define NAME_TEXT_LINE_HEIGHT 40.0f

#define COLOR_BLACK 0xFF000000u
#define COLOR_WHITE 0xFFFFFFFFu

#define CHARACTER_SELECT_NO_SUPPORT_SECTION(name) \
    __attribute__((section(name), noinline))

typedef void (*NativePopulateSupportList)(void *character_select);
typedef u32 (*NativeSupportCompatibility)(u32 support_id, u32 character_id);
typedef u32 (*NativeSupportDisplayId)(u32 support_id);
typedef u32 (*NativeSelectedSupportId)(void *character_select);
typedef void (*NativeSelectedSupportNameDraw)(void *character_select);
typedef void (*NativeFontSetContext)(void *renderer, void *context);
typedef void (*NativeTextDraw)(float x, float y, const u8 *text, u32 color);

typedef struct FontV2Session {
    u32 previous;
    const u8 *text;
    float box_x;
    float box_y;
    u32 box_width;
    u32 box_height;
    u32 horizontal_alignment;
    u32 vertical_alignment;
    u32 flags;
    u32 line_limit;
    float line_height;
    u32 callback;
    u32 measured_width;
    u32 line_count;
    float scale_x;
    float scale_y;
    float rendered_width;
    float rendered_height;
    float draw_x;
    float draw_y;
    u32 callback_arg0;
    u32 callback_arg1;
    u32 callback_arg2;
    u32 callback_arg3;
    u32 saved_tracking;
    u32 saved_scale;
    float glyph_height;
} FontV2Session;

typedef char font_v2_session_size_must_be_0x6c[
    sizeof(FontV2Session) == 0x6Cu ? 1 : -1
];

extern int font_v2_adapter_call(FontV2Session *session);

typedef struct AdditionalSupportEntry {
    u8 support_id;
    u8 state;
    u8 display_id;
    u8 reserved;
    const u8 *name;
    u32 name_box_width;
} AdditionalSupportEntry;

static const u8 NO_SUPPORT_NAME[]
    __attribute__((
        section(".rodata.qol_character_select_no_support_entries"),
        used
    )) = "NO SUPPORT";

/*
 * Entries declared here are prepended in order. The native list and its
 * availability states remain intact behind them.
 */
static const AdditionalSupportEntry ADDITIONAL_SUPPORT_ENTRIES[]
    __attribute__((
        section(".rodata.qol_character_select_no_support_entries"),
        used
    )) = {
        {
            0x25u,
            SUPPORT_STATE_AVAILABLE,
            0x5Fu, /* Leaf record in the imported official NUN5 atlas. */
            0u,
            NO_SUPPORT_NAME,
            84u,
        },
    };

static __attribute__((always_inline)) inline
const AdditionalSupportEntry *find_additional_support_entry(u32 support_id)
{
    u8 normalized_support_id = (u8)support_id;
    u32 additional_count =
        (u32)(sizeof(ADDITIONAL_SUPPORT_ENTRIES) /
              sizeof(ADDITIONAL_SUPPORT_ENTRIES[0]));
    u32 index;

    for (index = 0u; index < additional_count; index = index + 1u) {
        if (
            normalized_support_id ==
            ADDITIONAL_SUPPORT_ENTRIES[index].support_id
        ) {
            return &ADDITIONAL_SUPPORT_ENTRIES[index];
        }
    }

    return (const AdditionalSupportEntry *)0;
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_prepend"
)
void qol_character_select_no_support_prepend(void *character_select)
{
    NativePopulateSupportList native_populate =
        (NativePopulateSupportList)NATIVE_POPULATE_SUPPORT_LIST_ADDRESS;
    u8 *base = (u8 *)character_select;
    u32 *count = (u32 *)(base + CHARACTER_SELECT_SUPPORT_COUNT_OFFSET);
    u8 *support_ids = base + CHARACTER_SELECT_SUPPORT_IDS_OFFSET;
    u8 *support_states = base + CHARACTER_SELECT_SUPPORT_STATES_OFFSET;
    u32 native_count;
    u32 additional_count;
    u32 index;

    native_populate(character_select);

    native_count = *count;
    if (native_count >= CHARACTER_SELECT_SUPPORT_CAPACITY) {
        return;
    }

    additional_count =
        (u32)(sizeof(ADDITIONAL_SUPPORT_ENTRIES) /
              sizeof(ADDITIONAL_SUPPORT_ENTRIES[0]));
    if (additional_count > CHARACTER_SELECT_SUPPORT_CAPACITY - native_count) {
        additional_count = CHARACTER_SELECT_SUPPORT_CAPACITY - native_count;
    }

    for (index = native_count; index > 0u; index = index - 1u) {
        support_ids[index + additional_count - 1u] = support_ids[index - 1u];
        support_states[index + additional_count - 1u] =
            support_states[index - 1u];
    }

    for (index = 0u; index < additional_count; index = index + 1u) {
        support_ids[index] = ADDITIONAL_SUPPORT_ENTRIES[index].support_id;
        support_states[index] = ADDITIONAL_SUPPORT_ENTRIES[index].state;
    }

    *count = native_count + additional_count;
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_is_compatible"
)
u32 qol_character_select_no_support_is_compatible(
    u32 support_id,
    u32 character_id
)
{
    NativeSupportCompatibility native_is_compatible =
        (NativeSupportCompatibility)NATIVE_SUPPORT_COMPATIBILITY_ADDRESS;
    const AdditionalSupportEntry *entry =
        find_additional_support_entry(support_id);

    if (entry != (const AdditionalSupportEntry *)0) {
        return 1u;
    }

    return native_is_compatible(support_id, character_id);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_display_id"
)
u32 qol_character_select_no_support_display_id(u32 support_id)
{
    NativeSupportDisplayId native_display_id =
        (NativeSupportDisplayId)NATIVE_SUPPORT_DISPLAY_ID_ADDRESS;
    const AdditionalSupportEntry *entry =
        find_additional_support_entry(support_id);

    if (entry != (const AdditionalSupportEntry *)0) {
        return (u32)entry->display_id;
    }

    return native_display_id(support_id);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_draw_name_callback"
)
int qol_character_select_no_support_draw_name_callback(
    u32 unused0,
    u32 unused1,
    u32 unused2,
    u32 session_address
)
{
    NativeTextDraw draw_text = (NativeTextDraw)TEXT_DRAW_ADDRESS;
    FontV2Session *session = (FontV2Session *)session_address;

    (void)unused0;
    (void)unused1;
    (void)unused2;
    draw_text(
        session->draw_x + 1.0f,
        session->draw_y + 1.0f,
        session->text,
        COLOR_BLACK
    );
    draw_text(
        session->draw_x,
        session->draw_y,
        session->text,
        COLOR_WHITE
    );
    return 0;
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_draw_selected_name"
)
void qol_character_select_no_support_draw_selected_name(
    void *character_select
)
{
    NativeSelectedSupportNameDraw native_draw =
        (NativeSelectedSupportNameDraw)
            NATIVE_SELECTED_SUPPORT_NAME_DRAW_ADDRESS;
    NativeSelectedSupportId selected_support_id =
        (NativeSelectedSupportId)NATIVE_SELECTED_SUPPORT_ID_ADDRESS;
    NativeFontSetContext set_font_context =
        (NativeFontSetContext)FONT_SET_CONTEXT_ADDRESS;
    volatile u8 *base = (volatile u8 *)character_select;
    volatile u8 *frame;
    volatile u8 *renderer;
    const AdditionalSupportEntry *entry;
    FontV2Session session;
    void *previous_context;
    u32 phase;
    u32 state;
    u32 side;
    u32 name_box_width;
    u8 previous_flags;
    float center_x;

    phase = *(volatile u32 *)(base + CHARACTER_SELECT_PHASE_OFFSET);
    state = *(volatile u32 *)(base + CHARACTER_SELECT_STATE_OFFSET);
    if (
        phase == CHARACTER_SELECT_PHASE_HIDDEN ||
        state == CHARACTER_SELECT_STATE_HIDDEN ||
        state == CHARACTER_SELECT_STATE_EXITING
    ) {
        native_draw(character_select);
        return;
    }

    entry = find_additional_support_entry(
        selected_support_id(character_select)
    );
    if (
        entry == (const AdditionalSupportEntry *)0 ||
        entry->name == (const u8 *)0
    ) {
        native_draw(character_select);
        return;
    }

    frame = *(volatile u8 **)FRAME_POINTER_ADDRESS;
    renderer = *(volatile u8 **)FONT_RENDERER_POINTER_ADDRESS;
    if (frame == (volatile u8 *)0 || renderer == (volatile u8 *)0) {
        return;
    }

    previous_context =
        *(void **)(renderer + FONT_RENDERER_CONTEXT_OFFSET);
    previous_flags = renderer[FONT_RENDERER_FLAGS_OFFSET];
    set_font_context(
        (void *)renderer,
        (void *)(frame + FRAME_SCREEN_CONTEXT_OFFSET)
    );
    renderer[FONT_RENDERER_FLAGS_OFFSET] =
        previous_flags | (u8)FONT_RENDERER_ASCII_MODE_FLAG;

    name_box_width = entry->name_box_width;
    if (name_box_width == 0u) {
        name_box_width = 1u;
    }
    side = *(volatile u32 *)(base + CHARACTER_SELECT_SIDE_OFFSET);
    center_x = side == 0u ? LEFT_NAME_CENTER_X : RIGHT_NAME_CENTER_X;

    session.text = entry->name;
    session.box_x = center_x - (float)name_box_width * 0.5f;
    session.box_y = NAME_TEXT_Y;
    session.box_width = name_box_width;
    session.box_height = NAME_TEXT_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1u;
    session.line_height = NAME_TEXT_LINE_HEIGHT;
    session.callback =
        (u32)qol_character_select_no_support_draw_name_callback;
    session.callback_arg0 = 0u;
    session.callback_arg1 = 0u;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    font_v2_adapter_call(&session);

    renderer[FONT_RENDERER_FLAGS_OFFSET] = previous_flags;
    set_font_context((void *)renderer, previous_context);
}
