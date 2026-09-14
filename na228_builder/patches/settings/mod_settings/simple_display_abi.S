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
