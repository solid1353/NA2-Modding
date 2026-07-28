.ps2
.Open "./data/FILES/SLPS_258.37", 0x000FFE80

BASE_ADDRESS               equ 0x3E4410

.org BASE_ADDRESS
    .importobj "./test.o"

.org 0x001D0578
    jal printTest
    nop
    ld ra,0x00(sp)
    jr ra
    addiu sp,sp,0x10
.Close