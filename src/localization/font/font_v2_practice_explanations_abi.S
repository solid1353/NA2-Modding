/* Byte-exact native EE ABI and control-flow shims for the accepted NA228 payload. */
    .set noreorder
    .set noat

    .section .text.v2_practice_adapter,"ax",@progbits
    .balign 4
    .globl v2_practice_adapter
    .type v2_practice_adapter, @function
v2_practice_adapter:
    addiu $sp,$sp,-48                                    # 0x27BDFFD0
    sw $ra,44($sp)                                       # 0xAFBF002C
    addu $a3, $s3, $zero                                 # 0x02603821
    addu $t0, $s2, $zero                                 # 0x02404021
    mfc1 $t1,$f12                                        # 0x44096000
    jal v2_c_practice_adapter_impl                       # 0x0C000000
    nop                                                  # 0x00000000
    lw $ra,44($sp)                                       # 0x8FBF002C
    jr $ra                                               # 0x03E00008
    addiu $sp,$sp,48                                     # 0x27BD0030
    .size v2_practice_adapter, . - v2_practice_adapter
