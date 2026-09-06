/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_global_selected_record_draw,"ax",@progbits
    .balign 4
    .globl v2_global_selected_record_draw
    .type v2_global_selected_record_draw, @function
v2_global_selected_record_draw:
    lui $t0,0x3f80                                       # 0x3C083F80
    mtc1 $t0,$f0                                         # 0x44880000
    lwc1 $f1,0($a1)                                      # 0xC4A10000
    nop                                                  # 0x00000000
    add.s $f1,$f1,$f0                                    # 0x46000840
    swc1 $f1,0($a1)                                      # 0xE4A10000
    lui $t0,0x4000                                       # 0x3C084000
    mtc1 $t0,$f0                                         # 0x44880000
    lwc1 $f1,4($a1)                                      # 0xC4A10004
    nop                                                  # 0x00000000
    add.s $f1,$f1,$f0                                    # 0x46000840
    swc1 $f1,4($a1)                                      # 0xE4A10004
    j 0x3821d0                                           # 0x080E0874
    nop                                                  # 0x00000000
    .size v2_global_selected_record_draw, . - v2_global_selected_record_draw

    .section .text.v2_global_selected_style,"ax",@progbits
    .balign 4
    .globl v2_global_selected_style
    .type v2_global_selected_style, @function
v2_global_selected_style:
    lui $t0,0x3f80                                       # 0x3C083F80
    mtc1 $t0,$f0                                         # 0x44880000
    nop                                                  # 0x00000000
    add.s $f21,$f21,$f0                                  # 0x4600AD40
    lui $t0,0x4000                                       # 0x3C084000
    mtc1 $t0,$f0                                         # 0x44880000
    nop                                                  # 0x00000000
    add.s $f20,$f20,$f0                                  # 0x4600A500
    lw $a0,-13696($gp)                                   # 0x8F84CA80
    ori $v0, $zero, 0xff80                               # 0x3402FF80
    jr $ra                                               # 0x03E00008
    nop                                                  # 0x00000000
    .size v2_global_selected_style, . - v2_global_selected_style
