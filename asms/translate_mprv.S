.section .bss
    .align 12
physical_memory:
    .skip 4096  # Reserve one page for physical memory

.section .data
    .align 12
page_table:
    .quad 0x00000000200000ff  # Page table entry 0: virtual address 0 mapped to physical address 0x1000, permissions X/W/R/V
    # Add more page table entries...
    .skip 4096 - 8  # Pad the remaining space
    .quad 0x0000000012345678

.section .text
.global _start
_start:
    la t0, error_handler
    la t1, virtual_memory
    csrw mtvec, t0
    csrw mepc, t1
    # Configure satp
    # Set page table base address
    la t0, page_table
    # Set satp register
    li t1, 0x8000000000000000  # Sv39 mode
    srli t0, t0, 12            # Right shift page table base address by 12
    or t0, t0, t1              # Combine mode and base address
    csrw satp, t0              # Write to satp register
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
    # End of satp configuration
    # Clear MPP field in mstatus register and set to U-mode (00)
    csrr t0, mstatus
    li t1, ~(0x2 << 11)  # MPP field occupies bits 11 and 12
    and t0, t0, t1
    li t1, 0xE0000
    or t0, t0, t1
    csrw mstatus, t0
    # MPP field reset complete
    csrr t0, mstatus
    # Because VCD waveform export currently uses mstatus changes as the trigger, put mstatus update last
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
