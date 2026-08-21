/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.c_numeric_format_decimal,"ax",@progbits
    .balign 4
    .globl c_numeric_format_decimal
    .type c_numeric_format_decimal, @function
c_numeric_format_decimal:
    addu $a2, $a1, $zero                                 # 0x00A03021
    lui $a1,0x60                                         # 0x3C050060
    ori $a1,$a1,0x42d3                                   # 0x34A542D3
    j 0x17bca0                                           # 0x0805EF28
    nop                                                  # 0x00000000
    .size c_numeric_format_decimal, . - c_numeric_format_decimal

    .section .text.c_numeric_format_two_decimal,"ax",@progbits
    .balign 4
    .globl c_numeric_format_two_decimal
    .type c_numeric_format_two_decimal, @function
c_numeric_format_two_decimal:
    addu $a2, $a1, $zero                                 # 0x00A03021
    lui $a1,0x60                                         # 0x3C050060
    ori $a1,$a1,0x5c20                                   # 0x34A55C20
    j 0x17bca0                                           # 0x0805EF28
    nop                                                  # 0x00000000
    .size c_numeric_format_two_decimal, . - c_numeric_format_two_decimal
