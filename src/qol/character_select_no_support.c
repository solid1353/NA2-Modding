/* Build compact per-player support lists and enforce their compatibility. */

typedef unsigned char u8;
typedef signed int s32;
typedef unsigned int u32;

#define CHARACTER_SELECT_SUPPORT_CAPACITY 40u

#define CHARACTER_SELECT_DATA_OFFSET 0x24u
#define CHARACTER_SELECT_DATA_SIZE 0x454u
#define CHARACTER_SELECT_DATA_SUPPORT_COUNT_OFFSET 0x1F8u
#define CHARACTER_SELECT_DATA_SUPPORT_IDS_OFFSET 0x1FCu
#define CHARACTER_SELECT_DATA_SUPPORT_STATES_OFFSET 0x224u
#define CHARACTER_SELECT_PLAYER_OBJECTS_OFFSET 0x478u
#define CHARACTER_SELECT_PLAYER_COUNT 2u

#define CHARACTER_SELECT_PLAYER_SUPPORT_INDEX_OFFSET 0x30u
#define CHARACTER_SELECT_PLAYER_SUPPORT_PAGE_OFFSET 0x34u
#define CHARACTER_SELECT_PLAYER_DATA_POINTER_OFFSET 0x74u
#define CHARACTER_SELECT_PLAYER_LINKED_MODE_OFFSET 0x10u
#define CHARACTER_SELECT_PLAYER_SECONDARY_SELECTION_OFFSET 0x08u
#define CHARACTER_SELECT_PLAYER_RETURN_READY_OFFSET 0xA0u

#define SUPPORT_STATE_AVAILABLE 4u
#define NO_SUPPORT_ID 0x25u
#define CHARACTER_SELECT_LINKED_MODE_MANUAL 0u

#define CHARACTER_SELECT_STATE_FIGHTER_SELECTION 1u
#define CHARACTER_SELECT_STATE_ENTERING_SUPPORT_SELECTION 2u
#define CHARACTER_SELECT_STATE_SUPPORT_SELECTION 5u
#define CHARACTER_SELECT_STATE_FINALIZED 12u

#define NATIVE_POPULATE_SUPPORT_LIST_ADDRESS 0x003BB210u
#define NATIVE_SELECTED_CHARACTER_ID_ADDRESS 0x003B4A90u
#define NATIVE_CONFIRM_FIGHTER_ADDRESS 0x003B52E0u
#define NATIVE_SUPPORT_CELL_DRAW_ADDRESS 0x0037BC40u
#define NATIVE_SUPPORT_DISPLAY_ID_ADDRESS 0x008859A0u
#define NATIVE_SELECTED_SUPPORT_ID_ADDRESS 0x003B4D30u
#define NATIVE_SELECTED_SUPPORT_NAME_DRAW_ADDRESS 0x003B8A90u
#define NATIVE_SET_CHARACTER_SELECT_STATE_ADDRESS 0x003B5670u

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
typedef u32 (*NativeSelectedCharacterId)(void *player_select);
typedef void (*NativeSupportCellDraw)(
    float x,
    float y,
    void *draw_context,
    const void *rectangle
);
typedef u32 (*NativeSupportDisplayId)(u32 support_id);
typedef u32 (*NativeSelectedSupportId)(void *character_select);
typedef void (*NativeSelectedSupportNameDraw)(void *character_select);
typedef void (*NativeConfirmFighter)(void *player_select);
typedef void (*NativeSetCharacterSelectState)(
    void *player_select,
    u32 state
);
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

typedef struct SelectableSupportPair {
    u8 character_id;
    u8 support_id;
} SelectableSupportPair;

static const u8 NO_SUPPORT_NAME[]
    __attribute__((
        section(".rodata.qol_character_select_no_support_entries"),
        used
    )) = "NO SUPPORT";

/* Entries declared here lead every compact per-player support list. */
static const AdditionalSupportEntry ADDITIONAL_SUPPORT_ENTRIES[]
    __attribute__((
        section(".rodata.qol_character_select_no_support_entries"),
        used
    )) = {
        {
            NO_SUPPORT_ID,
            SUPPORT_STATE_AVAILABLE,
            0x5Fu, /* Leaf record in the imported official NUN5 atlas. */
            0u,
            NO_SUPPORT_NAME,
            84u,
        },
    };

/*
 * Exact Character Select compatibility whitelist. Each row is directional:
 * the first byte is the selected fighter and the second is the support ID.
 * Bidirectional relationships therefore have one row in each direction.
 */
static const SelectableSupportPair SELECTABLE_SUPPORT_PAIRS[]
    __attribute__((
        section(".rodata.qol_character_select_no_support_entries"),
        used
    )) = {
        {0x39u, 0x01u}, /* Naruto -> Sakura */
        {0x39u, 0x20u}, /* Naruto -> Sai */
        {0x39u, 0x08u}, /* Naruto -> Gaara */
        {0x3Au, 0x00u}, /* Sakura -> Naruto */
        {0x3Au, 0x1Bu}, /* Sakura -> Chiyo */
        {0x3Eu, 0x01u}, /* Chiyo -> Sakura */
        {0x47u, 0x0Eu}, /* Itachi -> Kisame */
        {0x48u, 0x0Du}, /* Kisame -> Itachi */
        {0x3Fu, 0x0Bu}, /* Sasori -> Deidara */
        {0x40u, 0x1Eu}, /* Deidara -> Sasori */
        {0x5Du, 0x1Cu}, /* Sasuke -> Orochimaru */
        {0x5Du, 0x00u}, /* Sasuke -> Naruto */
        {0x59u, 0x21u}, /* Orochimaru -> Sasuke */
        {0x54u, 0x18u}, /* Tsunade -> Jiraiya */
        {0x44u, 0x13u}, /* Shikamaru -> Choji */
    };

/*
 * Native Character Select points both players at one shared selector-data
 * block. Copy the complete block, including the character and support portrait
 * object tables, so each selector can retain a different compact roster.
 */
static u8 CHARACTER_SELECT_DATA_COPIES
    [CHARACTER_SELECT_PLAYER_COUNT][CHARACTER_SELECT_DATA_SIZE]
    __attribute__((
        section(".bss.qol_character_select_no_support_buffers"),
        aligned(4),
        used
    ));

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

static __attribute__((always_inline)) inline
u32 is_selectable_support_pair(u32 character_id, u32 support_id)
{
    u8 normalized_character_id = (u8)character_id;
    u8 normalized_support_id = (u8)support_id;
    u32 pair_count =
        (u32)(sizeof(SELECTABLE_SUPPORT_PAIRS) /
              sizeof(SELECTABLE_SUPPORT_PAIRS[0]));
    u32 index;

    for (index = 0u; index < pair_count; index = index + 1u) {
        if (
            normalized_character_id ==
                SELECTABLE_SUPPORT_PAIRS[index].character_id &&
            normalized_support_id ==
                SELECTABLE_SUPPORT_PAIRS[index].support_id
        ) {
            return 1u;
        }
    }

    return 0u;
}

static __attribute__((always_inline)) inline
void copy_character_select_data(u8 *destination, const u8 *source)
{
    u32 index;

    for (index = 0u; index < CHARACTER_SELECT_DATA_SIZE; index = index + 1u) {
        destination[index] = source[index];
    }
}

static __attribute__((always_inline)) inline
void populate_compact_support_list(u8 *data, u32 character_id)
{
    u32 *count =
        (u32 *)(data + CHARACTER_SELECT_DATA_SUPPORT_COUNT_OFFSET);
    u8 *support_ids = data + CHARACTER_SELECT_DATA_SUPPORT_IDS_OFFSET;
    u8 *support_states = data + CHARACTER_SELECT_DATA_SUPPORT_STATES_OFFSET;
    u8 native_ids[CHARACTER_SELECT_SUPPORT_CAPACITY];
    u8 native_states[CHARACTER_SELECT_SUPPORT_CAPACITY];
    u32 native_count = *count;
    u32 additional_count =
        (u32)(sizeof(ADDITIONAL_SUPPORT_ENTRIES) /
              sizeof(ADDITIONAL_SUPPORT_ENTRIES[0]));
    u32 pair_count =
        (u32)(sizeof(SELECTABLE_SUPPORT_PAIRS) /
              sizeof(SELECTABLE_SUPPORT_PAIRS[0]));
    u32 output_count = 0u;
    u32 index;
    u32 source_index;

    if (native_count > CHARACTER_SELECT_SUPPORT_CAPACITY) {
        native_count = CHARACTER_SELECT_SUPPORT_CAPACITY;
    }
    for (index = 0u; index < native_count; index = index + 1u) {
        native_ids[index] = support_ids[index];
        native_states[index] = support_states[index];
    }

    for (
        index = 0u;
        index < additional_count &&
            output_count < CHARACTER_SELECT_SUPPORT_CAPACITY;
        index = index + 1u
    ) {
        support_ids[output_count] =
            ADDITIONAL_SUPPORT_ENTRIES[index].support_id;
        support_states[output_count] =
            ADDITIONAL_SUPPORT_ENTRIES[index].state;
        output_count = output_count + 1u;
    }

    for (
        index = 0u;
        index < pair_count && output_count < CHARACTER_SELECT_SUPPORT_CAPACITY;
        index = index + 1u
    ) {
        if (
            (u8)character_id !=
            SELECTABLE_SUPPORT_PAIRS[index].character_id
        ) {
            continue;
        }
        for (
            source_index = 0u;
            source_index < native_count;
            source_index = source_index + 1u
        ) {
            if (
                native_ids[source_index] ==
                SELECTABLE_SUPPORT_PAIRS[index].support_id
            ) {
                support_ids[output_count] = native_ids[source_index];
                support_states[output_count] = native_states[source_index];
                output_count = output_count + 1u;
                break;
            }
        }
    }

    *count = output_count;
    for (
        index = output_count;
        index < CHARACTER_SELECT_SUPPORT_CAPACITY;
        index = index + 1u
    ) {
        support_ids[index] = 0x24u;
        support_states[index] = 7u;
    }
}

static __attribute__((always_inline)) inline
void clamp_support_cursor(void *player_select, u32 support_count)
{
    u8 *player = (u8 *)player_select;
    u32 *support_index =
        (u32 *)(player + CHARACTER_SELECT_PLAYER_SUPPORT_INDEX_OFFSET);
    u32 *support_page =
        (u32 *)(player + CHARACTER_SELECT_PLAYER_SUPPORT_PAGE_OFFSET);

    if (*support_page != 0u || *support_index >= support_count) {
        *support_index = 0u;
        *support_page = 0u;
    }
}

static __attribute__((always_inline)) inline
u32 has_only_no_support(void *player_select)
{
    u8 *player = (u8 *)player_select;
    u8 *data = *(u8 **)(
        player + CHARACTER_SELECT_PLAYER_DATA_POINTER_OFFSET
    );

    return
        data != (u8 *)0 &&
        *(u32 *)(data + CHARACTER_SELECT_DATA_SUPPORT_COUNT_OFFSET) == 1u &&
        data[CHARACTER_SELECT_DATA_SUPPORT_IDS_OFFSET] == NO_SUPPORT_ID;
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_prepend"
)
void qol_character_select_no_support_prepend(void *character_select)
{
    NativePopulateSupportList native_populate =
        (NativePopulateSupportList)NATIVE_POPULATE_SUPPORT_LIST_ADDRESS;
    NativeSelectedCharacterId selected_character_id =
        (NativeSelectedCharacterId)NATIVE_SELECTED_CHARACTER_ID_ADDRESS;
    u8 *base = (u8 *)character_select;
    u8 *shared_data = base + CHARACTER_SELECT_DATA_OFFSET;
    u32 player_index;

    native_populate(character_select);

    for (
        player_index = 0u;
        player_index < CHARACTER_SELECT_PLAYER_COUNT;
        player_index = player_index + 1u
    ) {
        void *player_select =
            *(void **)(
                base + CHARACTER_SELECT_PLAYER_OBJECTS_OFFSET +
                player_index * sizeof(void *)
            );
        u8 *player_data = CHARACTER_SELECT_DATA_COPIES[player_index];
        u32 character_id;
        u32 support_count;

        if (player_select == (void *)0) {
            continue;
        }
        *(void **)(
            (u8 *)player_select +
            CHARACTER_SELECT_PLAYER_DATA_POINTER_OFFSET
        ) = shared_data;
        character_id = selected_character_id(player_select);
        copy_character_select_data(player_data, shared_data);
        populate_compact_support_list(player_data, character_id);
        support_count =
            *(u32 *)(
                player_data + CHARACTER_SELECT_DATA_SUPPORT_COUNT_OFFSET
            );
        clamp_support_cursor(player_select, support_count);
        *(void **)(
            (u8 *)player_select +
            CHARACTER_SELECT_PLAYER_DATA_POINTER_OFFSET
        ) = player_data;
    }

    /* Newly constructed selectors use the shared block until the next refresh. */
    populate_compact_support_list(shared_data, 0xFFu);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_confirm_fighter"
)
void qol_character_select_no_support_confirm_fighter(
    void *player_select
)
{
    NativeConfirmFighter native_confirm =
        (NativeConfirmFighter)NATIVE_CONFIRM_FIGHTER_ADDRESS;
    NativeSetCharacterSelectState set_state =
        (NativeSetCharacterSelectState)
            NATIVE_SET_CHARACTER_SELECT_STATE_ADDRESS;
    u8 *player = (u8 *)player_select;

    native_confirm(player_select);

    if (
        *(u32 *)player !=
            CHARACTER_SELECT_STATE_ENTERING_SUPPORT_SELECTION ||
        !has_only_no_support(player_select)
    ) {
        return;
    }

    *(u32 *)(
        player + CHARACTER_SELECT_PLAYER_SUPPORT_INDEX_OFFSET
    ) = 0u;
    *(u32 *)(
        player + CHARACTER_SELECT_PLAYER_SUPPORT_PAGE_OFFSET
    ) = 0u;
    *(u32 *)(
        player + CHARACTER_SELECT_PLAYER_LINKED_MODE_OFFSET
    ) = CHARACTER_SELECT_LINKED_MODE_MANUAL;
    set_state(player_select, CHARACTER_SELECT_STATE_FINALIZED);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_finalize_support"
)
void qol_character_select_no_support_finalize_support(
    void *player_select
)
{
    NativeSetCharacterSelectState set_state =
        (NativeSetCharacterSelectState)
            NATIVE_SET_CHARACTER_SELECT_STATE_ADDRESS;
    u8 *player = (u8 *)player_select;

    *(u32 *)(
        player + CHARACTER_SELECT_PLAYER_LINKED_MODE_OFFSET
    ) = CHARACTER_SELECT_LINKED_MODE_MANUAL;
    set_state(player_select, CHARACTER_SELECT_STATE_FINALIZED);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_return_from_finalized"
)
void qol_character_select_no_support_return_from_finalized(
    void *player_select
)
{
    NativeSetCharacterSelectState set_state =
        (NativeSetCharacterSelectState)
            NATIVE_SET_CHARACTER_SELECT_STATE_ADDRESS;
    u8 *player = (u8 *)player_select;
    u32 next_state;

    if (
        *(u32 *)(
            player + CHARACTER_SELECT_PLAYER_RETURN_READY_OFFSET
        ) == 0u
    ) {
        return;
    }

    if (
        has_only_no_support(player_select) ||
        *(u32 *)(
            player + CHARACTER_SELECT_PLAYER_SECONDARY_SELECTION_OFFSET
        ) != 0u
    ) {
        next_state = CHARACTER_SELECT_STATE_FIGHTER_SELECTION;
    } else {
        *(u32 *)(
            player + CHARACTER_SELECT_PLAYER_LINKED_MODE_OFFSET
        ) = CHARACTER_SELECT_LINKED_MODE_MANUAL;
        next_state = CHARACTER_SELECT_STATE_SUPPORT_SELECTION;
    }

    set_state(player_select, next_state);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_draw_support_cell"
)
void qol_character_select_no_support_draw_support_cell(
    float x,
    float y,
    void *draw_context,
    const void *rectangle
)
{
    NativeSupportCellDraw native_draw =
        (NativeSupportCellDraw)NATIVE_SUPPORT_CELL_DRAW_ADDRESS;
    u8 *player_select;
    s32 carousel_offset;
    u8 *data;
    u32 support_count;
    u32 selected_index;
    s32 first_offset;
    s32 past_last_offset;

    /* FUN_003b84d0 keeps its selector and loop offset in s4 and s6. */
    __asm__ volatile(
        "move\t%0, $20\n\t"
        "move\t%1, $22\n\t"
        : "=r"(player_select), "=r"(carousel_offset)
    );

    data = *(u8 **)(
        player_select + CHARACTER_SELECT_PLAYER_DATA_POINTER_OFFSET
    );
    support_count = *(u32 *)(
        data + CHARACTER_SELECT_DATA_SUPPORT_COUNT_OFFSET
    );
    selected_index = *(u32 *)(
        player_select + CHARACTER_SELECT_PLAYER_SUPPORT_INDEX_OFFSET
    );
    if (support_count == 0u || selected_index >= support_count) {
        return;
    }

    first_offset = -(s32)selected_index;
    past_last_offset = (s32)(support_count - selected_index);
    if (
        carousel_offset < first_offset ||
        carousel_offset >= past_last_offset
    ) {
        return;
    }

    native_draw(x, y, draw_context, rectangle);
}

CHARACTER_SELECT_NO_SUPPORT_SECTION(
    ".text.qol_character_select_no_support_is_compatible"
)
u32 qol_character_select_no_support_is_compatible(
    u32 support_id,
    u32 character_id
)
{
    const AdditionalSupportEntry *entry =
        find_additional_support_entry(support_id);

    if (entry != (const AdditionalSupportEntry *)0) {
        return 1u;
    }

    return is_selectable_support_pair(character_id, support_id);
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
