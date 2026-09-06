    .set noreorder
    .set noat

    .section .text.items_settings_spawn_bridge,"ax",@progbits
    .balign 4
    .globl items_settings_spawn_bridge
    .type items_settings_spawn_bridge, @function
items_settings_spawn_bridge:
    andi $v0, $a1, 0xff
    beq $v0, $zero, 1f
    nop
    lui $t9, 0x003a
    ori $t9, $t9, 0xeaf0
    jr $t9
    nop
1:
    jr $ra
    move $v0, $zero
    .size items_settings_spawn_bridge, . - items_settings_spawn_bridge

    .section .text.items_settings_extra_spawn_bridge,"ax",@progbits
    .balign 4
    .globl items_settings_extra_spawn_bridge
    .type items_settings_extra_spawn_bridge, @function
items_settings_extra_spawn_bridge:
    addiu $sp, $sp, -0x70
    sd $ra, 0($sp)
    sq $a0, 0x10($sp)
    sq $a1, 0x20($sp)
    sq $a2, 0x30($sp)
    sq $a3, 0x40($sp)
    sq $t0, 0x50($sp)
    sq $t1, 0x60($sp)
    jal items_settings_extra_enabled
    nop
    ld $ra, 0($sp)
    lq $a0, 0x10($sp)
    lq $a1, 0x20($sp)
    lq $a2, 0x30($sp)
    lq $a3, 0x40($sp)
    lq $t0, 0x50($sp)
    lq $t1, 0x60($sp)
    addiu $sp, $sp, 0x70
    beq $v0, $zero, 1f
    nop
    lui $t9, 0x0037
    ori $t9, $t9, 0x3fb0
    jr $t9
    nop
1:
    jr $ra
    move $v0, $zero
    .size items_settings_extra_spawn_bridge, . - items_settings_extra_spawn_bridge
