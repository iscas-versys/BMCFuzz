.section .text
.global _start

_start:
    la t0, loop
    csrw mepc, t0

    li t0, 0x1
    slli t0, t0, 11
    csrs mstatus, t0
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

    mret

loop:
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
    j loop
