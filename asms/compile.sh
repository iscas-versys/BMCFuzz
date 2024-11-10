#!/bin/bash

# 遍历当前目录下所有以.S结尾的文件
for asm_file in *.S; do
    # 去掉文件扩展名
    base_name="${asm_file%.S}"
    
    # 编译生成目标文件
    riscv64-linux-gnu-as -o "${base_name}.o" "$asm_file"
    
    # 链接生成ELF文件
    # riscv64-linux-gnu-ld -o "${base_name}.elf" "${base_name}.o"
    riscv64-linux-gnu-ld -T linker.ld -o "${base_name}.elf" "${base_name}.o"
    # riscv64-linux-gnu-ld -T linker.ld -o program.elf program.o
    # 生成BIN文件
    riscv64-linux-gnu-objcopy -O binary "${base_name}.elf" "${base_name}.bin"
    
    # 生成反汇编文件
    riscv64-linux-gnu-objdump -D "${base_name}.elf" > "${base_name}.dump"
    
    echo "Processed $asm_file: Generated ${base_name}.o, ${base_name}.elf, ${base_name}.bin, ${base_name}.dump"
done
