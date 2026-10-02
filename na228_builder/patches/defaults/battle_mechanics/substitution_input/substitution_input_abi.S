/*
 * Select native attack timing for Default, the current input record for Hold,
 * or a total input window of 1..15 records.
 */
    .set noreorder
    .set noat

    .section .text.battle_logic_substitution_select_input_window,"ax",@progbits
    .balign 4
    .globl battle_logic_substitution_select_input_window
    .type battle_logic_substitution_select_input_window, @function
battle_logic_substitution_select_input_window:
    addiu $sp, $sp, -16
    sw $v0, 0($sp)
    sd $ra, 8($sp)

    jal substitution_input_get
    nop
    beq $v0, $zero, native_timing
    nop
    addiu $s0, $v0, -2
    bgez $s0, 1f
    nop
    move $s0, $zero
1:

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
    .size battle_logic_substitution_select_input_window, . - battle_logic_substitution_select_input_window
