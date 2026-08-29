/* Runtime adapter for the deterministic pre-impact substitution window. */
    .set noreorder
    .set noat

    .section .text.battle_logic_substitution_select_active_history,"ax",@progbits
    .balign 4
    .globl battle_logic_substitution_select_active_history
    .type battle_logic_substitution_select_active_history, @function
battle_logic_substitution_select_active_history:
    addiu $sp, $sp, -16
    sw $v0, 0($sp)
    sd $ra, 8($sp)

    jal sub_active_frames_get
    nop
    move $s0, $v0

    lw $v0, 0($sp)
    ld $ra, 8($sp)
    j 0x00229620
    addiu $sp, $sp, 16
    .size battle_logic_substitution_select_active_history, . - battle_logic_substitution_select_active_history
