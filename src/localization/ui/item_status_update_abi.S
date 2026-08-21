/* ABI bridge from the native common item-status updater into its C-owned tail. */

    .set noreorder
    .set noat

    .section .text.localization_item_status_update_tail_bridge, "ax", @progbits
    .align 2
    .globl localization_item_status_update_tail_bridge
    .type localization_item_status_update_tail_bridge, @function
localization_item_status_update_tail_bridge:
    /* The hook delay slot has already placed the native object in a0. */
    addiu $a1, $sp, 0x30
    jal localization_item_status_update_tail
    nop

    /* The native epilogue restores the original caller's ra and s0. */
    j 0x0070DF98
    nop
    .size localization_item_status_update_tail_bridge, . - localization_item_status_update_tail_bridge
