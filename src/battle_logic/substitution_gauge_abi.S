/* Native EE control-flow adapters for the substitution-gauge hooks. */
    .set noreorder
    .set noat

    .section .text.substitution_gauge_can_spend_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_can_spend_shim
    .type substitution_gauge_can_spend_shim, @function
substitution_gauge_can_spend_shim:
    jal substitution_gauge_can_spend
    nop
    lui $t9, 0x0022
    ori $t9, $t9, 0x973c
    jr $t9
    nop
    .size substitution_gauge_can_spend_shim, . - substitution_gauge_can_spend_shim

    .section .text.substitution_gauge_spend_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_spend_shim
    .type substitution_gauge_spend_shim, @function
substitution_gauge_spend_shim:
    jal substitution_gauge_route_spend
    nop
    beqz $v0, 1f
    nop
    lui $t9, 0x0022
    ori $t9, $t9, 0x98f0
    jr $t9
    nop
1:
    daddu $a0, $s3, $zero
    lui $t9, 0x0030
    ori $t9, $t9, 0x74f0
    jalr $t9
    nop
    lui $t9, 0x0022
    ori $t9, $t9, 0x988c
    jr $t9
    nop
    .size substitution_gauge_spend_shim, . - substitution_gauge_spend_shim

    .section .text.substitution_gauge_success_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_success_shim
    .type substitution_gauge_success_shim, @function
substitution_gauge_success_shim:
    addiu $sp, $sp, -32
    sw $a0, 16($sp)
    sd $ra, 24($sp)
    jal substitution_gauge_note_success
    nop
    lw $a0, 16($sp)
    lui $t9, 0x0022
    ori $t9, $t9, 0xd5b0
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .size substitution_gauge_success_shim, . - substitution_gauge_success_shim

    .section .text.substitution_gauge_hp_sample_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_hp_sample_shim
    .type substitution_gauge_hp_sample_shim, @function
substitution_gauge_hp_sample_shim:
    addiu $sp, $sp, -32
    sw $a0, 16($sp)
    sd $ra, 24($sp)
    jal substitution_gauge_sample_hp
    nop
    lw $a0, 16($sp)
    lui $t9, 0x0024
    ori $t9, $t9, 0x49c0
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .size substitution_gauge_hp_sample_shim, . - substitution_gauge_hp_sample_shim

    .section .text.substitution_gauge_battle_clock_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_battle_clock_shim
    .type substitution_gauge_battle_clock_shim, @function
substitution_gauge_battle_clock_shim:
    addiu $sp, $sp, -32
    sw $a0, 16($sp)
    sd $ra, 24($sp)
    jal substitution_gauge_advance_battle
    nop
    lw $a0, 16($sp)
    lui $t9, 0x001e
    ori $t9, $t9, 0xba80
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .size substitution_gauge_battle_clock_shim, . - substitution_gauge_battle_clock_shim

    .section .text.substitution_gauge_reset_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_reset_shim
    .type substitution_gauge_reset_shim, @function
substitution_gauge_reset_shim:
    addiu $sp, $sp, -32
    sw $a0, 16($sp)
    sd $ra, 24($sp)
    daddu $a0, $s0, $zero
    jal substitution_gauge_reset_battle
    nop
    lw $a0, 16($sp)
    lui $t9, 0x0070
    ori $t9, $t9, 0x96e0
    jalr $t9
    nop
    ld $ra, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .size substitution_gauge_reset_shim, . - substitution_gauge_reset_shim

    .section .text.substitution_gauge_adjust_battle_hud_character_name_y_shim,"ax",@progbits
    .balign 4
    .globl substitution_gauge_adjust_battle_hud_character_name_y_shim
    .type substitution_gauge_adjust_battle_hud_character_name_y_shim, @function
substitution_gauge_adjust_battle_hud_character_name_y_shim:
    addiu $sp, $sp, -64
    sw $v1, 16($sp)
    sw $a1, 20($sp)
    swc1 $f1, 24($sp)
    swc1 $f3, 28($sp)
    swc1 $f4, 32($sp)
    swc1 $f5, 36($sp)
    sd $ra, 48($sp)
    mov.s $f12, $f0
    jal substitution_gauge_adjust_battle_hud_character_name_y
    nop
    lwc1 $f1, 24($sp)
    lwc1 $f3, 28($sp)
    lwc1 $f4, 32($sp)
    lwc1 $f5, 36($sp)
    mul.s $f2, $f0, $f1
    lw $a1, 20($sp)
    lw $v1, 16($sp)
    lbu $v0, 12($a1)
    ld $ra, 48($sp)
    jr $ra
    addiu $sp, $sp, 64
    .size substitution_gauge_adjust_battle_hud_character_name_y_shim, . - substitution_gauge_adjust_battle_hud_character_name_y_shim
