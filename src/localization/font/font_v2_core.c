/*
 * Address-independent C form of the accepted Font v2 measurement and
 * preparation algorithms. The runtime injector compiles this source through
 * the generic EE C fragment extractor during composition; the payload builder
 * owns final 228.BIN placement, and this unit owns no hooks or addresses.
 */

typedef unsigned char u8;
typedef signed char s8;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;

/*
 * Screen geometry uses the game's local coordinates, not capture pixels.
 * Larger X moves right; smaller X moves left. Larger Y moves down; smaller Y
 * moves up. Larger widths wrap later. Address, offset, flag, count, and buffer
 * constants are internal contracts, not visual tuning controls.
 */

/* === Shared layout engine: internal flags and alignment modes === */

/* Allows horizontal shrinking when measured text exceeds its box width. */
#define FONT_V2_FLAG_SHRINK_X 0x01u

/* Makes measurement treat the four-byte <br> tag as a line break. */
#define FONT_V2_FLAG_BR_TAGS 0x02u

/* Makes measurement treat an actual '\n' byte as a line break. */
#define FONT_V2_FLAG_NEWLINE_BYTES 0x04u

/* Uses line_height as row spacing instead of the glyph's native advance. */
#define FONT_V2_FLAG_SEPARATE_LINE_ADVANCE 0x08u

/* Scales row spacing together with vertical text scale when enabled. */
#define FONT_V2_FLAG_SCALE_LINE_ADVANCE 0x20u

/* Overrides drawn glyph-quad height; misuse visibly squeezes or stretches text. */
#define FONT_V2_FLAG_GLYPH_HEIGHT 0x40u

/* Uses the caller-supplied horizontal scale instead of deriving an overflow fit. */
#define FONT_V2_FLAG_FIXED_SCALE_X 0x80u

/* Native fallback row advance when no separate line spacing is requested. */
#define FONT_V2_NATIVE_LINE_ADVANCE 40.0f

/* Trusts caller-supplied measured_width and line_count instead of remeasuring. */
#define FONT_V2_FLAG_PREMEASURED 0x10u

/* Anchors content at the box's left or top edge. */
#define FONT_V2_ALIGN_START 0u

/* Centers content within the box on the selected axis. */
#define FONT_V2_ALIGN_CENTER 1u

/* Anchors content at the box's right or bottom edge. */
#define FONT_V2_ALIGN_END 2u

/* === Native renderer ABI: fixed addresses and structure offsets === */

/* Fixed EE address containing NA2's live renderer pointer; do not tune. */
#define FONT_RENDERER_POINTER_ADDRESS 0x00607470u

/* Fixed EE address of NA2's live horizontal text scale; do not tune. */
#define FONT_HORIZONTAL_SCALE_ADDRESS 0x0060737Cu

/* Fixed renderer-field offset for extra inter-character tracking. */
#define FONT_RENDERER_TRACKING_OFFSET 0x3Cu

/* Fixed renderer-field offset and bit for the ordinary ASCII glyph mode. */
#define FONT_RENDERER_FLAGS_OFFSET 0x70u
#define FONT_RENDERER_ASCII_MODE_FLAG 0x08u

/* Fixed renderer-field offset for the caller's logical X position. */
#define FONT_RENDERER_POSITION_X_OFFSET 0x14u

/* Fixed renderer-field offset for the caller's logical Y position. */
#define FONT_RENDERER_POSITION_Y_OFFSET 0x18u

/* Fixed renderer-field offset for the current draw-origin X. */
#define FONT_RENDERER_DRAW_X_OFFSET 0x28u

/* Fixed renderer-field offset for the current draw-origin Y. */
#define FONT_RENDERER_DRAW_Y_OFFSET 0x2Cu

/* Fixed renderer-field offset for the active native drawing context. */
#define FONT_RENDERER_CONTEXT_OFFSET 0x6Cu

/* Fixed native renderer-initialization function address; do not tune. */
#define FONT_INITIALIZE_ADDRESS 0x00186510u

/* Fixed native renderer-context setter address; do not tune. */
#define FONT_SET_CONTEXT_ADDRESS 0x001866D0u

/* Fixed native renderer-position setter address; do not tune. */
#define FONT_SET_POSITION_ADDRESS 0x00186700u

/* Fixed native renderer-color setter address; do not tune. */
#define FONT_SET_COLOR_ADDRESS 0x00186B30u

/* Fixed ordinary native text-draw function address; do not tune. */
#define FONT_DRAW_ADDRESS 0x00379040u

/* Fixed unselected section-heading draw function address; do not tune. */
#define FONT_HEADING_DRAW_ADDRESS 0x00378FD0u

/* Fixed ordinary colored text-draw function address; do not tune. */
#define FONT_BODY_DRAW_ADDRESS 0x00378F50u

/* Fixed Battle Settings/Jutsu native draw function address; do not tune. */
#define FONT_JUTSU_DRAW_ADDRESS 0x00188140u

/* Fixed selected Character Select row draw function address; do not tune. */
#define FONT_CHARACTER_SELECTED_DRAW_ADDRESS 0x00382610u

/* === Control Settings: first eight action labels === */

/* Label box width; larger values delay shrinking and widen rendered labels. */
#define FONT_CONTROLS_BOX_WIDTH 128u

/* Label box height used for vertical centering. */
#define FONT_CONTROLS_BOX_HEIGHT 20u

/* Single-row layout height used by the Controls adapter. */
#define FONT_CONTROLS_LINE_HEIGHT 20.0f

/* === Battle Settings and Practice Settings rows === */

/* NUN5 left edge and width for Battle Settings labels. */
#define FONT_BATTLE_SETTINGS_LABEL_X 92.0f
#define FONT_BATTLE_SETTINGS_LABEL_WIDTH 158u

/* NUN5 left edge and width for Practice Settings labels. */
#define FONT_PRACTICE_SETTINGS_LABEL_X 92.0f
#define FONT_PRACTICE_SETTINGS_LABEL_WIDTH 150u

/* NUN5 left edge and width for both settings value columns. */
#define FONT_SETTINGS_VALUE_X 303.25f
#define FONT_SETTINGS_VALUE_WIDTH 104u

/* NUN5 uses one 104-unit box; descriptive phrases retain their accepted fit. */
#define FONT_SETTINGS_PHRASE_FIT_WIDTH 99u
#define FONT_SETTINGS_PHRASE_X_OFFSET -1.5f

/* Raster-phase correction when NA2's special-value branch enters ASCII mode. */
#define FONT_SETTINGS_SPECIAL_VALUE_X_OFFSET -1.0f

/* Shared geometry for digit-leading Settings values. */
#define FONT_SETTINGS_NUMERIC_VALUE_X_OFFSET 1.8f
#define FONT_SETTINGS_NUMERIC_VALUE_Y_OFFSET 1.875f
#define FONT_SETTINGS_NUMERIC_VALUE_SCALE_X 1.02f
#define FONT_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT 26.0f

/* Shared row baselines; selected labels use the taller selected glyph pass. */
#define FONT_BATTLE_SETTINGS_ROW_Y_OFFSET 1.0f
#define FONT_PRACTICE_SETTINGS_ROW_Y_OFFSET 0.75f
#define FONT_SETTINGS_SELECTED_Y_OFFSET 1.5f

/* NUN5 left edge and width for the Practice Settings section heading. */
#define FONT_PRACTICE_SETTINGS_HEADING_X 84.0f
#define FONT_PRACTICE_SETTINGS_HEADING_WIDTH 158u

/* Native one-line height retained by every Settings row adapter. */
#define FONT_SETTINGS_LINE_HEIGHT 20.0f

/* === Ninja Song objective and arithmetic rows === */

/* NUN5 objective text box geometry relative to the native NA2 origin. */
#define FONT_NINJA_OBJECTIVE_X_OFFSET -10.0f
#define FONT_NINJA_OBJECTIVE_WRAP_WIDTH 300u
#define FONT_NINJA_OBJECTIVE_WIDTH 288u
#define FONT_NINJA_OBJECTIVE_LINE_LIMIT 2u
#define FONT_NINJA_OBJECTIVE_LINE_ADVANCE 16.0f
#define FONT_NINJA_OBJECTIVE_GLYPH_HEIGHT 20.0f

/* NUN5 arithmetic positions relative to the shared formula origin. */
#define FONT_NINJA_FORMULA_Y_OFFSET 0.975f
#define FONT_NINJA_HITS_X_OFFSET 176.0f
#define FONT_NINJA_HITS_Y_OFFSET -6.0f
#define FONT_NINJA_HITS_SCALE_X 0.62f
#define FONT_NINJA_HITS_WIDTH 52u
#define FONT_NINJA_HITS_HEIGHT 32u
#define FONT_NINJA_EQUALS_X_OFFSET 227.0f
#define FONT_NINJA_TOTAL_X_OFFSET 263.4f
#define FONT_NINJA_TOTAL_WIDTH 64u
#define FONT_NINJA_EMPTY_X_OFFSET 256.075f
#define FONT_NINJA_EMPTY_WIDTH 96u
#define FONT_NINJA_EMPTY_SCALE_X 0.97f
#define FONT_NINJA_SINGLE_LINE_HEIGHT 20.0f

/* Fixed NA2 Ninja Song renderer data contracts; do not tune. */
#define FONT_NINJA_MULTIPLY_POINTER_ADDRESS 0x00899A90u
#define FONT_NINJA_EQUALS_POINTER_ADDRESS 0x00899A94u
#define FONT_NINJA_EMPTY_POINTER_ADDRESS 0x00899A98u
#define FONT_NINJA_UNIT_TABLE_ADDRESS 0x00899AE0u
#define FONT_NINJA_MULTIPLIER_TABLE_ADDRESS 0x008C3CB0u
#define FONT_NINJA_RENDERER_FLAGS_OFFSET 0x70u

/* === Command Chart: title === */

/* Left edge of the Command Chart title; increase to move it right. */
#define FONT_COMMAND_TITLE_BOX_X 27.2f

/* Title width; larger values shrink less and permit longer titles. */
#define FONT_COMMAND_TITLE_BOX_WIDTH 288u

/* Added to the native title Y; more negative moves the title up. */
#define FONT_COMMAND_TITLE_Y_OFFSET -3.8f

/* === Command Chart: relationship descriptions and inline icons === */

/* Fixed runtime address of the Command Chart text table; do not tune. */
#define FONT_COMMAND_TEXT_TABLE_ADDRESS 0x008BD1D0u

/* Left edge of wrapped relationship text; increase to move it right. */
#define FONT_COMMAND_RELATION_BOX_X 43.2f

/* Added to wrapped-block Y; more negative moves multiline text up. */
#define FONT_COMMAND_RELATION_Y_OFFSET -11.5f

/* Added only to fitting one-line relationship text; more negative moves it up. */
#define FONT_COMMAND_RELATION_SINGLE_LINE_Y_OFFSET -8.0f

/* Relationship text width; larger values wrap later. */
#define FONT_COMMAND_RELATION_BOX_WIDTH 226u

/* Relationship box height used to center one- or two-line output. */
#define FONT_COMMAND_RELATION_BOX_HEIGHT 32u

/* Vertical distance between wrapped relationship lines. */
#define FONT_COMMAND_RELATION_LINE_HEIGHT 30.0f

/* Requested relationship glyph-quad height when that override is enabled. */
#define FONT_COMMAND_RELATION_GLYPH_HEIGHT 14.0f

/* Maximum relationship lines; reduce only if truncation is intentionally desired. */
#define FONT_COMMAND_RELATION_LINE_LIMIT 2u

/* Icon X offset when the relationship-description row is present. */
#define FONT_COMMAND_ICON_RELATION_OFFSET 16.0f

/* Icon X offset when no relationship-description row precedes the commands. */
#define FONT_COMMAND_ICON_PLAIN_OFFSET 38.0f

/* === Battle Settings: left and right Jutsu-selector lists === */

/* Nominal wrap width; larger values produce fewer or later line breaks. */
#define FONT_JUTSU_BOX_WIDTH 186u

/* Wrapped-block box height used for vertical centering. */
#define FONT_JUTSU_BOX_HEIGHT 32u

/* Horizontal correction for the left list; more negative moves rows left. */
#define FONT_JUTSU_LEFT_X_OFFSET -8.0f

/* Horizontal correction for the right list; more negative moves rows left. */
#define FONT_JUTSU_RIGHT_X_OFFSET -4.0f

/* Draw-width multiplier shared by one-line and wrapped Jutsu-title rows. */
#define FONT_JUTSU_HORIZONTAL_SCALE 0.96f

/* Vertical correction for fitting one-line rows; more negative moves them up. */
#define FONT_JUTSU_SINGLE_LINE_Y_OFFSET -4.0f

/* Applied only to wrapped blocks; more negative moves the block up. */
#define FONT_JUTSU_Y_OFFSET -6.5f

/* Native X below this value is classified as the left-side list. */
#define FONT_JUTSU_SIDE_THRESHOLD 256.0f

/* Vertical distance between wrapped Jutsu-title lines. */
#define FONT_JUTSU_LINE_ADVANCE 16.0f

/* Drawn glyph height for wrapped two-line rows; one-line rows bypass it. */
#define FONT_JUTSU_LAYOUT_GLYPH_HEIGHT 22.0f

/* Target maximum line count for adaptive wrapping. */
#define FONT_JUTSU_LINE_LIMIT 2u

/* Higher values widen the retry box more aggressively after a third line appears. */
#define FONT_JUTSU_OVERFLOW_WIDTH_FACTOR 0.4f

/* Extra width added per retry until the title fits within the line limit. */
#define FONT_JUTSU_WRAP_WIDTH_STEP 16.0f

/* === Collection: Movie and character move-list classification === */

/* First text address classified as a Movie row; fixed identity boundary. */
#define FONT_COLLECTION_MOVIE_TEXT_START 0x003FFAA0u

/* Exclusive end of the Movie-row text range; fixed identity boundary. */
#define FONT_COLLECTION_MOVIE_TEXT_END 0x003FFC10u

/* Fixed first narrow Figure-row text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_152_TEXT_0 0x006D9BD8u

/* Fixed second narrow Figure-row text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_152_TEXT_1 0x006D9C00u

/* Fixed third narrow Figure-row text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_152_TEXT_2 0x006D9C40u

/* Fixed first wide character-list text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_192_TEXT_0 0x006DC340u

/* Fixed second wide character-list text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_192_TEXT_1 0x006DC370u

/* Fixed third wide character-list text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_192_TEXT_2 0x006DC3A0u

/* Fixed fourth wide character-list text pointer; not a position value. */
#define FONT_CHARACTER_MOVE_192_TEXT_3 0x006DC3C0u

/* Added to wrapped Collection rows; more negative moves the block up. */
#define FONT_COLLECTION_LIST_BOX_Y_OFFSET -10.0f

/* Movie-list wrap width; larger values wrap later. */
#define FONT_COLLECTION_MOVIE_BOX_WIDTH 192u

/* Narrow Figure-page wrap width; larger values wrap later. */
#define FONT_CHARACTER_MOVE_152_BOX_WIDTH 152u

/* Wide character-page wrap width; larger values wrap later. */
#define FONT_CHARACTER_MOVE_192_BOX_WIDTH 192u

/* Collection row box height used for vertical block placement. */
#define FONT_COLLECTION_LIST_BOX_HEIGHT 32u

/* Vertical distance between wrapped Collection-row lines. */
#define FONT_COLLECTION_LIST_LINE_ADVANCE 16.0f

/* Glyph height used for Collection block layout, not automatic squeezing. */
#define FONT_COLLECTION_LIST_GLYPH_HEIGHT 20.0f

/* Maximum wrapped lines supported by the Collection list adapter. */
#define FONT_COLLECTION_LIST_LINE_LIMIT 2u

/* === Practice: screen title === */

/* Left edge of the Practice title; increase to move it right. */
#define FONT_PRACTICE_TITLE_BOX_X 31.2f

/* Practice-title width; larger values shrink less. */
#define FONT_PRACTICE_TITLE_BOX_WIDTH 352u

/* Added to native Practice-title Y; more negative moves it up. */
#define FONT_PRACTICE_TITLE_Y_OFFSET -6.8f

/* === Shared Command Chart and Practice title geometry === */

/* Shared title box height used for vertical placement. */
#define FONT_TITLE_BOX_HEIGHT 20u

/* Shared single-line title height. */
#define FONT_TITLE_LINE_HEIGHT 20.0f

/* === Pause menu: Controls list === */

/* Pause label width; larger values shrink less. */
#define FONT_PAUSE_LIST_BOX_WIDTH 216u

/* Pause label box height used for vertical centering. */
#define FONT_PAUSE_LIST_BOX_HEIGHT 20u

/* Added to every Pause Controls row Y; more negative moves rows up. */
#define FONT_PAUSE_LIST_Y_OFFSET -4.0f

/* Extra X correction for the selected red row; positive moves it right. */
#define FONT_PAUSE_LIST_SELECTED_X_OFFSET 2.0f

/* Single-row layout height for Pause Controls labels. */
#define FONT_PAUSE_LIST_LINE_HEIGHT 20.0f

/* === Character Select: player-mode option list === */

/* Option-row width; larger values shrink less. */
#define FONT_CHARACTER_LIST_BOX_WIDTH 240u

/* Option-row box height used for vertical centering. */
#define FONT_CHARACTER_LIST_BOX_HEIGHT 20u

/* Added to ordinary option-row X; positive moves rows right. */
#define FONT_CHARACTER_LIST_X_OFFSET 5.0f

/* Single-row layout height for Character Select options. */
#define FONT_CHARACTER_LIST_LINE_HEIGHT 20.0f

/* === Shared Yes/No selectors: quit, return, and Special Controls === */

/* Exact native Y bit pattern identifying the ordinary Yes row. */
#define FONT_QUIT_YES_SOURCE_BITS 0x41C00000u

/* Exact native Y bit pattern identifying the ordinary No row. */
#define FONT_QUIT_NO_SOURCE_BITS 0x42600000u

/* Target local Yes X; increase to move Yes right. */
#define FONT_QUIT_YES_X 64.5f

/* Target local Yes Y; increase to move Yes down. */
#define FONT_QUIT_YES_Y 31.5f

/* Target local No X; increase to move No right. */
#define FONT_QUIT_NO_X 68.5f

/* Target local No Y; increase to move No down. */
#define FONT_QUIT_NO_Y 49.0f

/* Collection-local Yes X; increase to move Yes right. */
#define FONT_COLLECTION_YES_X 64.2f

/* Collection-local Yes Y; increase to move Yes down. */
#define FONT_COLLECTION_YES_Y 29.85f

/* Collection-local No X; increase to move No right. */
#define FONT_COLLECTION_NO_X 68.1f

/* Collection-local No Y; increase to move No down. */
#define FONT_COLLECTION_NO_Y 48.2f

/* Marks the body-to-choice interval of the Collection exit prompt. */
#define FONT_COLLECTION_CHOICE_SCOPE 2u

/* Mode Select bottom-body X origin; larger values move it right. */
#define FONT_MODE_SELECT_BODY_BOX_X 24.0f

/* Mode Select bottom-body Y origin; smaller values move it up. */
#define FONT_MODE_SELECT_BODY_BOX_Y 12.0f

/* Mode Select bottom-body width before wrapping or shrink-only fitting. */
#define FONT_MODE_SELECT_BODY_BOX_WIDTH 420u

/* Mode Select bottom-body height available to its single text line. */
#define FONT_MODE_SELECT_BODY_BOX_HEIGHT 40u

/* Mode Select bottom-body line cadence if the source ever contains a break. */
#define FONT_MODE_SELECT_BODY_LINE_HEIGHT 20.0f

/* Mode Select bottom body is intentionally limited to one line. */
#define FONT_MODE_SELECT_BODY_LINE_LIMIT 1u

/* Fixed runtime pointer identifying Special Controls ON. */
#define FONT_SPECIAL_ON_TEXT 0x006059F0u

/* Fixed runtime pointer identifying Special Controls OFF. */
#define FONT_SPECIAL_OFF_TEXT 0x006059F8u

/* Special Controls ON local X; increase to move it right. */
#define FONT_SPECIAL_ON_X 66.0f

/* Special Controls ON local Y; increase to move it down. */
#define FONT_SPECIAL_ON_Y 31.0f

/* Special Controls OFF local X; increase to move it right. */
#define FONT_SPECIAL_OFF_X 59.0f

/* Special Controls OFF local Y; increase to move it down. */
#define FONT_SPECIAL_OFF_Y 49.0f

/* Shared font-only geometry for both Special Controls choices. */
#define FONT_SPECIAL_CHOICE_BOX_WIDTH 104u
#define FONT_SPECIAL_CHOICE_BOX_HEIGHT 20u
#define FONT_SPECIAL_CHOICE_LINE_HEIGHT 20.0f
#define FONT_SPECIAL_CHOICE_SELECTED_X_OFFSET 1.0f
#define FONT_SPECIAL_CHOICE_SELECTED_SCALE_X 1.02f
#define FONT_SPECIAL_CHOICE_UNSELECTED_SCALE_X 1.01f
#define FONT_SPECIAL_CHOICE_GLYPH_HEIGHT 26.0f

/* === Battle/Practice quit-confirmation body === */

/* Quit prompt body left edge; increase to move the body right. */
#define FONT_QUIT_BODY_BOX_X 19.0f

/* Quit prompt body top edge; increase to move the body down. */
#define FONT_QUIT_BODY_BOX_Y 12.0f

/* Quit prompt width; larger values wrap later. */
#define FONT_QUIT_BODY_BOX_WIDTH 420u

/* Quit prompt box height used to place its wrapped block. */
#define FONT_QUIT_BODY_BOX_HEIGHT 40u

/* Vertical distance between quit-prompt lines. */
#define FONT_QUIT_BODY_LINE_HEIGHT 20.0f

/* Maximum quit-prompt line count. */
#define FONT_QUIT_BODY_LINE_LIMIT 2u

/* === Character Select return-confirmation body === */

/* Return prompt left edge; increase to move the body right. */
#define FONT_CHARACTER_BODY_BOX_X 8.0f

/* Return prompt top edge; increase to move the body down. */
#define FONT_CHARACTER_BODY_BOX_Y 8.0f

/* Return prompt width; larger values wrap later or shrink less. */
#define FONT_CHARACTER_BODY_BOX_WIDTH 368u

/* Return prompt box height used for vertical centering. */
#define FONT_CHARACTER_BODY_BOX_HEIGHT 24u

/* Return prompt line height. */
#define FONT_CHARACTER_BODY_LINE_HEIGHT 20.0f

/* Keeps the Character Select return prompt on one line. */
#define FONT_CHARACTER_BODY_LINE_LIMIT 1u

/* === Special Controls explanatory body === */

/* Special Controls body left edge; increase to move it right. */
#define FONT_SPECIAL_BODY_BOX_X 24.0f

/* Special Controls body top edge; increase to move it down. */
#define FONT_SPECIAL_BODY_BOX_Y 12.0f

/* Special Controls body width; larger values wrap later. */
#define FONT_SPECIAL_BODY_BOX_WIDTH 400u

/* Special Controls body height used for vertical placement. */
#define FONT_SPECIAL_BODY_BOX_HEIGHT 60u

/* Vertical distance between Special Controls body lines. */
#define FONT_SPECIAL_BODY_LINE_HEIGHT 20.0f

/* Maximum Special Controls body line count. */
#define FONT_SPECIAL_BODY_LINE_LIMIT 2u

/* === Collection exit-confirmation body === */

/* Collection exit body left edge; increase to move it right. */
#define FONT_COLLECTION_BODY_BOX_X 24.8f

/* Collection exit body top edge; increase to move it down. */
#define FONT_COLLECTION_BODY_BOX_Y 12.0f

/* Collection exit body width; larger values wrap later. */
#define FONT_COLLECTION_BODY_BOX_WIDTH 400u

/* Collection exit body height used for vertical placement. */
#define FONT_COLLECTION_BODY_BOX_HEIGHT 60u

/* Collection exit body glyph width; larger values widen visible letters. */
#define FONT_COLLECTION_BODY_SCALE_X 1.0f

/* Vertical distance between Collection exit body lines. */
#define FONT_COLLECTION_BODY_LINE_HEIGHT 20.0f

/* Maximum Collection exit body line count. */
#define FONT_COLLECTION_BODY_LINE_LIMIT 2u

/* === Shared temporary body storage: internal capacity === */

/* Maximum copied body/list text bytes including the terminator; not geometry. */
#define FONT_BODY_BUFFER_SIZE 0x100u

/* === Practice explanations and inline controller icons === */

/* Fixed runtime address of Practice's native icon records; do not tune. */
#define FONT_PRACTICE_ICON_TABLE_ADDRESS 0x008D14C0u

/* Fixed runtime address of Practice's native text table; do not tune. */
#define FONT_PRACTICE_TEXT_TABLE_ADDRESS 0x008BD510u

/* Practice explanation left edge; increase to move the block right. */
#define FONT_PRACTICE_BOX_X 39.2f

/* Added to native explanation Y; increase to move the block down. */
#define FONT_PRACTICE_BOX_Y_OFFSET 21.2f

/* Explanation width; larger values wrap later. */
#define FONT_PRACTICE_BOX_WIDTH 364u

/* Explanation box height used for vertical placement. */
#define FONT_PRACTICE_BOX_HEIGHT 48u

/* Glyph-quad height used by the Practice explanation renderer. */
#define FONT_PRACTICE_GLYPH_HEIGHT 28.0f

/* Vertical distance between wrapped Practice explanation lines. */
#define FONT_PRACTICE_LINE_ADVANCE 14.0f

/* Zero means Practice explanations have no artificial line-count limit. */
#define FONT_PRACTICE_LINE_LIMIT 0u

/* Number of direct text/icon token records in the native token table. */
#define FONT_PRACTICE_TOKEN_COUNT 13u

/* Byte stride between direct Practice token records. */
#define FONT_PRACTICE_TOKEN_STRIDE 16u

/* Number of entries in the controller-icon remapping table. */
#define FONT_PRACTICE_ICON_MAP_COUNT 18u

/* Maximum assembled mixed text/icon bytes including the terminator. */
#define FONT_PRACTICE_BUFFER_SIZE 0x200u

#define FONT_V2_SECTION(name) \
    __attribute__((section(name), noinline))

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

typedef union FontV2Bits {
    u32 u;
    s32 s;
    float f;
} FontV2Bits;

typedef struct FontV2BodyFrame {
    FontV2Session session;
    u8 padding[0x14];
    u8 buffer[FONT_BODY_BUFFER_SIZE];
} FontV2BodyFrame;

typedef struct FontV2PracticeFrame {
    FontV2Session session;
    u32 object_primary;
    u32 object_secondary;
    u32 saved_metric_callback;
    u32 saved_draw_callback;
    u32 padding;
    u8 buffer[FONT_PRACTICE_BUFFER_SIZE];
} FontV2PracticeFrame;

typedef struct FontV2IconRecord {
    u32 unknown;
    s16 width;
    s16 height;
} FontV2IconRecord;

typedef struct FontV2UiDrawRecord {
    float draw_x;
    float draw_y;
    const u8 *text;
    u32 arg2;
} FontV2UiDrawRecord;

typedef struct FontV2SpecialChoiceFrame {
    FontV2Session session;
    u32 native_arg3;
} FontV2SpecialChoiceFrame;

#define FONT_V2_OFFSET(type, member) ((u32)&(((type *)0)->member))
#define FONT_V2_ASSERT(name, expression) \
    typedef char font_v2_assert_##name[(expression) ? 1 : -1]

FONT_V2_ASSERT(text_offset, FONT_V2_OFFSET(FontV2Session, text) == 0x04);
FONT_V2_ASSERT(flags_offset, FONT_V2_OFFSET(FontV2Session, flags) == 0x20);
FONT_V2_ASSERT(callback_offset, FONT_V2_OFFSET(FontV2Session, callback) == 0x2C);
FONT_V2_ASSERT(measured_width_offset,
               FONT_V2_OFFSET(FontV2Session, measured_width) == 0x30);
FONT_V2_ASSERT(scale_x_offset,
               FONT_V2_OFFSET(FontV2Session, scale_x) == 0x38);
FONT_V2_ASSERT(draw_x_offset, FONT_V2_OFFSET(FontV2Session, draw_x) == 0x48);
FONT_V2_ASSERT(saved_scale_offset,
               FONT_V2_OFFSET(FontV2Session, saved_scale) == 0x64);
FONT_V2_ASSERT(glyph_height_offset,
               FONT_V2_OFFSET(FontV2Session, glyph_height) == 0x68);
FONT_V2_ASSERT(session_size, sizeof(FontV2Session) == 0x6C);
FONT_V2_ASSERT(special_choice_arg3_offset,
               FONT_V2_OFFSET(FontV2SpecialChoiceFrame, native_arg3) ==
                   0x6C);
FONT_V2_ASSERT(body_buffer_offset,
               FONT_V2_OFFSET(FontV2BodyFrame, buffer) == 0x80);
FONT_V2_ASSERT(practice_primary_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, object_primary) == 0x6C);
FONT_V2_ASSERT(practice_secondary_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, object_secondary) == 0x70);
FONT_V2_ASSERT(practice_metric_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, saved_metric_callback) ==
                   0x74);
FONT_V2_ASSERT(practice_draw_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, saved_draw_callback) ==
                   0x78);
FONT_V2_ASSERT(practice_buffer_offset,
               FONT_V2_OFFSET(FontV2PracticeFrame, buffer) == 0x80);

extern const u8 font_v2_ascii_widths[95];
extern FontV2Session *font_v2_active_session;
extern volatile u32 font_v2_quit_active;
extern const u8 font_v2_practice_tokens[];
extern const u8 font_v2_practice_icon_map[];
extern int font_v2_controls_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_title_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_pause_list_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_pause_list_selected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_quit_unselected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_special_choice_selected_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_quit_body_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_v2_special_controls_body_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern u32 font_v2_native_measure_callback(const u8 *text);
extern void font_v2_practice_icon_draw_callback(
    u32 object,
    u32 record,
    float draw_x,
    float draw_y
);
extern int font_v2_practice_callback(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 arg3
);
extern int font_ninja_song_ascii_number(
    u32 unused,
    s32 value,
    s32 width,
    u8 *destination,
    s32 mode
);

typedef int (*FontV2Callback)(u32 arg0, u32 arg1, u32 arg2, u32 arg3);
typedef void (*FontV2NativeInitialize)(u32 renderer, u32 mode);
typedef void (*FontV2NativeSetContext)(u32 renderer, u32 context);
typedef void (*FontV2NativeSetPosition)(
    float draw_x,
    float draw_y,
    u32 renderer
);
typedef void (*FontV2NativeSetColor)(u32 renderer, u32 color, u32 mode);
typedef void (*FontV2NativeTextDraw)(u32 renderer, const u8 *text);
typedef void (*FontV2NativeDraw)(
    float draw_x,
    float draw_y,
    const u8 *text,
    u32 highlighted
);
typedef int (*FontV2NativeUiDraw)(
    u32 context,
    const FontV2UiDrawRecord *record,
    u32 state,
    s32 index
);

static u32 font_v2_is_br(const u8 *text) {
    return text[0] == (u8)'<' &&
           text[1] == (u8)'b' &&
           text[2] == (u8)'r' &&
           text[3] == (u8)'>';
}

static u32 font_v2_is_mode_select_body(const u8 *text) {
    return text &&
           text[0] == (u8)'R' &&
           text[1] == (u8)'e' &&
           text[2] == (u8)'t' &&
           text[3] == (u8)'u' &&
           text[4] == (u8)'r' &&
           text[5] == (u8)'n' &&
           text[6] == (u8)' ' &&
           text[7] == (u8)'t' &&
           text[8] == (u8)'o' &&
           text[9] == (u8)' ' &&
           text[10] == (u8)'T' &&
           text[11] == (u8)'i' &&
           text[12] == (u8)'t' &&
           text[13] == (u8)'l' &&
           text[14] == (u8)'e' &&
           text[15] == (u8)' ' &&
           text[16] == (u8)'S' &&
           text[17] == (u8)'c' &&
           text[18] == (u8)'r' &&
           text[19] == (u8)'e' &&
           text[20] == (u8)'e' &&
           text[21] == (u8)'n' &&
           text[22] == (u8)'?' &&
           text[23] == 0;
}

FONT_V2_SECTION(".text.font_v2_measure")
int font_v2_measure(
    const u8 *text,
    u32 flags,
    u32 *measured_width,
    u32 *line_count
) {
    u32 current_width = 0;
    u32 maximum_width = 0;
    u32 lines = 1;

    if (!text || !measured_width || !line_count) {
        return -1;
    }

    while (*text) {
        u32 character = *text;
        if ((flags & FONT_V2_FLAG_BR_TAGS) && font_v2_is_br(text)) {
            text += 4;
        } else if (
            (flags & FONT_V2_FLAG_NEWLINE_BYTES) &&
            character == 0x0Au
        ) {
            text += 1;
        } else {
            if (character < 0x20u || character > 0x7Eu) {
                return -1;
            }
            current_width += font_v2_ascii_widths[character - 0x20u];
            text += 1;
            continue;
        }

        if (current_width > maximum_width) {
            maximum_width = current_width;
        }
        current_width = 0;
        lines += 1;
    }

    if (current_width > maximum_width) {
        maximum_width = current_width;
    }
    *measured_width = maximum_width;
    *line_count = lines;
    return 0;
}

FONT_V2_SECTION(".text.font_v2_prepare")
int font_v2_prepare(FontV2Session *session) {
    u32 measured_width;
    u32 line_count;
    float box_width;
    float box_height;

    if (!session || !session->text) {
        return -1;
    }

    if (session->flags & FONT_V2_FLAG_PREMEASURED) {
        measured_width = session->measured_width;
        line_count = session->line_count;
    } else {
        if (font_v2_measure(
                session->text,
                session->flags,
                &measured_width,
                &line_count
            ) != 0) {
            return -1;
        }
        session->measured_width = measured_width;
        session->line_count = line_count;
    }

    if ((s32)measured_width < 0 || line_count == 0) {
        return -1;
    }
    if (session->line_limit && line_count > session->line_limit) {
        return -1;
    }
    if (!session->box_width || !session->box_height) {
        return -1;
    }

    if (session->flags & FONT_V2_FLAG_FIXED_SCALE_X) {
        if (session->scale_x <= 0.0f) {
            return -1;
        }
    } else {
        session->scale_x = 1.0f;
    }
    session->scale_y = 1.0f;
    if (session->flags & FONT_V2_FLAG_SCALE_LINE_ADVANCE) {
        session->scale_y =
            session->line_height / FONT_V2_NATIVE_LINE_ADVANCE;
    }
    if (
        !(session->flags & FONT_V2_FLAG_FIXED_SCALE_X) &&
        (session->flags & FONT_V2_FLAG_SHRINK_X) &&
        measured_width > session->box_width
    ) {
        session->scale_x =
            (float)(s32)session->box_width / (float)(s32)measured_width;
    }
    session->rendered_width =
        (float)(s32)measured_width * session->scale_x;

    if (session->flags & FONT_V2_FLAG_SEPARATE_LINE_ADVANCE) {
        session->rendered_height =
            (float)(s32)(line_count - 1u) * session->line_height +
            session->glyph_height;
    } else {
        session->rendered_height =
            (float)(s32)line_count * session->line_height;
    }

    box_width = (float)(s32)session->box_width;
    if (session->horizontal_alignment == FONT_V2_ALIGN_START) {
        session->draw_x = session->box_x;
    } else if (session->horizontal_alignment == FONT_V2_ALIGN_CENTER) {
        session->draw_x =
            session->box_x +
            (box_width - session->rendered_width) * 0.5f;
    } else if (session->horizontal_alignment == FONT_V2_ALIGN_END) {
        session->draw_x =
            session->box_x + box_width - session->rendered_width;
    } else {
        return -1;
    }

    box_height = (float)(s32)session->box_height;
    if (session->vertical_alignment == FONT_V2_ALIGN_START) {
        session->draw_y = session->box_y;
    } else if (session->vertical_alignment == FONT_V2_ALIGN_CENTER) {
        session->draw_y =
            session->box_y +
            (box_height - session->rendered_height) * 0.5f;
    } else if (session->vertical_alignment == FONT_V2_ALIGN_END) {
        session->draw_y =
            session->box_y + box_height - session->rendered_height;
    } else {
        return -1;
    }

    return 0;
}

FONT_V2_SECTION(".text.font_v2_adapter_call")
int font_v2_adapter_call(FontV2Session *session) {
    volatile u32 *renderer;
    volatile u32 *scale_bits =
        (volatile u32 *)FONT_HORIZONTAL_SCALE_ADDRESS;
    FontV2Callback callback;
    int result;

    if (!session || !session->callback) {
        return -1;
    }
    if (font_v2_prepare(session) != 0) {
        return -1;
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (!renderer) {
        return -1;
    }

    session->previous = (u32)font_v2_active_session;
    session->saved_tracking =
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)];
    session->saved_scale = *scale_bits;

    renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
    *(volatile float *)FONT_HORIZONTAL_SCALE_ADDRESS = session->scale_x;
    font_v2_active_session = session;

    callback = (FontV2Callback)session->callback;
    result = callback(
        session->callback_arg0,
        session->callback_arg1,
        session->callback_arg2,
        session->callback_arg3
    );

    *scale_bits = session->saved_scale;
    renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] =
        session->saved_tracking;
    font_v2_active_session = (FontV2Session *)session->previous;
    return result;
}

FONT_V2_SECTION(".text.font_v2_controls_adapter")
int font_v2_controls_adapter(
    const u8 *text,
    u32 style,
    float center_x,
    float draw_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = center_x - (float)(FONT_CONTROLS_BOX_WIDTH / 2u);
    session.box_y = draw_y;
    session.box_width = FONT_CONTROLS_BOX_WIDTH;
    session.box_height = FONT_CONTROLS_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CONTROLS_LINE_HEIGHT;
    session.callback = (u32)font_v2_controls_callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = (u32)&session;
    session.callback_arg3 = 0;

    return font_v2_adapter_call(&session);
}

static FONT_V2_SECTION(".text.font_v2_title_adapter_common")
int font_v2_title_adapter_common(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_y,
    float box_x,
    float y_offset,
    u32 box_width
) {
    FontV2Session session;

    session.text = text;
    session.box_x = box_x;
    session.box_y = native_y + y_offset;
    session.box_width = box_width;
    session.box_height = FONT_TITLE_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_TITLE_LINE_HEIGHT;
    session.callback = (u32)font_v2_title_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_command_title_entry")
int font_v2_command_title_entry(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_title_adapter_common(
        arg0,
        text,
        arg2,
        native_y,
        FONT_COMMAND_TITLE_BOX_X,
        FONT_COMMAND_TITLE_Y_OFFSET,
        FONT_COMMAND_TITLE_BOX_WIDTH
    );
}

FONT_V2_SECTION(".text.font_v2_practice_title_entry")
int font_v2_practice_title_entry(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_title_adapter_common(
        arg0,
        text,
        arg2,
        native_y,
        FONT_PRACTICE_TITLE_BOX_X,
        FONT_PRACTICE_TITLE_Y_OFFSET,
        FONT_PRACTICE_TITLE_BOX_WIDTH
    );
}

FONT_V2_SECTION(".text.font_v2_pause_list_adapter")
int font_v2_pause_list_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float native_x,
    float native_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = native_x;
    session.box_y = native_y + FONT_PAUSE_LIST_Y_OFFSET;
    session.box_width = FONT_PAUSE_LIST_BOX_WIDTH;
    session.box_height = FONT_PAUSE_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_PAUSE_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_pause_list_selected_impl")
int font_v2_pause_list_selected_impl(
    u32 arg0,
    s32 native_x,
    s32 native_y,
    const u8 *text,
    u32 color
) {
    FontV2Session session;
    FontV2Bits color_bits;

    color_bits.u = color;
    session.text = text;
    session.box_x = (float)native_x + FONT_PAUSE_LIST_SELECTED_X_OFFSET;
    session.box_y = (float)native_y + FONT_PAUSE_LIST_Y_OFFSET;
    session.box_width = FONT_PAUSE_LIST_BOX_WIDTH;
    session.box_height = FONT_PAUSE_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_PAUSE_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_selected_callback;
    session.callback_arg0 = arg0;
    session.callback_arg1 = (u32)native_x;
    session.callback_arg2 = (u32)native_y;
    session.callback_arg3 = (u32)&session;
    session.glyph_height = color_bits.f;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_character_selected_adapter")
int font_v2_character_selected_adapter(
    u32 object,
    s32 draw_x,
    s32 draw_y,
    const u8 *text
) {
    FontV2Session session;

    session.text = text;
    session.box_x =
        (float)draw_x + FONT_CHARACTER_LIST_X_OFFSET;
    session.box_y = (float)draw_y;
    session.box_width = FONT_CHARACTER_LIST_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CHARACTER_LIST_LINE_HEIGHT;
    session.callback = FONT_CHARACTER_SELECTED_DRAW_ADDRESS;
    session.callback_arg0 = object;
    session.callback_arg1 =
        (u32)(draw_x + (s32)FONT_CHARACTER_LIST_X_OFFSET);
    session.callback_arg2 = (u32)draw_y;
    session.callback_arg3 = (u32)text;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_character_unselected_adapter")
int font_v2_character_unselected_adapter(
    u32 object,
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    FontV2Session session;

    session.text = text;
    session.box_x = native_x + FONT_CHARACTER_LIST_X_OFFSET;
    session.box_y = native_y;
    session.box_width = FONT_CHARACTER_LIST_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_LIST_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_START;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = 1;
    session.line_height = FONT_CHARACTER_LIST_LINE_HEIGHT;
    session.callback = (u32)font_v2_pause_list_callback;
    session.callback_arg0 = object;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = color;
    session.callback_arg3 = (u32)&session;

    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_quit_scope_enter")
u32 font_v2_quit_scope_enter(void) {
    u32 previous = font_v2_quit_active;
    if (previous != FONT_COLLECTION_CHOICE_SCOPE) {
        font_v2_quit_active = 1;
    }
    return previous;
}

FONT_V2_SECTION(".text.font_v2_quit_scope_leave")
void font_v2_quit_scope_leave(u32 previous) {
    font_v2_quit_active =
        previous == FONT_COLLECTION_CHOICE_SCOPE ? 0u : previous;
}

static FONT_V2_SECTION(".text.font_v2_map_choice")
u32 font_v2_map_choice(
    u32 text,
    u32 source_y,
    u32 *target_x,
    u32 *target_y
) {
    FontV2Bits x;
    FontV2Bits y;

    if (
        text == 0x00604570u &&
        source_y == FONT_QUIT_YES_SOURCE_BITS
    ) {
        x.f = FONT_COLLECTION_YES_X;
        y.f = FONT_COLLECTION_YES_Y;
    } else if (
        text == 0x00604568u &&
        source_y == FONT_QUIT_NO_SOURCE_BITS
    ) {
        x.f = FONT_COLLECTION_NO_X;
        y.f = FONT_COLLECTION_NO_Y;
    } else if (font_v2_quit_active == FONT_COLLECTION_CHOICE_SCOPE) {
        if (source_y == FONT_QUIT_YES_SOURCE_BITS) {
            x.f = FONT_COLLECTION_YES_X;
            y.f = FONT_COLLECTION_YES_Y;
        } else if (source_y == FONT_QUIT_NO_SOURCE_BITS) {
            x.f = FONT_COLLECTION_NO_X;
            y.f = FONT_COLLECTION_NO_Y;
        } else {
            return 0;
        }
    } else if (font_v2_quit_active) {
        if (source_y == FONT_QUIT_YES_SOURCE_BITS) {
            x.f = FONT_QUIT_YES_X;
            y.f = FONT_QUIT_YES_Y;
        } else if (source_y == FONT_QUIT_NO_SOURCE_BITS) {
            x.f = FONT_QUIT_NO_X;
            y.f = FONT_QUIT_NO_Y;
        } else {
            return 0;
        }
    } else if (text == FONT_SPECIAL_ON_TEXT) {
        x.f = FONT_SPECIAL_ON_X;
        y.f = FONT_SPECIAL_ON_Y;
    } else if (text == FONT_SPECIAL_OFF_TEXT) {
        x.f = FONT_SPECIAL_OFF_X;
        y.f = FONT_SPECIAL_OFF_Y;
    } else {
        return 0;
    }

    *target_x = x.u;
    *target_y = y.u;
    return 1;
}

FONT_V2_SECTION(".text.font_v2_quit_selected_map")
u32 font_v2_quit_selected_map(
    u32 text,
    u32 source_y,
    u32 source_x,
    u32 *target_y
) {
    u32 target_x = source_x;
    u32 mapped_y = source_y;

    font_v2_map_choice(text, source_y, &target_x, &mapped_y);
    *target_y = mapped_y;
    return target_x;
}

static FONT_V2_SECTION(".text.font_v2_special_choice_session_init")
void font_v2_special_choice_session_init(
    FontV2Session *session,
    const u8 *text,
    float draw_x,
    float draw_y,
    float scale_x,
    u32 callback
) {
    session->text = text;
    session->box_x = draw_x;
    session->box_y = draw_y;
    session->box_width = FONT_SPECIAL_CHOICE_BOX_WIDTH;
    session->box_height = FONT_SPECIAL_CHOICE_BOX_HEIGHT;
    session->horizontal_alignment = FONT_V2_ALIGN_START;
    session->vertical_alignment = FONT_V2_ALIGN_START;
    session->flags =
        FONT_V2_FLAG_FIXED_SCALE_X | FONT_V2_FLAG_GLYPH_HEIGHT;
    session->line_limit = 1u;
    session->line_height = FONT_SPECIAL_CHOICE_LINE_HEIGHT;
    session->callback = callback;
    session->scale_x = scale_x;
    session->glyph_height = FONT_SPECIAL_CHOICE_GLYPH_HEIGHT;
}

FONT_V2_SECTION(".text.font_v2_special_choice_selected_adapter")
int font_v2_special_choice_selected_adapter(
    u32 text,
    u32 arg1,
    u32 arg2,
    u32 arg3,
    u32 native_x_bits,
    u32 native_y_bits
) {
    FontV2SpecialChoiceFrame frame;
    FontV2Bits draw_x;
    FontV2Bits draw_y;

    draw_x.u = native_x_bits;
    draw_y.u = native_y_bits;
    font_v2_map_choice(text, native_y_bits, &draw_x.u, &draw_y.u);
    draw_x.f += FONT_SPECIAL_CHOICE_SELECTED_X_OFFSET;
    font_v2_special_choice_session_init(
        &frame.session,
        (const u8 *)text,
        draw_x.f,
        draw_y.f,
        FONT_SPECIAL_CHOICE_SELECTED_SCALE_X,
        (u32)font_v2_special_choice_selected_callback
    );
    frame.session.callback_arg0 = text;
    frame.session.callback_arg1 = arg1;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame;
    frame.native_arg3 = arg3;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_quit_unselected_adapter")
int font_v2_quit_unselected_adapter(
    u32 arg0,
    u32 *record,
    u32 arg2,
    u32 arg3
) {
    FontV2Session session;
    u32 original_x;
    u32 original_y;
    u32 target_x;
    u32 target_y;
    u32 text;
    u32 special_choice;
    int result;

    original_x = record[0];
    original_y = record[1];
    text = record[2];
    special_choice =
        text == FONT_SPECIAL_ON_TEXT || text == FONT_SPECIAL_OFF_TEXT;

    target_x = original_x;
    target_y = original_y;
    if (!font_v2_map_choice(text, original_y, &target_x, &target_y)) {
        return font_v2_quit_unselected_callback(
            arg0, (u32)record, arg2, arg3
        );
    }

    record[0] = target_x;
    record[1] = target_y;
    if (special_choice) {
        FontV2Bits draw_x;
        FontV2Bits draw_y;

        draw_x.u = target_x;
        draw_y.u = target_y;
        font_v2_special_choice_session_init(
            &session,
            (const u8 *)text,
            draw_x.f,
            draw_y.f,
            FONT_SPECIAL_CHOICE_UNSELECTED_SCALE_X,
            (u32)font_v2_quit_unselected_callback
        );
        session.callback_arg0 = arg0;
        session.callback_arg1 = (u32)record;
        session.callback_arg2 = arg2;
        session.callback_arg3 = arg3;
        result = font_v2_adapter_call(&session);
    } else {
        result = font_v2_quit_unselected_callback(
            arg0, (u32)record, arg2, arg3
        );
    }
    record[0] = original_x;
    record[1] = original_y;
    return result;
}

FONT_V2_SECTION(".text.font_v2_native_measure")
u32 font_v2_native_measure(const u8 *text) {
    u32 width = font_v2_native_measure_callback(text);
    const u8 *cursor = text;

    while (*cursor) {
        if (*cursor == (u8)' ') {
            width -= 6u;
        }
        cursor += 1;
    }
    return width;
}

FONT_V2_SECTION(".text.font_v2_wrap_native")
int font_v2_wrap_native(
    u8 *text,
    u32 box_width,
    u32 line_limit,
    u32 *measured_width,
    u32 *line_count
) {
    volatile u32 *renderer;
    u32 saved_tracking = 0;
    u8 *cursor;
    u8 *line_start;
    u8 *last_space = (u8 *)0;
    u32 lines = 1;
    u32 maximum_width = 0;

    if (!text || !measured_width || !line_count) {
        return -1;
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (renderer) {
        saved_tracking =
            renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)];
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
    }

    cursor = text;
    line_start = text;
    while (*cursor) {
        if (*cursor == (u8)'\n') {
            line_start = cursor + 1;
            last_space = (u8 *)0;
            lines += 1;
        } else if (*cursor == (u8)' ') {
            u32 width;
            *cursor = 0;
            width = font_v2_native_measure(line_start);
            *cursor = (u8)' ';
            if (
                width > box_width &&
                (!line_limit || lines < line_limit)
            ) {
                u8 *wrap = last_space ? last_space : cursor;
                *wrap = (u8)'\n';
                line_start = wrap + 1;
                lines += 1;
            }
            last_space = cursor;
        }
        cursor += 1;
    }

    if (
        font_v2_native_measure(line_start) > box_width &&
        last_space &&
        (!line_limit || lines < line_limit)
    ) {
        *last_space = (u8)'\n';
        lines += 1;
    }

    cursor = text;
    line_start = text;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            u32 width;
            *cursor = 0;
            width = font_v2_native_measure(line_start);
            if (width > maximum_width) {
                maximum_width = width;
            }
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
        } else {
            cursor += 1;
        }
    }

    if (renderer) {
        renderer[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] =
            saved_tracking;
    }
    *measured_width = maximum_width;
    *line_count = lines;
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_label_callback")
int font_v2_settings_label_callback(
    u32 text,
    u32 style,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        style
    );
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_heading_callback")
int font_v2_settings_heading_callback(
    u32 text,
    u32 style,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw =
        (FontV2NativeDraw)FONT_HEADING_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        style
    );
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_value_callback")
int font_v2_settings_value_callback(
    u32 text,
    u32 color,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_BODY_DRAW_ADDRESS;

    (void)unused;
    draw(
        session->draw_x,
        session->draw_y,
        (const u8 *)text,
        color
    );
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_settings_row_common")
int font_v2_settings_row_common(
    const u8 *text,
    u32 style,
    float native_y,
    float box_x,
    u32 box_width,
    u32 fit_width,
    float fixed_scale_x,
    float glyph_height,
    u32 horizontal_alignment,
    u32 callback
) {
    FontV2Session session;

    session.text = text;
    session.box_x = box_x;
    session.box_y = native_y;
    session.box_width = box_width;
    session.box_height = (u32)FONT_SETTINGS_LINE_HEIGHT;
    session.horizontal_alignment = horizontal_alignment;
    session.vertical_alignment = FONT_V2_ALIGN_START;
    session.flags = FONT_V2_FLAG_PREMEASURED;
    if (glyph_height > 0.0f) {
        session.flags |= FONT_V2_FLAG_GLYPH_HEIGHT;
        session.glyph_height = glyph_height;
    }
    session.line_limit = 1u;
    session.line_height = FONT_SETTINGS_LINE_HEIGHT;
    session.measured_width = font_v2_native_measure(text);
    if (fixed_scale_x > 0.0f) {
        session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x = fixed_scale_x;
    } else if (fit_width && session.measured_width > fit_width) {
        session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x =
            (float)(s32)fit_width / (float)(s32)session.measured_width;
    } else if (!fit_width) {
        session.flags |= FONT_V2_FLAG_SHRINK_X;
    }
    session.line_count = 1u;
    session.callback = callback;
    session.callback_arg0 = (u32)text;
    session.callback_arg1 = style;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    return font_v2_adapter_call(&session);
}

FONT_V2_SECTION(".text.font_v2_battle_settings_label_adapter")
int font_v2_battle_settings_label_adapter(
    const u8 *text,
    u32 style,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        style,
        native_y + FONT_BATTLE_SETTINGS_ROW_Y_OFFSET +
            (style ? FONT_SETTINGS_SELECTED_Y_OFFSET : 0.0f),
        FONT_BATTLE_SETTINGS_LABEL_X,
        FONT_BATTLE_SETTINGS_LABEL_WIDTH,
        0u,
        0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        (u32)font_v2_settings_label_callback
    );
}

FONT_V2_SECTION(".text.font_v2_practice_settings_label_adapter")
int font_v2_practice_settings_label_adapter(
    const u8 *text,
    u32 style,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        style,
        native_y + FONT_PRACTICE_SETTINGS_ROW_Y_OFFSET +
            (style ? FONT_SETTINGS_SELECTED_Y_OFFSET : 0.0f),
        FONT_PRACTICE_SETTINGS_LABEL_X,
        FONT_PRACTICE_SETTINGS_LABEL_WIDTH,
        0u,
        0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        (u32)font_v2_settings_label_callback
    );
}

FONT_V2_SECTION(".text.font_v2_settings_value_adapter")
int font_v2_settings_value_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    volatile u8 *renderer =
        *(volatile u8 **)FONT_RENDERER_POINTER_ADDRESS;
    const u8 *cursor = text;
    float box_x = FONT_SETTINGS_VALUE_X;
    u32 fit_width = 0u;
    u8 saved_renderer_flags = 0u;
    u32 numeric_value = 0u;
    u32 restore_renderer_flags = 0u;
    int result;

    (void)native_x;
    if (text && *text) {
        numeric_value = *text >= (u8)'0' && *text <= (u8)'9';
    }
    if (numeric_value) {
        box_x += FONT_SETTINGS_NUMERIC_VALUE_X_OFFSET;
        native_y += FONT_SETTINGS_NUMERIC_VALUE_Y_OFFSET;
    }
    if (
        renderer && text && *text && !numeric_value &&
        !(renderer[FONT_RENDERER_FLAGS_OFFSET] &
            (u8)FONT_RENDERER_ASCII_MODE_FLAG)
    ) {
        saved_renderer_flags = renderer[FONT_RENDERER_FLAGS_OFFSET];
        renderer[FONT_RENDERER_FLAGS_OFFSET] =
            saved_renderer_flags | (u8)FONT_RENDERER_ASCII_MODE_FLAG;
        restore_renderer_flags = 1u;
        box_x += FONT_SETTINGS_SPECIAL_VALUE_X_OFFSET;
    }
    while (cursor && *cursor) {
        if (*cursor == (u8)' ') {
            box_x += FONT_SETTINGS_PHRASE_X_OFFSET;
            fit_width = FONT_SETTINGS_PHRASE_FIT_WIDTH;
            break;
        }
        cursor += 1;
    }
    result = font_v2_settings_row_common(
        text,
        color,
        native_y,
        box_x,
        FONT_SETTINGS_VALUE_WIDTH,
        fit_width,
        numeric_value ? FONT_SETTINGS_NUMERIC_VALUE_SCALE_X : 0.0f,
        numeric_value ? FONT_SETTINGS_NUMERIC_VALUE_GLYPH_HEIGHT : 0.0f,
        FONT_V2_ALIGN_CENTER,
        (u32)font_v2_settings_value_callback
    );
    if (restore_renderer_flags) {
        renderer[FONT_RENDERER_FLAGS_OFFSET] = saved_renderer_flags;
    }
    return result;
}

FONT_V2_SECTION(".text.font_v2_practice_settings_heading_adapter")
int font_v2_practice_settings_heading_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    (void)native_x;
    return font_v2_settings_row_common(
        text,
        color,
        native_y,
        FONT_PRACTICE_SETTINGS_HEADING_X,
        FONT_PRACTICE_SETTINGS_HEADING_WIDTH,
        0u,
        0.0f,
        0.0f,
        FONT_V2_ALIGN_START,
        (u32)font_v2_settings_heading_callback
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_text_callback")
int font_v2_ninja_text_callback(
    u32 renderer_address,
    u32 text,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;

    (void)unused;
    set_position(session->draw_x, session->draw_y, renderer_address);
    draw(renderer_address, (const u8 *)text);
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_ninja_text_common")
int font_v2_ninja_text_common(
    u32 renderer_address,
    const u8 *text,
    float x_offset,
    float y_offset,
    u32 box_width,
    u32 box_height,
    u32 horizontal_alignment,
    float fixed_scale_x
) {
    volatile float *renderer = (volatile float *)renderer_address;
    FontV2Session session;

    if (!renderer || !text) {
        return -1;
    }
    session.text = text;
    session.box_x =
        renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)] +
        x_offset;
    session.box_y =
        renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)] +
        y_offset;
    session.box_width = box_width;
    session.box_height = box_height;
    session.horizontal_alignment = horizontal_alignment;
    session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    if (fixed_scale_x > 0.0f) {
        session.flags = FONT_V2_FLAG_FIXED_SCALE_X;
        session.scale_x = fixed_scale_x;
    } else {
        session.flags = FONT_V2_FLAG_SHRINK_X;
    }
    session.line_limit = 1u;
    session.line_height = FONT_NINJA_SINGLE_LINE_HEIGHT;
    session.callback = (u32)font_v2_ninja_text_callback;
    session.callback_arg0 = renderer_address;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = 0u;
    session.callback_arg3 = (u32)&session;
    return font_v2_adapter_call(&session);
}

static FONT_V2_SECTION(".text.font_v2_ninja_compact_adapter")
int font_v2_ninja_compact_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        512u,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_START,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_hits_adapter")
int font_v2_ninja_hits_adapter(
    u32 renderer_address,
    const u8 *text
) {
    if (!text || !*text) {
        return 0;
    }
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_HITS_WIDTH,
        FONT_NINJA_HITS_HEIGHT,
        FONT_V2_ALIGN_START,
        FONT_NINJA_HITS_SCALE_X
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_equals_adapter")
int font_v2_ninja_equals_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        32u,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_START,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_total_adapter")
int font_v2_ninja_total_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_TOTAL_WIDTH,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_CENTER,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_ninja_empty_adapter")
int font_v2_ninja_empty_adapter(
    u32 renderer_address,
    const u8 *text
) {
    return font_v2_ninja_text_common(
        renderer_address,
        text,
        0.0f,
        0.0f,
        FONT_NINJA_EMPTY_WIDTH,
        (u32)FONT_NINJA_SINGLE_LINE_HEIGHT,
        FONT_V2_ALIGN_CENTER,
        FONT_NINJA_EMPTY_SCALE_X
    );
}

FONT_V2_SECTION(".text.font_v2_ninja_arithmetic_template")
void font_v2_ninja_arithmetic_template(
    float native_x,
    float native_y,
    u32 row_set,
    s32 row_index
) {
    FontV2NativeSetColor set_color =
        (FontV2NativeSetColor)FONT_SET_COLOR_ADDRESS;
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    u32 renderer_address = *(volatile u32 *)FONT_RENDERER_POINTER_ADDRESS;
    volatile u8 *renderer_flags;
    s32 *row;
    u32 descriptor;
    const u8 *unit_text;
    u8 number[32];

    if (!renderer_address || !row_set) {
        return;
    }
    renderer_flags = (volatile u8 *)(
        renderer_address + FONT_NINJA_RENDERER_FLAGS_OFFSET
    );
    native_x += 10.0f;
    native_y += FONT_NINJA_FORMULA_Y_OFFSET;
    row = (s32 *)(
        *(u32 *)(row_set + 4u) + (u32)row_index * 12u
    );
    descriptor = (u32)row[0];
    set_color(renderer_address, 0x00404070u, 1u);

    if (row[2] == 0) {
        set_position(
            native_x + FONT_NINJA_EMPTY_X_OFFSET,
            native_y,
            renderer_address
        );
        font_v2_ninja_empty_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_EMPTY_POINTER_ADDRESS
        );
        return;
    }

    *renderer_flags &= (u8)0xF7u;
    if (row_index != 10 && row_index != 13 && row_index != 9) {
        font_ninja_song_ascii_number(
            0u,
            (s32)*(s16 *)descriptor,
            3,
            number,
            0
        );
        set_position(native_x + 30.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(renderer_address, number);

        set_position(native_x + 90.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_MULTIPLY_POINTER_ADDRESS
        );

        font_ninja_song_ascii_number(
            0u,
            row[1],
            3,
            number,
            0
        );
        if (
            row[1] == (s32)*(s16 *)(
                FONT_NINJA_MULTIPLIER_TABLE_ADDRESS +
                (s32)*(s8 *)(descriptor + 4u) * 2
            )
        ) {
            set_color(renderer_address, 0x000000D4u, 1u);
        } else {
            set_color(renderer_address, 0x00404070u, 1u);
        }
        set_position(native_x + 120.0f, native_y, renderer_address);
        font_v2_ninja_compact_adapter(renderer_address, number);
        set_color(renderer_address, 0x00404070u, 1u);

        unit_text = ((const u8 **)FONT_NINJA_UNIT_TABLE_ADDRESS)[
            (u32)*(s16 *)(descriptor + 2u)
        ];
        set_position(
            native_x + FONT_NINJA_HITS_X_OFFSET,
            native_y + FONT_NINJA_HITS_Y_OFFSET,
            renderer_address
        );
        font_v2_ninja_hits_adapter(renderer_address, unit_text);

        set_position(
            native_x + FONT_NINJA_EQUALS_X_OFFSET,
            native_y,
            renderer_address
        );
        font_v2_ninja_equals_adapter(
            renderer_address,
            *(const u8 **)FONT_NINJA_EQUALS_POINTER_ADDRESS
        );
    }

    font_ninja_song_ascii_number(0u, row[2], 5, number, 0);
    set_position(
        native_x + FONT_NINJA_TOTAL_X_OFFSET,
        native_y,
        renderer_address
    );
    font_v2_ninja_total_adapter(renderer_address, number);
    *renderer_flags = (*renderer_flags & (u8)0xF7u) | (u8)8u;
}

static FONT_V2_SECTION(".text.font_v2_ninja_objective_ascii_width")
u32 font_v2_ninja_objective_ascii_width(const u8 *text) {
    u32 width = 0u;

    while (*text) {
        u32 character = *text;
        if (character < 0x20u || character > 0x7Eu) {
            text += 1;
            continue;
        }
        width += font_v2_ascii_widths[character - 0x20u];
        text += 1;
    }
    return width;
}

static FONT_V2_SECTION(".text.font_v2_ninja_objective_wrap")
int font_v2_ninja_objective_wrap(
    u8 *text,
    u32 box_width,
    u32 line_limit,
    u32 *measured_width,
    u32 *line_count
) {
    u8 *cursor;
    u8 *line_start;
    u8 *last_space = (u8 *)0;
    u32 lines = 1u;
    u32 maximum_width = 0u;

    if (!text || !measured_width || !line_count) {
        return -1;
    }
    cursor = text;
    line_start = text;
    while (*cursor) {
        if (*cursor == (u8)'\n') {
            line_start = cursor + 1;
            last_space = (u8 *)0;
            lines += 1u;
        } else if (
            *cursor == (u8)' ' ||
            *cursor < 0x20u ||
            *cursor > 0x7Eu
        ) {
            u8 separator = *cursor;
            u32 width;
            *cursor = 0;
            width = font_v2_ninja_objective_ascii_width(line_start);
            *cursor = separator;
            if (
                width > box_width &&
                (!line_limit || lines < line_limit)
            ) {
                u8 *wrap = last_space ? last_space : cursor;
                *wrap = (u8)'\n';
                line_start = wrap + 1;
                lines += 1u;
            }
            last_space = cursor;
        }
        cursor += 1;
    }

    if (
        font_v2_ninja_objective_ascii_width(line_start) > box_width &&
        last_space &&
        (!line_limit || lines < line_limit)
    ) {
        *last_space = (u8)'\n';
        lines += 1u;
    }

    cursor = text;
    line_start = text;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            u32 width;
            *cursor = 0;
            width = font_v2_ninja_objective_ascii_width(line_start);
            *cursor = saved;
            if (width > maximum_width) {
                maximum_width = width;
            }
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
        } else {
            cursor += 1;
        }
    }
    *measured_width = maximum_width;
    *line_count = lines;
    return 0;
}

static FONT_V2_SECTION(".text.font_v2_ninja_objective_callback")
int font_v2_ninja_objective_callback(
    u32 text,
    u32 color,
    u32 unused,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_BODY_DRAW_ADDRESS;
    u8 *cursor = (u8 *)text;
    u8 *line_start = cursor;
    u32 line_index = 0u;

    (void)unused;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            draw(
                session->draw_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height,
                line_start,
                color
            );
            *cursor = saved;
            if (!saved) {
                break;
            }
            line_index += 1u;
            cursor += 1;
            line_start = cursor;
        } else {
            cursor += 1;
        }
    }
    return 0;
}

FONT_V2_SECTION(".text.font_v2_ninja_objective_adapter")
int font_v2_ninja_objective_adapter(
    const u8 *text,
    u32 color,
    float native_x,
    float native_y
) {
    FontV2BodyFrame frame;
    u32 index = 0u;
    u32 wrapped_lines;

    if (!text) {
        return -1;
    }
    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        frame.buffer[index] = text[index];
        index += 1u;
    }
    frame.buffer[index] = 0;
    if (
        font_v2_ninja_objective_wrap(
            frame.buffer,
            FONT_NINJA_OBJECTIVE_WRAP_WIDTH,
            FONT_NINJA_OBJECTIVE_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }
    wrapped_lines = frame.session.line_count;

    frame.session.text = frame.buffer;
    frame.session.box_x = native_x + FONT_NINJA_OBJECTIVE_X_OFFSET;
    frame.session.box_y = native_y + (wrapped_lines == 1u ? 0.0f : -6.0f);
    frame.session.box_width = FONT_NINJA_OBJECTIVE_WIDTH;
    frame.session.box_height = (u32)FONT_NINJA_OBJECTIVE_GLYPH_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_START;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = 1u;
    frame.session.line_count = 1u;
    frame.session.line_height = FONT_NINJA_OBJECTIVE_LINE_ADVANCE;
    frame.session.glyph_height = FONT_NINJA_OBJECTIVE_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_ninja_objective_callback;
    frame.session.callback_arg0 = (u32)frame.buffer;
    frame.session.callback_arg1 = color;
    frame.session.callback_arg2 = 0u;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

static FONT_V2_SECTION(".text.font_v2_jutsu_draw_callback")
int font_v2_jutsu_draw_callback(
    u32 renderer_address,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    volatile float *renderer = (volatile float *)renderer_address;
    FontV2NativeSetPosition set_position =
        (FontV2NativeSetPosition)FONT_SET_POSITION_ADDRESS;
    FontV2NativeTextDraw draw =
        (FontV2NativeTextDraw)FONT_JUTSU_DRAW_ADDRESS;
    float saved_x;
    float saved_y;
    float origin_x;
    float origin_y;
    u8 *cursor;
    u8 *line_start;
    u32 line_index;

    (void)arg2;
    if (!renderer || !text || !session) {
        return -1;
    }

    saved_x = renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)];
    saved_y = renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)];
    origin_x = renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(float)];
    origin_y = renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(float)];
    cursor = (u8 *)text;
    line_start = cursor;
    line_index = 0;

    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            set_position(
                session->draw_x - origin_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height -
                    origin_y,
                renderer_address
            );
            draw(renderer_address, line_start);
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
            line_index += 1;
        } else {
            cursor += 1;
        }
    }

    set_position(
        saved_x - origin_x,
        saved_y - origin_y,
        renderer_address
    );
    return 0;
}

FONT_V2_SECTION(".text.font_v2_jutsu_draw_entry")
int font_v2_jutsu_draw_entry(
    u32 renderer_address,
    const u8 *text
) {
    FontV2BodyFrame frame;
    u8 original[FONT_BODY_BUFFER_SIZE];
    volatile float *renderer = (volatile float *)renderer_address;
    volatile u32 *renderer_words = (volatile u32 *)renderer_address;
    float native_x;
    float native_y;
    float wrap_width;
    u32 index = 0;

    if (!renderer || !text) {
        return -1;
    }

    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        original[index] = text[index];
        frame.buffer[index] = text[index];
        index += 1;
    }
    original[index] = 0;
    frame.buffer[index] = 0;

    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_JUTSU_BOX_WIDTH,
            0,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    if (frame.session.line_count > FONT_JUTSU_LINE_LIMIT) {
        u8 *cursor = frame.buffer;
        u8 *line_start = cursor;
        u32 line_index = 0;
        u32 overflow_width = 0;
        u32 overflow_lines = 0;
        u32 saved_tracking =
            renderer_words[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)];

        renderer_words[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] = 0;
        for (;;) {
            if (!*cursor || *cursor == (u8)'\n') {
                u8 saved = *cursor;
                *cursor = 0;
                if (line_index >= FONT_JUTSU_LINE_LIMIT) {
                    overflow_width += font_v2_native_measure(line_start);
                    overflow_lines += 1;
                }
                *cursor = saved;
                if (!saved) {
                    break;
                }
                cursor += 1;
                line_start = cursor;
                line_index += 1;
            } else {
                cursor += 1;
            }
        }
        renderer_words[FONT_RENDERER_TRACKING_OFFSET / sizeof(u32)] =
            saved_tracking;

        wrap_width = (float)(s32)FONT_JUTSU_BOX_WIDTH;
        if (overflow_lines) {
            wrap_width +=
                (
                    (float)(s32)overflow_width /
                    (float)(s32)overflow_lines
                ) * FONT_JUTSU_OVERFLOW_WIDTH_FACTOR;
        }

        do {
            index = 0;
            while (
                index < FONT_BODY_BUFFER_SIZE - 1u &&
                original[index]
            ) {
                frame.buffer[index] = original[index];
                index += 1;
            }
            frame.buffer[index] = 0;
            if (
                font_v2_wrap_native(
                    frame.buffer,
                    (u32)wrap_width,
                    0,
                    &frame.session.measured_width,
                    &frame.session.line_count
                ) != 0
            ) {
                return -1;
            }
            wrap_width += FONT_JUTSU_WRAP_WIDTH_STEP;
        } while (frame.session.line_count > FONT_JUTSU_LINE_LIMIT);
    }

    native_x =
        renderer[FONT_RENDERER_POSITION_X_OFFSET / sizeof(float)];
    native_y =
        renderer[FONT_RENDERER_POSITION_Y_OFFSET / sizeof(float)];

    if (frame.session.line_count <= 1u) {
        frame.session.text = frame.buffer;
        frame.session.box_x =
            native_x +
            (
                native_x < FONT_JUTSU_SIDE_THRESHOLD
                    ? FONT_JUTSU_LEFT_X_OFFSET
                    : FONT_JUTSU_RIGHT_X_OFFSET
            );
        frame.session.box_y =
            native_y + FONT_JUTSU_SINGLE_LINE_Y_OFFSET;
        frame.session.box_width = FONT_JUTSU_BOX_WIDTH;
        frame.session.box_height = FONT_JUTSU_BOX_HEIGHT;
        frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
        frame.session.vertical_alignment = FONT_V2_ALIGN_START;
        frame.session.flags =
            FONT_V2_FLAG_FIXED_SCALE_X |
            FONT_V2_FLAG_PREMEASURED;
        frame.session.line_limit = 1u;
        frame.session.line_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
        frame.session.scale_x = FONT_JUTSU_HORIZONTAL_SCALE;
        frame.session.glyph_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
        frame.session.callback = (u32)font_v2_jutsu_draw_callback;
        frame.session.callback_arg0 = renderer_address;
        frame.session.callback_arg1 = (u32)frame.buffer;
        frame.session.callback_arg2 = 0;
        frame.session.callback_arg3 = (u32)&frame.session;
        return font_v2_adapter_call(&frame.session);
    }

    frame.session.text = frame.buffer;
    frame.session.box_x =
        native_x +
        (
            native_x < FONT_JUTSU_SIDE_THRESHOLD
                ? FONT_JUTSU_LEFT_X_OFFSET
                : FONT_JUTSU_RIGHT_X_OFFSET
        );
    frame.session.box_y = native_y + FONT_JUTSU_Y_OFFSET;
    frame.session.box_width = FONT_JUTSU_BOX_WIDTH;
    frame.session.box_height = FONT_JUTSU_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_GLYPH_HEIGHT |
        FONT_V2_FLAG_FIXED_SCALE_X |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_JUTSU_LINE_LIMIT;
    frame.session.line_height = FONT_JUTSU_LINE_ADVANCE;
    frame.session.scale_x = FONT_JUTSU_HORIZONTAL_SCALE;
    frame.session.glyph_height = FONT_JUTSU_LAYOUT_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_jutsu_draw_callback;
    frame.session.callback_arg0 = renderer_address;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

static FONT_V2_SECTION(".text.font_v2_collection_list_callback")
int font_v2_collection_list_callback(
    u32 text,
    u32 highlighted,
    u32 arg2,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;
    u8 *cursor = (u8 *)text;
    u8 *line_start = cursor;
    u32 line_index = 0;

    (void)arg2;
    for (;;) {
        if (!*cursor || *cursor == (u8)'\n') {
            u8 saved = *cursor;
            *cursor = 0;
            draw(
                session->draw_x,
                session->draw_y +
                    (float)(s32)line_index * session->line_height,
                line_start,
                highlighted
            );
            *cursor = saved;
            if (!saved) {
                break;
            }
            cursor += 1;
            line_start = cursor;
            line_index += 1;
        } else {
            cursor += 1;
        }
    }
    return 0;
}

FONT_V2_SECTION(".text.font_v2_collection_list_entry")
int font_v2_collection_list_entry(
    const u8 *text,
    u32 highlighted,
    float native_x,
    float native_y
) {
    FontV2BodyFrame frame;
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;
    u32 text_address = (u32)text;
    u32 box_width = 0;
    u32 movie_row = 0;
    u32 index = 0;

    if (!text) {
        return -1;
    }
    if (
        text_address >= FONT_COLLECTION_MOVIE_TEXT_START &&
        text_address < FONT_COLLECTION_MOVIE_TEXT_END
    ) {
        box_width = FONT_COLLECTION_MOVIE_BOX_WIDTH;
        movie_row = 1;
    } else if (
        text_address == FONT_CHARACTER_MOVE_152_TEXT_0 ||
        text_address == FONT_CHARACTER_MOVE_152_TEXT_1 ||
        text_address == FONT_CHARACTER_MOVE_152_TEXT_2
    ) {
        box_width = FONT_CHARACTER_MOVE_152_BOX_WIDTH;
    } else if (
        text_address == FONT_CHARACTER_MOVE_192_TEXT_0 ||
        text_address == FONT_CHARACTER_MOVE_192_TEXT_1 ||
        text_address == FONT_CHARACTER_MOVE_192_TEXT_2 ||
        text_address == FONT_CHARACTER_MOVE_192_TEXT_3
    ) {
        box_width = FONT_CHARACTER_MOVE_192_BOX_WIDTH;
    } else {
        draw(native_x, native_y, text, highlighted);
        return 0;
    }

    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        frame.buffer[index] = text[index];
        index += 1;
    }
    frame.buffer[index] = 0;

    if (
        font_v2_wrap_native(
            frame.buffer,
            box_width,
            FONT_COLLECTION_LIST_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    if (movie_row && frame.session.line_count == 1u) {
        draw(native_x, native_y, text, highlighted);
        return 0;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x = native_x;
    frame.session.box_y = native_y + FONT_COLLECTION_LIST_BOX_Y_OFFSET;
    frame.session.box_width = box_width;
    frame.session.box_height = FONT_COLLECTION_LIST_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_COLLECTION_LIST_LINE_LIMIT;
    frame.session.line_height = FONT_COLLECTION_LIST_LINE_ADVANCE;
    frame.session.glyph_height = FONT_COLLECTION_LIST_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_collection_list_callback;
    frame.session.callback_arg0 = (u32)frame.buffer;
    frame.session.callback_arg1 = highlighted;
    frame.session.callback_arg2 = 0;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

static FONT_V2_SECTION(".text.font_v2_wrapped_body_common")
int font_v2_wrapped_body_common(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    float box_x,
    float box_y,
    u32 box_width,
    u32 box_height,
    float line_height,
    u32 line_limit,
    u32 callback,
    float fixed_scale_x
) {
    FontV2BodyFrame frame;
    u32 index = 0;

    while (index < FONT_BODY_BUFFER_SIZE - 1u && text[index]) {
        frame.buffer[index] = text[index];
        index += 1;
    }
    frame.buffer[index] = 0;

    if (
        font_v2_wrap_native(
            frame.buffer,
            box_width,
            line_limit,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    frame.session.text = frame.buffer;
    frame.session.box_x = box_x;
    frame.session.box_y = box_y;
    frame.session.box_width = box_width;
    frame.session.box_height = box_height;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_START;
    frame.session.flags =
        FONT_V2_FLAG_NEWLINE_BYTES | FONT_V2_FLAG_PREMEASURED;
    if (fixed_scale_x > 0.0f) {
        frame.session.flags |= FONT_V2_FLAG_FIXED_SCALE_X;
        frame.session.scale_x = fixed_scale_x;
    }
    frame.session.line_limit = line_limit;
    frame.session.line_height = line_height;
    frame.session.callback = callback;
    frame.session.callback_arg0 = arg0;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_quit_body_adapter")
int font_v2_quit_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    return font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_QUIT_BODY_BOX_X,
        FONT_QUIT_BODY_BOX_Y,
        FONT_QUIT_BODY_BOX_WIDTH,
        FONT_QUIT_BODY_BOX_HEIGHT,
        FONT_QUIT_BODY_LINE_HEIGHT,
        FONT_QUIT_BODY_LINE_LIMIT,
        (u32)font_v2_quit_body_callback,
        0.0f
    );
}

static FONT_V2_SECTION(
    ".text.font_v2_character_confirmation_body_callback"
)
int font_v2_character_confirmation_body_callback(
    u32 arg0,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    FontV2NativeDraw draw = (FontV2NativeDraw)FONT_DRAW_ADDRESS;

    (void)arg0;
    (void)arg2;
    draw(
        session->draw_x,
        session->draw_y,
        text,
        0u
    );
    return 0;
}

FONT_V2_SECTION(".text.font_v2_character_confirmation_body_adapter")
int font_v2_character_confirmation_body_adapter(
    u32 object,
    const u8 *text,
    u32 arg2
) {
    volatile u32 *renderer =
        *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    volatile u32 *object_words = (volatile u32 *)object;
    FontV2NativeInitialize initialize =
        (FontV2NativeInitialize)FONT_INITIALIZE_ADDRESS;
    FontV2NativeSetContext set_context =
        (FontV2NativeSetContext)FONT_SET_CONTEXT_ADDRESS;
    FontV2Session session;
    u32 saved_draw_x;
    u32 saved_draw_y;
    u32 saved_context;
    int result;

    if (!renderer || !object_words || !text) {
        return -1;
    }

    saved_draw_x =
        renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(u32)];
    saved_draw_y =
        renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(u32)];
    saved_context =
        renderer[FONT_RENDERER_CONTEXT_OFFSET / sizeof(u32)];

    initialize((u32)renderer, 1u);
    renderer[FONT_RENDERER_DRAW_X_OFFSET / sizeof(u32)] = saved_draw_x;
    renderer[FONT_RENDERER_DRAW_Y_OFFSET / sizeof(u32)] = saved_draw_y;
    set_context(
        (u32)renderer,
        object_words[0x74u / sizeof(u32)]
    );

    session.text = text;
    session.box_x = FONT_CHARACTER_BODY_BOX_X;
    session.box_y = FONT_CHARACTER_BODY_BOX_Y;
    session.box_width = FONT_CHARACTER_BODY_BOX_WIDTH;
    session.box_height = FONT_CHARACTER_BODY_BOX_HEIGHT;
    session.horizontal_alignment = FONT_V2_ALIGN_CENTER;
    session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    session.flags = FONT_V2_FLAG_SHRINK_X;
    session.line_limit = FONT_CHARACTER_BODY_LINE_LIMIT;
    session.line_height = FONT_CHARACTER_BODY_LINE_HEIGHT;
    session.callback =
        (u32)font_v2_character_confirmation_body_callback;
    session.callback_arg0 = object;
    session.callback_arg1 = (u32)text;
    session.callback_arg2 = arg2;
    session.callback_arg3 = (u32)&session;

    result = font_v2_adapter_call(&session);
    renderer[FONT_RENDERER_CONTEXT_OFFSET / sizeof(u32)] = saved_context;
    return result;
}

FONT_V2_SECTION(".text.font_v2_special_controls_body_adapter")
int font_v2_special_controls_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    return font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_SPECIAL_BODY_BOX_X,
        FONT_SPECIAL_BODY_BOX_Y,
        FONT_SPECIAL_BODY_BOX_WIDTH,
        FONT_SPECIAL_BODY_BOX_HEIGHT,
        FONT_SPECIAL_BODY_LINE_HEIGHT,
        FONT_SPECIAL_BODY_LINE_LIMIT,
        (u32)font_v2_special_controls_body_callback,
        0.0f
    );
}

static FONT_V2_SECTION(".text.font_v2_collection_body_callback")
int font_v2_collection_body_callback(
    u32 object,
    const u8 *text,
    u32 arg2,
    FontV2Session *session
) {
    volatile u8 *object_bytes = (volatile u8 *)object;
    volatile u32 *object_words = (volatile u32 *)object;
    FontV2NativeUiDraw draw = (FontV2NativeUiDraw)0x00379A20u;
    FontV2UiDrawRecord record;

    if (!object_bytes || !text || !session || object_bytes[0x62] == 0) {
        return 0;
    }

    record.draw_x = session->draw_x;
    record.draw_y = session->draw_y;
    record.text = text;
    record.arg2 = arg2;
    return draw(
        object_words[0x78u / sizeof(u32)],
        &record,
        object_words[0x74u / sizeof(u32)],
        -1
    );
}

FONT_V2_SECTION(".text.font_v2_collection_body_adapter")
int font_v2_collection_body_adapter(
    u32 arg0,
    const u8 *text,
    u32 arg2
) {
    int result;

    if (font_v2_is_mode_select_body(text)) {
        return font_v2_wrapped_body_common(
            arg0,
            text,
            arg2,
            FONT_MODE_SELECT_BODY_BOX_X,
            FONT_MODE_SELECT_BODY_BOX_Y,
            FONT_MODE_SELECT_BODY_BOX_WIDTH,
            FONT_MODE_SELECT_BODY_BOX_HEIGHT,
            FONT_MODE_SELECT_BODY_LINE_HEIGHT,
            FONT_MODE_SELECT_BODY_LINE_LIMIT,
            (u32)font_v2_collection_body_callback,
            0.0f
        );
    }

    result = font_v2_wrapped_body_common(
        arg0,
        text,
        arg2,
        FONT_COLLECTION_BODY_BOX_X,
        FONT_COLLECTION_BODY_BOX_Y,
        FONT_COLLECTION_BODY_BOX_WIDTH,
        FONT_COLLECTION_BODY_BOX_HEIGHT,
        FONT_COLLECTION_BODY_LINE_HEIGHT,
        FONT_COLLECTION_BODY_LINE_LIMIT,
        (u32)font_v2_collection_body_callback,
        FONT_COLLECTION_BODY_SCALE_X
    );
    if (result >= 0) {
        font_v2_quit_active = FONT_COLLECTION_CHOICE_SCOPE;
    }
    return result;
}

FONT_V2_SECTION(".text.font_v2_practice_append")
u8 *font_v2_practice_append(
    u8 *destination,
    const u8 *source,
    u8 *limit
) {
    while (*source && destination < limit) {
        *destination = *source;
        destination += 1;
        source += 1;
    }
    *destination = 0;
    return destination;
}

FONT_V2_SECTION(".text.font_v2_command_relationship_impl")
int font_v2_command_relationship_impl(
    u32 arg0,
    const u8 *record,
    u32 arg2,
    u32 native_y_bits
) {
    FontV2BodyFrame frame;
    const u8 *volatile *text_table =
        (const u8 *volatile *)FONT_COMMAND_TEXT_TABLE_ADDRESS;
    u8 *destination = frame.buffer;
    u8 *limit = frame.buffer + FONT_BODY_BUFFER_SIZE - 1u;
    FontV2Bits native_y;

    if (!record || !record[4]) {
        return -1;
    }

    *destination = 0;
    destination = font_v2_practice_append(
        destination, text_table[record[4]], limit
    );
    if (record[5]) {
        destination = font_v2_practice_append(
            destination, text_table[record[5]], limit
        );
    }

    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_COMMAND_RELATION_BOX_WIDTH,
            FONT_COMMAND_RELATION_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        return -1;
    }

    native_y.u = native_y_bits;
    frame.session.text = frame.buffer;
    frame.session.box_x = FONT_COMMAND_RELATION_BOX_X;
    frame.session.box_y =
        native_y.f + FONT_COMMAND_RELATION_Y_OFFSET;
    if (frame.session.line_count == 1u) {
        frame.session.box_y +=
            FONT_COMMAND_RELATION_SINGLE_LINE_Y_OFFSET;
    }
    frame.session.box_width = FONT_COMMAND_RELATION_BOX_WIDTH;
    frame.session.box_height = FONT_COMMAND_RELATION_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_SCALE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_COMMAND_RELATION_LINE_LIMIT;
    frame.session.line_height = FONT_COMMAND_RELATION_LINE_HEIGHT;
    frame.session.glyph_height = FONT_COMMAND_RELATION_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_title_callback;
    frame.session.callback_arg0 = arg0;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = arg2;
    frame.session.callback_arg3 = (u32)&frame.session;
    return font_v2_adapter_call(&frame.session);
}

FONT_V2_SECTION(".text.font_v2_command_icon_offset")
float font_v2_command_icon_offset(const u8 *record) {
    if (record && record[4]) {
        return FONT_COMMAND_ICON_RELATION_OFFSET;
    }
    return FONT_COMMAND_ICON_PLAIN_OFFSET;
}

static FONT_V2_SECTION(".text.font_v2_icon_record")
const FontV2IconRecord *font_v2_icon_record(u32 token) {
    u32 mapped;
    if (token >= FONT_PRACTICE_ICON_MAP_COUNT) {
        return (const FontV2IconRecord *)0;
    }
    mapped = font_v2_practice_icon_map[token];
    if (mapped == 0xFFu) {
        return (const FontV2IconRecord *)0;
    }
    return (
        (const FontV2IconRecord *)FONT_PRACTICE_ICON_TABLE_ADDRESS
    ) + mapped;
}

FONT_V2_SECTION(".text.font_v2_practice_icon_metric")
void font_v2_practice_icon_metric(
    float *width,
    float *height,
    u32 token
) {
    const FontV2IconRecord *record = font_v2_icon_record(token);
    if (record) {
        *width = (float)record->width;
        *height = (float)record->height;
    }
}

FONT_V2_SECTION(".text.font_v2_practice_icon_draw")
void font_v2_practice_icon_draw(
    float *draw_x,
    float *draw_y,
    u32 token
) {
    const FontV2IconRecord *record = font_v2_icon_record(token);
    FontV2PracticeFrame *frame =
        (FontV2PracticeFrame *)font_v2_active_session;
    u32 object;
    float y;

    if (!record || !frame) {
        return;
    }

    object = frame->object_primary;
    if (token >= 4u && token < 8u) {
        object = frame->object_secondary;
    }
    y = *draw_y;
    if (token >= 11u && token < 15u) {
        y -= 3.0f;
    } else if (token == 17u) {
        y += 1.0f;
    }
    font_v2_practice_icon_draw_callback(
        object,
        (u32)record,
        *draw_x,
        y
    );
    *draw_x += (float)record->width;
}

FONT_V2_SECTION(".text.font_v2_practice_adapter_impl")
int font_v2_practice_adapter_impl(
    u32 arg0,
    u32 arg1,
    u32 arg2,
    u32 object_primary,
    u32 object_secondary,
    u32 native_y_bits
) {
    FontV2PracticeFrame frame;
    volatile u32 *renderer;
    const u8 *record = (const u8 *)(arg0 + arg1);
    const s32 *tokens = (const s32 *)(record + 0x40);
    u32 token_count = *(const u32 *)(record + 0x68);
    u8 *destination = frame.buffer;
    u8 *limit = frame.buffer + FONT_PRACTICE_BUFFER_SIZE - 1u;
    u32 index;
    u32 previous_was_text = 0;
    FontV2Bits native_y;
    int result;

    frame.object_primary = object_primary;
    frame.object_secondary = object_secondary;
    *destination = 0;
    for (index = 0; index < token_count; index += 1) {
        s32 token = tokens[index];
        const u8 *payload;

        if (token < 0 || token >= 26) {
            continue;
        }
        if ((u32)token >= FONT_PRACTICE_TOKEN_COUNT) {
            if (index) {
                destination = font_v2_practice_append(
                    destination,
                    font_v2_practice_tokens +
                        FONT_PRACTICE_TOKEN_COUNT *
                            FONT_PRACTICE_TOKEN_STRIDE,
                    limit
                );
            }
            payload = (
                (const u8 *volatile *)
                    FONT_PRACTICE_TEXT_TABLE_ADDRESS
            )[token - (s32)FONT_PRACTICE_TOKEN_COUNT];
            destination = font_v2_practice_append(
                destination, payload, limit
            );
            previous_was_text = 1;
        } else {
            if (index && previous_was_text) {
                destination = font_v2_practice_append(
                    destination,
                    font_v2_practice_tokens +
                        FONT_PRACTICE_TOKEN_COUNT *
                            FONT_PRACTICE_TOKEN_STRIDE,
                    limit
                );
            }
            destination = font_v2_practice_append(
                destination,
                font_v2_practice_tokens +
                    (u32)token * FONT_PRACTICE_TOKEN_STRIDE,
                limit
            );
            previous_was_text = 0;
        }
    }

    renderer = *(volatile u32 **)FONT_RENDERER_POINTER_ADDRESS;
    if (!renderer) {
        return -1;
    }
    frame.saved_metric_callback = renderer[0x7C / sizeof(u32)];
    frame.saved_draw_callback = renderer[0x78 / sizeof(u32)];
    renderer[0x7C / sizeof(u32)] = (u32)font_v2_practice_icon_metric;
    renderer[0x78 / sizeof(u32)] = (u32)font_v2_practice_icon_draw;

    if (
        font_v2_wrap_native(
            frame.buffer,
            FONT_PRACTICE_BOX_WIDTH,
            FONT_PRACTICE_LINE_LIMIT,
            &frame.session.measured_width,
            &frame.session.line_count
        ) != 0
    ) {
        renderer[0x7C / sizeof(u32)] = frame.saved_metric_callback;
        renderer[0x78 / sizeof(u32)] = frame.saved_draw_callback;
        return -1;
    }

    native_y.u = native_y_bits;
    frame.session.text = frame.buffer;
    frame.session.box_x = FONT_PRACTICE_BOX_X;
    frame.session.box_y = native_y.f + FONT_PRACTICE_BOX_Y_OFFSET;
    frame.session.box_width = FONT_PRACTICE_BOX_WIDTH;
    frame.session.box_height = FONT_PRACTICE_BOX_HEIGHT;
    frame.session.horizontal_alignment = FONT_V2_ALIGN_START;
    frame.session.vertical_alignment = FONT_V2_ALIGN_CENTER;
    frame.session.flags =
        FONT_V2_FLAG_SHRINK_X |
        FONT_V2_FLAG_NEWLINE_BYTES |
        FONT_V2_FLAG_SEPARATE_LINE_ADVANCE |
        FONT_V2_FLAG_PREMEASURED;
    frame.session.line_limit = FONT_PRACTICE_LINE_LIMIT;
    frame.session.line_height = FONT_PRACTICE_LINE_ADVANCE;
    frame.session.glyph_height = FONT_PRACTICE_GLYPH_HEIGHT;
    frame.session.callback = (u32)font_v2_practice_callback;
    frame.session.callback_arg0 = arg2;
    frame.session.callback_arg1 = (u32)frame.buffer;
    frame.session.callback_arg2 = 0x0Fu;
    frame.session.callback_arg3 = (u32)&frame.session;

    result = font_v2_adapter_call(&frame.session);
    renderer[0x7C / sizeof(u32)] = frame.saved_metric_callback;
    renderer[0x78 / sizeof(u32)] = frame.saved_draw_callback;
    return result;
}
