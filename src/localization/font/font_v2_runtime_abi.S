/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

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
