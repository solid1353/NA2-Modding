/* Run UJ presentation logic before the native per-side HUD update. */
    .set noreorder
    .set noat

    .section .text.battle_logic_ultimate_jutsu_battle_hud_transition,"ax",@progbits
    .balign 4
    .globl battle_logic_ultimate_jutsu_battle_hud_transition
    .type battle_logic_ultimate_jutsu_battle_hud_transition, @function
battle_logic_ultimate_jutsu_battle_hud_transition:
    addiu $sp, $sp, -0x20
    sw $a0, 0x10($sp)
    sd $ra, 0x18($sp)

    jal ultimate_jutsu_hud_update
    nop
    lw $a0, 0x10($sp)
    ld $ra, 0x18($sp)
    addiu $sp, $sp, 0x20

    /* Replay the displaced battlegauge update prologue. */
    addiu $sp, $sp, -0x20
    sd $ra, 0x10($sp)
    lui $t9, 0x0071
    ori $t9, $t9, 0xaf38
    jr $t9
    nop
    .size battle_logic_ultimate_jutsu_battle_hud_transition, . - battle_logic_ultimate_jutsu_battle_hud_transition
