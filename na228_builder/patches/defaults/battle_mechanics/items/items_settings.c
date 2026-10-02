/* Shared item availability and Custom's weighted field-item pool. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int s32;

#define ITEMS_SECTION(name) __attribute__((section(name), noinline))
#define FIELD_ITEM_COUNT 25u
#define CUSTOM_MODE 4u
#define ALL_ITEMS ((1u << FIELD_ITEM_COUNT) - 1u)
#define MANAGER_POINTER 0x00607600u

typedef struct ItemsSettingsConfig {
    u32 mode;
    u32 availability;
    u32 enabled;
    u8 codes[FIELD_ITEM_COUNT];
} ItemsSettingsConfig;

typedef struct ItemsSettingsState {
    u32 mode;
    u32 availability;
    u32 enabled;
    u32 initialized;
} ItemsSettingsState;

extern const ItemsSettingsConfig items_settings_config;
volatile ItemsSettingsState items_settings_state
    __attribute__((section(".bss.items_settings_state")));

static void items_initialize(void)
{
    if (items_settings_state.initialized == 0u) {
        items_settings_state.mode = items_settings_config.mode;
        items_settings_state.availability = items_settings_config.availability;
        items_settings_state.enabled = items_settings_config.enabled;
        items_settings_state.initialized = 1u;
    }
}

static u32 items_active(void *manager)
{
    u32 mode;
    if (manager == (void *)0) return 0u;
    mode = *(volatile u32 *)((u8 *)manager + 0x0Cu);
    return mode == 2u || mode == 3u;
}

ITEMS_SECTION(".text.items_settings_option_get")
u32 items_settings_option_get(u32 option)
{
    items_initialize();
    if (option == 0u) return items_settings_state.mode;
    if (option == 1u) return items_settings_state.availability;
    if (option < FIELD_ITEM_COUNT + 2u)
        return (items_settings_state.enabled >> (option - 2u)) & 1u;
    return 0u;
}

ITEMS_SECTION(".text.items_settings_option_set")
void items_settings_option_set(u32 option, u32 value)
{
    items_initialize();
    if (option == 0u) {
        if (value <= CUSTOM_MODE) items_settings_state.mode = value;
    } else if (option == 1u) {
        if (value < CUSTOM_MODE) items_settings_state.availability = value;
    } else if (option < FIELD_ITEM_COUNT + 2u && value <= 1u) {
        u32 bit = 1u << (option - 2u);
        items_settings_state.enabled =
            (items_settings_state.enabled & ~bit) | (value != 0u ? bit : 0u);
    }
}

ITEMS_SECTION(".text.items_settings_availability")
u32 items_settings_availability(void *manager)
{
    if (items_active(manager) == 0u)
        return ((u32 (*)(void *))0x001F6E40u)(manager);
    items_initialize();
    return items_settings_state.mode == CUSTOM_MODE
        ? items_settings_state.availability : items_settings_state.mode;
}

/* Native amount handling adds code 04: the smaller chakra pickup. */
ITEMS_SECTION(".text.items_settings_extra_enabled")
u32 items_settings_extra_enabled(void)
{
    void *manager = *(void * volatile *)MANAGER_POINTER;
    if (items_active(manager) == 0u) return 1u;
    items_initialize();
    return items_settings_state.mode != CUSTOM_MODE ||
        (items_settings_state.enabled & (1u << 1u)) != 0u;
}

static u32 items_pool_count(u32 kind)
{
    if (kind == 0u || kind == 4u) return 2u;
    if (kind == 1u) return 12u;
    if (kind == 2u) return 15u;
    if (kind == 3u) return 1u;
    return 0u;
}

static u32 items_pool_code(u32 kind, u32 lane)
{
    if (kind == 0u) return lane == 0u ? 2u : 3u;
    if (kind == 1u) return ((const u32 *)0x005B3C10u)[lane];
    if (kind == 2u) return ((const u32 *)0x005B3C40u)[lane];
    if (kind == 3u) return 3u;
    return 2u;
}

ITEMS_SECTION(".text.items_settings_select")
u32 items_settings_select(const s32 *distribution)
{
    u32 weights[FIELD_ITEM_COUNT];
    u32 index;
    u32 total = 0u;
    u32 roll;
    s32 previous = -1;
    s32 threshold = distribution[1];
    const s32 *entry = distribution;
    void *manager = *(void * volatile *)MANAGER_POINTER;

    items_initialize();
    if (items_active(manager) == 0u || items_settings_state.mode != CUSTOM_MODE ||
        items_settings_state.enabled == ALL_ITEMS) {
        return ((u32 (*)(const s32 *))0x003AE890u)(distribution);
    }
    for (index = 0u; index < FIELD_ITEM_COUNT; ++index) weights[index] = 0u;
    do {
        u32 kind = (u32)entry[0];
        u32 count = items_pool_count(kind);
        s32 upper = threshold < 99 ? threshold : 99;
        if (upper > previous && count != 0u) {
            u32 lane;
            /* LCM(2,12,15,1) keeps the authored bucket/lane weights integral. */
            u32 weight = (u32)(upper - previous) * 60u / count;
            for (lane = 0u; lane < count; ++lane) {
                u32 code = items_pool_code(kind, lane);
                for (index = 0u; index < FIELD_ITEM_COUNT; ++index) {
                    if (items_settings_config.codes[index] == code &&
                        (items_settings_state.enabled & (1u << index)) != 0u) {
                        weights[index] += weight;
                        total += weight;
                        break;
                    }
                }
            }
        }
        if (upper > previous) previous = upper;
        entry += 2;
        threshold += entry[1];
    } while (entry[0] != 0 && previous < 99);
    if (total == 0u) return 0u;
    roll = ((u32 (*)(u32))0x00180210u)(total - 1u);
    for (index = 0u; index < FIELD_ITEM_COUNT; ++index) {
        if (roll < weights[index]) return items_settings_config.codes[index];
        roll -= weights[index];
    }
    return 0u;
}
