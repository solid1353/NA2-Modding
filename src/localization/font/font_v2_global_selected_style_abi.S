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

    .section .text.v2_global_two_choice_draw,"ax",@progbits
    .balign 4
    .globl v2_global_two_choice_draw
    .type v2_global_two_choice_draw, @function
v2_global_two_choice_draw:
    addiu $sp,$sp,-64                                    # 0x27BDFFC0
    sw $s2,48($sp)                                       # 0xAFB20030
    sw $s1,52($sp)                                       # 0xAFB10034
    sw $s0,56($sp)                                       # 0xAFB00038
    sw $ra,60($sp)                                       # 0xAFBF003C
    addu $s0, $a0, $zero                                 # 0x00808021
    addu $s1, $a1, $zero                                 # 0x00A08821
    lui $s2,0x5b                                         # 0x3C12005B
    ori $s2,$s2,0x1280                                   # 0x36521280
    lw $a0,-13696($gp)                                   # 0x8F84CA80
    lw $a1,28($s0)                                       # 0x8E05001C
    jal 0x1866d0                                         # 0x0C0619B4
    nop                                                  # 0x00000000
    lwc1 $f12,16($s2)                                    # 0xC64C0010
    lwc1 $f13,20($s2)                                    # 0xC64D0014
    lw $a0,24($s2)                                       # 0x8E440018
    addiu $t0, $zero, 1                                  # 0x24080001
    beq $s1, $t0, .Lv2_global_two_choice_draw_060        # 0x12280006
    nop                                                  # 0x00000000
    lui $a1,0xff00                                       # 0x3C05FF00
    jal 0x378f50                                         # 0x0C0DE3D4
    nop                                                  # 0x00000000
    beq $zero, $zero, .Lv2_global_two_choice_draw_070    # 0x10000005
    nop                                                  # 0x00000000
.Lv2_global_two_choice_draw_060:
    lui $a1,0xff00                                       # 0x3C05FF00
    ori $a1,$a1,0xd4                                     # 0x34A500D4
    jal 0x379150                                         # 0x0C0DE454
    nop                                                  # 0x00000000
.Lv2_global_two_choice_draw_070:
    lwc1 $f12,0($s2)                                     # 0xC64C0000
    lwc1 $f13,4($s2)                                     # 0xC64D0004
    lw $a0,8($s2)                                        # 0x8E440008
    beq $s1, $zero, .Lv2_global_two_choice_draw_098      # 0x12200006
    nop                                                  # 0x00000000
    lui $a1,0xff00                                       # 0x3C05FF00
    jal 0x378f50                                         # 0x0C0DE3D4
    nop                                                  # 0x00000000
    beq $zero, $zero, .Lv2_global_two_choice_draw_0A8    # 0x10000005
    nop                                                  # 0x00000000
.Lv2_global_two_choice_draw_098:
    lui $a1,0xff00                                       # 0x3C05FF00
    ori $a1,$a1,0xd4                                     # 0x34A500D4
    jal 0x379150                                         # 0x0C0DE454
    nop                                                  # 0x00000000
.Lv2_global_two_choice_draw_0A8:
    lw $a0,-13696($gp)                                   # 0x8F84CA80
    lw $a1,-13692($gp)                                   # 0x8F85CA84
    jal 0x1866d0                                         # 0x0C0619B4
    nop                                                  # 0x00000000
    lw $s2,48($sp)                                       # 0x8FB20030
    lw $s1,52($sp)                                       # 0x8FB10034
    lw $s0,56($sp)                                       # 0x8FB00038
    lw $ra,60($sp)                                       # 0x8FBF003C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,64                                     # 0x27BD0040
    .size v2_global_two_choice_draw, . - v2_global_two_choice_draw
