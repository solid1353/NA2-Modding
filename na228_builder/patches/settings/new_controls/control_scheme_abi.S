    .set noreorder
    .set noat

    .section .text.control_scheme_held_guard_bridge,"ax",@progbits
    .balign 4
    .globl control_scheme_held_guard_bridge
    .type control_scheme_held_guard_bridge, @function
control_scheme_held_guard_bridge:
    addiu $sp, $sp, -16
    sd $t9, 0($sp)
    sd $ra, 8($sp)
    lui $t9, %hi(mod_settings_state)
    lw $t9, %lo(mod_settings_state)($t9)
    beqz $t9, 1f
    nop
    lw $a0, 0x24($s4)
    jal control_settings_substitution_held
    nop
    bnez $v0, 4f
    nop
    addiu $v0, $zero, 1
    b 2f
    nop
1:
    slti $v0, $v0, 16
    b 2f
    nop
2:
    ld $ra, 8($sp)
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 3f
    nop
    lui $k0, 0x0022
    ori $k0, $k0, 0x9638
    jr $k0
    nop
3:
    lui $k0, 0x0022
    ori $k0, $k0, 0x962c
    jr $k0
    nop
4:
    ld $ra, 8($sp)
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    lui $k0, 0x0022
    ori $k0, $k0, 0x96c0
    jr $k0
    nop
    .size control_scheme_held_guard_bridge, . - control_scheme_held_guard_bridge

    .section .text.control_scheme_logical_block_bridge,"ax",@progbits
    .balign 4
    .globl control_scheme_logical_block_bridge
    .type control_scheme_logical_block_bridge, @function
control_scheme_logical_block_bridge:
    addiu $sp, $sp, -16
    sd $t9, 0($sp)
    lui $t9, %hi(mod_settings_state)
    lw $t9, %lo(mod_settings_state)($t9)
    bnez $t9, 1f
    nop
    lh $v0, 14($s1)
    b 2f
    nop
1:
    move $v0, $zero
2:
    and $v0, $v1, $v0
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    lui $k0, 0x006e
    ori $k0, $k0, 0xff34
    jr $k0
    nop
    .size control_scheme_logical_block_bridge, . - control_scheme_logical_block_bridge
