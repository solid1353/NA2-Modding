/* Extended NA228 memory-card records and persistent settings. */

typedef unsigned char u8;
typedef unsigned short u16;
typedef signed int s32;
typedef unsigned int u32;

#define SAVE_APPENDIX_SECTION(name) \
    __attribute__((section(name), noinline))

#define NATIVE_RECORD_SIZE 0x2400u
#define CARD_RECORD_SIZE 0x3400u
#define APPENDIX_SIZE 0x1000u
#define APPENDIX_MAGIC 0x5332414Eu
#define APPENDIX_FORMAT_VERSION 1u
#define APPENDIX_HEADER_SIZE 0x10u
#define APPENDIX_ENTRY_SIZE 4u
#define APPENDIX_CHECKSUM_OFFSET 0x0Cu
#define CALL_WITH_ARGUMENT 0u
#define NATIVE_READ_ADDRESS 0x001C1E60u
#define NATIVE_GET_DIRECTORY_ADDRESS 0x001C2BA0u
#define NATIVE_DIRECTORY_ENTRY_SIZE_ADDRESS 0x0061F750u
#define NATIVE_HEADER_COPY_ADDRESS 0x001E30F0u
#define MEMORY_CARD_WORKER_POINTER_ADDRESS 0x006075F4u
#define NATIVE_READ_FAILURE 6
#define NATIVE_IO_SUCCESS (-777)
#define NATIVE_RECORD_COUNT 13u
#define LOAD_STATUS_NONE 0u
#define LOAD_STATUS_SETTINGS_RESET 1u
#define WORKER_STATUS_LOAD_COMPLETE 0x13u
#define WORKER_RESULT_SUCCESS 1u

typedef s32 (*NativeRead)(
    void *context, u32 port, u32 slot, u32 record,
    void *destination, u32 size, u32 wait
);
typedef s32 (*NativeGetDirectory)(
    const void *base_path, const u8 *suffix,
    u32 maximum_entries, u32 port, u32 slot
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
} SaveAppendixLoadStatus;

extern const SaveAppendixSchema save_appendix_schema;
extern volatile SaveAppendixLoadStatus save_appendix_load_status;
extern const u8 mod_text_save__settings_reset[];
extern u32 (*const save_appendix_next_update)(void *, u32);

static u8 save_appendix_notice[256];

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
void save_appendix_set(const SaveSettingDescriptor *descriptor, u32 value)
{
    if (descriptor->call_kind == CALL_WITH_ARGUMENT) {
        ((SetWithArgument)descriptor->setter)(descriptor->argument, value);
    } else {
        ((SetValue)descriptor->setter)(value);
    }
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_record_size(
    const void *base_path, u32 port, u32 slot, u32 record_index
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
    if (((NativeGetDirectory)NATIVE_GET_DIRECTORY_ADDRESS)(
            base_path, suffix, 1u, port, slot
        ) < 1) {
        return -1;
    }
    return *(volatile s32 *)NATIVE_DIRECTORY_ENTRY_SIZE_ADDRESS;
}

/* Physical integrity is checked before interpreting the current setting schema. */
static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_validate_envelope(const u8 *appendix)
{
    u16 count;
    u32 entries_end;
    u32 index;

    if (save_appendix_read_u32(appendix) != APPENDIX_MAGIC ||
        save_appendix_read_u16(appendix + 4u) != APPENDIX_FORMAT_VERSION ||
        save_appendix_read_u16(appendix + 10u) != 0u ||
        save_appendix_read_u32(appendix + APPENDIX_CHECKSUM_OFFSET) !=
            save_appendix_crc32(appendix)) {
        return 0;
    }
    count = save_appendix_read_u16(appendix + 8u);
    entries_end = APPENDIX_HEADER_SIZE + (u32)count * APPENDIX_ENTRY_SIZE;
    if (entries_end > APPENDIX_SIZE) {
        return 0;
    }
    for (index = 0u; index < count; ++index) {
        const u8 *entry = appendix + APPENDIX_HEADER_SIZE +
            index * APPENDIX_ENTRY_SIZE;
        u16 id = save_appendix_read_u16(entry);
        u32 earlier;
        if (id == 0u) {
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
    for (index = entries_end; index < APPENDIX_SIZE; ++index) {
        if (appendix[index] != 0u) {
            return 0;
        }
    }
    return 1;
}

/* Zero is invalid, one is compatible, two requires resetting settings. */
static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
s32 save_appendix_validate(const u8 *record)
{
    const u8 *appendix = record + NATIVE_RECORD_SIZE;
    u16 count;
    u32 index;

    if (save_appendix_validate_envelope(appendix) == 0) {
        return 0;
    }
    if (save_appendix_read_u16(appendix + 6u) !=
        save_appendix_schema.schema_version) {
        return 2;
    }
    count = save_appendix_read_u16(appendix + 8u);
    for (index = 0u; index < count; ++index) {
        const u8 *entry = appendix + APPENDIX_HEADER_SIZE +
            index * APPENDIX_ENTRY_SIZE;
        const SaveSettingDescriptor *descriptor = save_appendix_find(
            save_appendix_read_u16(entry)
        );
        if (descriptor != (const SaveSettingDescriptor *)0 &&
            save_appendix_read_u16(entry + 2u) > descriptor->maximum) {
            return 0;
        }
    }
    return 1;
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_apply(const u8 *record, u32 compatible)
{
    const u8 *appendix = record + NATIVE_RECORD_SIZE;
    u16 count = save_appendix_read_u16(appendix + 8u);
    u32 index;

    for (index = 0u; index < save_appendix_schema.count; ++index) {
        const SaveSettingDescriptor *descriptor =
            &save_appendix_schema.descriptors[index];
        save_appendix_set(descriptor, descriptor->default_value);
    }
    if (compatible == 0u) {
        return;
    }
    for (index = 0u; index < count; ++index) {
        const u8 *entry = appendix + APPENDIX_HEADER_SIZE +
            index * APPENDIX_ENTRY_SIZE;
        const SaveSettingDescriptor *descriptor = save_appendix_find(
            save_appendix_read_u16(entry)
        );
        if (descriptor != (const SaveSettingDescriptor *)0) {
            save_appendix_set(descriptor, save_appendix_read_u16(entry + 2u));
        }
    }
}

static SAVE_APPENDIX_SECTION(".text.save_appendix_helpers")
void save_appendix_encode(u8 *record)
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
        u32 value = save_appendix_get(descriptor);
        if (value > descriptor->maximum) {
            value = descriptor->default_value;
        }
        save_appendix_write_u16(entry, descriptor->id);
        save_appendix_write_u16(entry + 2u, (u16)value);
    }
    save_appendix_write_u32(appendix + APPENDIX_CHECKSUM_OFFSET,
        save_appendix_crc32(appendix));
}

SAVE_APPENDIX_SECTION(".text.save_appendix_read_profile")
s32 save_appendix_read_profile(
    void *context, u32 port, u32 slot, u32 record_index,
    void *destination, u32 size, u32 wait
)
{
    s32 result;
    (void)size;
    save_appendix_load_status.outcome = LOAD_STATUS_NONE;
    if (save_appendix_record_size(context, port, slot, record_index) !=
        (s32)CARD_RECORD_SIZE) {
        return NATIVE_READ_FAILURE;
    }
    result = ((NativeRead)NATIVE_READ_ADDRESS)(
        context, port, slot, record_index, destination, CARD_RECORD_SIZE, wait
    );
    if (result != NATIVE_IO_SUCCESS ||
        save_appendix_validate((const u8 *)destination) == 0) {
        return NATIVE_READ_FAILURE;
    }
    return result;
}

SAVE_APPENDIX_SECTION(".text.save_appendix_update")
u32 save_appendix_update(void *controller_pointer, u32 mode)
{
    volatile u32 *controller = (volatile u32 *)controller_pointer;
    volatile u32 *worker = *(volatile u32 **)MEMORY_CARD_WORKER_POINTER_ADDRESS;
    u32 result = save_appendix_next_update(controller_pointer, mode);

    if (mode == 1u && worker != (volatile u32 *)0 &&
        worker[0x4Cu / 4u] == WORKER_STATUS_LOAD_COMPLETE &&
        worker[0x50u / 4u] == WORKER_RESULT_SUCCESS &&
        save_appendix_load_status.outcome == LOAD_STATUS_SETTINGS_RESET) {
        volatile u8 *ui = (volatile u8 *)controller[9];
        const u8 *message;
        u32 length = 0u;
        u32 reset_length = 0u;

        if (ui == (volatile u8 *)0) {
            return result;
        }
        message = *(const u8 * volatile *)(ui + 0x40u);
        if (message == (const u8 *)0 || message == save_appendix_notice) {
            return result;
        }
        while (length < 120u && message[length] != 0u) {
            save_appendix_notice[length] = message[length];
            ++length;
        }
        if (length == 120u) {
            return result;
        }
        save_appendix_notice[length++] = 0u;
        while (reset_length < 120u &&
            mod_text_save__settings_reset[reset_length] != 0u) {
            save_appendix_notice[length++] =
                mod_text_save__settings_reset[reset_length++];
        }
        save_appendix_clear(save_appendix_notice + length,
            sizeof(save_appendix_notice) - length);
        *(volatile u32 *)(ui + 0x40u) = (u32)save_appendix_notice;
    }
    return result;
}

SAVE_APPENDIX_SECTION(".text.save_appendix_load_profile")
void save_appendix_load_profile(void *destination, const void *source)
{
    s32 validity = save_appendix_validate((const u8 *)source);
    if (validity == 0) {
        return;
    }
    ((NativeHeaderCopy)NATIVE_HEADER_COPY_ADDRESS)(destination, source);
    save_appendix_apply((const u8 *)source, validity == 1);
    if (validity == 2) {
        save_appendix_load_status.outcome = LOAD_STATUS_SETTINGS_RESET;
    }
}

SAVE_APPENDIX_SECTION(".text.save_appendix_serialize_profile")
void save_appendix_serialize_profile(void *destination, const void *source)
{
    ((NativeHeaderCopy)NATIVE_HEADER_COPY_ADDRESS)(destination, source);
    save_appendix_encode((u8 *)destination);
}
