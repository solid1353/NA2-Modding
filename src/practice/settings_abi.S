/* Native EE control-flow adapters for the compact Practice Settings row map. */
    .set noreorder
    .set noat

    .section .text.practice_settings_after_value_change_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_after_value_change_bridge
    .type practice_settings_after_value_change_bridge, @function
practice_settings_after_value_change_bridge:
    lui $t9, 0x0088
    ori $t9, $t9, 0x18e8
    jr $t9
    nop
    .size practice_settings_after_value_change_bridge, . - practice_settings_after_value_change_bridge

    .section .text.practice_settings_geometry_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_geometry_bridge
    .type practice_settings_geometry_bridge, @function
practice_settings_geometry_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal practice_settings_update_window
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1ca0
    jr $t9
    nop
    .size practice_settings_geometry_bridge, . - practice_settings_geometry_bridge

    .section .text.practice_settings_help_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_help_bridge
    .type practice_settings_help_bridge, @function
practice_settings_help_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal practice_settings_update_help
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1e1c
    jr $t9
    nop
    .size practice_settings_help_bridge, . - practice_settings_help_bridge

    .section .text.practice_settings_selected_is_player,"ax",@progbits
    .balign 4
    .globl practice_settings_selected_is_player
    .type practice_settings_selected_is_player, @function
practice_settings_selected_is_player:
    lui $v0, %hi(practice_settings_schema)
    addiu $v0, $v0, %lo(practice_settings_schema)
    lw $v0, 4($v0)
    slt $v0, $a1, $v0
    jr $ra
    nop
    .size practice_settings_selected_is_player, . - practice_settings_selected_is_player

    .section .text.practice_settings_helper_max_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_helper_max_bridge
    .type practice_settings_helper_max_bridge, @function
practice_settings_helper_max_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    lw $a1, 0x3c($s2)
    jal practice_settings_get_max_value
    nop
    move $s0, $v0
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1f38
    jr $t9
    nop
    .size practice_settings_helper_max_bridge, . - practice_settings_helper_max_bridge

    .section .text.practice_settings_helper_value_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_helper_value_bridge
    .type practice_settings_helper_value_bridge, @function
practice_settings_helper_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    lw $a1, 0x3c($s2)
    jal practice_settings_get_value
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1f48
    jr $t9
    nop
    .size practice_settings_helper_value_bridge, . - practice_settings_helper_value_bridge

    .section .text.practice_settings_scroll_flags_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_scroll_flags_bridge
    .type practice_settings_scroll_flags_bridge, @function
practice_settings_scroll_flags_bridge:
    lw $t0, 0x3c($s2)
    lui $t1, %hi(practice_settings_schema)
    addiu $t1, $t1, %lo(practice_settings_schema)
    lw $t2, 4($t1)
    slt $v0, $t0, $t2
    beqz $v0, 1f
    nop
    lw $t0, 0xb0($s2)
    addiu $t2, $t2, -7
    bgez $t2, 2f
    nop
    move $t2, $zero
2:
    slt $v1, $zero, $t0
    slt $s0, $t0, $t2
    bnez $s0, 3f
    nop
    lw $t2, 8($t1)
    slt $s0, $zero, $t2
    b 3f
    nop
1:
    lw $t0, 0xb4($s2)
    lw $t2, 8($t1)
    addiu $t2, $t2, -6
    bgez $t2, 4f
    nop
    move $t2, $zero
4:
    slt $s0, $t0, $t2
    slt $v1, $zero, $t0
    bnez $v1, 3f
    nop
    lw $t2, 4($t1)
    slt $v1, $zero, $t2
3:
    beqz $v1, 5f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x2080
    jr $t9
    nop
5:
    lui $t9, 0x0088
    ori $t9, $t9, 0x20fc
    jr $t9
    nop
    .size practice_settings_scroll_flags_bridge, . - practice_settings_scroll_flags_bridge

    .section .text.practice_settings_draw_section_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_draw_section_bridge
    .type practice_settings_draw_section_bridge, @function
practice_settings_draw_section_bridge:
    lui $v0, %hi(practice_settings_schema)
    addiu $v0, $v0, %lo(practice_settings_schema)
    lw $v0, 4($v0)
    beq $s0, $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x2440
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x2404
    jr $t9
    nop
    .size practice_settings_draw_section_bridge, . - practice_settings_draw_section_bridge

    .section .text.practice_settings_draw_value_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_draw_value_bridge
    .type practice_settings_draw_value_bridge, @function
practice_settings_draw_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    sd $a1, 8($sp)
    move $a0, $s1
    move $a1, $s0
    jal practice_settings_get_value
    nop
    sll $a0, $s0, 2
    lui $t0, 0x43b2
    mtc1 $t0, $f12
    ld $a1, 8($sp)
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x24b4
    jr $t9
    nop
    .size practice_settings_draw_value_bridge, . - practice_settings_draw_value_bridge

    .section .text.practice_settings_cursor_section_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_cursor_section_bridge
    .type practice_settings_cursor_section_bridge, @function
practice_settings_cursor_section_bridge:
    lui $v0, %hi(practice_settings_schema)
    addiu $v0, $v0, %lo(practice_settings_schema)
    lw $v0, 4($v0)
    slt $v0, $v1, $v0
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x21cc
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x21b8
    jr $t9
    nop
    .size practice_settings_cursor_section_bridge, . - practice_settings_cursor_section_bridge

    .section .text.practice_settings_draw_loop_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_draw_loop_bridge
    .type practice_settings_draw_loop_bridge, @function
practice_settings_draw_loop_bridge:
    lui $v0, %hi(practice_settings_schema)
    addiu $v0, $v0, %lo(practice_settings_schema)
    lw $v0, 0($v0)
    slt $v0, $s0, $v0
    beqz $v0, 1f
    nop
    lui $t9, 0x0088
    ori $t9, $t9, 0x23f8
    jr $t9
    nop
1:
    lui $t9, 0x0088
    ori $t9, $t9, 0x24fc
    jr $t9
    nop
    .size practice_settings_draw_loop_bridge, . - practice_settings_draw_loop_bridge
