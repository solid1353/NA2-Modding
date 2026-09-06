/* Native EE control-flow adapters for the paged Practice Settings row map. */
    .set noreorder
    .set noat

    .section .text.practice_settings_initialize_help_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_initialize_help_bridge
    .type practice_settings_initialize_help_bridge, @function
practice_settings_initialize_help_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    lui $t9, 0x0037
    ori $t9, $t9, 0xeee0
    jalr $t9
    nop
    move $a0, $s0
    jal practice_settings_update_help
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    jr $ra
    nop
    .size practice_settings_initialize_help_bridge, . - practice_settings_initialize_help_bridge

    .section .text.practice_settings_cancel_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_cancel_bridge
    .type practice_settings_cancel_bridge, @function
practice_settings_cancel_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal practice_settings_cancel
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x18b4
    jr $t9
    nop
    .size practice_settings_cancel_bridge, . - practice_settings_cancel_bridge

    .section .text.practice_settings_after_value_change_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_after_value_change_bridge
    .type practice_settings_after_value_change_bridge, @function
practice_settings_after_value_change_bridge:
    lui $t9, 0x0088
    ori $t9, $t9, 0x18e8
    jr $t9
    nop
    .size practice_settings_after_value_change_bridge, . - practice_settings_after_value_change_bridge

    .section .text.practice_settings_geometry_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_geometry_bridge
    .type practice_settings_geometry_bridge, @function
practice_settings_geometry_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal practice_settings_update_window
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1ca0
    jr $t9
    nop
    .size practice_settings_geometry_bridge, . - practice_settings_geometry_bridge

    .section .text.practice_settings_help_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_help_bridge
    .type practice_settings_help_bridge, @function
practice_settings_help_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal practice_settings_update_help
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1e1c
    jr $t9
    nop
    .size practice_settings_help_bridge, . - practice_settings_help_bridge
