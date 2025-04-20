.section .data
page_table:
    .quad 0x0000000000000000  # Simple mapped page table entry

.section .text
.global _start

_start:
    la t0, loop
    csrw mepc, t0
    # Set the page table base register (satp)
    la a0, page_table
    srli a0, a0, 12           # Page table base address must be shifted right by 12
    li a1, 0x8000000000000000 # Sv39 mode
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

    # Flush the TLB
    sfence.vma

    # Set the return address for S-mode
    la a0, supervisor_mode
    csrw mepc, a0

    # Configure mstatus register to enable S-mode
    li a0, (1 << 11)         # Set MPP to S-mode
    csrs mstatus, a0
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    # Switch to S-mode
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
    # Example virtual address access
    li a0, 0x0000000000000000 # Virtual address
    lw a1, 0(a0)              # Load data

    # Exit program
    li a7, 10
    ecall

loop:
    # Infinite loop
    j loop
