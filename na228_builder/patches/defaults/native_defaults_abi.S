/* Native mode-selection bridge for independent Battle settings defaults. */
    .set noreorder
    .set noat

    .section .text.settings_select_battle_defaults_bridge,"ax",@progbits
    .balign 4
    .globl settings_select_battle_defaults_bridge
    .type settings_select_battle_defaults_bridge, @function
settings_select_battle_defaults_bridge:
    addiu $a0, $zero, 2
    lw $v1, -13296($gp)
    sw $a0, 12($v1)
    move $a0, $v1
    jal settings_apply_selected_defaults
    nop
    lui $t9, 0x001e
    ori $t9, $t9, 0xa818
    jr $t9
    nop
    .size settings_select_battle_defaults_bridge, . - settings_select_battle_defaults_bridge
