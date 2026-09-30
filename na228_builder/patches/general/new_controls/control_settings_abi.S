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

    .section .text.control_settings_commit_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_commit_bridge
    .type control_settings_commit_bridge, @function
control_settings_commit_bridge:
    addiu $sp, $sp, -16
    sd $t9, 0($sp)
    sd $ra, 8($sp)
    move $a0, $s1
    jal control_settings_commit
    nop
    ld $ra, 8($sp)
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    lui $k0, 0x0038
    ori $k0, $k0, 0x8004
    jr $k0
    nop
    .size control_settings_commit_bridge, . - control_settings_commit_bridge

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

    .section .text.control_settings_step_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_step_bridge
    .type control_settings_step_bridge, @function
control_settings_step_bridge:
    move $a0, $s1
    jal control_settings_action_step
    move $a1, $s0
    sll $v0, $s0, 3
    addu $v0, $v0, $s0
    sll $v0, $v0, 2
    addu $v0, $v0, $s1
    addiu $s2, $v0, 0x14
    lui $k0, 0x0038
    ori $k0, $k0, 0x83e0
    jr $k0
    nop
    .size control_settings_step_bridge, . - control_settings_step_bridge

    .section .text.control_settings_reset_rows_bridge,"ax",@progbits
    .balign 4
    .globl control_settings_reset_rows_bridge
    .type control_settings_reset_rows_bridge, @function
/* Select reset: copy the eight row actions and the vibration word from the
   generated default layout instead of the retail table. */
control_settings_reset_rows_bridge:
    lui $t0, %hi(control_default_reset_actions)
    addiu $t0, $t0, %lo(control_default_reset_actions)
    addiu $t1, $v1, 0x14
    li $t2, 9
1:
    lw $t3, 0($t0)
    addiu $t0, $t0, 4
    sw $t3, 0($t1)
    addiu $t2, $t2, -1
    bnez $t2, 1b
    addiu $t1, $t1, 4
    lui $k0, 0x0038
    ori $k0, $k0, 0x80f8
    jr $k0
    nop
    .size control_settings_reset_rows_bridge, . - control_settings_reset_rows_bridge
