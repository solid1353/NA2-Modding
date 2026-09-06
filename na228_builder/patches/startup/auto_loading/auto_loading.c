/* Automatically load the first save and report its outcome in the main menu. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define MEMORY_CARD_WORKER_POINTER_ADDRESS 0x006075F4u
#define MAIN_MENU_CONTROLLER_POINTER_ADDRESS 0x00607600u
#define MODE_SELECT_CONTROLLER_POINTER_ADDRESS 0x0060760Cu
#define FRAME_POINTER_ADDRESS 0x006073FCu
#define FONT_RENDERER_POINTER_ADDRESS 0x00607470u

#define LOAD_MODE_PREAMBLE_ADDRESS 0x001E1D80u
#define LOAD_MODE_PREPARE_ADDRESS 0x001D9600u
#define SCAN_MEMORY_CARD_ADDRESS 0x001E1DA0u
#define REQUEST_RECORD_LOAD_ADDRESS 0x001E1E10u
#define RESOLVE_WORKER_RESULT_ADDRESS 0x001E3120u
#define GET_OSD_CONFIG_PARAM_ADDRESS 0x0015DD90u
#define MAIN_MENU_UPDATE_ADDRESS 0x00203C50u
#define FONT_SET_CONTEXT_ADDRESS 0x001866D0u
#define TEXT_DRAW_ADDRESS 0x00378F50u
#define TEXT_MEASURE_ADDRESS 0x003798E0u

#define CONTROLLER_PHASE_WORD 2u
#define MAIN_MENU_STATE_WORD 2u
#define MAIN_MENU_MODE_WORD 3u
#define FRAME_SCREEN_CONTEXT_OFFSET 0x150u
#define FONT_RENDERER_CONTEXT_OFFSET 0x6Cu

#define WORKER_RECORD_ZERO_PRESENT_OFFSET 0x00u
#define WORKER_RECORD_ZERO_PLAY_TICKS_OFFSET 0x04u
#define WORKER_RECORD_ZERO_MINUTE_OFFSET 0x0Au
#define WORKER_RECORD_ZERO_HOUR_OFFSET 0x0Bu
#define WORKER_RECORD_ZERO_DAY_OFFSET 0x0Cu
#define WORKER_RECORD_ZERO_MONTH_OFFSET 0x0Du
#define WORKER_RECORD_ZERO_YEAR_OFFSET 0x0Eu
#define WORKER_STATUS_OFFSET 0x4Cu
#define WORKER_RESULT_OFFSET 0x50u
#define WORKER_MODE_OFFSET 0x54u

#define WORKER_STATUS_SCAN_COMPLETE 0x01u
#define WORKER_STATUS_BUSY 0x04u
#define WORKER_STATUS_NO_CARD 0x05u
#define WORKER_STATUS_UNSUPPORTED_CARD 0x07u
#define WORKER_STATUS_LOAD_CONFIRMATION 0x10u
#define WORKER_STATUS_READING_PORT_ZERO 0x11u
#define WORKER_STATUS_READING_PORT_ONE 0x12u
#define WORKER_STATUS_LOAD_COMPLETE 0x13u
#define WORKER_STATUS_UNFORMATTED_CARD 0x28u
#define WORKER_STATUS_NO_GAME_DATA 0x29u

#define WORKER_RESULT_NONE 0u
#define WORKER_RESULT_SUCCESS 1u
#define WORKER_RESULT_CONFIRMATION 3u

#define CONTINUE_PENDING 0u
#define CONTINUE_LOADED 1u
#define CONTINUE_WITHOUT_LOAD 2u

#define NOTIFICATION_NONE 0u
#define NOTIFICATION_LOADED 1u
#define NOTIFICATION_NO_SAVE_DATA 2u
#define NOTIFICATION_NO_GAME_DATA 3u
#define NOTIFICATION_NO_CARD 4u
#define NOTIFICATION_UNFORMATTED_CARD 5u
#define NOTIFICATION_UNSUPPORTED_CARD 6u
#define NOTIFICATION_LOAD_FAILED 7u

#define USABLE_MAIN_MENU_STATE 4u
#define USABLE_MAIN_MENU_MODE 1u
#define MODE_SELECT_VISIBLE_STATE 4u

#define EE_COUNT_TICKS_PER_SECOND 294912000u
#define NOTIFICATION_DURATION_TICKS (EE_COUNT_TICKS_PER_SECOND * 10u)
#define MAX_PLAY_TIME_TICKS 0x066FF2E2u
#define PLAY_TIME_TICKS_PER_HOUR 108000u
#define PLAY_TIME_TICKS_PER_MINUTE 1800u
#define PLAY_TIME_TICKS_PER_SECOND 30u

#define PS2_CLOCK_TIMEZONE_MINUTES 540
#define MIN_TIMEZONE_MINUTES -720
#define MAX_TIMEZONE_MINUTES 840
#define OSD_CONFIG_VERSION_SHIFT 13u
#define OSD_CONFIG_VERSION_MASK 0x07u
#define OSD_CONFIG_TIMEZONE_SHIFT 21u
#define OSD_CONFIG_DAYLIGHT_SAVING_BIT 0x10u

#define NOTIFICATION_RIGHT_X 500.0f
#define NOTIFICATION_LEFT_X 12.0f
#define NOTIFICATION_TOP_Y 12.0f
#define NOTIFICATION_LINE_HEIGHT 24.0f
#define COLOR_BLACK 0xFF000000u

#define AUTO_LOADING_SECTION(name) \
    __attribute__((section(name), noinline))
#define ALWAYS_INLINE static inline __attribute__((always_inline))

typedef struct StartupSaveNotificationState {
    volatile u32 outcome;
    volatile u32 start_ticks;
    volatile u32 play_ticks;
    volatile u32 saved_date;
    volatile u32 saved_time;
} StartupSaveNotificationState;

extern volatile StartupSaveNotificationState startup_save_notification_state;

static const u8 MESSAGE_LOADED[] = "Save data loaded";
static const u8 MESSAGE_NO_SAVE_DATA[] = "No save data found";
static const u8 MESSAGE_NO_GAME_DATA[] = "No game data found";
static const u8 MESSAGE_NO_CARD[] = "No memory card detected";
static const u8 MESSAGE_UNFORMATTED_CARD[] = "Memory card is not formatted";
static const u8 MESSAGE_UNSUPPORTED_CARD[] = "Unsupported memory card";
static const u8 MESSAGE_LOAD_FAILED[] = "Save data could not be loaded";
static const u8 PLAY_TIME_PREFIX[] = "Play Time ";
static const u8 SAVED_PREFIX[] = "Saved ";

ALWAYS_INLINE void reset_notification(void)
{
    startup_save_notification_state.outcome = NOTIFICATION_NONE;
    startup_save_notification_state.start_ticks = 0u;
    startup_save_notification_state.play_ticks = 0u;
    startup_save_notification_state.saved_date = 0u;
    startup_save_notification_state.saved_time = 0u;
}

ALWAYS_INLINE void publish_notification(u32 outcome)
{
    startup_save_notification_state.start_ticks = 0u;
    startup_save_notification_state.outcome = outcome;
}

ALWAYS_INLINE u32 classify_scan_failure(u32 status)
{
    if (status == WORKER_STATUS_NO_CARD) {
        return NOTIFICATION_NO_CARD;
    }
    if (status == WORKER_STATUS_UNSUPPORTED_CARD) {
        return NOTIFICATION_UNSUPPORTED_CARD;
    }
    if (status == WORKER_STATUS_UNFORMATTED_CARD) {
        return NOTIFICATION_UNFORMATTED_CARD;
    }
    if (status == WORKER_STATUS_NO_GAME_DATA) {
        return NOTIFICATION_NO_GAME_DATA;
    }
    return NOTIFICATION_LOAD_FAILED;
}

ALWAYS_INLINE u32 is_leap_year(u32 year)
{
    return
        year % 4u == 0u &&
        (year % 100u != 0u || year % 400u == 0u);
}

ALWAYS_INLINE u32 days_in_month(u32 year, u32 month)
{
    if (month == 2u) {
        return is_leap_year(year) != 0u ? 29u : 28u;
    }
    if (month == 4u || month == 6u || month == 9u || month == 11u) {
        return 30u;
    }
    return 31u;
}

ALWAYS_INLINE void get_osd_config_param2(u8 *config)
{
    register u8 *argument0 __asm__("$4") = config;
    register s32 argument1 __asm__("$5") = 1;
    register s32 argument2 __asm__("$6") = 1;

    __asm__ volatile(
        "li\t$3, 0x6f\n\t"
        "syscall\n\t"
        : "+r"(argument0), "+r"(argument1), "+r"(argument2)
        :
        : "$2", "$3", "memory"
    );
}

ALWAYS_INLINE s32 local_timezone_minutes(void)
{
    void (*get_osd_config)(u32 *) =
        (void (*)(u32 *))GET_OSD_CONFIG_PARAM_ADDRESS;
    u32 config = 0u;
    u8 config2 = 0u;
    s32 timezone;

    get_osd_config(&config);
    if (((config >> OSD_CONFIG_VERSION_SHIFT) &
         OSD_CONFIG_VERSION_MASK) == 0u) {
        return PS2_CLOCK_TIMEZONE_MINUTES;
    }

    timezone = (s32)config >> OSD_CONFIG_TIMEZONE_SHIFT;
    if (timezone < MIN_TIMEZONE_MINUTES ||
        timezone > MAX_TIMEZONE_MINUTES) {
        return PS2_CLOCK_TIMEZONE_MINUTES;
    }

    get_osd_config_param2(&config2);
    if ((config2 & OSD_CONFIG_DAYLIGHT_SAVING_BIT) != 0u) {
        timezone += 60;
    }
    return timezone;
}

ALWAYS_INLINE void decrement_date(u32 *year, u32 *month, u32 *day)
{
    if (*day > 1u) {
        --*day;
        return;
    }

    if (*month > 1u) {
        --*month;
    } else {
        *month = 12u;
        --*year;
    }
    *day = days_in_month(*year, *month);
}

ALWAYS_INLINE void increment_date(u32 *year, u32 *month, u32 *day)
{
    if (*day < days_in_month(*year, *month)) {
        ++*day;
        return;
    }

    *day = 1u;
    if (*month < 12u) {
        ++*month;
    } else {
        *month = 1u;
        ++*year;
    }
}

ALWAYS_INLINE void convert_saved_timestamp_to_local(
    u32 *saved_date,
    u32 *saved_time
)
{
    u32 year = *saved_date >> 16;
    u32 month = (*saved_date >> 8) & 0xFFu;
    u32 day = *saved_date & 0xFFu;
    u32 hour = *saved_time >> 8;
    u32 minute = *saved_time & 0xFFu;
    s32 local_minutes;

    if (year == 0u || year > 9999u || month == 0u || month > 12u ||
        day == 0u || day > days_in_month(year, month) ||
        hour > 23u || minute > 59u) {
        return;
    }

    local_minutes =
        (s32)(hour * 60u + minute) +
        local_timezone_minutes() -
        PS2_CLOCK_TIMEZONE_MINUTES;
    while (local_minutes < 0) {
        local_minutes += 24 * 60;
        decrement_date(&year, &month, &day);
    }
    while (local_minutes >= 24 * 60) {
        local_minutes -= 24 * 60;
        increment_date(&year, &month, &day);
    }

    *saved_date = (year << 16) | (month << 8) | day;
    *saved_time =
        ((u32)(local_minutes / 60) << 8) |
        (u32)(local_minutes % 60);
}

ALWAYS_INLINE void capture_loaded_record(volatile u8 *worker)
{
    u32 saved_date;
    u32 saved_time;

    saved_date =
        ((u32)*(volatile u16 *)(
            worker + WORKER_RECORD_ZERO_YEAR_OFFSET
        ) << 16) |
        ((u32)worker[WORKER_RECORD_ZERO_MONTH_OFFSET] << 8) |
        (u32)worker[WORKER_RECORD_ZERO_DAY_OFFSET];
    saved_time =
        ((u32)worker[WORKER_RECORD_ZERO_HOUR_OFFSET] << 8) |
        (u32)worker[WORKER_RECORD_ZERO_MINUTE_OFFSET];
    convert_saved_timestamp_to_local(&saved_date, &saved_time);

    startup_save_notification_state.play_ticks =
        *(volatile u32 *)(
            worker + WORKER_RECORD_ZERO_PLAY_TICKS_OFFSET
        );
    startup_save_notification_state.saved_date = saved_date;
    startup_save_notification_state.saved_time = saved_time;
    publish_notification(NOTIFICATION_LOADED);
}

AUTO_LOADING_SECTION(".text.startup_auto_loading_update")
u32 startup_auto_loading_update(void *controller, u32 mode)
{
    void (*load_mode_preamble)(void *) =
        (void (*)(void *))LOAD_MODE_PREAMBLE_ADDRESS;
    void (*prepare_load_mode)(u32) =
        (void (*)(u32))LOAD_MODE_PREPARE_ADDRESS;
    void (*scan_memory_card)(void *, u32) =
        (void (*)(void *, u32))SCAN_MEMORY_CARD_ADDRESS;
    void (*request_record_load)(void *, u32) =
        (void (*)(void *, u32))REQUEST_RECORD_LOAD_ADDRESS;
    void (*resolve_worker_result)(void *, u32) =
        (void (*)(void *, u32))RESOLVE_WORKER_RESULT_ADDRESS;
    volatile u32 *controller_words = (volatile u32 *)controller;
    volatile u8 *worker =
        *(volatile u8 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
    u32 phase;
    u32 status;
    u32 result;

    if (controller == (void *)0 || mode != 1u || worker == (volatile u8 *)0) {
        if (startup_save_notification_state.outcome == NOTIFICATION_NONE) {
            publish_notification(NOTIFICATION_LOAD_FAILED);
        }
        return CONTINUE_WITHOUT_LOAD;
    }

    phase = controller_words[CONTROLLER_PHASE_WORD];
    if (phase == 0u) {
        reset_notification();
        *(volatile u32 *)(worker + WORKER_MODE_OFFSET) = 1u;
        load_mode_preamble((void *)worker);
        prepare_load_mode(0u);
        scan_memory_card((void *)worker, 0u);
        controller_words[CONTROLLER_PHASE_WORD] = 1u;
        return CONTINUE_PENDING;
    }

    status = *(volatile u32 *)(worker + WORKER_STATUS_OFFSET);
    result = *(volatile u32 *)(worker + WORKER_RESULT_OFFSET);

    if (phase == 1u) {
        if (status == WORKER_STATUS_BUSY) {
            return CONTINUE_PENDING;
        }
        if (status == WORKER_STATUS_SCAN_COMPLETE &&
            result == WORKER_RESULT_NONE) {
            if (worker[WORKER_RECORD_ZERO_PRESENT_OFFSET] == 0u) {
                publish_notification(NOTIFICATION_NO_SAVE_DATA);
                return CONTINUE_WITHOUT_LOAD;
            }

            request_record_load((void *)worker, 0u);
            controller_words[CONTROLLER_PHASE_WORD] = 2u;
            return CONTINUE_PENDING;
        }

        publish_notification(classify_scan_failure(status));
        return CONTINUE_WITHOUT_LOAD;
    }

    if (phase == 2u) {
        if (status == WORKER_STATUS_BUSY) {
            return CONTINUE_PENDING;
        }
        if (status == WORKER_STATUS_LOAD_CONFIRMATION &&
            result != WORKER_RESULT_CONFIRMATION) {
            return CONTINUE_PENDING;
        }
        if (status != WORKER_STATUS_LOAD_CONFIRMATION) {
            publish_notification(NOTIFICATION_LOAD_FAILED);
            return CONTINUE_WITHOUT_LOAD;
        }

        resolve_worker_result((void *)worker, 1u);
        controller_words[CONTROLLER_PHASE_WORD] = 3u;
        return CONTINUE_PENDING;
    }

    if (phase == 3u) {
        if (status == WORKER_STATUS_BUSY ||
            status == WORKER_STATUS_READING_PORT_ZERO ||
            status == WORKER_STATUS_READING_PORT_ONE) {
            return CONTINUE_PENDING;
        }
        if (status == WORKER_STATUS_LOAD_COMPLETE) {
            if (result == WORKER_RESULT_SUCCESS) {
                capture_loaded_record(worker);
                return CONTINUE_LOADED;
            }
            return CONTINUE_PENDING;
        }

        publish_notification(NOTIFICATION_LOAD_FAILED);
        return CONTINUE_WITHOUT_LOAD;
    }

    publish_notification(NOTIFICATION_LOAD_FAILED);
    return CONTINUE_WITHOUT_LOAD;
}

AUTO_LOADING_SECTION(".text.startup_auto_loading_suppress_draw")
void startup_auto_loading_suppress_draw(void)
{
}

ALWAYS_INLINE u8 *append_text(u8 *destination, const u8 *source)
{
    while (*source != 0u) {
        *destination = *source;
        ++destination;
        ++source;
    }
    return destination;
}

ALWAYS_INLINE u8 *append_two_digits(u8 *destination, u32 value)
{
    value %= 100u;
    *destination++ = (u8)('0' + value / 10u);
    *destination++ = (u8)('0' + value % 10u);
    return destination;
}

ALWAYS_INLINE u8 *append_four_digits(u8 *destination, u32 value)
{
    if (value > 9999u) {
        value = 9999u;
    }
    *destination++ = (u8)('0' + value / 1000u);
    *destination++ = (u8)('0' + (value / 100u) % 10u);
    *destination++ = (u8)('0' + (value / 10u) % 10u);
    *destination++ = (u8)('0' + value % 10u);
    return destination;
}

ALWAYS_INLINE u8 *append_unpadded_number(u8 *destination, u32 value)
{
    u8 reverse[10];
    u32 length = 0u;

    do {
        reverse[length++] = (u8)('0' + value % 10u);
        value /= 10u;
    } while (value != 0u);

    while (length != 0u) {
        *destination++ = reverse[--length];
    }
    return destination;
}

ALWAYS_INLINE void format_play_time(u8 *destination, u32 ticks)
{
    u32 hours;
    u32 minutes;
    u32 seconds;

    destination = append_text(destination, PLAY_TIME_PREFIX);
    if (ticks >= MAX_PLAY_TIME_TICKS) {
        hours = 999u;
        minutes = 59u;
        seconds = 59u;
    } else {
        hours = ticks / PLAY_TIME_TICKS_PER_HOUR;
        minutes =
            (ticks % PLAY_TIME_TICKS_PER_HOUR) /
            PLAY_TIME_TICKS_PER_MINUTE;
        seconds =
            (ticks % PLAY_TIME_TICKS_PER_MINUTE) /
            PLAY_TIME_TICKS_PER_SECOND;
    }

    destination = append_unpadded_number(destination, hours);
    *destination++ = ':';
    destination = append_two_digits(destination, minutes);
    *destination++ = ':';
    destination = append_two_digits(destination, seconds);
    *destination = 0u;
}

ALWAYS_INLINE void format_saved_time(
    u8 *destination,
    u32 saved_date,
    u32 saved_time
)
{
    destination = append_text(destination, SAVED_PREFIX);
    destination = append_two_digits(destination, saved_date & 0xFFu);
    *destination++ = '/';
    destination = append_two_digits(destination, (saved_date >> 8) & 0xFFu);
    *destination++ = '/';
    destination = append_four_digits(destination, saved_date >> 16);
    *destination++ = ' ';
    destination = append_two_digits(destination, saved_time >> 8);
    *destination++ = ':';
    destination = append_two_digits(destination, saved_time & 0xFFu);
    *destination = 0u;
}

ALWAYS_INLINE const u8 *notification_message(u32 outcome)
{
    if (outcome == NOTIFICATION_NO_SAVE_DATA) {
        return MESSAGE_NO_SAVE_DATA;
    }
    if (outcome == NOTIFICATION_NO_GAME_DATA) {
        return MESSAGE_NO_GAME_DATA;
    }
    if (outcome == NOTIFICATION_NO_CARD) {
        return MESSAGE_NO_CARD;
    }
    if (outcome == NOTIFICATION_UNFORMATTED_CARD) {
        return MESSAGE_UNFORMATTED_CARD;
    }
    if (outcome == NOTIFICATION_UNSUPPORTED_CARD) {
        return MESSAGE_UNSUPPORTED_CARD;
    }
    return MESSAGE_LOAD_FAILED;
}

ALWAYS_INLINE void draw_notification_line(const u8 *text, float y)
{
    void (*draw_text)(float, float, const u8 *, u32) =
        (void (*)(float, float, const u8 *, u32))TEXT_DRAW_ADDRESS;
    s32 (*measure_text)(const u8 *, s32) =
        (s32 (*)(const u8 *, s32))TEXT_MEASURE_ADDRESS;
    s32 width = measure_text(text, 0);
    float x;

    if (width < 0) {
        width = 0;
    }
    x = NOTIFICATION_RIGHT_X - (float)width;
    if (x < NOTIFICATION_LEFT_X) {
        x = NOTIFICATION_LEFT_X;
    }

    draw_text(x, y, text, COLOR_BLACK);
}

AUTO_LOADING_SECTION(".text.startup_auto_loading_notification_draw")
void startup_auto_loading_notification_draw(void)
{
    void (*update_main_menu)(void) =
        (void (*)(void))MAIN_MENU_UPDATE_ADDRESS;
    void (*set_font_context)(void *, void *) =
        (void (*)(void *, void *))FONT_SET_CONTEXT_ADDRESS;
    volatile u32 *menu;
    volatile u32 *mode_select;
    volatile u8 *frame;
    volatile u8 *renderer;
    void *previous_context;
    u32 outcome;
    u32 start_ticks;
    u32 now;
    u8 play_time[24];
    u8 saved_time[24];

    update_main_menu();

    outcome = startup_save_notification_state.outcome;
    if (outcome == NOTIFICATION_NONE) {
        return;
    }

    menu = *(volatile u32 **)MAIN_MENU_CONTROLLER_POINTER_ADDRESS;
    mode_select =
        *(volatile u32 **)MODE_SELECT_CONTROLLER_POINTER_ADDRESS;
    if (menu == (volatile u32 *)0 ||
        menu[MAIN_MENU_STATE_WORD] != USABLE_MAIN_MENU_STATE ||
        menu[MAIN_MENU_MODE_WORD] != USABLE_MAIN_MENU_MODE ||
        mode_select == (volatile u32 *)0 ||
        mode_select[0] != MODE_SELECT_VISIBLE_STATE) {
        if (startup_save_notification_state.start_ticks != 0u) {
            reset_notification();
        }
        return;
    }

    __asm__ volatile("mfc0\t%0, $9\n" : "=r"(now));
    start_ticks = startup_save_notification_state.start_ticks;
    if (start_ticks == 0u) {
        start_ticks = now == 0u ? 1u : now;
        startup_save_notification_state.start_ticks = start_ticks;
    } else if (now - start_ticks >= NOTIFICATION_DURATION_TICKS) {
        reset_notification();
        return;
    }

    frame = *(volatile u8 **)FRAME_POINTER_ADDRESS;
    renderer = *(volatile u8 **)FONT_RENDERER_POINTER_ADDRESS;
    if (frame == (volatile u8 *)0 || renderer == (volatile u8 *)0) {
        return;
    }

    previous_context = *(void **)(renderer + FONT_RENDERER_CONTEXT_OFFSET);
    set_font_context(
        (void *)renderer,
        (void *)(frame + FRAME_SCREEN_CONTEXT_OFFSET)
    );

    if (outcome == NOTIFICATION_LOADED) {
        format_play_time(
            play_time,
            startup_save_notification_state.play_ticks
        );
        format_saved_time(
            saved_time,
            startup_save_notification_state.saved_date,
            startup_save_notification_state.saved_time
        );
        draw_notification_line(MESSAGE_LOADED, NOTIFICATION_TOP_Y);
        draw_notification_line(
            play_time,
            NOTIFICATION_TOP_Y + NOTIFICATION_LINE_HEIGHT
        );
        draw_notification_line(
            saved_time,
            NOTIFICATION_TOP_Y + NOTIFICATION_LINE_HEIGHT * 2.0f
        );
    } else {
        draw_notification_line(
            notification_message(outcome),
            NOTIFICATION_TOP_Y
        );
    }

    set_font_context((void *)renderer, previous_context);
}
