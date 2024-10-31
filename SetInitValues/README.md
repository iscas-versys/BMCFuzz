# 存放一些处理数据用的脚本

## FIXME

- 暂不支持二维数组的信号名字的处理
- input名里面有logic声明等之类的情况

## SystemVerilog文件处理

### 从原始的多个module的SystemVerilog文件分离为多个文件

脚本名：`split_sv_mudules.py`

输入：`SimTop.sv`

输出：`./SimTop_split/*.sv`

### 生成层次结构

#### svinst库

用于生成yaml形式的层次结构，仓库链接[svinst](https://github.com/sgherbst/svinst)

下载二进制包：

```bash
mkdir bin && cd bin
wget https://github.com/sgherbst/svinst/releases/download/v0.1.6/svinst-v0.1.6-x86_64-lnx.zip
unzip svinst-v0.1.6-x86_64-lnx.zip
cd ../
./bin/svinst SimTop.sv > hierarchy_emu.yaml
```

能够得到sv文件的层次结构的yaml文件。

#### YAML转JSON

为了方便起见，整个项目都需要使用JSON格式。

脚本名：`generate_hierarchy.py`

输入：`hierarchy_emu.yaml`

输出：`hierarchy_emu.json`

## 在原始JSON中加入寄存器列表

原始的JSON文件中没有寄存器列表（reg_list），通过分析源文件，可以获得每个模块的寄存器列表。

脚本名：`json_add_initval.py`

输入：`hierarchy_emu.json`和`分离好的一个模块对应一个sv文件的_split文件夹`

输出：`hierarchy_emu_new.json`
## 波形转换

波形从VCD转换为VCD不需要脚本，而是需要安装GTKWave 软件包。

```bash
    sudo apt-get install gtkwave
```

安装之后，不仅可以使用gtkwave，还可以使用`vcd2fst`和`fst2vcd`两个关键程序。

### vcd转换为fst
```bash
    vcd2fst input.vcd output.fst
```

### fst转换为vcd
```bash
    fst2vcd output.fst > input2.vcd
```

可以尝试用来回的转换来将波形文件进行修正。

## 波形VCD文件转换为JSON

请使用vcd_parser.py将VCD文件转换为JSON文件。

脚本名：`vcd_parser.py`

输入：`VCD波形文件`

输出：`vcd_parser.json`

注意：直接Verilator生成的VCD存在读取问题的bug，需要经过转换后的vcd波形，可以理解为一种修复。

## 从波形的JSON文件中获得数据并生成含initval的新JSON文件

### 原脚本

脚本名：`connect_reginit_vcd_parser.py`

输入：`hierarchy_emu_new.json` 和 `vcd_parser.json`

输出：`updated_registers.json`

该脚本提示的Unmatched Registers的列表应该为空。

## 还原为源文件

脚本名：`new_init_folder.py`

输入：`updated_registers.json`, `SimTop_split 文件夹`

输出：`SimTop_Init 文件夹`以及`SimTop_init.sv`文件

注意：`SimTop_init.sv`文件用于提供给原始仓库的Verilator重新编译生成新的emu仿真程序。

## Verilator编译执行

目前直接替换原始的SimTop文件，然后直接`make emu`重新编译即可，需要进一步优化和修改。

需要进一步注意的是，当前重置初始值之后，就不能reset了，否则就无效了。

## Formal相关

如果使用了波形提供的默认值，那么就不用reset重置整个电路的状态了，详见difftest中reset_cycles部分。

需要进一步优化......
