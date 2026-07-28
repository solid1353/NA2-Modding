.ps2
.Open "./data/FILES/SLOP_NA2.28", 0x000FFF00

BASE_ADDRESS               equ 0x8F0000

.org BASE_ADDRESS
    .importobj "./test.o"

.org 0x001D0578
    jal injectionLabTick
    nop
    ld ra,0x00(sp)
    jr ra
    addiu sp,sp,0x10
.Close
