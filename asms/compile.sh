#!/bin/bash

# Traverse all files ending with .S in the current directory
for asm_file in *.S; do
    # Remove the file extension
    base_name="${asm_file%.S}"
    
    # Assemble to generate object file
    riscv64-linux-gnu-as -o "${base_name}.o" "$asm_file"
    
    # Link to generate ELF file
    # riscv64-linux-gnu-ld -o "${base_name}.elf" "${base_name}.o"
    riscv64-linux-gnu-ld -T linker.ld -o "${base_name}.elf" "${base_name}.o"
    # riscv64-linux-gnu-ld -T linker.ld -o program.elf program.o

    # Generate binary file
    riscv64-linux-gnu-objcopy -O binary "${base_name}.elf" "${base_name}.bin"
    
    # Generate disassembly file
    riscv64-linux-gnu-objdump -D "${base_name}.elf" > "${base_name}.dump"
    
    echo "Processed $asm_file: Generated ${base_name}.o, ${base_name}.elf, ${base_name}.bin, ${base_name}.dump"
done
