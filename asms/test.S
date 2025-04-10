.section .text
.global _start

_start:
    nop
data:
    .word 0x00000020
    nop
    nop
    nop
    nop

loop:
    # 死循环
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    slli t0, t0, 1
    csrw satp, t0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    j loop
    nop
    nop
    nop
    nop
