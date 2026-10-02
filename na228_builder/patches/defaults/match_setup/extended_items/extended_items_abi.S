    .set noreorder
    .set noat

/* Run the native routine while Extended Items is off; otherwise tail-call C. */
    .macro ENTRY name, impl, first, second, resume
    .section .text.\name,"ax",@progbits
    .balign 4
    .globl \name
    .type \name, @function
\name:
    lui $t9, %hi(extended_items_active)
    lw $t9, %lo(extended_items_active)($t9)
    bnez $t9, 1f
    nop
    \first
    \second
    lui $t9, (\resume >> 16)
    ori $t9, $t9, (\resume & 0xFFFF)
    jr $t9
    nop
1:
    j \impl
    nop
    .size \name, . - \name
    .endm

    .macro CALL_AND_RESUME name, setup, setup2, impl, result, resume
    .section .text.\name,"ax",@progbits
    .balign 4
    .globl \name
    .type \name, @function
\name:
    \setup
    \setup2
    jal \impl
    nop
    \result
    lui $t9, (\resume >> 16)
    ori $t9, $t9, (\resume & 0xFFFF)
    jr $t9
    nop
    .size \name, . - \name
    .endm

    ENTRY extended_items_full_bridge, extended_items_full, "addiu $sp, $sp, -16", "sd $ra, 0($sp)", 0x0070FC88
    ENTRY extended_items_selected_count_bridge, extended_items_selected_count, "addiu $sp, $sp, -32", "sd $ra, 16($sp)", 0x0070FCB8
    ENTRY extended_items_code_at_bridge, extended_items_code_at, "addiu $sp, $sp, -32", "sd $ra, 16($sp)", 0x0070FD98
    ENTRY extended_items_selected_code_bridge, extended_items_selected_code, "addiu $sp, $sp, -32", "sd $ra, 16($sp)", 0x0070FDE8
    ENTRY extended_items_count_copy_bridge, extended_items_count, "move $v0, $zero", "move $a2, $zero", 0x0070FE78
    ENTRY extended_items_room_bridge, extended_items_room, "addiu $sp, $sp, -48", "sd $ra, 32($sp)", 0x0070FEF8
    ENTRY extended_items_add_bridge, extended_items_add, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x00710048
    ENTRY extended_items_consume_code_bridge, extended_items_consume_code, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x007102D8
    ENTRY extended_items_consume_selected_bridge, extended_items_consume_selected, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x00710478
    ENTRY extended_items_clear_bridge, extended_items_clear, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x007105C8
    ENTRY extended_items_step_occupied_bridge, extended_items_step_occupied, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x007106D8
    ENTRY extended_items_step_empty_bridge, extended_items_step_empty, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x00710858
    ENTRY extended_items_cache_build_bridge, extended_items_cache_build, "addiu $sp, $sp, -112", "sd $ra, 96($sp)", 0x007109F8
    ENTRY extended_items_cache_restore_bridge, extended_items_cache_restore, "addiu $sp, $sp, -96", "sd $ra, 80($sp)", 0x00710B08
    ENTRY extended_items_count_bridge, extended_items_count, "move $v0, $zero", "move $a2, $zero", 0x00710C78
    ENTRY extended_items_relation_bridge, extended_items_relation, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x00710CF8
    ENTRY extended_items_category_bridge, extended_items_category, "addiu $sp, $sp, -16", "sd $ra, 0($sp)", 0x00710E28
    ENTRY extended_items_use_code_bridge, extended_items_use_code, "addiu $sp, $sp, -64", "sd $ra, 48($sp)", 0x007111C8
    ENTRY extended_items_has_two_bridge, extended_items_has_two, "move $a1, $zero", "move $a2, $zero", 0x00711AC8
    ENTRY extended_items_draw_bridge, extended_items_draw, "addiu $sp, $sp, -144", "sd $ra, 96($sp)", 0x00711E58
    /* The native find and cache clear continue at their first branch target. */
    ENTRY extended_items_find_bridge, extended_items_find, "move $a3, $zero", "nop", 0x0070FD78
    ENTRY extended_items_cache_clear_bridge, extended_items_cache_clear, "move $a2, $zero", "nop", 0x0070F238

    .section .text.extended_items_constructor_bridge,"ax",@progbits
    .balign 4
    .globl extended_items_constructor_bridge
    .type extended_items_constructor_bridge, @function
extended_items_constructor_bridge:
    addiu $sp, $sp, -32
    sd $ra, 0($sp)
    sd $a0, 8($sp)
    sd $a1, 16($sp)
    jal extended_items_begin_panel
    nop
    ld $ra, 0($sp)
    ld $a0, 8($sp)
    ld $a1, 16($sp)
    addiu $sp, $sp, 32
    addiu $sp, $sp, -96
    sd $ra, 64($sp)
    lui $t9, 0x0070
    ori $t9, $t9, 0xF748
    jr $t9
    nop
    .size extended_items_constructor_bridge, . - extended_items_constructor_bridge

    CALL_AND_RESUME extended_items_activation_count_bridge, "move $a0, $s0", "nop", extended_items_count, "move $a1, $v0", 0x00711444
    CALL_AND_RESUME extended_items_activation_slot_bridge, "move $a0, $s0", "nop", extended_items_selected_slot, "move $s2, $v0", 0x0071160C
    CALL_AND_RESUME extended_items_update_count_bridge, "move $a0, $s2", "nop", extended_items_update_count, "move $s1, $v0", 0x0071246C
    CALL_AND_RESUME extended_items_update_code_bridge, "move $a0, $s2", "move $a1, $v0", extended_items_code_of, "move $a1, $v0", 0x00712764
    CALL_AND_RESUME extended_items_root_two_bridge, "move $a0, $s0", "nop", extended_items_has_two, "nop", 0x00712850
