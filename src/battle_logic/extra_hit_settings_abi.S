/* Runtime branch adapter for selectable Extra Hit. */
    .set noreorder
    .set noat

    .macro save_volatile_state
    addiu $sp, $sp, -0x50
    sw $v0, 0x00($sp)
    sw $v1, 0x04($sp)
    sw $a0, 0x08($sp)
    sw $a1, 0x0c($sp)
    sw $a2, 0x10($sp)
    sw $a3, 0x14($sp)
    sw $t0, 0x18($sp)
    sw $t1, 0x1c($sp)
    sw $t2, 0x20($sp)
    sw $t3, 0x24($sp)
    sw $t4, 0x28($sp)
    sw $t5, 0x2c($sp)
    sw $t6, 0x30($sp)
    sw $t7, 0x34($sp)
    sw $t8, 0x38($sp)
    sw $t9, 0x3c($sp)
    sd $ra, 0x48($sp)
    .endm

    .macro restore_volatile_state
    ld $ra, 0x48($sp)
    lw $t9, 0x3c($sp)
    lw $t8, 0x38($sp)
    lw $t7, 0x34($sp)
    lw $t6, 0x30($sp)
    lw $t5, 0x2c($sp)
    lw $t4, 0x28($sp)
    lw $t3, 0x24($sp)
    lw $t2, 0x20($sp)
    lw $t1, 0x1c($sp)
    lw $t0, 0x18($sp)
    lw $a3, 0x14($sp)
    lw $a2, 0x10($sp)
    lw $a1, 0x0c($sp)
    lw $a0, 0x08($sp)
    lw $v1, 0x04($sp)
    lw $v0, 0x00($sp)
    addiu $sp, $sp, 0x50
    .endm

    .macro jump_absolute high, low
    lui $k1, \high
    ori $k1, $k1, \low
    jr $k1
    nop
    .endm

    .section .text.extra_hit_branch_bridge,"ax",@progbits
    .balign 4
    .globl extra_hit_branch_bridge
    .type extra_hit_branch_bridge, @function
extra_hit_branch_bridge:
    save_volatile_state
    jal extra_hit_get
    nop
    move $k0, $v0
    restore_volatile_state

    addiu $k1, $zero, 1
    bne $v0, $k1, 1f
    nop
    bnez $k0, 2f
    nop
    jump_absolute 0x0023, 0xb910
1:
    jump_absolute 0x0023, 0xb5f0
2:
    jump_absolute 0x0023, 0xb60c
    .size extra_hit_branch_bridge, . - extra_hit_branch_bridge
