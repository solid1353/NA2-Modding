/* Select native attack timing or a total pre-impact input window. */
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
    beq $v0, $zero, native_timing
    nop
    addiu $s0, $v0, -1

    lw $v0, 0($sp)
    ld $ra, 8($sp)
    j 0x00229620
    addiu $sp, $sp, 16

native_timing:
    lw $v0, 0($sp)
    ld $ra, 8($sp)
    addiu $sp, $sp, 16
    bltz $s0, native_random_timing
    nop
    j 0x00229610
    nop
native_random_timing:
    j 0x002295d0
    nop
    .size battle_logic_substitution_select_active_history, . - battle_logic_substitution_select_active_history
