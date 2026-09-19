    .set noreorder
    .set noat

    .section .text.localization_ui_victory_initialize_name_adapter,"ax",@progbits
    .balign 4
    .globl localization_ui_victory_initialize_name_adapter
localization_ui_victory_initialize_name_adapter:
    # Enter immediately after texture binding. Replace the inlined Japanese
    # rectangle lookup, then resume the native combined-width centering.
    # Preserve the full EE registers used by the C helper, including upper lanes.
    addiu $sp, $sp, -64
    sd $ra, 0($sp)
    sq $s0, 16($sp)
    sq $s1, 32($sp)
    sq $s2, 48($sp)
    move $a0, $s4
    jal localization_ui_victory_initialize_name
    move $a1, $s3
    lq $s2, 48($sp)
    lq $s1, 32($sp)
    lq $s0, 16($sp)
    ld $ra, 0($sp)
    addiu $sp, $sp, 64
    j 0x0076CFD4
    nop
