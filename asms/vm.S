.section .data
page_table:
    .quad 0x0000000000000000  # 简单映射的页表项

.section .text
.global _start

_start:
    la t0, loop
    csrw mepc, t0
    # 设置页表基地址寄存器 (satp)
    la a0, page_table
    srli a0, a0, 12          # 页表基地址需要右移12位
    li a1, 0x8000000000000000 # Sv39模式
    or a0, a0, a1
    csrw satp, a0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    # 刷新TLB
    sfence.vma

    # 设置S模式的返回地址
    la a0, supervisor_mode
    csrw mepc, a0

    # 设置mstatus寄存器，启用S模式
    li a0, (1 << 11)         # 设置MPP为S模式
    csrs mstatus, a0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    # 切换到S模式
    mret
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

supervisor_mode:
    # 示例虚拟地址访问
    li a0, 0x0000000000000000 # 虚拟地址
    lw a1, 0(a0)              # 加载数据

    # 结束程序
    li a7, 10
    ecall

loop:
    # 死循环
    j loop
