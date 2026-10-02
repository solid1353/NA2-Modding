/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.substitution_cost_shim,"ax",@progbits
    .balign 4
    .globl substitution_cost_shim
    .type substitution_cost_shim, @function
substitution_cost_shim:
    daddu $a1, $v0, $zero                                # 0x0040282D
    j substitution_cost_for_fighter                      # 0x08000000
    nop                                                  # 0x00000000
    .size substitution_cost_shim, . - substitution_cost_shim
