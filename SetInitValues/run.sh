# 输入SimTop.sv
python3 split_sv_mudules.py
# 输入SimTop.sv
./bin/svinst SimTop.sv > hierarchy_emu.yaml
# 输入hierarchy_emu.yaml
python3 generate_hierarchy.py # 输出 hierarchy_emu.json
# 输入hierarchy_emu.json和_split代码文件夹
python3 json_add_initval.py # 输出 hierarchy_emu_new.json
# 输入波形 vcd2fst和fst2vcd 这两个命令目前执行是没有意义的 需要用GTKWave修复（待定）
vcd2fst ./input.vcd ./output.fst
fst2vcd ./output.fst > ./input2.vcd
# 输入修复后的波形
python3 vcd_parser.py input2.vcd # 输出 vcd_parser.json
# 输入hierarchy_emu_new.json和vcd_parser.json
python3 connect_reginit_vcd_parser.py # 输出 updated_registers.json
# 输入updated_registers.json和_split 文件夹
python3 new_init_folder.py # 输出 SimTop_Init 文件夹以及SimTop_init.sv文件