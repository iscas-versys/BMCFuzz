# 脚本说明

本文件夹中的脚本用于连接Symbiyosys调用限界模型检测（BMC）进行覆盖点覆盖的尝试。

## cover_rename.py（必要，先执行）

设置好rtl_dir的路径，用于将文件中的cover语句重新按照序号进行命名，并生成待验证任务文件夹。

## cover_run.py（必要，后执行）

设置好sby环境变量的路径，调用Symbiyosys寻找cover点，然后在coverTasks/Hexbin里面生成对应的二进制文件。

## cover2csv.py

输入：`uncovered_points.txt`

输出：`structured_points.csv`

用途：从文本文件中提取出未覆盖点的CSV文件。
## csv2coverNo.py

整体最重要的脚本！！

## hex2asm.py

使用capstone库，将16进制指令转换为汇编代码，但是暂无法生成标准的RISC-V汇编指令，暂不使用。

## print_cover_id.py

使用正则表达式分析文件，输出SystemVerilog文件中的所有cover声明，格式为:[cover_id] module.cover_signal_name。

## template.sby

模板文件，用于生成验证任务的sby文件。

## uncover_analysis.py

未覆盖点的分析，待完善。


## 针对NutShell的注意事项
1. 需要修改SDHelper.v
2. 需要修改MemRwHelp.v -> MemRwHelp.sv
3. 需要修改FBHelper.v
4. 实际上，每次更换SimTop.sv文件即可
4. (很重要)SimTop的module里面要对reset进行提前的规定（initial assume(reset);）