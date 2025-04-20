.section .text
.global _start

_start:
    la t0, loop
    csrw mepc, t0
    
    addi t1, t0, 12
    csrw mtvec, t1

    csrr t0, mstatus
    li t1, ~(0x3 << 11)  # MPP for bit 11 and 12
    and t0, t0, t1
    csrw mstatus, t0

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
