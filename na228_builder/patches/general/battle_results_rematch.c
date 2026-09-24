/* Battle Results rematch; the session outcome counters remain native-owned. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;

#define ENTRY(name) __attribute__((section(".text.rematch." name), noinline))
#define LABEL_WIDTH 96u
#define LABEL_HEIGHT 24u
#define CALL(address, type) ((type)(address))

typedef void (*ObjectCall)(void *);
typedef void (*Destroy)(void *, u32);
typedef void (*DrawRect)(float, float, void *, const u16 *);
typedef void (*DrawPrompt)(float, float, void *, u32, u32);
typedef void *(*FindObject)(void *, const u8 *, u32);
typedef void *(*FindArchive)(const u8 *);
typedef void *(*CreateSprite)(void *, const u8 *, u32, u32, void *);

extern const u8 rematch_label_pixels[LABEL_WIDTH * LABEL_HEIGHT];

static struct {
    u8 *result;
    void *archive;
    void *badge;
    u32 pending;
    u8 archive_owned;
} rematch __attribute__((section(".bss.rematch")));

static const u8 archive_name[] = "vs.ccs";
static const u8 badge_name[] = "TEX_vs_t01";
static const u8 label_name[] = "TEX_xninka";
static const u16 badge_rect[] = {5, 233, 22, 22};
static const u16 label_rect[] = {8, 0, 80, LABEL_HEIGHT};

static u8 *manager(void)
{
    return *(u8 **)0x00607600u;
}

static void release_prompt(void)
{
    if (rematch.badge != (void *)0) {
        CALL(0x001CBDF0u, Destroy)(rematch.badge, 1u);
    }
    if (rematch.archive_owned) {
        void *archive = CALL(0x001AA450u, FindArchive)(archive_name);
        if (archive != (void *)0) {
            CALL(0x001A9790u, Destroy)(archive, 1u);
        }
    }
    rematch.badge = (void *)0;
    rematch.archive = (void *)0;
    rematch.archive_owned = 0u;
    rematch.result = (u8 *)0;
}

ENTRY("queue_resources")
void rematch_queue_resources(u32 flags)
{
    u8 *outer = *(u8 **)0x00607620u;
    if (manager() != (u8 *)0 && *(u32 *)(manager() + 0x0C) == 2u &&
        outer != (u8 *)0 && *(u32 *)(outer + 0x14) == 1u) {
        release_prompt();
        rematch.pending = 0u;
        rematch.result = *(u8 **)(outer + 0x3C);
        rematch.archive = CALL(0x001AA450u, FindArchive)(archive_name);
        if (rematch.archive == (void *)0) {
            CALL(0x001CF9E0u, void (*)(const u8 *, u32))(archive_name, 0u);
            rematch.archive_owned = 1u;
        }
    }
    CALL(0x001CFCD0u, void (*)(u32))(flags);
}

ENTRY("initialize")
void rematch_initialize(u8 *result)
{
    u8 *summary;
    u8 *texture;
    u8 *mipmap;
    u8 *pixels;
    u32 x;
    u32 y;

    CALL(0x00719ED0u, ObjectCall)(result);
    if (result != rematch.result) {
        return;
    }
    summary = *(u8 **)(result + 0x164);
    if (summary == (u8 *)0) {
        goto failed;
    }
    texture = CALL(0x001A8F00u, FindObject)(
        *(void **)(summary + 8), label_name, 1u);
    if (texture == (u8 *)0 || texture[0x36] != 9u || texture[0x37] != 8u) {
        goto failed;
    }
    mipmap = *(u8 **)(texture + 0x28);
    if (mipmap == (u8 *)0 || *(u32 *)(mipmap + 8) * 16u < 512u * 256u) {
        goto failed;
    }
    pixels = *(u8 **)(mipmap + 4);
    if (pixels == (u8 *)0) {
        goto failed;
    }
    for (y = 0u; y < LABEL_HEIGHT; ++y) {
        for (x = 0u; x < LABEL_WIDTH; ++x) {
            pixels[(256u - LABEL_HEIGHT + y) * 512u + x] =
                rematch_label_pixels[y * LABEL_WIDTH + x];
        }
    }
    CALL(0x0010F860u, ObjectCall)(mipmap);
    rematch.archive = CALL(0x001AA450u, FindArchive)(archive_name);
    if (rematch.archive != (void *)0) {
        rematch.badge = CALL(0x0037B670u, CreateSprite)(
            rematch.archive, badge_name, 10u, 1u, *(void **)(summary + 0x118));
    }
    if (rematch.badge == (void *)0) {
        goto failed;
    }
    return;

failed:
    release_prompt();
}

ENTRY("draw")
void rematch_draw(float x, float y, void *sprite, u32 prompt, u32 backing)
{
    u8 *summary;
    void *label;
    CALL(0x0037C980u, DrawPrompt)(x, y, sprite, prompt, backing);
    if (rematch.result == (u8 *)0 || rematch.badge == (void *)0) {
        return;
    }
    summary = *(u8 **)(rematch.result + 0x164);
    /* Match the 22-unit Next/Details gap and four-unit badge/text gap. */
    CALL(0x0037BC40u, DrawRect)(x - 150.0f, y, rematch.badge, badge_rect);
    CALL(0x001CC070u, ObjectCall)(rematch.badge);
    label = *(void **)(summary + 0x140);
    /* Display details fills this sprite's one-rectangle batch. */
    CALL(0x001CC070u, ObjectCall)(label);
    CALL(0x0037BC40u, DrawRect)(x - 95.0f, y, label, label_rect);
}

ENTRY("accept")
s32 rematch_accept(u8 *result)
{
    u8 *input;
    s32 side;
    s32 accepted = CALL(0x0071A380u, s32 (*)(void *))(result);
    if (accepted != 0) {
        return accepted;
    }
    if (result != rematch.result || *(u16 *)result != 1u) {
        return 0;
    }
    input = *(u8 **)0x006073FCu;
    side = *(s16 *)(result + 2);
    if (input != (u8 *)0 && side >= 0 && side < 2 &&
        (*(u32 *)(input + 0x84u + (u32)side * 0x78u) & 0x20u) != 0u) {
        rematch.pending = 1u;
        return 1;
    }
    return 0;
}

ENTRY("cleanup")
void rematch_cleanup(u8 *result)
{
    if (result == rematch.result) {
        release_prompt();
    }
    CALL(0x00719140u, ObjectCall)(result);
}

ENTRY("restart")
void rematch_restart(u32 *outer)
{
    u8 *game;
    u32 i;
    CALL(0x001EEA80u, ObjectCall)(outer);
    if (rematch.pending != 1u) {
        return;
    }
    game = manager();
    CALL(0x001ED110u, ObjectCall)(outer);
    /* Native state 3 clears selection. Restore the setup saved before battle. */
    for (i = 0u; i < 0x7Cu; ++i) {
        game[0x20u + i] = game[0x9Cu + i];
    }
    rematch.pending = 2u;
}

ENTRY("begin_battle")
void rematch_begin_battle(u32 *outer)
{
    if (rematch.pending == 2u) {
        if (CALL(0x00200670u, u32 (*)(void))() == 0u) {
            return;
        }
        rematch.pending = 0u;
        CALL(0x002005B0u, void (*)(u32, u32))(1u, 0u);
        outer[1] = 3u;
        outer[0] = 10u;
        return;
    }
    CALL(0x001ED400u, ObjectCall)(outer);
}
