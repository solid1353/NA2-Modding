/* Request the native ordinary-jutsu HUD transition for the UJ contest. */
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

    jal ultimate_jutsu_mode_get
    nop

    lui $t0, 0x0060
    lw $t0, 0x7750($t0)
    lui $t1, %hi(battle_logic_ultimate_jutsu_hud_transition_active)
    lw $t2, %lo(battle_logic_ultimate_jutsu_hud_transition_active)($t1)
    addiu $t3, $zero, 7
    bne $v0, $t3, 2f
    nop

    beqz $t0, 2f
    nop

    bnez $t2, 3f
    nop

    addiu $t2, $zero, 1
    sw $t2, %lo(battle_logic_ultimate_jutsu_hud_transition_active)($t1)
    addiu $a0, $zero, -1
    lui $t9, 0x001f
    ori $t9, $t9, 0x1820
    jalr $t9
    nop
    b 3f
    nop

2:
    beqz $t2, 3f
    nop

    sw $zero, %lo(battle_logic_ultimate_jutsu_hud_transition_active)($t1)
    addiu $a0, $zero, -1
    lui $t9, 0x001f
    ori $t9, $t9, 0x1a20
    jalr $t9
    nop

3:
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
