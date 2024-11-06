import split_sv_mudules 
import subprocess
import generate_hierarchy
import json_add_initval
import vcd_parser
import connect_reginit_vcd_parser
import new_init_folder
from pathlib import Path
from sys import argv

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
def generate_newinit_sv_files(default_sv_file, top_module_name, vcd_wave):
    # Value Settings
    hierarchy_yaml = './hierarchy_emu.yaml'
    hierarchy_json = './hierarchy_emu.json'
    hierarchy_json_with_regs = './hierarchy_emu_with_regs.json'
    sv_split_dir = './' + top_module_name + '_split'
    sv_init_dir  = './' + top_module_name + '_Init'
    vcd_json = "./vcd_parser.json"
    updated_registers_json = "./updated_registers.json"
    new_init_file_name = './' + top_module_name + '_init.sv'
    print("[Step1] --------")
    # 分割sv文件
    split_sv_mudules.split_sv_modules(default_sv_file)
    print("[Step2] --------")
    # 生成含有文件层次结构信息的hierarchy.yaml
    ret_step2 = run_svinst(default_sv_file, hierarchy_yaml)
    if ret_step2 != 0:
        exit(ret_step2)
    print("[Step3] --------")
    # 将含有文件层次结构信息的hierarchy.yaml转换为JSON格式
    ret_step3 = generate_hierarchy.hierarchy_yaml_parser(hierarchy_yaml, hierarchy_json, top_module_name)
    if ret_step3 != 0:
        exit(ret_step3)
    print("[Step4] --------")
    # 在JSON文件中添加寄存器初始值字段
    json_add_initval.add_regs(hierarchy_json, hierarchy_json_with_regs, sv_split_dir)
    print("[Step5] --------")
    # 转换VCD到JSON
    vcd_parser.vcd_to_json(vcd_wave, vcd_json)
    print("[Step6] --------")
    # 将寄存器初始值与VCD数据连接
    ret_step6 = connect_reginit_vcd_parser.connect_json_vcd(hierarchy_json_with_regs, vcd_json, updated_registers_json)
    if ret_step6 != 0:
        exit(ret_step6)
    print("[Step7] --------")
    # 生成新的初始化文件和单模块文件目录
    new_init_folder.create_init_files(sv_split_dir, sv_init_dir, updated_registers_json, new_init_file_name)

if __name__ == "__main__":
    # default_sv_file = './SimTop.sv' # 提供该文件作为输入
    # top_module_name = 'SimTop' # 提供该信息
    # vcd_wave = "./input.vcd" # 提供该文件作为输入
    # change to argv to run
    default_sv_file = argv[1]
    top_module_name = argv[2]
    vcd_wave = argv[3]
    if len(argv) != 4:
        print("Usage: python3 main.py <default_sv_file> <top_module_name> <vcd_wave>")
        exit(1)
    generate_newinit_sv_files(default_sv_file, top_module_name, vcd_wave)