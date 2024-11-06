# 存放一些处理数据用的脚本

## 简而言之
现在的脚本需要提供Chisel编译生成的核心SV文件，并制定Top Module，以及波形文件，然后根据波形文件，生成一个初始化文件，用于重新编译生成新的仿真程序。

### 依赖安装
你需要安装Python的Verilog_VCD，以及下载svinst的二进制并解药到当前目录下的bin文件夹。
#### 安装Verilog_VCD
```bash
    pip install Verilog_VCD
```
#### 安装SVInst

用于生成yaml形式的层次结构，仓库链接[svinst](https://github.com/sgherbst/svinst)

下载二进制包：

```bash
mkdir bin && cd bin
wget https://github.com/sgherbst/svinst/releases/download/v0.1.6/svinst-v0.1.6-x86_64-lnx.zip
unzip svinst-v0.1.6-x86_64-lnx.zip
cd ../
```

### 使用方法
```bash
# 直接运行下述指令即可
python3 main.py ./SimTop.sv SimTop ./input.vcd
# 会在当前目录生成 SimTop_Init 文件夹和 SimTop_init.sv文件
```

## Verilator编译执行

目前直接替换原始的SimTop文件，然后直接`make emu`重新编译即可，需要进一步优化和修改。

需要进一步注意的是，当前重置初始值之后，就不能reset了，否则就无效了。

## Formal相关

如果使用了波形提供的默认值，那么就不用reset重置整个电路的状态了，详见difftest中reset_cycles部分。

需要进一步优化......

## 待办事项

- 自动化reset的编译流程？ 用于调试，但是实际上并用不到，我们跑BMC
- Fuzz找到状态变化后的波形 -> 反馈生成新的BMC验证Files
- 注意1：上述过程除了波形收据前期的生成层次结构等都可以复用
- 记录状态变化的指令序+波形 -> BMC新指令（可能需要assume） ->  新指令的反馈

## FIXME

- 暂不支持二维数组的信号名字的处理
- input名里面有logic声明等之类的情况

## 解耦合的多文件脚本的说明

### 从原始的多个module的SystemVerilog文件分离为多个文件

脚本名：`split_sv_mudules.py`

输入：`SimTop.sv`

输出：`./SimTop_split/*.sv`


```bash
python3 split_sv_mudules.py
```

### 生成层次结构

```bash
./bin/svinst SimTop.sv > hierarchy_emu.yaml
```

能够得到sv文件的层次结构的yaml文件。

### YAML转JSON

为了方便起见，整个项目都需要使用JSON格式。

脚本名：`generate_hierarchy.py`

输入：`hierarchy_emu.yaml`

输出：`hierarchy_emu.json`

```bash
    python3 generate_hierarchy.py
```

### 在原始JSON中加入寄存器列表

原始的JSON文件中没有寄存器列表（reg_list），通过分析源文件，可以获得每个模块的寄存器列表。

脚本名：`json_add_initval.py`

输入：`hierarchy_emu.json`和`分离好的一个模块对应一个sv文件的_split文件夹`

输出：`hierarchy_emu_new.json`

命令：

```bash
    python3 json_add_initval.py
```

### 波形VCD文件转换为JSON(请先安装依赖)

请使用vcd_parser.py将VCD文件转换为JSON文件。

脚本名：`vcd_parser.py`

输入：`VCD波形文件`

输出：`vcd_parser.json`

命令：

```bash
    python3 vcd_parser.py  input.vcd vcd_parser.json
```

注意：直接Verilator生成的VCD存在读取问题的bug，需要经过转换后的vcd波形，可以理解为一种修复。

### 从波形的JSON文件中获得数据并生成含initval的新JSON文件

脚本名：`connect_reginit_vcd_parser.py`

输入：`hierarchy_emu_new.json` 和 `vcd_parser.json`

输出：`updated_registers.json`

命令：

```bash
    python3 connect_reginit_vcd_parser.py
```

该脚本提示的Unmatched Registers的列表应该为空。

### 还原为源文件

脚本名：`new_init_folder.py`

输入：`updated_registers.json`, `SimTop_split 文件夹`

输出：`SimTop_Init 文件夹`以及`SimTop_init.sv`文件

注意：`SimTop_init.sv`文件用于提供给原始仓库的Verilator重新编译生成新的emu仿真程序。

命令：

```bash
    python3 new_init_folder.py
```
