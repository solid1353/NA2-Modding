/* Native EE control-flow adapters for the feature-aware Battle Settings map. */
    .set noreorder
    .set noat


    .section .text.battle_settings_confirm_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_confirm_bridge
    .type battle_settings_confirm_bridge, @function
battle_settings_confirm_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal battle_settings_confirm
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $t9, 0x0087
    ori $t9, $t9, 0xfdbc
    jr $t9
    nop
1:
    lui $t9, 0x0087
    ori $t9, $t9, 0xfb38
    jr $t9
    nop
    .size battle_settings_confirm_bridge, . - battle_settings_confirm_bridge

    .section .text.battle_settings_cancel_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_cancel_bridge
    .type battle_settings_cancel_bridge, @function
battle_settings_cancel_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal battle_settings_cancel
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0087
    ori $t9, $t9, 0xfdbc
    jr $t9
    nop
    .size battle_settings_cancel_bridge, . - battle_settings_cancel_bridge

    .section .text.battle_settings_ultimate_help_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_ultimate_help_bridge
    .type battle_settings_ultimate_help_bridge, @function
battle_settings_ultimate_help_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    lh $a0, 0x48($s0)
    jal battle_settings_row_id
    nop
    addiu $t0, $zero, 4
    bne $v0, $t0, 2f
    nop
    lw $a0, 0x18($s0)
    lui $t9, 0x0037
    ori $t9, $t9, 0xeee0
    jalr $t9
    nop
    move $a0, $s0
    lh $a1, 0x48($s0)
    jal battle_settings_get_value
    nop
    sltiu $t0, $v0, 6
    bnez $t0, 1f
    nop
    addiu $v0, $zero, 2
1:
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0087
    ori $t9, $t9, 0xfd78
    jr $t9
    nop
2:
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0087
    ori $t9, $t9, 0xfda8
    jr $t9
    nop
    .size battle_settings_ultimate_help_bridge, . - battle_settings_ultimate_help_bridge

    .section .text.battle_settings_label_loop_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_label_loop_bridge
    .type battle_settings_label_loop_bridge, @function
battle_settings_label_loop_bridge:
    lui $t0, %hi(battle_settings_visible_count)
    lw $t0, %lo(battle_settings_visible_count)($t0)
    slt $v1, $s2, $t0
    beqz $v1, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x0214
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x0284
    jr $t9
    nop
    .size battle_settings_label_loop_bridge, . - battle_settings_label_loop_bridge

    .section .text.battle_settings_draw_time_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_draw_time_bridge
    .type battle_settings_draw_time_bridge, @function
battle_settings_draw_time_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    jal battle_settings_visible_row_id
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x0350
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x0298
    jr $t9
    nop
    .size battle_settings_draw_time_bridge, . - battle_settings_draw_time_bridge

    .section .text.battle_settings_draw_ordinary_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_draw_ordinary_bridge
    .type battle_settings_draw_ordinary_bridge, @function
battle_settings_draw_ordinary_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    jal battle_settings_use_native_handicap
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x035c
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x0460
    jr $t9
    nop
    .size battle_settings_draw_ordinary_bridge, . - battle_settings_draw_ordinary_bridge

    .section .text.battle_settings_handicap_red_value_y_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_handicap_red_value_y_bridge
    .type battle_settings_handicap_red_value_y_bridge, @function
battle_settings_handicap_red_value_y_bridge:
    lui $t0, %hi(battle_settings_handicap_value_y)
    lwc1 $f13, %lo(battle_settings_handicap_value_y)($t0)
    lui $t9, 0x0088
    ori $t9, $t9, 0x03a8
    jr $t9
    nop
    .size battle_settings_handicap_red_value_y_bridge, . - battle_settings_handicap_red_value_y_bridge

    .section .text.battle_settings_handicap_blue_value_y_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_handicap_blue_value_y_bridge
    .type battle_settings_handicap_blue_value_y_bridge, @function
battle_settings_handicap_blue_value_y_bridge:
    lui $t0, %hi(battle_settings_handicap_value_y)
    lwc1 $f13, %lo(battle_settings_handicap_value_y)($t0)
    lui $t9, 0x0088
    ori $t9, $t9, 0x0420
    jr $t9
    nop
    .size battle_settings_handicap_blue_value_y_bridge, . - battle_settings_handicap_blue_value_y_bridge

    .section .text.battle_settings_draw_value_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_draw_value_bridge
    .type battle_settings_draw_value_bridge, @function
battle_settings_draw_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s3
    move $a1, $s2
    jal battle_settings_get_visible_value
    nop
    sll $a0, $s2, 2
    sll $v1, $v0, 2
    lui $v0, %hi(battle_settings_active_value_tables)
    addiu $v0, $v0, %lo(battle_settings_active_value_tables)
    addu $v0, $v0, $a0
    lw $v0, 0($v0)
    addu $v0, $v0, $v1
    lui $t0, 0x43b2
    mtc1 $t0, $f12
    mov.s $f13, $f20
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x0490
    jr $t9
    nop
    .size battle_settings_draw_value_bridge, . - battle_settings_draw_value_bridge

    .section .text.battle_settings_value_loop_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_value_loop_bridge
    .type battle_settings_value_loop_bridge, @function
battle_settings_value_loop_bridge:
    lui $t0, %hi(battle_settings_visible_count)
    lw $t0, %lo(battle_settings_visible_count)($t0)
    slt $v1, $s2, $t0
    beqz $v1, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x0290
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x04c4
    jr $t9
    nop
    .size battle_settings_value_loop_bridge, . - battle_settings_value_loop_bridge

    .section .text.battle_settings_helper_max_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_helper_max_bridge
    .type battle_settings_helper_max_bridge, @function
battle_settings_helper_max_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a1, $a0
    move $a0, $s2
    jal battle_settings_get_visible_max_value
    nop
    move $s0, $v0
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x059c
    jr $t9
    nop
    .size battle_settings_helper_max_bridge, . - battle_settings_helper_max_bridge

    .section .text.battle_settings_helper_value_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_helper_value_bridge
    .type battle_settings_helper_value_bridge, @function
battle_settings_helper_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    lh $a1, 0x48($s2)
    jal battle_settings_get_visible_value
    nop
    lh $v1, 0x48($s2)
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x05ac
    jr $t9
    nop
    .size battle_settings_helper_value_bridge, . - battle_settings_helper_value_bridge

    .section .text.battle_settings_helper_ordinary_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_helper_ordinary_bridge
    .type battle_settings_helper_ordinary_bridge, @function
battle_settings_helper_ordinary_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $v1
    jal battle_settings_use_native_handicap
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x05d4
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x05d8
    jr $t9
    nop
    .size battle_settings_helper_ordinary_bridge, . - battle_settings_helper_ordinary_bridge

    .section .text.battle_settings_cursor_ordinary_bridge,"ax",@progbits
    .balign 4
    .globl battle_settings_cursor_ordinary_bridge
    .type battle_settings_cursor_ordinary_bridge, @function
battle_settings_cursor_ordinary_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    swc1 $f0, 8($sp)
    move $a0, $v1
    jal battle_settings_use_native_handicap
    nop
    lwc1 $f0, 8($sp)
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x06e4
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x06f0
    jr $t9
    nop
    .size battle_settings_cursor_ordinary_bridge, . - battle_settings_cursor_ordinary_bridge
