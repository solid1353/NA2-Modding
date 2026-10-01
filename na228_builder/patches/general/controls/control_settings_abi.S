    .set noreorder
    .set noat

    .section .text.control_settings_held_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_held_bridge
    .type control_settings_held_bridge, @function
control_settings_held_bridge:
    addiu $sp, $sp, -32
    sd $v0, 0($sp)
    sd $t9, 8($sp)
    sd $ra, 16($sp)
    lw $a0, 0x24($s4)
    jal control_settings_substitution_accepted
    move $a1, $s0
    beqz $v0, 1f
    nop
    ld $ra, 16($sp)
    ld $t9, 8($sp)
    addiu $sp, $sp, 32
    lui $k0, 0x0022
    ori $k0, $k0, 0x96c0
    jr $k0
    nop
1:
    ld $v0, 0($sp)
    ld $ra, 16($sp)
    ld $t9, 8($sp)
    addiu $sp, $sp, 32
    slti $v0, $v0, 16
    bnez $v0, 2f
    nop
    lui $k0, 0x0022
    ori $k0, $k0, 0x962c
    jr $k0
    nop
2:
    lui $k0, 0x0022
    ori $k0, $k0, 0x9638
    jr $k0
    nop
    .size control_settings_held_bridge, . - control_settings_held_bridge

    .section .text.control_settings_history_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_history_bridge
    .type control_settings_history_bridge, @function
control_settings_history_bridge:
    addiu $sp, $sp, -16
    sd $t9, 0($sp)
    sd $ra, 8($sp)
    move $a0, $s1
    move $a1, $s0
    jal control_settings_history_any
    nop
    ld $ra, 8($sp)
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $k0, 0x0022
    ori $k0, $k0, 0x96c0
    jr $k0
    nop
1:
    lui $k0, 0x0022
    ori $k0, $k0, 0x96b4
    jr $k0
    nop
    .size control_settings_history_bridge, . - control_settings_history_bridge

    .section .text.control_settings_block_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_block_bridge
    .type control_settings_block_bridge, @function
control_settings_block_bridge:
    addiu $sp, $sp, -32
    sd $a0, 0($sp)
    sd $v1, 8($sp)
    sd $t9, 16($sp)
    sd $ra, 24($sp)
    move $a0, $s5
    move $a1, $v1
    jal control_settings_guard_pressed
    nop
    ld $ra, 24($sp)
    ld $t9, 16($sp)
    ld $v1, 8($sp)
    ld $a0, 0($sp)
    addiu $sp, $sp, 32
    lui $k0, 0x006e
    ori $k0, $k0, 0xff34
    jr $k0
    nop
    .size control_settings_block_bridge, . - control_settings_block_bridge

    .section .text.control_settings_item_select_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_item_select_bridge
    .type control_settings_item_select_bridge, @function
control_settings_item_select_bridge:
    move $a0, $s5
    jal control_settings_item_select_bits
    move $a1, $s3
    or $s4, $s4, $v0
    beqz $s7, 2f
    nop
    lui $v1, 0x4000
    or $s4, $s4, $v1
2:
    lui $k0, 0x006f
    ori $k0, $k0, 0x05bc
    jr $k0
    nop
    .size control_settings_item_select_bridge, . - control_settings_item_select_bridge

# The binding match and count wrappers (live 0x006EFC40 and 0x006EFD90) load a
# native binding and tail-call the history primitive. A zero binding is a subset
# of every record, so an unbound action requests 0x10000, which no record holds.
    .section .text.control_settings_match_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_match_bridge
    .type control_settings_match_bridge, @function
control_settings_match_bridge:
    sll $v0, $a1, 1
    addu $v0, $v0, $a0
    lh $a1, 0x68($v0)
    bnez $a1, 1f
    nop
    lui $a1, 0x0001
1:
    lui $k0, 0x006e
    ori $k0, $k0, 0xfac0
    jr $k0
    nop
    .size control_settings_match_bridge, . - control_settings_match_bridge

    .section .text.control_settings_count_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_count_bridge
    .type control_settings_count_bridge, @function
control_settings_count_bridge:
    sll $v0, $a1, 1
    addu $v0, $v0, $a0
    lh $a1, 0x68($v0)
    bnez $a1, 1f
    nop
    lui $a1, 0x0001
1:
    lui $k0, 0x006e
    ori $k0, $k0, 0xfc70
    jr $k0
    nop
    .size control_settings_count_bridge, . - control_settings_count_bridge
