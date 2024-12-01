
.section .bss
    .align 12
physical_memory:
    .skip 4096  # 为物理内存预留一页大小

.section .data
    .align 12
page_table:
    .quad 0x00000000200000ff  # 页表项0: 虚拟地址0映射到物理地址0x1000，权限为X/W/R/V
    # 添加更多页表项...
    .skip 4096 - 8  # 填充剩余空间
    .quad 0x0000000012345678
.section .text
.global _start
_start:
    la t0, error_handler
    la t1, virtual_memory
    csrw mtvec, t0
    csrw mepc, t1
    # 配置satp
    # 设置页表基地址
    la t0, page_table
    # 配置satp寄存器
    li t1, 0x8000000000000000  # Sv39模式
    srli t0, t0, 12            # 页表基地址右移12位
    or t0, t0, t1              # 组合模式和基地址
    csrw satp, t0              # 写入satp寄存器
    # 配置satp结束
    # 清除mstatus寄存器的MPP字段，设置为U态 (00)
    csrr t0, mstatus
    li t1, ~(0x2 << 11)  # MPP字段占用11和12位
    and t0, t0, t1
    li t1, 0xE0000
    or t0, t0, t1
    csrw mstatus, t0
    # 完成MPP字段的重置
    csrr t0, mstatus
    # 由于状态VCD波形的导出当前以mstatus变换为准则 把mstatus值修改放在最后
    # val satp = RegInit(UInt(XLEN.W), "h8000_0000_0008_0002".U)
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
    nop

virtual_memory:
    # 刷新TLB
    sfence.vma
    # 写入虚拟地址0x0
    li t0, 0x2000
    li t1, 43                  # 要写入的值
    lw t3, 0x0(t0)
    sw t1, 0x0(t0)             # 将值写入虚拟地址0x0
    # 读取虚拟地址0x0
    lw t3, 0x0(t0)             # 从虚拟地址0x0读取值
    # 验证读取的值是否正确
    beq t1, t3, success        # 如果值正确，跳转到success
    # 错误处理
    j failure

success:
    # 成功处理
    j success                 # 无限循环表示成功

failure:
    # 失败处理
    j failure                 # 无限循环表示失败

error_handler:
    # 死循环
    nop
    nop
    nop
    slli t1, t0, 2
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
    j error_handler
