.section .text
.global _start

_start:
    # 设置mepc寄存器为死循环的地址
    la t0, loop
    csrw mepc, t0
    
    addi t1, t0, 12
    csrw mtvec, t1

    # 清除mstatus寄存器的MPP字段，设置为U态 (00)
    csrr t0, mstatus
    li t1, ~(0x3 << 11)  # MPP字段占用11和12位
    and t0, t0, t1
    csrw mstatus, t0

    # 执行mret以切换到U态
    nop
    nop
    nop
    nop
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
