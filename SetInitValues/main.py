import split_sv_mudules 
import subprocess
import generate_hierarchy
import json_add_initval
import vcd_parser
import connect_reginit_vcd_parser
import new_init_folder
from pathlib import Path

def run_svinst(file_path, output_yaml):
    # 使用格式化字符串插入变量
    command = f"./bin/svinst {file_path} > {output_yaml}"
    # 使用 subprocess.run
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    # 检查命令执行结果
    if result.returncode == 0:
        print("[Step2] svinst Command: " + command + " executed successfully")
    else:
        print("Command failed with return code:", result.returncode)
        print("Error output:", result.stderr)
    return result.returncode

if __name__ == "__main__":
    # Step1 --------
    print("[Step1] --------")
    input_file = './SimTop.sv'
    split_sv_mudules.split_sv_modules(input_file)
    # Step2 --------
    print("[Step2] --------")
    output_yaml = './hierarchy_emu.yaml'
    ret_step2 = run_svinst(input_file, output_yaml)
    if ret_step2 != 0:
        exit(ret_step2)
    # Step3 --------
    print("[Step3] --------")
    yaml_file_path = './hierarchy_emu.yaml'
    json_file_path = './hierarchy_emu.json'
    top_module_name = 'SimTop'
    ret_step3 = generate_hierarchy.hierarchy_yaml_parser(yaml_file_path, json_file_path, top_module_name)
    if ret_step3 != 0:
        exit(ret_step3)
    # Step4 --------
    print("[Step4] --------")
    json_file_regs_path = './hierarchy_emu_new.json'
    sv_dir = './SimTop_split'
    json_add_initval.add_regs(json_file_path, json_file_regs_path, sv_dir)
    # Step5 --------
    print("[Step5] --------")
    # 转换VCD的JSON
    vcd_path = "./input.vcd"
    vcd_json_path = "./vcd_parser.json"
    vcd_parser.vcd_to_json(vcd_path, vcd_json_path)
    # Step6 --------
    print("[Step6] --------")
    # python3 connect_reginit_vcd_parser.py
    hierarchy_emu_new = "./hierarchy_emu_new.json"
    vcd_parser_json = "./vcd_parser.json"
    updated_registers_json = "./updated_registers.json"
    connect_reginit_vcd_parser.connect_json_vcd(hierarchy_emu_new, vcd_parser_json, updated_registers_json)
    # Step7 --------
    print("[Step7] --------")
    # python3 new_init_folder.py # 输出 SimTop_Init 文件夹以及SimTop_init.sv文件
    source_dir = Path('SimTop_split')
    target_dir = Path('SimTop_Init')
    json_file_path = 'updated_registers.json'
    merged_file_name = 'SimTop_init.sv'
    new_init_folder.create_init_files(source_dir, target_dir, json_file_path, merged_file_name)