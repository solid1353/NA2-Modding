    .set noreorder
    .set noat

    .section .text.localization_ui_battle_hud_fit_width_adapter,"ax",@progbits
    .balign 4
    .globl localization_ui_battle_hud_fit_width_adapter
localization_ui_battle_hud_fit_width_adapter:
    addiu $sp, $sp, -32
    sd $ra, 0($sp)
    sw $v1, 8($sp)
    sw $a1, 12($sp)
    swc1 $f1, 16($sp)
    mov.s $f12, $f0
    jal localization_ui_battle_hud_fit_width
    mov.s $f13, $f1
    mov.s $f5, $f0
    lwc1 $f1, 16($sp)
    lw $a1, 12($sp)
    lw $v1, 8($sp)
    ld $ra, 0($sp)
    addiu $sp, $sp, 32
    jr $ra
    lwc1 $f0, 100($v1)

    .section .text.localization_ui_common_prompt_x_offset,"ax",@progbits
    .balign 4
    .globl localization_ui_common_prompt_x_offset
localization_ui_common_prompt_x_offset:
    .word 0x44830000
    .word 0x46006300
    .word 0x080DF260
    .word 0x00000000

    .section .text.localization_ui_vs_confirmation_jutsu_label_place,"ax",@progbits
    .balign 4
    .globl localization_ui_vs_confirmation_jutsu_label_place
localization_ui_vs_confirmation_jutsu_label_place:
    .word 0x3C0241D0
    .word 0x44820000
    .word 0x03E00008
    .word 0x46150300
