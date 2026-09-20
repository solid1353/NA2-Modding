/* Versioned settings appendix for dedicated NA228 memory-card records. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef signed int s32;
typedef unsigned int u32;

#define SAVE_APPENDIX_SECTION(name) \
    __attribute__((section(name), noinline))

#define NATIVE_RECORD_SIZE 0x2400u
#define CARD_RECORD_SIZE 0x2600u
#define APPENDIX_SIZE 0x0200u
#define APPENDIX_MAGIC 0x5332414Eu
#define APPENDIX_FORMAT_VERSION 1u
#define APPENDIX_HEADER_SIZE 0x10u
#define APPENDIX_ENTRY_SIZE 4u
#define APPENDIX_CHECKSUM_OFFSET 0x0Cu
#define CALL_WITH_ARGUMENT 0u
#define CALL_WITH_VALUE 1u
#define NATIVE_READ_ADDRESS 0x001C1E60u
#define NATIVE_CHECK_CARD_ADDRESS 0x001C20A0u
#define NATIVE_ALLOCATE_ADDRESS 0x00117700u
#define NATIVE_FREE_ADDRESS 0x00117C40u
#define MEMORY_CARD_WORKER_POINTER_ADDRESS 0x006075F4u
#define NATIVE_GET_DIRECTORY_ADDRESS 0x001C2BA0u
#define NATIVE_DIRECTORY_ENTRY_SIZE_ADDRESS 0x0061F750u
#define NATIVE_HEADER_COPY_ADDRESS 0x001E30F0u
#define NATIVE_READ_FAILURE 6
#define NATIVE_RECORD_COUNT 13u
#define LOAD_STATUS_NONE 0u
#define LOAD_STATUS_INCOMPATIBLE_SCHEMA 1u
#define LOAD_STATUS_UNSUPPORTED_FORMAT 2u
#define WORKER_STATUS_INCOMPATIBLE 0x30u
#define WORKER_STATUS_UPGRADE_FAILED 0x31u
#define WORKER_STATUS_UPGRADED 0x32u
#define WORKER_OPERATION_UPGRADE 0x0Fu
#define NATIVE_IO_SUCCESS (-777)

typedef s32 (*NativeRead)(
    void *context,
    u32 port,
    u32 slot,
    u32 record,
    void *destination,
    u32 size,
    u32 wait
);
typedef s32 (*NativeGetDirectory)(
    const void *base_path,
    const u8 *suffix,
    u32 maximum_entries,
    u32 port,
    u32 slot
);
typedef void (*NativeHeaderCopy)(void *destination, const void *source);
typedef u32 (*GetWithArgument)(u32 argument);
typedef void (*SetWithArgument)(u32 argument, u32 value);
typedef u32 (*GetValue)(void);
typedef void (*SetValue)(u32 value);

typedef struct SaveSettingDescriptor {
    u16 id;
    u16 maximum;
    u16 call_kind;
    u16 reserved;
    u32 argument;
    u32 default_value;
    u32 getter;
    u32 setter;
} SaveSettingDescriptor;

typedef struct SaveAppendixSchema {
    u16 schema_version;
    u16 count;
    u32 reserved;
    SaveSettingDescriptor descriptors[1];
} SaveAppendixSchema;

typedef struct SaveAppendixLoadStatus {
    volatile u32 outcome;
    volatile u16 found_version;
    volatile u16 required_version;
} SaveAppendixLoadStatus;

extern const SaveAppendixSchema save_appendix_schema;
extern volatile SaveAppendixLoadStatus save_appendix_load_status;

typedef u32 (*SaveLoadUpdate)(void *, u32);
extern const SaveLoadUpdate save_appendix_next_update;

static struct {
    u32 ui;
    u32 phase;
    volatile u32 port;
    volatile u16 version;
    volatile u16 approved;
    u8 message[256];
} save_appendix_dialog;

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u16 save_appendix_read_u16(const u8 *source)
{
    return (u16)((u16)source[0] | ((u16)source[1] << 8));
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u32 save_appendix_read_u32(const u8 *source)
{
    return (u32)source[0] |
        ((u32)source[1] << 8) |
        ((u32)source[2] << 16) |
        ((u32)source[3] << 24);
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_write_u16(u8 *destination, u16 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_write_u32(u8 *destination, u32 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
    destination[2] = (u8)(value >> 16);
    destination[3] = (u8)(value >> 24);
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_clear(u8 *destination, u32 size)
{
    u32 index;

    for (index = 0u; index < size; ++index) {
        destination[index] = 0u;
    }
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u32 save_appendix_crc32(const u8 *appendix)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    u32 bit;

    for (index = 0u; index < APPENDIX_SIZE; ++index) {
        u8 value = (
            index >= APPENDIX_CHECKSUM_OFFSET &&
            index < APPENDIX_CHECKSUM_OFFSET + 4u
        ) ? 0u : appendix[index];

        crc ^= value;
        for (bit = 0u; bit < 8u; ++bit) {
            u32 mask = 0u - (crc & 1u);
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return ~crc;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
const SaveSettingDescriptor *save_appendix_find(u16 id)
{
    u32 index;

    for (index = 0u; index < save_appendix_schema.count; ++index) {
        const SaveSettingDescriptor *descriptor =
            &save_appendix_schema.descriptors[index];
        if (descriptor->id == id) {
            return descriptor;
        }
    }
    return (const SaveSettingDescriptor *)0;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u32 save_appendix_get(const SaveSettingDescriptor *descriptor)
{
    if (descriptor->call_kind == CALL_WITH_ARGUMENT) {
        return ((GetWithArgument)descriptor->getter)(descriptor->argument);
    }
    return ((GetValue)descriptor->getter)();
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_set(
    const SaveSettingDescriptor *descriptor,
    u32 value
)
{
    if (descriptor->call_kind == CALL_WITH_ARGUMENT) {
        ((SetWithArgument)descriptor->setter)(descriptor->argument, value);
    } else {
        ((SetValue)descriptor->setter)(value);
    }
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_record_size(
    const void *base_path,
    u32 port,
    u32 slot,
    u32 record_index
)
{
    u8 suffix[8];
    u32 record_number;

    if (record_index >= NATIVE_RECORD_COUNT) {
        return -1;
    }
    record_number = record_index + 1u;
    suffix[0] = (u8)'/';
    suffix[1] = (u8)'d';
    suffix[2] = (u8)'a';
    suffix[3] = (u8)'t';
    suffix[4] = (u8)'a';
    suffix[5] = (u8)(record_number >= 10u ? '1' : '0');
    suffix[6] = (u8)('0' + (record_number >= 10u ? record_number - 10u : record_number));
    suffix[7] = 0u;
    if (
        ((NativeGetDirectory)NATIVE_GET_DIRECTORY_ADDRESS)(
            base_path,
            suffix,
            1u,
            port,
            slot
        ) < 1
    ) {
        return -1;
    }
    return *(volatile s32 *)NATIVE_DIRECTORY_ENTRY_SIZE_ADDRESS;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_validate_envelope(const u8 *appendix)
{
    u16 count;
    u32 entries_end;
    u32 index;

    if (
        save_appendix_read_u32(appendix) != APPENDIX_MAGIC ||
        save_appendix_read_u16(appendix + 4u) != APPENDIX_FORMAT_VERSION ||
        save_appendix_read_u16(appendix + 10u) != 0u ||
        save_appendix_read_u32(appendix + APPENDIX_CHECKSUM_OFFSET) !=
            save_appendix_crc32(appendix)
    ) {
        return 0;
    }
    count = save_appendix_read_u16(appendix + 8u);
    entries_end = APPENDIX_HEADER_SIZE + (u32)count * APPENDIX_ENTRY_SIZE;
    if (entries_end > APPENDIX_SIZE) {
        return 0;
    }
    for (index = entries_end; index < APPENDIX_SIZE; ++index) {
        if (appendix[index] != 0u) {
            return 0;
        }
    }
    return 1;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_validate(const u8 *record)
{
    const u8 *appendix = record + NATIVE_RECORD_SIZE;
    u16 count;
    u32 index;

    if (
        save_appendix_validate_envelope(appendix) == 0 ||
        save_appendix_read_u16(appendix + 6u) !=
            save_appendix_schema.schema_version
    ) {
        return 0;
    }
    count = save_appendix_read_u16(appendix + 8u);
    for (index = 0u; index < count; ++index) {
        const u8 *entry = appendix + APPENDIX_HEADER_SIZE +
            index * APPENDIX_ENTRY_SIZE;
        u16 id = save_appendix_read_u16(entry);
        u16 value = save_appendix_read_u16(entry + 2u);
        const SaveSettingDescriptor *descriptor = save_appendix_find(id);
        u32 earlier;

        if (descriptor == (const SaveSettingDescriptor *)0 ||
            value > descriptor->maximum) {
            return 0;
        }
        for (earlier = 0u; earlier < index; ++earlier) {
            const u8 *prior = appendix + APPENDIX_HEADER_SIZE +
                earlier * APPENDIX_ENTRY_SIZE;
            if (save_appendix_read_u16(prior) == id) {
                return 0;
            }
        }
    }
    return 1;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_apply(const u8 *record)
{
    const u8 *appendix = record + NATIVE_RECORD_SIZE;
    u16 count = save_appendix_read_u16(appendix + 8u);
    u32 index;

    for (index = 0u; index < save_appendix_schema.count; ++index) {
        const SaveSettingDescriptor *descriptor =
            &save_appendix_schema.descriptors[index];
        save_appendix_set(descriptor, descriptor->default_value);
    }
    for (index = 0u; index < count; ++index) {
        const u8 *entry = appendix + APPENDIX_HEADER_SIZE +
            index * APPENDIX_ENTRY_SIZE;
        const SaveSettingDescriptor *descriptor = save_appendix_find(
            save_appendix_read_u16(entry)
        );
        save_appendix_set(descriptor, save_appendix_read_u16(entry + 2u));
    }
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_encode(u8 *record, u32 defaults)
{
    u8 *appendix = record + NATIVE_RECORD_SIZE;
    u32 index;

    save_appendix_clear(appendix, APPENDIX_SIZE);
    save_appendix_write_u32(appendix, APPENDIX_MAGIC);
    save_appendix_write_u16(appendix + 4u, APPENDIX_FORMAT_VERSION);
    save_appendix_write_u16(appendix + 6u, save_appendix_schema.schema_version);
    save_appendix_write_u16(appendix + 8u, save_appendix_schema.count);
    for (index = 0u; index < save_appendix_schema.count; ++index) {
        const SaveSettingDescriptor *descriptor =
            &save_appendix_schema.descriptors[index];
        u8 *entry = appendix + APPENDIX_HEADER_SIZE + index * APPENDIX_ENTRY_SIZE;
        u32 value = defaults != 0u ? descriptor->default_value :
            save_appendix_get(descriptor);
        if (value > descriptor->maximum) {
            value = descriptor->default_value;
        }
        save_appendix_write_u16(entry, descriptor->id);
        save_appendix_write_u16(entry + 2u, (u16)value);
    }
    save_appendix_write_u32(appendix + APPENDIX_CHECKSUM_OFFSET,
        save_appendix_crc32(appendix));
}

/* Upgrade I/O checks the actual transfer count, unlike the native wrappers.
 * Index four names the descriptor table; it is only ever read here. */
static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_file_io(void *context, u32 port, u32 slot, u32 index,
    void *data, u32 size, u32 writing)
{
    u8 path[64];
    const u8 *base = (const u8 *)context;
    const u8 *suffix = index == 4u ? base : (const u8 *)"/data01";
    u32 length = 0u;
    u32 offset = 0u;
    s32 handle;
    s32 transferred = -1;
    s32 success = 0;
    void (*wait_io)(void *, s32 *) = (void (*)(void *, s32 *))0x001C2B70u;

    while (base[offset] != 0u && length < sizeof(path) - 1u) {
        path[length++] = base[offset++];
    }
    if (base[offset] != 0u) {
        return 0;
    }
    offset = 0u;
    while (suffix[offset] != 0u && length < sizeof(path) - 1u) {
        path[length++] = suffix[offset++];
    }
    if (suffix[offset] != 0u || index > 4u || (index == 4u && writing != 0u)) {
        return 0;
    }
    if (index < 4u) {
        path[length - 1u] = (u8)('1' + index);
    }
    path[length] = 0u;
    /* Open existing files only; never create or truncate a save. */
    if (((s32 (*)(void *, u32, u32, const u8 *, u32))0x001C2870u)(
            context, port, slot, path, writing != 0u ? 2u : 1u) == 0) {
        return 0;
    }
    handle = *(s32 *)((u8 *)context + 0x44u);
    if (((s32 (*)(s32, void *, u32))(writing != 0u ?
            0x00175F88u : 0x00175E70u))(handle, data, size) == 0) {
        wait_io(context, &transferred);
        success = transferred == (s32)size;
        if (writing != 0u) {
            if (((s32 (*)(s32))0x00176920u)(handle) == 0) {
                wait_io(context, &transferred);
                success = success != 0 && transferred == 0;
            } else {
                success = 0;
            }
        }
    }
    if (((s32 (*)(void *, s32))0x001C2AD0u)(context, handle) == 0) {
        success = 0;
    }
    return success;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_upgrade(void *context, u32 port, u32 slot)
{
    u32 table[16];
    u8 *records;
    u8 *verify;
    u32 old_records = 0u;
    u32 index;
    u32 byte;
    s32 success = 0;

    /* This is an explicit conversion, not a generic lower-version fallback. */
    if (save_appendix_schema.schema_version != 1u ||
        save_appendix_file_io(context, port, slot, 4u, table, sizeof(table), 0u) == 0 ||
        ((s32 (*)(void *, void *))0x001E1F50u)(context, table) == 0) {
        return 0;
    }
    records = ((u8 *(*)(u32))NATIVE_ALLOCATE_ADDRESS)(CARD_RECORD_SIZE * 5u);
    if (records == (u8 *)0) {
        return 0;
    }
    verify = records + CARD_RECORD_SIZE * 4u;
    /* Read and validate the entire set before the first write. */
    for (index = 0u; index < 4u; ++index) {
        u8 *record = records + CARD_RECORD_SIZE * index;
        const u8 *descriptor = (const u8 *)table + index * 0x10u;
        s32 size = save_appendix_record_size(context, port, slot, index);
        u32 checksum = 0u;

        if ((size != (s32)NATIVE_RECORD_SIZE && size != (s32)CARD_RECORD_SIZE) ||
            save_appendix_file_io(context, port, slot, index, record, (u32)size, 0u) == 0) {
            goto done;
        }
        if (descriptor[0] != 0u) {
            for (byte = 0u; byte < NATIVE_RECORD_SIZE; ++byte) {
                if (byte != 2u && byte != 3u) {
                    checksum += record[byte];
                }
            }
            if ((u16)checksum != save_appendix_read_u16(descriptor + 2u)) {
                goto done;
            }
        } else {
            for (byte = 0u; byte < NATIVE_RECORD_SIZE; ++byte) {
                if (record[byte] != 0xFFu) {
                    goto done;
                }
            }
        }
        if (size == (s32)NATIVE_RECORD_SIZE) {
            old_records |= 1u << index;
            save_appendix_encode(record, 1u);
        } else if (descriptor[0] == 0u && record[NATIVE_RECORD_SIZE] == 0xFFu) {
            /* Native creation leaves unused extended files completely erased. */
            for (byte = NATIVE_RECORD_SIZE; byte < CARD_RECORD_SIZE; ++byte) {
                if (record[byte] != 0xFFu) {
                    goto done;
                }
            }
            continue;
        }
        if (save_appendix_validate(record) == 0) {
            goto done;
        }
    }
    /* Keep data04 until last. Already-upgraded records remain untouched. */
    for (index = 0u; index < 4u; ++index) {
        u8 *record = records + CARD_RECORD_SIZE * index;
        if ((old_records & (1u << index)) == 0u) {
            continue;
        }
        if (save_appendix_file_io(context, port, slot, index, record, CARD_RECORD_SIZE, 1u) == 0 ||
            save_appendix_record_size(context, port, slot, index) != (s32)CARD_RECORD_SIZE ||
            save_appendix_file_io(context, port, slot, index, verify, CARD_RECORD_SIZE, 0u) == 0) {
            goto done;
        }
        for (byte = 0u; byte < CARD_RECORD_SIZE; ++byte) {
            if (verify[byte] != record[byte]) {
                goto done;
            }
        }
    }
    success = 1;
done:
    ((void (*)(void *))NATIVE_FREE_ADDRESS)(records);
    return success;
}

SAVE_APPENDIX_SECTION(".text.save_appendix_read_profile")
s32 save_appendix_read_profile(
    void *context,
    u32 port,
    u32 slot,
    u32 record_index,
    void *destination,
    u32 size,
    u32 wait
)
{
    s32 result;
    s32 record_size;
    u8 *record = (u8 *)destination;
    u8 *appendix = record + NATIVE_RECORD_SIZE;

    (void)size;
    save_appendix_load_status.outcome = LOAD_STATUS_NONE;
    save_appendix_load_status.found_version = 0u;
    save_appendix_load_status.required_version = 0u;
    record_size = save_appendix_record_size(
        context,
        port,
        slot,
        record_index
    );
    if (record_size == (s32)NATIVE_RECORD_SIZE) {
        result = ((NativeRead)NATIVE_READ_ADDRESS)(
            context,
            port,
            slot,
            record_index,
            destination,
            NATIVE_RECORD_SIZE,
            wait
        );
        if (result != NATIVE_IO_SUCCESS) {
            return NATIVE_READ_FAILURE;
        }
        save_appendix_load_status.found_version = 0u;
        save_appendix_load_status.required_version =
            save_appendix_schema.schema_version;
        save_appendix_load_status.outcome = LOAD_STATUS_INCOMPATIBLE_SCHEMA;
        return NATIVE_READ_FAILURE;
    }
    if (record_size < (s32)(NATIVE_RECORD_SIZE + APPENDIX_HEADER_SIZE)) {
        return NATIVE_READ_FAILURE;
    }
    save_appendix_clear(appendix, APPENDIX_SIZE);
    result = ((NativeRead)NATIVE_READ_ADDRESS)(
        context,
        port,
        slot,
        record_index,
        destination,
        record_size < (s32)CARD_RECORD_SIZE ? (u32)record_size : CARD_RECORD_SIZE,
        wait
    );
    if (result != NATIVE_IO_SUCCESS) {
        return NATIVE_READ_FAILURE;
    }
    if (save_appendix_read_u32(appendix) == APPENDIX_MAGIC &&
        (record_size != (s32)CARD_RECORD_SIZE ||
         save_appendix_read_u16(appendix + 4u) != APPENDIX_FORMAT_VERSION)) {
        save_appendix_load_status.outcome = LOAD_STATUS_UNSUPPORTED_FORMAT;
        return NATIVE_READ_FAILURE;
    }
    if (
        save_appendix_validate_envelope(appendix) != 0 &&
        save_appendix_read_u16(appendix + 6u) !=
            save_appendix_schema.schema_version
    ) {
        save_appendix_load_status.found_version =
            save_appendix_read_u16(appendix + 6u);
        save_appendix_load_status.required_version =
            save_appendix_schema.schema_version;
        save_appendix_load_status.outcome = LOAD_STATUS_INCOMPATIBLE_SCHEMA;
        return NATIVE_READ_FAILURE;
    }
    return save_appendix_validate(record) != 0 ? result : NATIVE_READ_FAILURE;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_probe(void *context, u32 port, u32 slot, u32 first, u32 count)
{
    void *record;
    u32 record_index;
    u32 outcome = LOAD_STATUS_NONE;
    u16 version = 0u;

    save_appendix_load_status.outcome = LOAD_STATUS_NONE;
    save_appendix_load_status.found_version = 0u;
    save_appendix_load_status.required_version = 0u;
    record = ((void *(*)(u32))NATIVE_ALLOCATE_ADDRESS)(CARD_RECORD_SIZE);
    if (record != (void *)0) {
        for (record_index = first; record_index < first + count; ++record_index) {
            save_appendix_read_profile(
                context, port, slot, record_index, record, CARD_RECORD_SIZE, 1u
            );
            if (save_appendix_load_status.outcome == LOAD_STATUS_UNSUPPORTED_FORMAT) {
                outcome = LOAD_STATUS_UNSUPPORTED_FORMAT;
                break;
            }
            if (save_appendix_load_status.outcome == LOAD_STATUS_INCOMPATIBLE_SCHEMA) {
                outcome = LOAD_STATUS_INCOMPATIBLE_SCHEMA;
                if (save_appendix_load_status.found_version > version) {
                    version = save_appendix_load_status.found_version;
                }
            }
        }
        ((void (*)(void *))NATIVE_FREE_ADDRESS)(record);
    }
    save_appendix_load_status.outcome = outcome;
    save_appendix_load_status.found_version = version;
    save_appendix_load_status.required_version = save_appendix_schema.schema_version;
}

SAVE_APPENDIX_SECTION(".text.save_appendix_check_card")
s32 save_appendix_check_card(void *context, u32 port, u32 slot)
{
    s32 result = ((s32 (*)(void *, u32, u32))NATIVE_CHECK_CARD_ADDRESS)(
        context, port, slot
    );
    volatile u32 *worker =
        *(volatile u32 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
    u32 operation;
    u32 save_mode;

    if (worker == (volatile u32 *)0) {
        return result;
    }
    operation = worker[0x48u / 4u];
    save_mode = worker[0x54u / 4u] == 2u;
    if (operation == WORKER_OPERATION_UPGRADE) {
        u32 approved = save_appendix_dialog.approved;
        save_appendix_dialog.approved = 0u;
        if (approved != 0u && save_appendix_dialog.version == 0u &&
            port == save_appendix_dialog.port && (result < 0 || result == 0x0B)) {
            if (save_appendix_upgrade(context, port, slot) != 0) {
                save_appendix_load_status.outcome = LOAD_STATUS_NONE;
                worker[0x48u / 4u] = 1u;
                worker[0x4Cu / 4u] = WORKER_STATUS_UPGRADED;
                worker[0x50u / 4u] = 1u;
                return -1;
            }
        }
        save_appendix_load_status.outcome = LOAD_STATUS_NONE;
        worker[0x48u / 4u] = 1u;
        worker[0x4Cu / 4u] = WORKER_STATUS_UPGRADE_FAILED;
        worker[0x50u / 4u] = 2u;
        return -1;
    }
    if (operation != 3u && operation != 5u && operation != 6u &&
        operation != 8u && operation != 9u && operation != 10u) {
        return result;
    }
    save_appendix_load_status.outcome = LOAD_STATUS_NONE;
    save_appendix_load_status.found_version = 0u;
    save_appendix_load_status.required_version = 0u;
    if (result >= 0 && result != 0x0B && result != 3) {
        return result;
    }
    save_appendix_probe(context, port, slot, 0u, 4u);
    if (save_appendix_load_status.outcome != LOAD_STATUS_NONE) {
        worker[0x48u / 4u] = 1u;
        worker[0x4Cu / 4u] = WORKER_STATUS_INCOMPATIBLE;
        worker[0x50u / 4u] = save_mode != 0u ? 3u : 1u;
        /* Idle the worker before its native corruption/recovery dispatch. */
        return -1;
    }
    return result;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u8 *save_appendix_text(u8 *destination, const char *source)
{
    while (*source != 0) {
        *destination++ = (u8)*source++;
    }
    return destination;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
u8 *save_appendix_number(u8 *destination, u32 value)
{
    u32 divisor = 10000u;
    while (divisor > value && divisor > 1u) {
        divisor /= 10u;
    }
    do {
        *destination++ = (u8)('0' + value / divisor);
        value %= divisor;
        divisor /= 10u;
    } while (divisor != 0u);
    return destination;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_message(u32 confirmation)
{
    u8 *text = save_appendix_dialog.message;
    /* The native panel reads four consecutive NUL-terminated lines. */
    save_appendix_clear(text, sizeof(save_appendix_dialog.message));
    if (confirmation != 0u) {
        text = save_appendix_text(text, "Upgrade the existing save data?");
        text = save_appendix_text(text + 1, "Your progress will be kept.");
    } else if (save_appendix_load_status.outcome == LOAD_STATUS_UNSUPPORTED_FORMAT) {
        text = save_appendix_text(text, "The existing save data");
        text = save_appendix_text(text + 1, "uses an unsupported format.");
        text = save_appendix_text(text + 1, "It cannot be loaded or changed.");
    } else {
        text = save_appendix_text(text, "The existing save data uses version ");
        text = save_appendix_number(text, save_appendix_load_status.found_version);
        text = save_appendix_text(text, ".");
        text = save_appendix_text(text + 1, "Version ");
        text = save_appendix_number(text, save_appendix_load_status.required_version);
        text = save_appendix_text(text, " is required.");
        if (save_appendix_load_status.found_version > save_appendix_schema.schema_version) {
            text = save_appendix_text(text + 1, "A newer game version is needed.");
        } else if (save_appendix_load_status.found_version != 0u ||
                   save_appendix_schema.schema_version != 1u) {
            text = save_appendix_text(text + 1, "This version cannot be upgraded.");
        }
    }
}

SAVE_APPENDIX_SECTION(".text.save_appendix_update")
u32 save_appendix_update(void *controller_pointer, u32 mode)
{
    volatile u32 *controller = (volatile u32 *)controller_pointer;
    volatile u32 *worker = *(volatile u32 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
    volatile u8 *ui = (volatile u8 *)controller[9];
    u32 save_mode = mode != 1u;
    u32 response = 0u;

    if (worker != (volatile u32 *)0 && save_appendix_dialog.ui == (u32)ui &&
        save_appendix_dialog.phase == 3u) {
        u32 status = worker[0x4Cu / 4u];
        if (status == WORKER_STATUS_UPGRADED) {
            save_appendix_dialog.phase = 0u;
            *(volatile u32 *)(ui + 0x40u) = 0u;
            controller[2] = 2u;
            controller[4] = 2u;
            ((void (*)(void *, u32))0x001E1DA0u)(
                (void *)worker, save_appendix_dialog.port);
            return save_appendix_next_update(controller_pointer, mode);
        }
        if (status == 4u || worker[0x48u / 4u] == WORKER_OPERATION_UPGRADE) {
            return 0u;
        }
        save_appendix_dialog.phase = 4u;
        save_appendix_clear(save_appendix_dialog.message, sizeof(save_appendix_dialog.message));
        save_appendix_text(save_appendix_dialog.message, "The save data could not be upgraded.");
    }

    if (save_appendix_dialog.phase != 4u && (worker == (volatile u32 *)0 ||
        (worker[0x4Cu / 4u] != WORKER_STATUS_INCOMPATIBLE &&
         !(worker[0x4Cu / 4u] == 0x14u &&
           save_appendix_load_status.outcome != LOAD_STATUS_NONE)) ||
        controller[2] < 2u || controller[2] > 6u)) {
        save_appendix_dialog.phase = 0u;
        return save_appendix_next_update(controller_pointer, mode);
    }
    /* The final read can observe a mismatch after an earlier probe succeeded. */
    if (save_appendix_dialog.phase != 4u) {
        worker[0x4Cu / 4u] = WORKER_STATUS_INCOMPATIBLE;
    }
    if (save_appendix_dialog.phase == 0u || save_appendix_dialog.ui != (u32)ui) {
        save_appendix_dialog.ui = (u32)ui;
        save_appendix_dialog.phase = 1u;
        save_appendix_dialog.port = worker[0x40u / 4u];
        *(volatile u32 *)(ui + 0x0Cu) = save_appendix_dialog.port;
        save_appendix_dialog.version = save_appendix_load_status.found_version;
        save_appendix_dialog.approved = 0u;
        save_appendix_message(0u);
        ((void (*)(void *, u32))0x001E5D10u)((void *)ui, 1u);
        *(volatile u32 *)(ui + 0x14u) = 1u;
    }
    *(volatile u32 *)(ui + 8u) = mode;
    *(volatile u32 *)(ui + 0x40u) = (u32)save_appendix_dialog.message;
    ui[1] = 1u;
    ui[2] = 0u;
    ui[4] = 0u;
    if (save_appendix_dialog.phase == 1u || save_appendix_dialog.phase == 4u) {
        response = ((u32 (*)(void *, u32))0x001E5DC0u)((void *)ui, 0u);
        if (response != 0u && save_appendix_dialog.phase == 1u &&
            save_appendix_load_status.outcome == LOAD_STATUS_INCOMPATIBLE_SCHEMA &&
            save_appendix_dialog.version == 0u && save_appendix_schema.schema_version == 1u) {
            save_appendix_dialog.phase = 2u;
            save_appendix_message(1u);
            response = 0u;
        }
    } else {
        response = ((u32 (*)(void *))0x001E6CE0u)((void *)ui);
        if (response == 1u) {
            u32 record_index = worker[0x44u / 4u];
            if (record_index >= 3u) {
                record_index = 0u;
            }
            controller[0] = worker[0x40u / 4u];
            controller[1] = record_index;
            controller[2] = 3u;
            worker[0x44u / 4u] = record_index;
            save_appendix_dialog.approved = 1u;
            save_appendix_dialog.phase = 3u;
            save_appendix_clear(save_appendix_dialog.message, sizeof(save_appendix_dialog.message));
            save_appendix_text(save_appendix_dialog.message, "Upgrading the existing save data...");
            worker[0x4Cu / 4u] = 4u;
            worker[0x50u / 4u] = 0u;
            worker[0x48u / 4u] = WORKER_OPERATION_UPGRADE;
            response = 0u;
        } else if (response != 2u && response != 3u) {
            response = 0u;
        }
    }
    if (response != 0u) {
        save_appendix_dialog.phase = 0u;
        save_appendix_dialog.approved = 0u;
        save_appendix_load_status.outcome = LOAD_STATUS_NONE;
        worker[0x48u / 4u] = 1u;
        worker[0x4Cu / 4u] = 1u;
        worker[0x50u / 4u] = 0u;
        controller[2] = save_mode != 0u ? 7u : 8u;
    }
    if (controller[3] < 0x1C2u) {
        ++controller[3];
    }
    return 0u;
}

SAVE_APPENDIX_SECTION(".text.save_appendix_load_profile")
void save_appendix_load_profile(void *destination, const void *source)
{
    if (save_appendix_validate((const u8 *)source) == 0) {
        return;
    }
    ((NativeHeaderCopy)NATIVE_HEADER_COPY_ADDRESS)(destination, source);
    save_appendix_apply((const u8 *)source);
}

SAVE_APPENDIX_SECTION(".text.save_appendix_serialize_profile")
void save_appendix_serialize_profile(void *destination, const void *source)
{
    ((NativeHeaderCopy)NATIVE_HEADER_COPY_ADDRESS)(destination, source);
    save_appendix_encode((u8 *)destination, 0u);
}
