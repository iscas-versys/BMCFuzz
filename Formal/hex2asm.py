# pip install capstone

from capstone import *

# 创建一个 RISC-V 的反汇编器实例
md = Cs(CS_ARCH_RISCV, CS_MODE_RISCV64)  # 32位模式，可根据需要修改为 CS_MODE_RISCV64

# 二进制指令，可以替换为你要反汇编的 RISC-V 机器码
code = b'\x93\x07\x00\x00'  # addi x15, x0, 0
# 0x143023EB
code = b'\x73\x00\x20\x30'
# 0x30200073
# 反汇编
for i in md.disasm(code, 0x80000000):
    print(f"0x{i.address:x}:\t{i.mnemonic}\t{i.op_str}")
