/* Route localized CCS reads through the external PRG/228_UI.BIN pack. */

typedef signed int s32;
typedef unsigned char u8;
typedef unsigned int u32;

#define NATIVE_OPEN_ADDRESS 0x001BE450u
#define NATIVE_CLOSE_ADDRESS 0x001BE540u
#define NATIVE_READ_ADDRESS 0x001BE560u
#define NATIVE_SEEK_ADDRESS 0x001BE740u
#define NATIVE_SIZE_ADDRESS 0x001BE7C0u
#define NATIVE_GZIP_SIZE_ADDRESS 0x001BE9B0u

#define PACK_SECTOR_SIZE 0x800u
#define PACK_ENTRY_SIZE 0x10u
#define PACK_MAX_ENTRIES ((PACK_SECTOR_SIZE - 16u) / PACK_ENTRY_SIZE)
#define ACTIVE_HANDLE_COUNT 8u

#define PACK_MAGIC_0 0x3232414Eu
#define PACK_MAGIC_1 0x50495538u

#define TEXTURE_SECTION(name) __attribute__((section(name), noinline))

typedef u32 (*NativeOpen)(const u8 *path);
typedef void (*NativeClose)(u32 handle);
typedef s32 (*NativeRead)(u32 handle, void *destination, u32 length);
typedef s32 (*NativeSeek)(u32 handle, s32 offset, s32 origin);
typedef u32 (*NativeSize)(u32 handle);
typedef u32 (*NativeGzipSize)(const u8 *path);

typedef struct TexturePackEntry {
    u32 path_hash;
    u32 sector;
    u32 sector_count;
    u32 decompressed_size;
} TexturePackEntry;

typedef struct ActiveTextureHandle {
    u32 handle;
    u32 size;
} ActiveTextureHandle;

static const u8 texture_pack_path[]
    __attribute__((section(".rodata.localization_ui_texture_pack_path"))) =
        "CDV:PRG/228_UI.BIN";

static u8 texture_pack_index[PACK_SECTOR_SIZE]
    __attribute__((
        section(".bss.localization_ui_texture_pack_index"),
        aligned(128)
    ));
static u32 texture_pack_index_loaded
    __attribute__((section(".bss.localization_ui_texture_pack_state")));
static u32 texture_pack_entry_count
    __attribute__((section(".bss.localization_ui_texture_pack_count")));
static ActiveTextureHandle active_texture_handles[ACTIVE_HANDLE_COUNT]
    __attribute__((section(".bss.localization_ui_texture_pack_handles")));

static u32 normalized_path_hash(const u8 *path)
{
    u32 hash = 0x811C9DC5u;
    u8 value;

    while (*path == '/' || *path == '\\') {
        ++path;
    }
    while ((value = *path++) != 0u) {
        if (value == '\\') {
            value = '/';
        } else if (value >= 'a' && value <= 'z') {
            value = (u8)(value - ('a' - 'A'));
        }
        hash ^= value;
        hash *= 0x01000193u;
    }
    return hash;
}

static void load_texture_pack_index(void)
{
    NativeOpen open_file = (NativeOpen)NATIVE_OPEN_ADDRESS;
    NativeClose close_file = (NativeClose)NATIVE_CLOSE_ADDRESS;
    NativeRead read_file = (NativeRead)NATIVE_READ_ADDRESS;
    u32 handle;
    u32 *header;

    if (texture_pack_index_loaded != 0u) {
        return;
    }
    handle = open_file(texture_pack_path);
    read_file(handle, texture_pack_index, PACK_SECTOR_SIZE);
    close_file(handle);
    header = (u32 *)texture_pack_index;
    if (header[0] == PACK_MAGIC_0 &&
        header[1] == PACK_MAGIC_1 &&
        header[2] != 0u &&
        header[2] <= PACK_MAX_ENTRIES &&
        header[3] == PACK_ENTRY_SIZE) {
        texture_pack_entry_count = header[2];
        texture_pack_index_loaded = 1u;
    }
}

static const TexturePackEntry *find_texture_pack_entry(const u8 *path)
{
    const TexturePackEntry *entries;
    u32 hash;
    u32 index;

    load_texture_pack_index();
    if (texture_pack_index_loaded == 0u) {
        return (const TexturePackEntry *)0;
    }
    hash = normalized_path_hash(path);
    entries = (const TexturePackEntry *)(texture_pack_index + 16u);
    for (index = 0u; index < texture_pack_entry_count; ++index) {
        if (entries[index].path_hash == hash) {
            return entries + index;
        }
    }
    return (const TexturePackEntry *)0;
}

static void clear_active_handle(u32 handle)
{
    u32 index;
    for (index = 0u; index < ACTIVE_HANDLE_COUNT; ++index) {
        if (active_texture_handles[index].handle == handle) {
            active_texture_handles[index].handle = 0u;
            active_texture_handles[index].size = 0u;
        }
    }
}

static void register_active_handle(u32 handle, u32 size)
{
    u32 index;
    clear_active_handle(handle);
    for (index = 0u; index < ACTIVE_HANDLE_COUNT; ++index) {
        if (active_texture_handles[index].handle == 0u) {
            active_texture_handles[index].handle = handle;
            active_texture_handles[index].size = size;
            return;
        }
    }
    active_texture_handles[0].handle = handle;
    active_texture_handles[0].size = size;
}

TEXTURE_SECTION(".text.localization_ui_texture_open")
u32 localization_ui_texture_open(const u8 *path)
{
    NativeOpen open_file = (NativeOpen)NATIVE_OPEN_ADDRESS;
    NativeSeek seek_file = (NativeSeek)NATIVE_SEEK_ADDRESS;
    const TexturePackEntry *entry = find_texture_pack_entry(path);
    u32 handle;

    if (entry == (const TexturePackEntry *)0) {
        handle = open_file(path);
        clear_active_handle(handle);
        return handle;
    }
    handle = open_file(texture_pack_path);
    seek_file(handle, (s32)(entry->sector * PACK_SECTOR_SIZE), 0);
    register_active_handle(
        handle,
        entry->sector_count * PACK_SECTOR_SIZE
    );
    return handle;
}

TEXTURE_SECTION(".text.localization_ui_texture_gzip_size")
u32 localization_ui_texture_gzip_size(const u8 *path)
{
    NativeGzipSize native_gzip_size =
        (NativeGzipSize)NATIVE_GZIP_SIZE_ADDRESS;
    const TexturePackEntry *entry = find_texture_pack_entry(path);
    if (entry != (const TexturePackEntry *)0) {
        return entry->decompressed_size;
    }
    return native_gzip_size(path);
}

TEXTURE_SECTION(".text.localization_ui_texture_file_size")
u32 localization_ui_texture_file_size(u32 handle)
{
    NativeSize native_size = (NativeSize)NATIVE_SIZE_ADDRESS;
    u32 index;
    for (index = 0u; index < ACTIVE_HANDLE_COUNT; ++index) {
        if (active_texture_handles[index].handle == handle) {
            return active_texture_handles[index].size;
        }
    }
    return native_size(handle);
}
