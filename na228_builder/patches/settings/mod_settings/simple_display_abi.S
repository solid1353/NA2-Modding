    .set noreorder
    .set noat
    .section .text.mod_settings_simple_display_bridge,"ax",@progbits
    .balign 4
    .globl mod_settings_simple_display_bridge
    .type mod_settings_simple_display_bridge, @function
mod_settings_simple_display_bridge:
    addiu $sp, $sp, -16
    sd $t9, 0($sp)
    lui $t9, %hi(mod_settings_state)
    lw $t9, %lo(mod_settings_state + 4)($t9)
    beqz $t9, 1f
    nop
    ori $v1, $v1, 2
1:
    sb $v1, 0($a0)
    ld $t9, 0($sp)
    addiu $sp, $sp, 16
    lui $k0, 0x001e
    ori $k0, $k0, 0x7ab4
    jr $k0
    nop
    .size mod_settings_simple_display_bridge, . - mod_settings_simple_display_bridge

    .section .text.mod_settings_simple_display_selection_bridge,"ax",@progbits
    .balign 4
    .globl mod_settings_simple_display_selection_bridge
    .type mod_settings_simple_display_selection_bridge, @function
mod_settings_simple_display_selection_bridge:
    /* The initializer keeps its child in s0 and has already saved ra.
       Following native code replaces the caller-saved registers before use. */
    lui $a0, 0x0060
    lw $a0, 0x7600($a0)
    lui $t9, 0x001f
    ori $t9, $t9, 0x6db0
    jalr $t9
    nop
    /* Native getter: enabled = 1. Menu rows: On = 0, Off = 1. */
    sltiu $v1, $v0, 1
    lw $v0, 0x0c($s0)
    lw $v0, 0x7c($v0)
    /* Keep native automatic completion disabled; select the actual row. */
    sh $zero, 0x10($v0)
    sw $v1, 0x18($v0)
    /* Replay the displaced child-window load and rejoin the initializer. */
    lw $v0, 0x0c($s0)
    lui $k0, 0x0087
    ori $k0, $k0, 0x790c
    jr $k0
    nop
    .size mod_settings_simple_display_selection_bridge, . - mod_settings_simple_display_selection_bridge
