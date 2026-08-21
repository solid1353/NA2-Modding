/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_command_icon_offset_adapter,"ax",@progbits
    .balign 4
    .globl v2_command_icon_offset_adapter
    .type v2_command_icon_offset_adapter, @function
v2_command_icon_offset_adapter:
    addu $a0, $s1, $zero                                 # 0x02202021
    j v2_c_command_icon_offset                           # 0x00000000
    nop                                                  # 0x00000000
    .size v2_command_icon_offset_adapter, . - v2_command_icon_offset_adapter

    .section .text.v2_command_relationship_adapter,"ax",@progbits
    .balign 4
    .globl v2_command_relationship_adapter
    .type v2_command_relationship_adapter, @function
v2_command_relationship_adapter:
    addiu $sp,$sp,-32                                    # 0x27BDFFE0
    sw $ra,28($sp)                                       # 0xAFBF001C
    addu $a1, $s1, $zero                                 # 0x02202821
    mfc1 $a3,$f13                                        # 0x44076800
    jal v2_c_command_relationship_impl                   # 0x0C000000
    nop                                                  # 0x00000000
    lw $ra,28($sp)                                       # 0x8FBF001C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,32                                     # 0x27BD0020
    .size v2_command_relationship_adapter, . - v2_command_relationship_adapter
