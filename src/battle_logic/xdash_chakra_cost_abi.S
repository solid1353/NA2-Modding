/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.xdash_pre_update_shim,"ax",@progbits
    .balign 4
    .globl xdash_pre_update_shim
    .type xdash_pre_update_shim, @function
xdash_pre_update_shim:
    addiu $sp,$sp,-16                                    # 0x27BDFFF0
    sw $ra,0($sp)                                        # 0xAFBF0000
    sw $a0,4($sp)                                        # 0xAFA40004
    jal battle_logic_xdash_pre_fighter_update            # 0x0C000000
    nop                                                  # 0x00000000
    lw $a0,4($sp)                                        # 0x8FA40004
    jal 0x20e280                                         # 0x0C0838A0
    nop                                                  # 0x00000000
    lw $ra,0($sp)                                        # 0x8FBF0000
    addiu $sp,$sp,16                                     # 0x27BD0010
    jr $ra                                               # 0x03E00008
    nop                                                  # 0x00000000
    .size xdash_pre_update_shim, . - xdash_pre_update_shim
