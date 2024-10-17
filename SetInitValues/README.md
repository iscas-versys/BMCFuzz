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

## 波形VCD文件转换为JSON

### 原脚本

脚本名：`vcd_to_json.py`

输入：`test.vcd`

输出：`testvcd.json`

这个脚本暂时废弃了，由于使用的VCD导出的信号存在一定的问题，后续采用了新的Parser进行了尝试。

```bash
### 注意提前安装好依赖项
### from pyDigitalWaveTools.vcd.parser import VcdParser
python3 vcd_to_json.py ./test.vcd > testvcd.json
```

### 修改后的脚本

请使用修改后的VCD_Parser库进行解析，生成新的JSON文件。

## 从波形的JSON文件中获得数据并生成含initval的新JSON文件

### 原脚本

脚本名：`connect_reginit_vcd.py`

输入：`hierarchy_emu_new.json` 和 `testvcd.json`

输出：`updated_hierarchy.json`

这个脚本暂时废弃了，由于使用的VCD导出的信号存在一定的问题，后续采用了新的Parser进行了尝试。

### 修改后的脚本

脚本名：`connect_reginit_vcd_parser.py`

输入：`hierarchy_emu_new.json` 和 `vcd_parser.json`

输出：`updated_registers.json`

## 还原为源文件

## Verilator编译执行

## Formal相关

TBD...
