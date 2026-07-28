.ps2
.Open "./data/FILES/SLOP_NA2.28", 0x000FFF00

BASE_ADDRESS               equ 0x8F0100

.definelabel injectionLabDispatch, 0x008F0000

.org BASE_ADDRESS
    .importobj "./test.o"

.org 0x008F0000
    lui t9, 0x008F
    lw t9, 0x0010(t9)
    jr t9
    nop

.org 0x008F0010
    .word injectionLabTick

.org 0x001D0578
    jal injectionLabDispatch
    nop
    ld ra,0x00(sp)
    jr ra
    addiu sp,sp,0x10
.Close
