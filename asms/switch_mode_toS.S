.section .text
.global _start

_start:
    # 设置mepc寄存器为死循环的地址
    la t0, loop
    csrw mepc, t0

    # 设置mstatus寄存器的MPP字段为S态 (01)
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

    # 执行mret以切换到S态
    mret

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
    j loop
