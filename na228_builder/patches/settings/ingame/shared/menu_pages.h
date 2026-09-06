#ifndef NA228_SETTINGS_MENU_PAGES_H
#define NA228_SETTINGS_MENU_PAGES_H

#define SETTINGS_MENU_ROW_FLAG_SUBMENU 0x4000u
#define SETTINGS_MENU_SUBMENU_MAX_VALUE 0
#define SETTINGS_MENU_INPUT_OPEN_SUBMENU 0x0080u
#define SETTINGS_MENU_HEADER_ORANGE_TINT 0x805F5888u
#define SETTINGS_MENU_NO_PAGE 0xFFFFFFFFu

typedef struct SettingsMenuOption {
    unsigned int (*get)(unsigned int argument);
    void (*set)(unsigned int argument, unsigned int value);
    unsigned int argument;
    unsigned int staged;
} SettingsMenuOption;

unsigned int settings_menu_value_page(
    const unsigned int *pages, unsigned int count, unsigned int value
);

typedef struct SettingsMenuPage {
    unsigned int row_start;
    unsigned int row_count;
    unsigned int primary_row_count;
    unsigned int secondary_row_count;
    unsigned int parent_page;
    unsigned int parent_row;
    unsigned int heading_reference;
} SettingsMenuPage;

typedef struct SettingsMenuActivePage {
    unsigned int row_start;
    unsigned int row_count;
    unsigned int primary_row_count;
    unsigned int secondary_row_count;
    unsigned int heading_reference;
} SettingsMenuActivePage;

extern volatile unsigned int settings_menu_open_values[1];

const SettingsMenuPage *settings_menu_page(
    const SettingsMenuPage *pages,
    unsigned int page_count,
    unsigned int page_index
);
signed int settings_menu_select_page(
    const SettingsMenuPage *pages,
    unsigned int page_count,
    unsigned int model_row_count,
    unsigned int page_index,
    unsigned int requested_row,
    volatile unsigned int *active_page_index,
    volatile SettingsMenuActivePage *active_page,
    unsigned int *selected_row
);
signed int settings_menu_model_index(
    const volatile SettingsMenuActivePage *active_page,
    signed int page_row,
    unsigned int model_row_count
);
void settings_menu_initialize_open_values(void);
void settings_menu_prepare_practice_backing(
    void *backing,
    unsigned int primary_row_count,
    unsigned int secondary_row_count
);
void settings_menu_draw_practice_backing(
    void *backing,
    unsigned int primary_row_count,
    unsigned int secondary_row_count,
    unsigned int submenu_rows
);
void settings_menu_draw_tinted_label(
    float alpha,
    void *object,
    unsigned int color
);

/* Menu-owned data consumed by the native Practice content renderer. */
typedef struct SettingsMenuPresentation {
    const volatile SettingsMenuActivePage *page;
    void *owner;
    unsigned int (*label)(int row);
    unsigned int (*values)(int row);
    int (*value)(void *owner, int row);
    int (*maximum)(void *owner, int row);
    int (*enabled)(void *owner, int row);
    unsigned int submenu_rows;
} SettingsMenuPresentation;
void settings_menu_draw_content(void *controller, const SettingsMenuPresentation *view);
void settings_menu_update_window(void *controller, const volatile SettingsMenuActivePage *page);
void settings_menu_initialize_window(void *controller, const volatile SettingsMenuActivePage *page, unsigned int selected);
float settings_menu_cursor_y(void *controller);

#endif
