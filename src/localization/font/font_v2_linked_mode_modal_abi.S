/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_linked_choice_selected_adapter,"ax",@progbits
    .balign 4
    .globl v2_linked_choice_selected_adapter
    .type v2_linked_choice_selected_adapter, @function
v2_linked_choice_selected_adapter:
    addiu $sp,$sp,-32                                    # 0x27BDFFE0
    sw $ra,28($sp)                                       # 0xAFBF001C
    jal v2_c_linked_choice_selected_impl                 # 0x0C000000
    nop                                                  # 0x00000000
    lw $ra,28($sp)                                       # 0x8FBF001C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,32                                     # 0x27BD0020
    .size v2_linked_choice_selected_adapter, . - v2_linked_choice_selected_adapter
