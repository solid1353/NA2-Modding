/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_c_native_measure_callback,"ax",@progbits
    .balign 4
    .globl v2_c_native_measure_callback
    .type v2_c_native_measure_callback, @function
v2_c_native_measure_callback:
    addu $a1, $zero, $zero                               # 0x00002821
    j 0x3798e0                                           # 0x080DE638
    nop                                                  # 0x00000000
    .size v2_c_native_measure_callback, . - v2_c_native_measure_callback

    .section .text.v2_c_practice_icon_draw_callback,"ax",@progbits
    .balign 4
    .globl v2_c_practice_icon_draw_callback
    .type v2_c_practice_icon_draw_callback, @function
v2_c_practice_icon_draw_callback:
    j 0x37bb40                                           # 0x080DEED0
    nop                                                  # 0x00000000
    .size v2_c_practice_icon_draw_callback, . - v2_c_practice_icon_draw_callback

    .section .text.v2_c_quit_unselected_callback,"ax",@progbits
    .balign 4
    .globl v2_c_quit_unselected_callback
    .type v2_c_quit_unselected_callback, @function
v2_c_quit_unselected_callback:
    j 0x379a20                                           # 0x080DE688
    nop                                                  # 0x00000000
    .size v2_c_quit_unselected_callback, . - v2_c_quit_unselected_callback

    .section .text.v2_controls_callback,"ax",@progbits
    .balign 4
    .globl v2_controls_callback
    .type v2_controls_callback, @function
v2_controls_callback:
    addiu $sp,$sp,-32                                    # 0x27BDFFE0
    sw $ra,28($sp)                                       # 0xAFBF001C
    sw $s0,24($sp)                                       # 0xAFB00018
    sw $s1,20($sp)                                       # 0xAFB10014
    sw $s2,16($sp)                                       # 0xAFB20010
    addu $s0, $a0, $zero                                 # 0x00808021
    addu $s1, $a1, $zero                                 # 0x00A08821
    addu $s2, $a2, $zero                                 # 0x00C09021
    addu $a1, $zero, $zero                               # 0x00002821
    jal 0x3798e0                                         # 0x0C0DE638
    nop                                                  # 0x00000000
    sra $t0,$v0,0x1                                      # 0x00024043
    mtc1 $t0,$f0                                         # 0x44880000
    cvt.s.w $f0,$f0                                      # 0x46800020
    lwc1 $f12,72($s2)                                    # 0xC64C0048
    add.s $f12,$f12,$f0                                  # 0x46006300
    lwc1 $f13,76($s2)                                    # 0xC64D004C
    addu $a0, $s0, $zero                                 # 0x02002021
    addu $a1, $s1, $zero                                 # 0x02202821
    jal 0x379240                                         # 0x0C0DE490
    nop                                                  # 0x00000000
    lw $s2,16($sp)                                       # 0x8FB20010
    lw $s1,20($sp)                                       # 0x8FB10014
    lw $s0,24($sp)                                       # 0x8FB00018
    lw $ra,28($sp)                                       # 0x8FBF001C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,32                                     # 0x27BD0020
    .size v2_controls_callback, . - v2_controls_callback

    .section .text.v2_pause_list_callback,"ax",@progbits
    .balign 4
    .globl v2_pause_list_callback
    .type v2_pause_list_callback, @function
v2_pause_list_callback:
    lwc1 $f12,72($a3)                                    # 0xC4EC0048
    lwc1 $f13,76($a3)                                    # 0xC4ED004C
    j 0x382470                                           # 0x080E091C
    nop                                                  # 0x00000000
    .size v2_pause_list_callback, . - v2_pause_list_callback

    .section .text.v2_pause_list_selected_callback,"ax",@progbits
    .balign 4
    .globl v2_pause_list_selected_callback
    .type v2_pause_list_selected_callback, @function
v2_pause_list_selected_callback:
    lwc1 $f0,72($a3)                                     # 0xC4E00048
    cvt.w.s $f0,$f0                                      # 0x46000024
    mfc1 $a1,$f0                                         # 0x44050000
    lwc1 $f1,76($a3)                                     # 0xC4E1004C
    cvt.w.s $f1,$f1                                      # 0x46000864
    mfc1 $a2,$f1                                         # 0x44060800
    lw $t0,104($a3)                                      # 0x8CE80068
    lw $a3,4($a3)                                        # 0x8CE70004
    j 0x3827a0                                           # 0x080E09E8
    nop                                                  # 0x00000000
    .size v2_pause_list_selected_callback, . - v2_pause_list_selected_callback

    .section .text.v2_practice_callback,"ax",@progbits
    .balign 4
    .globl v2_practice_callback
    .type v2_practice_callback, @function
v2_practice_callback:
    lwc1 $f12,72($a3)                                    # 0xC4EC0048
    lwc1 $f13,76($a3)                                    # 0xC4ED004C
    j 0x382310                                           # 0x080E08C4
    nop                                                  # 0x00000000
    .size v2_practice_callback, . - v2_practice_callback

    .section .text.v2_quit_body_callback,"ax",@progbits
    .balign 4
    .globl v2_quit_body_callback
    .type v2_quit_body_callback, @function
v2_quit_body_callback:
    addiu $sp,$sp,-48                                    # 0x27BDFFD0
    sw $ra,44($sp)                                       # 0xAFBF002C
    lui $t0,0x4198                                       # 0x3C084198
    sw $t0,0($sp)                                        # 0xAFA80000
    lui $t0,0x4140                                       # 0x3C084140
    sw $t0,4($sp)                                        # 0xAFA80004
    sw $a1,8($sp)                                        # 0xAFA50008
    sw $a2,12($sp)                                       # 0xAFA6000C
    lbu $t0,98($a0)                                      # 0x90880062
    beq $t0, $zero, .Lv2_quit_body_callback_040          # 0x11000006
    lw $a2,116($a0)                                      # 0x8C860074
    lw $a0,120($a0)                                      # 0x8C840078
    addiu $a1,$sp,0                                      # 0x27A50000
    addiu $a3, $zero, -1                                 # 0x2407FFFF
    jal 0x379a20                                         # 0x0C0DE688
    nop                                                  # 0x00000000
.Lv2_quit_body_callback_040:
    lw $ra,44($sp)                                       # 0x8FBF002C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,48                                     # 0x27BD0030
    .size v2_quit_body_callback, . - v2_quit_body_callback

    .section .text.v2_quit_choices_scope,"ax",@progbits
    .balign 4
    .globl v2_quit_choices_scope
    .type v2_quit_choices_scope, @function
v2_quit_choices_scope:
    addiu $sp,$sp,-64                                    # 0x27BDFFC0
    sw $ra,60($sp)                                       # 0xAFBF003C
    sw $a0,16($sp)                                       # 0xAFA40010
    sw $a1,20($sp)                                       # 0xAFA50014
    sw $a2,24($sp)                                       # 0xAFA60018
    sw $a3,28($sp)                                       # 0xAFA7001C
    swc1 $f12,32($sp)                                    # 0xE7AC0020
    swc1 $f13,36($sp)                                    # 0xE7AD0024
    jal v2_c_quit_scope_enter                            # 0x0C000000
    nop                                                  # 0x00000000
    sw $v0,40($sp)                                       # 0xAFA20028
    lw $a0,16($sp)                                       # 0x8FA40010
    lw $a1,20($sp)                                       # 0x8FA50014
    lw $a2,24($sp)                                       # 0x8FA60018
    lw $a3,28($sp)                                       # 0x8FA7001C
    lwc1 $f12,32($sp)                                    # 0xC7AC0020
    lwc1 $f13,36($sp)                                    # 0xC7AD0024
    jal 0x383600                                         # 0x0C0E0D80
    nop                                                  # 0x00000000
    sw $v0,44($sp)                                       # 0xAFA2002C
    lw $a0,40($sp)                                       # 0x8FA40028
    jal v2_c_quit_scope_leave                            # 0x0C000000
    nop                                                  # 0x00000000
    lw $v0,44($sp)                                       # 0x8FA2002C
    lw $ra,60($sp)                                       # 0x8FBF003C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,64                                     # 0x27BD0040
    .size v2_quit_choices_scope, . - v2_quit_choices_scope

    .section .text.v2_special_choice_selected_callback,"ax",@progbits
    .balign 4
    .globl v2_special_choice_selected_callback
    .type v2_special_choice_selected_callback, @function
v2_special_choice_selected_callback:
    lwc1 $f12,72($a3)                                    # 0xC4EC0048
    lwc1 $f13,76($a3)                                    # 0xC4ED004C
    lw $a3,108($a3)                                      # 0x8CE7006C
    j 0x379150                                           # 0x080DE454
    nop                                                  # 0x00000000
    .size v2_special_choice_selected_callback, . - v2_special_choice_selected_callback

    .section .text.v2_special_controls_body_callback,"ax",@progbits
    .balign 4
    .globl v2_special_controls_body_callback
    .type v2_special_controls_body_callback, @function
v2_special_controls_body_callback:
    addiu $sp,$sp,-48                                    # 0x27BDFFD0
    sw $ra,44($sp)                                       # 0xAFBF002C
    lui $t0,0x41c0                                       # 0x3C0841C0
    sw $t0,0($sp)                                        # 0xAFA80000
    lui $t0,0x4140                                       # 0x3C084140
    sw $t0,4($sp)                                        # 0xAFA80004
    sw $a1,8($sp)                                        # 0xAFA50008
    sw $a2,12($sp)                                       # 0xAFA6000C
    lbu $t0,98($a0)                                      # 0x90880062
    beq $t0, $zero, .Lv2_special_controls_body_callback_040 # 0x11000006
    lw $a2,116($a0)                                      # 0x8C860074
    lw $a0,120($a0)                                      # 0x8C840078
    addiu $a1,$sp,0                                      # 0x27A50000
    addiu $a3, $zero, -1                                 # 0x2407FFFF
    jal 0x379a20                                         # 0x0C0DE688
    nop                                                  # 0x00000000
.Lv2_special_controls_body_callback_040:
    lw $ra,44($sp)                                       # 0x8FBF002C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,48                                     # 0x27BD0030
    .size v2_special_controls_body_callback, . - v2_special_controls_body_callback

    .section .text.v2_title_callback,"ax",@progbits
    .balign 4
    .globl v2_title_callback
    .type v2_title_callback, @function
v2_title_callback:
    lwc1 $f12,72($a3)                                    # 0xC4EC0048
    lwc1 $f13,76($a3)                                    # 0xC4ED004C
    j 0x382310                                           # 0x080E08C4
    nop                                                  # 0x00000000
    .size v2_title_callback, . - v2_title_callback
