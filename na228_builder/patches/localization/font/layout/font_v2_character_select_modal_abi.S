/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_character_choices_scope,"ax",@progbits
    .balign 4
    .globl v2_character_choices_scope
    .type v2_character_choices_scope, @function
v2_character_choices_scope:
    addiu $sp,$sp,-64                                    # 0x27BDFFC0
    sw $ra,60($sp)                                       # 0xAFBF003C
    sw $a0,16($sp)                                       # 0xAFA40010
    sw $a1,20($sp)                                       # 0xAFA50014
    sw $a2,24($sp)                                       # 0xAFA60018
    sw $a3,28($sp)                                       # 0xAFA7001C
    swc1 $f12,32($sp)                                    # 0xE7AC0020
    swc1 $f13,36($sp)                                    # 0xE7AD0024
    jal v2_c_character_scope_enter                       # 0x0C000000
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
    .size v2_character_choices_scope, . - v2_character_choices_scope
