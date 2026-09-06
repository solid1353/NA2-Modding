/* Shared adapters into the native Practice content renderer. */
    .set noreorder
    .set noat
    .section .text.settings_menu_selected_is_player,"ax",@progbits
    .balign 4
    .globl settings_menu_selected_is_player
    .type settings_menu_selected_is_player, @function
settings_menu_selected_is_player:
    lui $v0, %hi(settings_menu_render_page)
    addiu $v0, $v0, %lo(settings_menu_render_page)
    lw $v0, 8($v0)
    slt $v0, $a1, $v0
    jr $ra
    nop
    .size settings_menu_selected_is_player, . - settings_menu_selected_is_player
    .section .text.settings_menu_helper_max_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_helper_max_bridge
    .type settings_menu_helper_max_bridge, @function
settings_menu_helper_max_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    lw $a1, 0x3c($s2)
    jal settings_menu_maximum
    nop
    move $s0, $v0
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1f38
    jr $t9
    nop
    .size settings_menu_helper_max_bridge, . - settings_menu_helper_max_bridge
    .section .text.settings_menu_helper_value_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_helper_value_bridge
    .type settings_menu_helper_value_bridge, @function
settings_menu_helper_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    lw $a1, 0x3c($s2)
    jal settings_menu_value
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x1f48
    jr $t9
    nop
    .size settings_menu_helper_value_bridge, . - settings_menu_helper_value_bridge
    .section .text.settings_menu_scroll_flags_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_scroll_flags_bridge
    .type settings_menu_scroll_flags_bridge, @function
settings_menu_scroll_flags_bridge:
    lw $t0, 0x3c($s2)
    lui $t1, %hi(settings_menu_render_page)
    addiu $t1, $t1, %lo(settings_menu_render_page)
    lw $t2, 8($t1)
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
    lw $t2, 12($t1)
    slt $s0, $zero, $t2
    b 3f
    nop
1:
    lw $t0, 0xb4($s2)
    lw $t2, 12($t1)
    addiu $t2, $t2, -6
    bgez $t2, 4f
    nop
    move $t2, $zero
4:
    slt $s0, $t0, $t2
    slt $v1, $zero, $t0
    bnez $v1, 3f
    nop
    lw $t2, 8($t1)
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
    .size settings_menu_scroll_flags_bridge, . - settings_menu_scroll_flags_bridge
    .section .text.settings_menu_draw_section_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_draw_section_bridge
    .type settings_menu_draw_section_bridge, @function
settings_menu_draw_section_bridge:
    lui $v0, %hi(settings_menu_render_page)
    addiu $v0, $v0, %lo(settings_menu_render_page)
    lw $v0, 8($v0)
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
    .size settings_menu_draw_section_bridge, . - settings_menu_draw_section_bridge
    .section .text.settings_menu_heading_text_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_heading_text_bridge
    .type settings_menu_heading_text_bridge, @function
settings_menu_heading_text_bridge:
    lui $t0, %hi(settings_menu_render_page)
    addiu $t0, $t0, %lo(settings_menu_render_page)
    lw $a0, 16($t0)
    jr $ra
    addiu $a1, $zero, 0xf
    .size settings_menu_heading_text_bridge, . - settings_menu_heading_text_bridge
    .section .text.settings_menu_draw_value_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_draw_value_bridge
    .type settings_menu_draw_value_bridge, @function
settings_menu_draw_value_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    sd $a1, 8($sp)
    move $a0, $s0
    jal settings_menu_value_text
    nop
    move $a0, $v0
    lui $t0, 0x43b2
    mtc1 $t0, $f12
    mov.s $f13, $f20
    ld $a1, 8($sp)
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x24d4
    jr $t9
    nop
    .size settings_menu_draw_value_bridge, . - settings_menu_draw_value_bridge
    .section .text.settings_menu_cursor_geometry_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_cursor_geometry_bridge
    .type settings_menu_cursor_geometry_bridge, @function
settings_menu_cursor_geometry_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s2
    jal settings_menu_cursor_y
    nop
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    addiu $v0, $sp, 0x50
    sqc2 $vf0, 0($v0)
    swc1 $f0, 0x58($sp)
    lui $t9, 0x0088
    ori $t9, $t9, 0x21cc
    jr $t9
    nop
    .size settings_menu_cursor_geometry_bridge, . - settings_menu_cursor_geometry_bridge
    .section .text.settings_menu_draw_loop_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_draw_loop_bridge
    .type settings_menu_draw_loop_bridge, @function
settings_menu_draw_loop_bridge:
    lui $v0, %hi(settings_menu_render_page)
    addiu $v0, $v0, %lo(settings_menu_render_page)
    lw $v0, 4($v0)
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
    .size settings_menu_draw_loop_bridge, . - settings_menu_draw_loop_bridge

    .section .text.settings_menu_draw_label_bridge,"ax",@progbits
    .balign 4
    .globl settings_menu_draw_label_bridge
    .type settings_menu_draw_label_bridge, @function
settings_menu_draw_label_bridge:
    addiu $sp, $sp, -16
    sd $ra, 0($sp)
    move $a0, $s0
    jal settings_menu_label
    nop
    move $a0, $v0
    lw $v0, 0x3c($s1)
    xor $a1, $v0, $s0
    sltiu $a1, $a1, 1
    lui $t0, 0x42c8
    mtc1 $t0, $f12
    mov.s $f13, $f20
    ld $ra, 0($sp)
    addiu $sp, $sp, 16
    lui $t9, 0x0088
    ori $t9, $t9, 0x246c
    jr $t9
    nop
    .size settings_menu_draw_label_bridge, . - settings_menu_draw_label_bridge

    .section .text.practice_settings_content_bridge,"ax",@progbits
    .balign 4
    .globl practice_settings_content_bridge
    .type practice_settings_content_bridge, @function
practice_settings_content_bridge:
    move $a0, $s1
    jal practice_settings_draw_content
    nop
    lui $v0, 0x3f99
    ori $v0, $v0, 0x999a
    lui $t9, 0x0088
    ori $t9, $t9, 0x2510
    jr $t9
    nop
    .size practice_settings_content_bridge, . - practice_settings_content_bridge

    .section .text.settings_menu_native_content,"ax",@progbits
    .balign 4
    .globl settings_menu_native_content
    .type settings_menu_native_content, @function
settings_menu_native_content:
    addiu $sp, $sp, -0x50
    sd $ra, 0x30($sp)
    sq $s1, 0x20($sp)
    sq $s0, 0x10($sp)
    swc1 $f20, 0($sp)
    lw $v0, -0x35fc($gp)
    sw $v0, 4($sp)
    move $s1, $a0
    lw $v0, 0x10($s1)
    sw $v0, -0x35fc($gp)
    lui $t9, 0x0088
    ori $t9, $t9, 0x2360
    jr $t9
    nop
    .size settings_menu_native_content, . - settings_menu_native_content

    .section .text.settings_menu_content_return,"ax",@progbits
    .balign 4
    .globl settings_menu_content_return
    .type settings_menu_content_return, @function
settings_menu_content_return:
    lw $v0, 4($sp)
    sw $v0, -0x35fc($gp)
    ld $ra, 0x30($sp)
    lq $s1, 0x20($sp)
    lq $s0, 0x10($sp)
    lwc1 $f20, 0($sp)
    addiu $sp, $sp, 0x50
    jr $ra
    nop
    .size settings_menu_content_return, . - settings_menu_content_return
