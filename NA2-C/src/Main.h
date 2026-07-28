extern int printConsole(int unk1, char* text, int unk2);  // 0x0015E110

typedef union
{
    void *ptr;
    unsigned char bytes[4];
} PtrBytes;

static inline void printConsolePtr(const char *text)
{
    PtrBytes pb;
    pb.ptr = (void *)text;
    printConsole(0x10, (char *)pb.bytes, 0xA);
}