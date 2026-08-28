/* Native EE adapter for the bounded post-impact substitution window. */
    .set noreorder
    .set noat

    .section .text.battle_logic_substitution_update_ordinary_response,"ax",@progbits
    .balign 4
    .globl battle_logic_substitution_update_ordinary_response
    .type battle_logic_substitution_update_ordinary_response, @function
battle_logic_substitution_update_ordinary_response:
    addiu $sp, $sp, -32
    sw $a0, 16($sp)
    sd $ra, 24($sp)

    lw $v0, 0x1c4($a0)
    blez $v0, 1f
    nop
    lui $v1, %hi(battle_logic_substitution_frames_after)
    lw $v1, %lo(battle_logic_substitution_frames_after)($v1)
    slt $at, $v1, $v0
    bnez $at, 1f
    nop

    move $a1, $zero
    addiu $a2, $zero, 5
    lh $a3, 0x190($a0)
    addiu $t0, $zero, 1
    lui $t9, 0x0022
    ori $t9, $t9, 0x9130
    jalr $t9
    nop
    beqz $v0, 1f
    nop

    lw $a0, 16($sp)
    addiu $a1, $zero, 0x11
    addiu $a2, $zero, 1
    lui $t9, 0x0022
    ori $t9, $t9, 0x97d0
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32

1:
    lw $a0, 16($sp)
    lui $t9, 0x0023
    ori $t9, $t9, 0x4da0
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .size battle_logic_substitution_update_ordinary_response, . - battle_logic_substitution_update_ordinary_response
